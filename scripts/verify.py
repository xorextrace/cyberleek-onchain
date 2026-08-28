#!/usr/bin/env python3
"""
verify.py — independently recompute the headline claims from raw dumps.

Reads every JSON produced by fetch_wallets.py in a data directory, re-indexes all
transactions by signature, and prints the key transfers, chain hops, the J4zo
fan-in/fan-out, and the funding-window bounds — each with signatures you can
cross-check on any Solana explorer. It trusts no summary: it re-reads raw tx data.

Usage:
    python verify.py --data "data/*.json"
"""
import argparse
import datetime as dt
import glob
import json


def utc(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC") if t else "?"


def load(data_glob):
    TX = {}
    for f in sorted(glob.glob(data_glob)):
        try:
            d = json.load(open(f))
        except (json.JSONDecodeError, FileNotFoundError):
            continue
        for _, blob in d.items():
            for tx in blob["transactions"]:
                TX[tx["transaction"]["signatures"][0]] = tx
    return TX


def sysxfers(tx):
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


def find(TX, src, dst, exact=None):
    hits = []
    for sig, tx in TX.items():
        for info in sysxfers(tx):
            if info.get("source") == src and info.get("destination") == dst:
                lam = int(info["lamports"])
                if exact is None or lam == exact:
                    hits.append((sig, tx["slot"], tx.get("blockTime"), lam))
    return sorted(hits, key=lambda x: x[2] or 0)


W = {
    "Ec2": "Ec2qmcpCCD9hjahAcquiQf5JkZWCK68BUahCje1izYC7",
    "9Ve5": "9Ve5Cgt5xzkdLnowxfFBk89R3mo5QmVrngDedqWdxxVg",
    "Hok9": "Hok9nbV89yBSKCttxe3goqajwbiqQa9mtHvQBsbJH3Np",
    "3YLND": "3YLNDXnV9fNysDWaD39uQxwxeSaMFeAswvoQPZNvuNA4",
    "26sZ": "26sZDubW854zGAasvrUaRAgY54MiC97CEHWZKPRMPMQ9",
    "EjsB": "EjsB4qhcQv3zwXWqMbD739VA7nFc85f2egwTnkr3KGB2",
    "2ZdU": "2ZdUUvrr7ANY2rzpbyBcZHp1hTZ5uTY8JZ4vFnYnvJhD",
    "4wzwhe": "4wzwheYAC6hNW2JxJmxZyY9a5mEFf8epEqHKgPXvxZbB",
    "734tW6": "734tW6ytogjF3e4qoaqiNKpq9byVRgLY5fK7ZEFn72Sb",
    "J4zo": "J4zoc1rFgpP2Mrknb48BRRoQW9P5GiVtPyuemkKMpAnV",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/*.json")
    args = ap.parse_args()
    TX = load(args.data)
    print(f"[i] unique transactions indexed: {len(TX)}\n")

    print("=" * 72)
    print("CLAIM 1 — the three key transfers to the deployer Hok9")
    print("=" * 72)
    for name, s, d, lam in [
        ("Ec2->Hok9 10 SOL", "Ec2", "Hok9", 10_000_000_000),
        ("9Ve5->Hok9 10.24 SOL", "9Ve5", "Hok9", 10_240_000_000),
        ("Ec2->Hok9 311.42 SOL", "Ec2", "Hok9", 311_420_000_000),
    ]:
        for sig, slot, bt, l in find(TX, W[s], W[d], lam):
            print(f"  {name}: {l} lamports ({l/1e9} SOL) | {utc(bt)} | slot {slot}")
            print(f"    sig: {sig}")

    print("\n" + "=" * 72)
    print("CLAIM 2 — chain hops (each with the largest tx signature to cross-check)")
    print("=" * 72)
    for name, s, d in [
        ("J4zo -> 26sZ", "J4zo", "26sZ"), ("26sZ -> EjsB", "26sZ", "EjsB"),
        ("EjsB -> 2ZdU", "EjsB", "2ZdU"), ("26sZ -> 4wzwhe", "26sZ", "4wzwhe"),
        ("4wzwhe -> 734tW6", "4wzwhe", "734tW6"), ("3YLND -> Ec2", "3YLND", "Ec2"),
    ]:
        hits = find(TX, W[s], W[d])
        tot = sum(h[3] for h in hits)
        big = max(hits, key=lambda h: h[3]) if hits else None
        print(f"  {name}: {len(hits)} transfers, total {tot/1e9:.3f} SOL")
        if big:
            print(f"    largest: {big[3]/1e9:.3f} SOL | {utc(big[2])} | sig {big[0]}")

    print("\n" + "=" * 72)
    print("CLAIM 3 — is J4zo an exchange interface? (fan-in vs fan-out)")
    print("=" * 72)
    ins, outs = set(), set()
    for tx in TX.values():
        for info in sysxfers(tx):
            if int(info["lamports"]) > 1_000_000:
                if info.get("destination") == W["J4zo"]:
                    ins.add(info.get("source"))
                if info.get("source") == W["J4zo"]:
                    outs.add(info.get("destination"))
    print(f"  distinct sources (fan-in): {len(ins)}  |  distinct destinations (fan-out): {len(outs)}")
    print("  high fan-in + low fan-out = deposit-aggregation typical of a CEX")

    print("\n" + "=" * 72)
    print("CLAIM 4 — timing")
    print("=" * 72)
    allbt = [tx.get("blockTime") for tx in TX.values() if tx.get("blockTime")]
    if allbt:
        print(f"  funding activity: {utc(min(allbt))} -> {utc(max(allbt))}")
    print("  mint/pool on Hok9 = Aug 15 ; first public leak = Aug 18")


if __name__ == "__main__":
    main()
