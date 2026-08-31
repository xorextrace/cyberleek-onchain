#!/usr/bin/env python3

"""
tally_pump_fees.py

Analyze SOL movements involving Pump.fun creator-fee infrastructure.

This script does NOT blindly treat every balance delta as a fee.
It reports:
  1. explicit System transfers
  2. account balance deltas
  3. Pump.fun instructions present in the transaction

The output is intended for forensic review, not automatic attribution.

Usage:

    python tally_pump_fees.py \
        --data data/round2.json \
        --addresses \
        EJTPHfVBj3NRh1i9hMXVcRKrJwUQcjrBu1Bnt9Hq6x9T \
        G8UKzgPZvJm28NuRVus8X2XtvaMZSGzH8pMuKc5oh1Ew \
        GLf2JhxRfSuDVnRRE7TssRN2LKDvW6Afoqfq3d1c9uCJ \
        6ehREaVX9kKAqwhaAsecpgjSy45xCNjxCgMgwNaud781
"""

import argparse
import glob
import json
from collections import defaultdict


LAMPORTS_PER_SOL = 1_000_000_000

PUMPFUN_PROGRAM = (
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
)

SYSTEM_PROGRAM = "11111111111111111111111111111111"

DUST = 1_000_000  # 0.001 SOL


def load_transactions(pattern, addresses):
    found = {}

    for filename in sorted(glob.glob(pattern)):

        try:
            with open(filename) as f:
                data = json.load(f)

        except (OSError, json.JSONDecodeError):
            continue

        for address in addresses:

            if address not in data:
                continue

            for tx in data[address].get("transactions", []):

                sig = (
                    tx.get("transaction", {})
                    .get("signatures", [None])[0]
                )

                if sig:
                    found[sig] = tx

    return list(found.values())


def account_keys(tx):
    return tx["transaction"]["message"].get("accountKeys", [])


def account_index(tx, address):
    keys = account_keys(tx)

    for i, key in enumerate(keys):

        if isinstance(key, dict):
            if key.get("pubkey") == address:
                return i

        elif key == address:
            return i

    return None


def balance_delta(tx, address):
    """
    Native SOL balance delta for an address.

    Important:
    This is a transaction-level delta, not automatically a fee transfer.
    It can include rent, transaction fees, account creation, etc.
    """

    idx = account_index(tx, address)

    if idx is None:
        return None

    meta = tx.get("meta") or {}

    pre = meta.get("preBalances", [])
    post = meta.get("postBalances", [])

    if idx >= len(pre) or idx >= len(post):
        return None

    return post[idx] - pre[idx]


def iter_instructions(tx):

    message = tx["transaction"]["message"]

    for ix in message.get("instructions", []):
        yield ("outer", None, ix)

    meta = tx.get("meta") or {}

    for group in meta.get("innerInstructions", []):

        parent = group.get("index")

        for ix in group.get("instructions", []):
            yield ("inner", parent, ix)


def explicit_system_transfers(tx):

    transfers = []

    for level, parent, ix in iter_instructions(tx):

        if ix.get("program") != "system":
            continue

        parsed = ix.get("parsed")

        if not isinstance(parsed, dict):
            continue

        if parsed.get("type") != "transfer":
            continue

        info = parsed.get("info", {})

        try:
            lamports = int(info["lamports"])
        except (KeyError, TypeError, ValueError):
            continue

        transfers.append({
            "level": level,
            "parent": parent,
            "source": info.get("source"),
            "destination": info.get("destination"),
            "lamports": lamports,
            "sol": lamports / LAMPORTS_PER_SOL,
        })

    return transfers


def pumpfun_instructions(tx):

    result = []

    for level, parent, ix in iter_instructions(tx):

        pid = ix.get("programId")

        if pid != PUMPFUN_PROGRAM:
            continue

        result.append({
            "level": level,
            "parent": parent,
            "parsed": ix.get("parsed"),
            "accounts": ix.get("accounts"),
            "data": ix.get("data"),
        })

    return result


def main():

    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--data",
        default="data/*.json",
    )

    ap.add_argument(
        "--addresses",
        nargs="+",
        required=True,
    )

    args = ap.parse_args()

    addresses = set(args.addresses)

    txs = load_transactions(
        args.data,
        addresses,
    )

    print(f"Loaded unique transactions: {len(txs)}")

    # ------------------------------------------------------------
    # 1. BALANCE DELTAS
    # ------------------------------------------------------------

    totals = defaultdict(int)

    print("\nBALANCE DELTAS")
    print("==============")

    for tx in txs:

        sig = tx["transaction"]["signatures"][0]
        block_time = tx.get("blockTime")
        slot = tx.get("slot")

        pump_ix = pumpfun_instructions(tx)

        for address in addresses:

            delta = balance_delta(tx, address)

            if delta is None:
                continue

            if abs(delta) <= DUST:
                continue

            totals[address] += delta

            direction = "IN " if delta > 0 else "OUT"

            print(
                f"{slot} | {block_time} | "
                f"{direction} | "
                f"{delta / LAMPORTS_PER_SOL:+.9f} SOL | "
                f"{address[:8]} | "
                f"{sig}"
            )

            if pump_ix:
                print(
                    f"    Pump.fun instructions: {len(pump_ix)}"
                )

    print("\nAGGREGATED BALANCE DELTAS")
    print("=========================")

    for address in sorted(addresses):

        delta = totals[address]

        print(
            f"{address} "
            f"{delta / LAMPORTS_PER_SOL:+.9f} SOL"
        )

    # ------------------------------------------------------------
    # 2. EXPLICIT SYSTEM TRANSFERS
    # ------------------------------------------------------------

    print("\nEXPLICIT SYSTEM TRANSFERS")
    print("=========================")

    system_totals = defaultdict(int)

    for tx in txs:

        sig = tx["transaction"]["signatures"][0]

        for tr in explicit_system_transfers(tx):

            src = tr["source"]
            dst = tr["destination"]

            if src not in addresses and dst not in addresses:
                continue

            lamports = tr["lamports"]

            print(
                f"{sig} | "
                f"{src} -> {dst} | "
                f"{tr['sol']:.9f} SOL"
            )

            if src in addresses:
                system_totals[src] -= lamports

            if dst in addresses:
                system_totals[dst] += lamports

    print("\nSYSTEM TRANSFER TOTALS")
    print("======================")

    for address in sorted(addresses):

        print(
            f"{address} "
            f"{system_totals[address] / LAMPORTS_PER_SOL:+.9f} SOL"
        )

    # ------------------------------------------------------------
    # 3. PUMPFUN TRANSACTIONS
    # ------------------------------------------------------------

    print("\nTRANSACTIONS CONTAINING PUMP.FUN")
    print("================================")

    seen = set()

    for tx in txs:

        sig = tx["transaction"]["signatures"][0]

        if sig in seen:
            continue

        pump_ix = pumpfun_instructions(tx)

        if not pump_ix:
            continue

        seen.add(sig)

        print(
            f"{tx.get('slot')} | "
            f"{tx.get('blockTime')} | "
            f"{sig} | "
            f"pump.fun ix={len(pump_ix)}"
        )

    print("\nDONE.")


if __name__ == "__main__":
    main()
