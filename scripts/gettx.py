#!/usr/bin/env python3
"""
gettx.py — decode a single Solana transaction: instructions, signers, and the
per-account SOL balance changes (postBalances - preBalances). Use it to verify
any signature in the report (e.g. the creator-fee distributions in Appendix A):
the printed balance deltas are the on-chain ground truth.

Usage:
    export SOLANA_RPC="https://mainnet.helius-rpc.com/?api-key=..."
    python gettx.py <SIGNATURE> [ADDRESS ...]   # optional addresses are checked
"""
import os, sys, datetime, requests

RPC = os.environ["SOLANA_RPC"]

KNOWN = {
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P": "Pump.fun",
    "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA": "Pump.fun-AMM",
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb": "Token-2022",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": "SPL-Token",
    "11111111111111111111111111111111": "System",
    "ComputeBudget111111111111111111111111111111": "ComputeBudget",
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL": "ATA",
    "Stake11111111111111111111111111111111111111": "Stake",
}


def utc(t):
    if t is None:
        return "?"
    return datetime.datetime.fromtimestamp(
        t, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def main():
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <SIGNATURE> [ADDRESS ...]")
        sys.exit(1)

    sig = sys.argv[1]
    checks = sys.argv[2:]

    body = {"jsonrpc": "2.0", "id": 1, "method": "getTransaction",
            "params": [sig, {"encoding": "jsonParsed",
                             "maxSupportedTransactionVersion": 0}]}
    tx = requests.post(RPC, json=body, timeout=60).json().get("result")
    if not tx:
        print("tx not found — right signature? SOLANA_RPC set?")
        sys.exit(1)

    meta = tx.get("meta") or {}
    msg = tx["transaction"]["message"]
    keys = [k["pubkey"] if isinstance(k, dict) else k
            for k in msg.get("accountKeys", [])]
    signers = [k["pubkey"] for k in msg.get("accountKeys", [])
               if isinstance(k, dict) and k.get("signer")]

    print("signature:", sig)
    print("blockTime:", utc(tx.get("blockTime")))
    print("slot:", tx.get("slot"), "| success:", meta.get("err") is None)
    print("signers:", signers)

    print("\n--- instructions ---")

    def show(ix, inner=False):
        pid = ix.get("programId", "")
        name = KNOWN.get(pid, pid)
        p = ix.get("parsed")
        t = p.get("type") if isinstance(p, dict) else ix.get("program")
        print(("  inner " if inner else "  ") + f"{name} | type={t}")

    for ix in msg.get("instructions", []):
        show(ix)
    for grp in meta.get("innerInstructions", []):
        for ix in grp.get("instructions", []):
            show(ix, True)

    print("\n--- SOL balance changes (postBalances - preBalances) ---")
    pre = meta.get("preBalances", [])
    post = meta.get("postBalances", [])
    for i, (p, q) in enumerate(zip(pre, post)):
        d = (q - p) / 1_000_000_000
        if abs(d) >= 0.000001:
            who = keys[i] if i < len(keys) else "?"
            print(f"  {who} {d:+.9f} SOL")

    if checks:
        print("\n--- account checks ---")
        for a in checks:
            where = "SIGNER" if a in signers else (
                "present" if a in keys else "ABSENT")
            print(f"  {a}: {where}")


if __name__ == "__main__":
    main()
