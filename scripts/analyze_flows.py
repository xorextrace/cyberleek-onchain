#!/usr/bin/env python3
"""
analyze_flows.py — characterize a wallet's SOL flows from raw dumps.

For a target address it prints: activity window, net inflow/outflow, distinct
fan-in/fan-out counts, and the top inflow sources / outflow destinations (dust
excluded). With --external it instead lists, across ALL fetched wallets, the
external injectors — addresses that pay INTO the fetched cluster but that no
fetched wallet funds — i.e. the mesh edges worth fetching next.

Usage:
    python analyze_flows.py --data "data/*.json" --target J4zoc1rFgpP2Mrknb48BRRoQW9P5GiVtPyuemkKMpAnV
    python analyze_flows.py --data "data/*.json" --external
"""
import argparse
import datetime as dt
import glob
import json

DUST = 1_000_000


def utc(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d %H:%M") if t else "?"


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


def load(data_glob):
    stores = []
    for f in sorted(glob.glob(data_glob)):
        try:
            stores.append(json.load(open(f)))
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    known = set()
    for s in stores:
        known |= set(s.keys())
    return stores, known


def analyze_target(stores, target):
    ins, outs = {}, {}
    tin = tout = 0
    bts = []
    for s in stores:
        for addr, blob in s.items():
            for tx in blob["transactions"]:
                if tx.get("blockTime"):
                    bts.append(tx["blockTime"])
                for info in sysxfers(tx):
                    lam = int(info["lamports"])
                    if lam <= DUST:
                        continue
                    if info.get("destination") == target:
                        ins[info["source"]] = ins.get(info["source"], 0) + lam
                        tin += lam
                    if info.get("source") == target:
                        outs[info["destination"]] = outs.get(info["destination"], 0) + lam
                        tout += lam
    tgt_bts = [b for s in stores if target in s for tx in s[target]["transactions"]
               if (b := tx.get("blockTime"))]
    print(f"target {target}")
    if tgt_bts:
        print(f"  window {utc(min(tgt_bts))} -> {utc(max(tgt_bts))} | {len(tgt_bts)} tx")
    print(f"  fan-in {len(ins)} sources, {tin/1e9:.2f} SOL | fan-out {len(outs)} dests, {tout/1e9:.2f} SOL")
    print("  TOP INFLOWS:")
    for a, l in sorted(ins.items(), key=lambda x: -x[1])[:10]:
        print(f"    {l/1e9:11.3f} SOL <- {a}")
    print("  TOP OUTFLOWS:")
    for a, l in sorted(outs.items(), key=lambda x: -x[1])[:10]:
        print(f"    {l/1e9:11.3f} SOL -> {a}")


def analyze_external(stores, known):
    ext, hits = {}, {}
    for s in stores:
        for addr, blob in s.items():
            for tx in blob["transactions"]:
                for info in sysxfers(tx):
                    lam = int(info["lamports"])
                    src, dst = info.get("source"), info.get("destination")
                    if dst in known and src not in known and lam > 10 * DUST:
                        ext[src] = ext.get(src, 0) + lam
                        hits[src] = hits.get(src, 0) + 1
    print(f"cluster wallets fetched: {len(known)}")
    print("EXTERNAL INJECTORS (pay INTO the cluster, not funded BY it) — mesh edges:")
    for a, l in sorted(ext.items(), key=lambda x: -x[1])[:20]:
        print(f"  {l/1e9:10.2f} SOL x{hits[a]:2d} <- {a}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/*.json")
    ap.add_argument("--target", help="address to characterize")
    ap.add_argument("--external", action="store_true", help="list external injectors instead")
    args = ap.parse_args()
    stores, known = load(args.data)
    if args.external:
        analyze_external(stores, known)
    elif args.target:
        analyze_target(stores, args.target)
    else:
        ap.error("provide --target ADDRESS or --external")


if __name__ == "__main__":
    main()
