#!/usr/bin/env python3

import json
import sys
from datetime import datetime, timezone


def utc(ts):
    if ts is None:
        return "?"

    return datetime.fromtimestamp(
        ts,
        timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S UTC")


def key_to_str(key):
    if isinstance(key, str):
        return key

    if isinstance(key, dict):
        return key.get("pubkey", "?")

    return str(key)


def main():

    if len(sys.argv) != 3:
        print(
            f"usage: {sys.argv[0]} FILE ADDRESS"
        )
        sys.exit(1)

    filename = sys.argv[1]
    address = sys.argv[2]

    with open(filename) as f:
        data = json.load(f)

    txs = data[address]["transactions"]

    for tx in sorted(
        txs,
        key=lambda x: (
            x.get("blockTime") or 0,
            x.get("slot") or 0,
        )
    ):

        meta = tx.get("meta") or {}
        msg = tx["transaction"]["message"]

        keys = [
            key_to_str(k)
            for k in msg.get("accountKeys", [])
        ]

        if address not in keys:
            continue

        idx = keys.index(address)

        pre = meta.get("preBalances", [])
        post = meta.get("postBalances", [])

        if idx >= len(pre) or idx >= len(post):
            continue

        delta = (
            post[idx] - pre[idx]
        ) / 1_000_000_000

        # Mostriamo solo movimenti significativi
        if abs(delta) < 0.01:
            continue

        sig = tx["transaction"]["signatures"][0]

        print("=" * 100)
        print("TIME :", utc(tx.get("blockTime")))
        print("SLOT :", tx.get("slot"))
        print("SIG  :", sig)
        print("DELTA:", f"{delta:+.9f} SOL")

        print()
        print("TOP LEVEL INSTRUCTIONS")

        for i, ix in enumerate(
            msg.get("instructions", [])
        ):
            program = ix.get("programId", "?")

            print(
                f"  [{i}] {program}"
            )

        print()
        print("LOGS")

        for log in (
            meta.get("logMessages") or []
        ):
            print(
                " ",
                log
            )

        print()
        print("ACCOUNT BALANCE CHANGES")

        for i, (p, q) in enumerate(
            zip(pre, post)
        ):

            d = (
                q - p
            ) / 1_000_000_000

            if abs(d) >= 0.01:

                print(
                    f"  {keys[i] if i < len(keys) else '?'} "
                    f"{d:+.9f} SOL"
                )


if __name__ == "__main__":
    main()