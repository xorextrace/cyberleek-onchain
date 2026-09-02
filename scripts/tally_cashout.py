#!/usr/bin/env python3
"""
tally_cashout.py — sum the SOL that reaches each cash-out endpoint, counting ONLY
direct transfers that originate from the known cash-out peel-chain wallets.

`trace_cashout.py` surfaces the terminal wallets of the 27 Aug 2026 cash-out;
their exchange labels are read on Solscan (third-party metadata, not an output of
this code). This script then reports how much SOL reached those endpoints.

Honesty rules (why the numbers here are correct and not inflated):

  1. Endpoints such as CCE.Cash (3Afn) and the KuCoin deposit (eS4n) receive
     deposits from the ENTIRE network, not just this cash-out. If you fetched
     those endpoints in full, their dumps contain thousands of unrelated
     transfers. So an endpoint's inflow is counted ONLY when the sender is one of
     the known cash-out peel-chain wallets (CASHOUT_CHAIN below). Everything else
     hitting that endpoint is somebody else's deposit and is ignored.

  2. Shared aggregators (e.g. GPscf) pool unrelated users' funds and forward one
     large lump onward (to a KuCoin hot wallet). That lump is NOT attributed:
     on-chain you cannot separate the CyberLeek portion from third-party funds in
     the same wallet. It is reported separately as "shared / not attributable".

The result is intentionally a lower bound on what is *cleanly* attributable —
which is the honest thing to publish for a fungible asset.

Usage:
    python tally_cashout.py --data "data/cashout.json"
"""
import argparse
import glob
import json

LAMPORTS = 1_000_000_000

ENDPOINTS = {
    "CCE.Cash (deposit)": "3AfnRwXvWxu4HpA6HQQwMzWfP6bETq62oUrwPMfHJ2rH",
    "KuCoin (deposit address)": "eS4n56zrQ4ESznC8mDxQhsY4JoCpEt1jDczgcQ299qW",
    "KuCoin (hot wallet BmFdp)": "BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6",
}

# The four first-level exits from Hok9 on 2026-08-27 (verified amounts).
SEED_OUT = {
    "He8QKFkGkZAKyXnV5xc7KXJLN5cjxxFXXM2JtbBnAUjL": 781.241,
    "BFeK4aW5N5zDPDJy4bHeWwxnSwAj2FyvaMvzdjJ7AUuL": 741.631,
    "Bv6U52fwZtwAAnxod34MqwtXTU4NMSCQTFPqeW3trZGJ": 676.521,
    "8hypa8YWmtyVvSUFzGSWJdPbEteLmxeCNdqGyNz8X3Rh": 505.681,
}

# Every wallet ON the cash-out peel chain (from trace_cashout.py). Only transfers
# whose SENDER is in this set are attributed to an endpoint. Single-purpose relays
# are the ones whose whole outflow is cash-out; the two shared aggregators
# (GPscf, CfHpd5 — they also pool third-party funds) are listed separately so
# their onward lumps are reported as "not attributable", never summed in.
SINGLE_PURPOSE = {
    "He8QKFkGkZAKyXnV5xc7KXJLN5cjxxFXXM2JtbBnAUjL",
    "BFeK4aW5N5zDPDJy4bHeWwxnSwAj2FyvaMvzdjJ7AUuL",
    "Bv6U52fwZtwAAnxod34MqwtXTU4NMSCQTFPqeW3trZGJ",
    "8hypa8YWmtyVvSUFzGSWJdPbEteLmxeCNdqGyNz8X3Rh",
    "7M79fHZ8ZDPfFU6hfn7rqMJQdgSHkZDxQD4Pgzy9HeMu",
    "G2VaQoWRGX2h7CGNfzcbkcFm9xrjWNsWFA4qkhj1GiZu",
    "CoSKZDV8V6mzJkwKZeQx1bp52yHMwQv28u1WaGZwCv59",
    "AZN1ecqeLDeAkALTTzYiu7mbZ5KDgVHszMSrQLvxftny",
    "GokFVhErnWVhyw39yFuLDRezKqLjJJp8Fs7ZkYSzBTK9",
    "HLSU45P2DqDNiVserd1iFzgzv6E2nKjXjbSCzKJSh9RL",
    "HHRZoUMxdWPP2ThsVbVjCJmDw6idP7rP6TUXyiVeMgDH",
    "btYkifQc6VZSkrDHMqYQEKFETHnvc3uAS26SsiAges5",
}
SHARED_AGGREGATORS = {
    "GPscfRmNgRjtv8dLAGcXTmX83AL1eTjXZwtR3BqubkQt",
    "CfHpd5knajdfTSvsfT3woSpvZpqVAHcrJHeDEVcyfWTf",
}


def load_index(data_glob):
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


def edges(by_addr, dust):
    seen, out = set(), []
    for _, txs in by_addr.items():
        for tx in txs:
            sig = tx["transaction"]["signatures"][0]
            for i, info in enumerate(sys_transfers(tx)):
                lam = int(info["lamports"])
                if lam <= dust:
                    continue
                k = (sig, i)
                if k in seen:
                    continue
                seen.add(k)
                out.append((info.get("source"), info.get("destination"), lam / LAMPORTS))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/cashout.json")
    ap.add_argument("--dust", type=float, default=0.001)
    args = ap.parse_args()

    by_addr = load_index(args.data)
    if not by_addr:
        raise SystemExit(f"no dumps found at {args.data}")

    dust = int(args.dust * LAMPORTS)
    addr2label = {v: k for k, v in ENDPOINTS.items()}
    endpoint_addrs = set(ENDPOINTS.values())

    attr = {l: [0.0, 0] for l in ENDPOINTS}     # from single-purpose relays
    shar = {l: [0.0, 0] for l in ENDPOINTS}     # from shared aggregators

    for src, dst, sol in edges(by_addr, dust):
        if dst not in endpoint_addrs:
            continue
        label = addr2label[dst]
        if src in SINGLE_PURPOSE:
            attr[label][0] += sol
            attr[label][1] += 1
        elif src in SHARED_AGGREGATORS:
            shar[label][0] += sol
            shar[label][1] += 1
        # senders outside the cash-out chain (other people's deposits) are ignored

    total_out = sum(SEED_OUT.values())
    print("===== CASH-OUT TALLY (SOL) =====")
    print(f"Total out of Hok9 (4 first-level exits): {total_out:.2f} SOL")
    print("Counting ONLY transfers whose sender is a known cash-out relay.\n")

    print("Directly attributable (single-purpose relays -> endpoint):")
    reached = 0.0
    for label in ENDPOINTS:
        reached += attr[label][0]
        print(f"  {attr[label][0]:9.2f} SOL  ({attr[label][1]:2d} tx)  ->  {label}")

    if any(shar[l][0] > 0 for l in ENDPOINTS):
        print("\nVia shared aggregators — NOT attributable "
              "(lump mixed with third-party funds; CyberLeek share is smaller):")
        for label in ENDPOINTS:
            if shar[label][0] > 0:
                print(f"  {shar[label][0]:9.2f} SOL  ({shar[label][1]:2d} tx)  ->  {label}")

    print(f"\nCleanly attributed to endpoints: {reached:.2f} / {total_out:.2f} SOL")
    print("The remainder is in transit through fresh relays, inside shared-"
          "aggregator lumps (not cleanly separable on-chain), or in dust. Figures "
          "are approximate; the cash-out was still in progress at capture (report S14b).")
    print("\nEndpoint labels are third-party Solscan metadata, verified manually "
          "-- not derived by this code.")


if __name__ == "__main__":
    main()
