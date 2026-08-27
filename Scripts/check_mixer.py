#!/usr/bin/env python3
"""
check_mixer.py — test whether a hub is a traceable disperser or an obfuscation
service (mixer / private-swap).

Two independent tests for a target wallet:
  1) Program profile — which Solana programs its transactions invoke. Only
     System / ComputeBudget / SPL-Token / Memo means plain transfers (consistent
     with a CEX/disperser). A recurring UNKNOWN program is a candidate mixing
     contract.
  2) Amount/timing reconciliation — how many outflows match an earlier inflow by
     amount (within 1%) and time order. ~100% => traceable pass-through.
     ~0% => funds were remixed (obfuscation).

Usage:
    python check_mixer.py --data "data/*.json" --target 26sZDubW854zGAasvrUaRAgY54MiC97CEHWZKPRMPMQ9
"""
import argparse
import collections
import glob
import json

DUST = 1_000_000

KNOWN_PROGRAMS = {
    "11111111111111111111111111111111": "System (SOL transfer)",
    "ComputeBudget111111111111111111111111111111": "ComputeBudget",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": "SPL-Token",
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb": "Token-2022",
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL": "ATA",
    "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr": "Memo (CEX deposit tag)",
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium-AMMv4",
    "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C": "Raydium-CPMM",
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": "Raydium-CLMM",
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P": "pump.fun",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter",
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": "Meteora-DLMM",
}


def load(data_glob, target):
    for f in sorted(glob.glob(data_glob)):
        try:
            d = json.load(open(f))
        except (json.JSONDecodeError, FileNotFoundError):
            continue
        if target in d:
            return d[target]["transactions"]
    return None


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


def program_profile(txs):
    c = collections.Counter()
    for tx in txs:
        groups = [tx["transaction"]["message"].get("instructions", [])]
        groups += [i["instructions"] for i in tx["meta"].get("innerInstructions", [])]
        for ins in groups:
            for ix in ins:
                pid = ix.get("programId", "?")
                c[pid] += 1
    print("PROGRAM PROFILE:")
    unknown = False
    for pid, n in c.most_common():
        tag = KNOWN_PROGRAMS.get(pid)
        if tag is None:
            tag = "*** UNKNOWN (possible service/contract) ***"
            unknown = True
        print(f"  {n:6d}x  {tag:35s} {pid}")
    print("  => " + ("UNKNOWN program present — inspect it." if unknown
                     else "only benign programs — no mixing contract."))


def reconciliation(txs, target):
    ins, outs = [], []
    for tx in txs:
        bt = tx.get("blockTime")
        for info in sysxfers(tx):
            lam = int(info["lamports"])
            if lam <= DUST:
                continue
            if info.get("destination") == target:
                ins.append((bt, lam / 1e9))
            if info.get("source") == target:
                outs.append((bt, lam / 1e9))
    matched = 0
    for bt_o, amt_o in outs:
        for bt_i, amt_i in ins:
            if bt_i is not None and bt_o is not None and bt_i <= bt_o and abs(amt_i - amt_o) / amt_o < 0.01:
                matched += 1
                break
    print("\nRECONCILIATION:")
    print(f"  inflows>0.001: {len(ins)} ({sum(a for _, a in ins):.2f} SOL) | "
          f"outflows>0.001: {len(outs)} ({sum(a for _, a in outs):.2f} SOL)")
    if outs:
        pct = 100 * matched / len(outs)
        print(f"  outflows reconciled with a prior inflow: {matched}/{len(outs)} ({pct:.0f}%)")
        print("  => " + ("traceable pass-through (no mixing)." if pct >= 80
                         else "low reconciliation — possible obfuscation."))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/*.json")
    ap.add_argument("--target", required=True)
    args = ap.parse_args()
    txs = load(args.data, args.target)
    if txs is None:
        raise SystemExit(f"target {args.target} not found in {args.data}")
    print(f"target {args.target} — {len(txs)} tx\n")
    program_profile(txs)
    reconciliation(txs, args.target)


if __name__ == "__main__":
    main()
