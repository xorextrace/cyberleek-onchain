#!/usr/bin/env python3
"""
trace_cashout.py — follow the 27 Aug 2026 cash-out peel chain from raw dumps.

Starting from the deployer's four first-level cash-out wallets (the SEEDS below),
this walks the SOL outflows hop by hop through the peel chain of fresh
single-purpose wallets and stops when a wallet looks like an endpoint:

  * high fan-in (many distinct sources)      -> exchange-grade interface
  * interacts with a non-System program      -> possible swap/other service
  * no outflow                               -> funds sitting there

For every wallet it prints tx count, fan-in, fan-out and the largest onward
destinations, so you can open the terminal endpoints on an explorer and read
their entity label yourself.

IMPORTANT — how the endpoints were identified in the report:
    This script does NOT assign exchange names. In the published analysis the
    terminal wallets it surfaces were then opened on Solscan and their entity
    labels were read manually:
        3AfnRwXvWxu4HpA6HQQwMzWfP6bETq62oUrwPMfHJ2rH  -> "CCE.Cash: Exchange Deposit Wallet"
        eS4n56zrQ4ESznC8mDxQhsY4JoCpEt1jDczgcQ299qW   -> "#Kucoin Exchange / #Deposit Address"
        BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6   -> "KuCoin Hot Wallet (BmFdp)"
    Those labels are third-party explorer metadata, not an output of this code.

This reads dumps produced by fetch_wallets.py (same format as verify.py). To
regenerate the needed dumps first, see the command in the repo README / report
(fetch the four L1 wallets and the wallets this script surfaces, over a window
that includes 27 Aug 2026).

Usage:
    python trace_cashout.py --data "data/*.json"
    python trace_cashout.py --data "data/*.json" --min-sol 10 --max-depth 6
"""
import argparse
import collections
import glob
import json

LAMPORTS = 1_000_000_000

# First-level wallets that received the four exits from the deployer Hok9
# on 2026-08-27 07:29-07:32 UTC (verified in the report, §14b).
SEEDS = [
    "He8QKFkGkZAKyXnV5xc7KXJLN5cjxxFXXM2JtbBnAUjL",
    "BFeK4aW5N5zDPDJy4bHeWwxnSwAj2FyvaMvzdjJ7AUuL",
    "Bv6U52fwZtwAAnxod34MqwtXTU4NMSCQTFPqeW3trZGJ",
    "8hypa8YWmtyVvSUFzGSWJdPbEteLmxeCNdqGyNz8X3Rh",
]

# System / ComputeBudget are ignored when checking for "interacts with a program".
BENIGN = {
    "11111111111111111111111111111111",
    "ComputeBudget111111111111111111111111111111",
}


def load_index(data_glob):
    """Index every fetched wallet's transactions by address."""
    by_addr = {}
    for f in sorted(glob.glob(data_glob)):
        try:
            d = json.load(open(f))
        except (json.JSONDecodeError, FileNotFoundError):
            continue
        for addr, blob in d.items():
            by_addr.setdefault(addr, blob["transactions"])
    return by_addr


def sys_transfers(tx):
    out = []
    meta = tx["meta"]
    groups = [tx["transaction"]["message"].get("instructions", [])]
    groups += [i["instructions"] for i in meta.get("innerInstructions", [])]
    for ins in groups:
        for ix in ins:
            p = ix.get("parsed")
            if isinstance(p, dict) and p.get("type") == "transfer" and ix.get("program") == "system":
                out.append(p["info"])
    return out


def profile(addr, txs, dust):
    """Return (n_tx, fan_in, {dest: sol}, {nonbenign_programs})."""
    src, dst, progs = set(), {}, set()
    for tx in txs:
        for ix in tx["transaction"]["message"].get("instructions", []):
            pid = ix.get("programId", "")
            if pid and pid not in BENIGN:
                progs.add(pid)
        for info in sys_transfers(tx):
            lam = int(info["lamports"])
            if lam <= dust:
                continue
            if info.get("destination") == addr:
                src.add(info.get("source"))
            if info.get("source") == addr:
                dst[info["destination"]] = dst.get(info["destination"], 0) + lam / LAMPORTS
    return len(txs), len(src), dst, progs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/*.json")
    ap.add_argument("--min-sol", type=float, default=10.0,
                    help="only follow onward branches at least this large")
    ap.add_argument("--max-depth", type=int, default=6)
    ap.add_argument("--exchange-fanin", type=int, default=100,
                    help="fan-in at or above this is treated as an exchange endpoint")
    args = ap.parse_args()

    by_addr = load_index(args.data)
    if not by_addr:
        raise SystemExit(f"no dumps found at {args.data}")

    dust = 1_000_000
    seen = set()
    frontier = list(SEEDS)
    depth = 0
    missing = []

    while frontier and depth < args.max_depth:
        depth += 1
        nxt = []
        print(f"\n===== LEVEL {depth} =====")
        for a in frontier:
            if a in seen:
                continue
            seen.add(a)
            if a not in by_addr:
                missing.append(a)
                print(f"{a[:8]}.. (not in dumps — fetch this wallet to continue)")
                continue
            n_tx, fan_in, dst, progs = profile(a, by_addr[a], dust)
            note = ""
            if fan_in >= args.exchange_fanin:
                note = "  <== EXCHANGE-GRADE endpoint (high fan-in) — open on Solscan to read label"
            elif progs:
                note = f"  <== interacts with program(s) {list(progs)[:2]} — inspect on Solscan"
            elif not dst:
                note = "  <== funds sitting here (no outflow)"
            print(f"{a[:8]}.. tx={n_tx} fan-in={fan_in} fan-out={len(dst)}{note}")
            for d2, amt in sorted(dst.items(), key=lambda x: -x[1])[:4]:
                print(f"      {amt:9.2f} SOL -> {d2}")
                if fan_in < args.exchange_fanin and not progs and amt >= args.min_sol:
                    nxt.append(d2)
        frontier = nxt

    if missing:
        print("\n[!] wallets referenced but not present in the dumps "
              "(fetch them to extend the trace):")
        for a in missing:
            print(f"    {a}")
    print("\nDone. Open any terminal endpoint on https://solscan.io/account/<address> "
          "to read its exchange label.")


if __name__ == "__main__":
    main()
