#!/usr/bin/env python3

"""
recon_token.py — reconstruct a Solana mint's genesis transaction.

Finds the ACTUAL mint-initialization transaction by paginating
getSignaturesForAddress and inspecting instructions for
initializeMint / initializeMint2 — rather than assuming the oldest
transaction in the first 1000 signatures is the genesis (that bug
mis-reported a false creation on high-volume mints).

Usage:
    export SOLANA_RPC="https://mainnet.helius-rpc.com/?api-key=..."
    python recon_token.py <MINT>
"""

import os
import sys
import time
import datetime
import requests

RPC = os.environ["SOLANA_RPC"]

GENESIS_TYPES = {
    "initializeMint",
    "initializeMint2",
}


def rpc(method, params, tries=8):
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }

    delay = 1.0

    for _ in range(tries):
        try:
            r = requests.post(RPC, json=body, timeout=60)

            if r.status_code in (429, 500, 502, 503, 504):
                retry_after = r.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else delay)
                delay = min(delay * 2, 30)
                continue

            r.raise_for_status()

            j = r.json()

            if "error" in j:
                print("RPC error:", j["error"], file=sys.stderr)
                time.sleep(delay)
                delay = min(delay * 2, 30)
                continue

            return j["result"]

        except requests.RequestException as e:
            print("HTTP error:", e, file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 2, 30)

    raise RuntimeError(f"RPC failed: {method}")


def utc(timestamp):
    if timestamp is None:
        return "?"

    return datetime.datetime.fromtimestamp(
        timestamp,
        datetime.timezone.utc,
    ).strftime("%Y-%m-%d %H:%M:%S UTC")


def get_transaction(signature):
    return rpc(
        "getTransaction",
        [
            signature,
            {
                "encoding": "jsonParsed",
                "maxSupportedTransactionVersion": 0,
            },
        ],
    )


def get_mint_info(mint):
    acc = rpc("getAccountInfo", [mint, {"encoding": "jsonParsed"}])

    value = acc.get("value")

    if not value:
        raise RuntimeError("Mint account not found")

    data = value.get("data")

    if not isinstance(data, dict):
        print("Mint data is not jsonParsed")
        return

    info = data.get("parsed", {}).get("info", {})

    print("\nMINT STATE")
    print("----------")
    print("mintAuthority:", info.get("mintAuthority"))
    print("freezeAuthority:", info.get("freezeAuthority"))
    print("supply:", info.get("supply"))
    print("decimals:", info.get("decimals"))


def iter_signatures_oldest_first(mint):
    """
    Yield signature entries from OLDEST to NEWEST, one page at a time.

    getSignaturesForAddress returns newest -> oldest, so we page all the
    way back, then hand pages out in reverse. Pages are yielded lazily so
    the caller can stop as soon as it finds the genesis, without holding
    the entire history (which can be > 100k signatures) or fetching a
    single transaction more than necessary.
    """

    pages = []
    before = None
    page = 0
    total = 0

    while True:
        opts = {"limit": 1000}
        if before:
            opts["before"] = before

        batch = rpc("getSignaturesForAddress", [mint, opts])

        if not batch:
            break

        page += 1
        total += len(batch)
        print(f"  page {page}: {len(batch)} signatures (total {total})",
              flush=True)

        pages.append(batch)
        before = batch[-1]["signature"]

        if len(batch) < 1000:
            break

        time.sleep(0.15)

    # Oldest is the last entry of the last page; walk pages/entries backwards.
    for batch in reversed(pages):
        for item in reversed(batch):
            yield item


def iter_instructions(tx):
    """Yield both top-level and inner instructions."""
    message = tx["transaction"]["message"]

    for ix in message.get("instructions", []):
        yield ix

    meta = tx.get("meta") or {}

    for group in meta.get("innerInstructions", []):
        for ix in group.get("instructions", []):
            yield ix


def find_mint_initialization(tx, mint):
    """Return the initializeMint/initializeMint2 ix that inits THIS mint."""
    for ix in iter_instructions(tx):
        parsed = ix.get("parsed")

        if not isinstance(parsed, dict):
            continue

        if parsed.get("type") not in GENESIS_TYPES:
            continue

        if parsed.get("info", {}).get("mint") != mint:
            continue

        return ix

    return None


def get_signers(tx):
    keys = tx["transaction"]["message"].get("accountKeys", [])
    return [k["pubkey"] for k in keys
            if isinstance(k, dict) and k.get("signer")]


def find_genesis(mint):
    """
    Walk signatures OLDEST -> NEWEST and stop at the first transaction that
    actually initializes this mint. Based on instruction semantics, not on
    transaction age, and cheap: on a fresh or a high-volume mint alike the
    genesis is among the oldest signatures, so only 1-2 getTransaction calls
    are needed.
    """
    print("\nSEARCHING FOR MINT GENESIS (oldest first)")
    print("-----------------------------------------")

    checked = 0

    for item in iter_signatures_oldest_first(mint):
        signature = item["signature"]

        tx = get_transaction(signature)
        checked += 1

        if tx is None:
            continue

        ix = find_mint_initialization(tx, mint)

        if ix is None:
            continue

        block_time = tx.get("blockTime")
        slot = tx.get("slot")
        signers = get_signers(tx)
        deployer = [s for s in signers if s != mint]

        print(f"\nGENESIS FOUND (after {checked} transaction(s))")
        print("-------------")
        print("signature:", signature)
        print("slot:", slot)
        print("blockTime:", utc(block_time))
        print("signers:", signers)
        print("deployer (signer != mint):", deployer)
        print("program:", ix.get("programId"))
        print("instruction:", ix.get("parsed", {}))

        return {
            "signature": signature,
            "slot": slot,
            "blockTime": block_time,
            "signers": signers,
            "deployer": deployer,
            "instruction": ix,
        }

    raise RuntimeError(
        f"No initializeMint/initializeMint2 found after checking "
        f"{checked} transactions"
    )


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <MINT>")
        sys.exit(1)

    mint = sys.argv[1]

    print(f"=== RECON {mint} ===")

    get_mint_info(mint)

    print("\nFETCHING SIGNATURE HISTORY (paginating to oldest)")
    print("-------------------------------------------------")

    genesis = find_genesis(mint)

    print("\nDONE.")
    return genesis


if __name__ == "__main__":
    main()
