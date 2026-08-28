#!/usr/bin/env python3
"""
fetch_wallets.py — pull raw Solana transaction history for a set of wallets.

Reads JSON-RPC data (getSignaturesForAddress + getTransaction, jsonParsed) and
writes a single JSON file with, per address, its signatures and full transactions.
Designed to be re-run round by round while walking a funding trail backwards.

Requirements: pip install requests
RPC endpoint: set SOLANA_RPC (a JSON-RPC URL). A key-gated endpoint (e.g. Helius)
is strongly recommended — the public mainnet-beta RPC is heavily rate-limited and
may not retain full history.

Usage:
    export SOLANA_RPC="https://mainnet.helius-rpc.com/?api-key=YOUR_KEY"
    python fetch_wallets.py \
        --addresses J4zoc1rFgpP2Mrknb48BRRoQW9P5GiVtPyuemkKMpAnV \
        --start 2025-06-01 --end 2026-08-21 \
        --out data/round.json

    # or read addresses (one per line, '#' comments allowed) from a file:
    python fetch_wallets.py --addresses-file wallets.txt --out data/round.json

Notes:
    * Retries with exponential backoff on HTTP 429/5xx (honours Retry-After).
    * Saves incrementally after each address, so an interrupted run keeps
      whatever completed.
    * Prints a crude "exchange signature" (distinct outbound destinations) per
      address: a hot/withdrawal wallet of an exchange typically has hundreds+.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time

import requests

DUST_LAMPORTS = 1_000_000  # ignore sub-0.001 SOL when counting fan-out


def parse_date(s: str) -> float:
    return dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()


def rpc(session, url, method, params, max_retries=8):
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    delay = 1.0
    for _ in range(max_retries):
        try:
            r = session.post(url, json=body, timeout=60)
        except requests.RequestException:
            time.sleep(delay)
            delay = min(delay * 2, 30)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            ra = r.headers.get("Retry-After")
            time.sleep(float(ra) if ra else delay)
            delay = min(delay * 2, 30)
            continue
        r.raise_for_status()
        j = r.json()
        if "error" in j:
            time.sleep(delay)
            delay = min(delay * 2, 30)
            continue
        return j["result"]
    raise RuntimeError(f"giving up on {method}")


def sigs_in_window(session, url, addr, start, end, max_sigs, pause):
    kept, before, scanned = [], None, 0
    while True:
        opts = {"limit": 1000}
        if before:
            opts["before"] = before
        batch = rpc(session, url, "getSignaturesForAddress", [addr, opts])
        if not batch:
            break
        for s in batch:
            scanned += 1
            bt = s.get("blockTime")
            if bt is None:
                kept.append(s)
                continue
            if bt > end:
                continue
            if bt < start:
                return kept, scanned
            kept.append(s)
            if len(kept) >= max_sigs:
                print(f"   !! MAX_SIGS hit for {addr[:6]} — narrow the window", flush=True)
                return kept, scanned
        before = batch[-1]["signature"]
        if len(batch) < 1000:
            break
        time.sleep(pause)
    return kept, scanned


def outbound_fanout(txs, addr):
    dests = set()
    for tx in txs:
        meta = tx["meta"]
        groups = [tx["transaction"]["message"].get("instructions", [])]
        groups += [i["instructions"] for i in meta.get("innerInstructions", [])]
        for ins in groups:
            for ix in ins:
                p = ix.get("parsed")
                if isinstance(p, dict) and p.get("type") == "transfer" and ix.get("program") == "system":
                    info = p["info"]
                    if info.get("source") == addr and int(info["lamports"]) > DUST_LAMPORTS:
                        dests.add(info.get("destination"))
    return len(dests)


def main():
    ap = argparse.ArgumentParser(description="Fetch raw Solana tx history for wallets.")
    ap.add_argument("--addresses", nargs="*", default=[], help="wallet addresses")
    ap.add_argument("--addresses-file", help="file with one address per line (# comments ok)")
    ap.add_argument("--start", default="2025-01-01", help="window start YYYY-MM-DD (UTC)")
    ap.add_argument("--end", default="2030-01-01", help="window end YYYY-MM-DD (UTC)")
    ap.add_argument("--out", default="data/round.json", help="output JSON path")
    ap.add_argument("--max-sigs", type=int, default=12000, help="per-wallet signature cap")
    ap.add_argument("--pause", type=float, default=0.15, help="seconds between RPC calls")
    args = ap.parse_args()

    url = os.environ.get("SOLANA_RPC")
    if not url:
        sys.exit("ERROR: set SOLANA_RPC to a JSON-RPC endpoint URL.")

    addresses = list(args.addresses)
    if args.addresses_file:
        for line in open(args.addresses_file):
            line = line.split("#", 1)[0].strip()
            if line:
                addresses.append(line)
    if not addresses:
        sys.exit("ERROR: provide --addresses or --addresses-file.")

    start, end = parse_date(args.start), parse_date(args.end)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    session = requests.Session()

    out = {}
    for addr in addresses:
        print("fetch", addr, flush=True)
        sigs, scanned = sigs_in_window(session, url, addr, start, end, args.max_sigs, args.pause)
        print(f"   in-window: {len(sigs)} (scanned {scanned})", flush=True)
        txs = []
        for i, s in enumerate(sigs):
            tx = rpc(session, url, "getTransaction",
                     [s["signature"], {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}])
            if tx:
                txs.append(tx)
            if i % 100 == 0:
                print(f"    {addr[:4]} {i}/{len(sigs)}", flush=True)
            time.sleep(args.pause)
        out[addr] = {"signatures": sigs, "transactions": txs}
        json.dump(out, open(args.out, "w"))
        nd = outbound_fanout(txs, addr)
        flag = "  <-- possible CEX withdrawal wallet" if nd >= 100 else ""
        print(f"   saved | outbound distinct destinations: {nd}{flag}", flush=True)

    print("DONE:", {a[:6]: len(v["transactions"]) for a, v in out.items()})


if __name__ == "__main__":
    main()
