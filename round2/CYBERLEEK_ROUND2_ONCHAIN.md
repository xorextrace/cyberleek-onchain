# CyberLeek "round 2" ($CYBER / "Grand Theft Leek") — On-Chain Observation from T-0

**Version 0.3 (draft for review).** *Independent, reproducible observation of the
Solana token launched during the CyberLeek "round 2" countdown window on
29 August 2026. Companion to the round-1 `$CYBERLEEK` funding-trail analysis.
Public blockchain data only — no identity attribution.*

**Source:** On-Chain Observation by *xorextrace* · Network: Solana mainnet-beta.

> **Changelog v0.2 → v0.3:** anchored every §4 fee figure to its transaction
> signature (new **Appendix A**) so the numbers can be re-derived with any
> `getTransaction` call, independent of the analysis scripts; tightened the
> recipient totals to exact sums; made §9 verification script-independent.

---

> [!IMPORTANT]
> ## Read this first — two questions, kept separate
>
> **1. Is this really CyberLeek's token?** — Supported at the **web/brand layer**,
> not on-chain. The domain used for round 1 (`cyberleek.wtf`) hosts `GPx5…pump`
> as `$CYBER`. That is website continuity with the round-1 project, and for a
> memecoin sequel it is where "official" is normally established. It is **not**
> confirmed by any independent tracker or outlet (mainstream trackers still cover
> only the round-1 mint `ApZux…`), **not** established on-chain, and it does not
> prove that whoever controls the website also controls the token's wallets.
> Residual risk: a compromised/cloned domain. Net: 🟡 official by web presence,
> unconfirmed by independent or on-chain evidence.
>
> **2. Same operator as round 1?** — **Unresolved.** The round-1 wallet-reuse test
> is negative (§6). That is not proof of a different actor, nor of the same one.
>
> `wallet A → wallet B` does **not** imply `person X = person Y`. No real-world
> identity is asserted anywhere.

**Confidence legend:** 🟢 verified (raw on-chain data) · 🟡 strong inference · 🟠 plausible / not excluded · 🔴 unknown / out of reach.

**One-line summary:** *The round-2 token carries the round-1 brand at the website
layer but runs on materially different, freshly created on-chain infrastructure
with no observed wallet reuse. Its creator fees are split, by a fixed configured
ratio, ~50/50 between the creation signer and a pre-existing wallet dedicated to
this single launch. Whether this is the same operator as round 1 is not
established.*

---

## 1. Scope & method

Observed live from the announced window (mint created 19:14 UTC, 29 Aug 2026).
Candidate mint taken from third-party explorers, never from CyberLeek's own sites.
RPC fetched locally against Helius; raw transactions decoded with the repo scripts
(`scripts/gettx.py`, `scripts/inspect_cashflows.py`, `scripts/tally_pump_fees.py`,
`scripts/recon_token.py`) and cross-checked on Solscan and Solana Explorer.
Standard inherited from round 1: **no figure is published until recomputed from a
real dump**; unreconciled figures are marked, and every headline number is anchored
to a transaction signature (Appendix A) so it can be verified independently of any
script.

## 2. Key addresses

| Label | Role | Address |
|---|---|---|
| $CYBER mint | token ("Grand Theft Leek") | `GPx5APBduaoYaG1jrqYNM81GDGgLyLWev9My4mmipump` |
| GLf2 | mint creation signer / creator; ~47.5% fee recipient | `GLf2JhxRfSuDVnRRE7TssRN2LKDvW6Afoqfq3d1c9uCJ` |
| 6ehREa | pre-existing wallet; ~50% fee co-recipient (dedicated) | `6ehREaVX9kKAqwhaAsecpgjSy45xCNjxCgMgwNaud781` |
| 8Nerkdt | small third fee recipient (~2.5%) | `8Nerkdt84Cq3AroU9319vBmC4iaJiEEGCxJRouWFSCcS` |
| GN1ZMK | fee-distribution source account (Pump.fun-internal) | `GN1ZMKUehXvRNwpUWbUSo5a8kvz6j9D7WpMiiJZjn5Xo` |
| G8UKzg | fee-claim cranker (Pump.fun-internal) | `G8UKzgPZvJm28NuRVus8X2XtvaMZSGzH8pMuKc5oh1Ew` |

## 3. Token foundation — 🟢 VERIFIED (raw transaction bytes)

Mint `GPx5…pump` created **2026-08-29 19:14:38 UTC** (slot 442683481) by signer
**GLf2**, in one Pump.fun creation transaction:

`2WXTx543UZkUwDaFJpTePTgKxjDQ5c3gFBx6RDL7EnnsXfrPL8LYiBdmx4eZB3pPaYSPrSsuF2BgWPmH7hyaEWNL`

Instruction sequence: Pump.fun `create` → Token-2022 `initializeMint2` (one-time
genesis) → `initializeTokenMetadata` → `mintTo` → `setAuthority` (authorities
revoked in the same atomic tx). State: mint & freeze authority revoked, supply
≈ 973M, Token-2022. Confirmed on a second explorer.

> **Tooling defect (documented & fixed):** `recon_token.py` initially reported a
> false creation (signer `6UF3nd…`, 20:58 UTC) because it read `sigs[-1]` of the
> 1000 most-recent signatures — not the genesis — on a high-volume mint (175k+
> signatures). Fixed: paginate to the oldest signatures and stop at the tx whose
> instruction is `initializeMint2` for this mint. The fixed tool re-derives the
> genesis above (`2WXTx…`, 19:14:38 UTC, `GLf2`) in a handful of calls; a
> regression test pins that expectation.

## 4. Creator-fee distribution — 🟢 VERIFIED (per-signature, Appendix A)

On a Pump.fun fair launch, money enters **from** the launch (creator/trading fees),
not into it: **no large external funding source was observed in the analyzed
pre-launch path.** Fees are paid on-chain by Pump.fun's `DistributeCreatorFees`
instruction to several recipients within the same instruction. Summed across the
seven distributions in the window (19:20 UTC 29 Aug → 02:43 UTC 30 Aug), each
anchored to its signature in **Appendix A**:

| Recipient | Fees received | Share |
|---|---|---|
| GLf2 (creator) | **51.288 SOL** | ~47.5% |
| **6ehREa (pre-existing, dedicated)** | **53.990 SOL** | ~50.0% |
| 8Nerkdt (third party) | **2.699 SOL** | ~2.5% |
| **Total to recipients** | **107.977 SOL** | |

**The split is a fixed configured ratio, not noise.** On every distribution the
three credits hold the same ~47.5 / 50.0 / 2.5 proportion, and per transaction they
sum to the amount debited from the Pump.fun fee accounts (minus transaction cost).
Example (sig #6, 20:47:10 UTC): `GN1ZMK` −1.502110 SOL → GLf2 +0.713097,
6ehREa +0.751055, 8Nerkdt +0.037553. A recurring fixed ratio is a per-launch
configuration parameter. 🟡 A near-even share to a wallet that predates the launch
by six weeks indicates a **deliberately configured co-recipient at token creation**.
`GN1ZMK` / `G8UKzg` are Pump.fun-internal plumbing; the operator-side recipients
are GLf2 and 6ehREa.

**Excluded — not income.** A stake round-trip at 02:44:24 UTC (GLf2 ↔ `AfE…`,
+1.1219 / −1.1223 SOL in the same slot 442768565) is **stake-account management,
net ≈ 0**, and is not counted as proceeds.

**Creator onward movement — figure withheld.** GLf2 forwarded funds to ~21 wallets
(including one 44.2 SOL transfer) in the first hours. No headline total is
published: GLf2's native outflow (~265 SOL observed) does not reconcile with its
~51 SOL fee income — the difference is almost certainly proceeds from selling its
own creator supply (AMM income, not captured by System-transfer tooling). A
combined income+dispersal tally is pending before any figure is published.

## 5. The `6ehREa` wallet — 🟢 (facts) / 🟡 (meaning)

- Real keypair (owner = System Program, `isOnCurve = true`); no exchange/program tag.
- **Active since 2026-07-12** — six weeks pre-launch — with its own July counterparty
  cluster and hundreds of SOL moved. Not a fresh, single-purpose wallet.
- Lifetime: IN ≈ 151.9 SOL, OUT ≈ 96.7 SOL; balance ≈ 55 SOL.
- Received ≈ 54 SOL as a ~50% creator-fee co-recipient (§4) and **retains** it.
- **Single-token:** across its full history (55 signatures) the only Pump.fun mint
  it ever touches is `GPx5…pump` (verified: no other `…pump` mint appears). It is
  **not** a serial fee collector / launch-service wallet.

🟡 A pre-existing, non-serial wallet configured to receive ~50% of exactly this
token's fees looks like an **operator or partner wallet dedicated to this
operation** — not generic tooling. This is a launch-specific financial
relationship. 🟠/🔴 It does **not** establish whose wallet it is, and it is **not**
a link to round 1 (it is the round-2 operator's node, a distinct claim). Its July
cluster is an **open lead, deliberately not pursued** (§8).

## 6. Round-1 linkage test — 🟠 NEGATIVE (and why that is not "fake")

The round-1 address set (`Hok9`, `Ec2`, `9Ve5`, `3YLND`, `26sZ`, `J4zo`, `9WwEfd`,
`BmFdp`) was searched across **all** round-2 material: creator dump, G8UKzg dump,
`2pFLeKp` dump, and the full `6ehREa` history. **Zero hits.**

> **Asymmetry — the crux.** A *positive* hit would be decisive (reuse = same hand).
> A *negative* is not: a competent operator uses fresh infrastructure at round 2
> precisely so nothing links back — which is also consistent with the observed
> web-layer continuity (§0). Honest statement: **"no wallet reuse from round-1 is
> demonstrable"** — never "fake", never "same people".

## 7. Proven / inferred / unknown

**🟢 Proven** — creation of `GPx5…` by `GLf2` at 19:14:38 UTC 29 Aug; creator fees
107.977 SOL distributed by a fixed ratio to GLf2 / 6ehREa / 8Nerkdt (51.288 /
53.990 / 2.699 SOL; Appendix A); `6ehREa` is a pre-existing (12 Jul), single-token
wallet retaining its ~54 SOL share; no round-1 wallet reuse on any traced wallet.

**🟡 Inferred** — the round-1 brand endorses this token at the website layer
(`cyberleek.wtf` hosts `GPx5…`); the fee split is a deliberately configured
per-launch structure; `6ehREa` is plausibly an operator/partner wallet of round 2.

**🟠 / 🔴 Unknown** — 🟠 same on-chain operator as round 1 (unresolved; no reuse);
🟠 that `GPx5…` is genuinely CyberLeek's beyond website continuity (no independent
or on-chain confirmation); 🔴 real-world identity of any controller; anything
behind the launchpad/exchange boundary.

## 8. Open leads (recorded, not pursued)

- **`6ehREa` July cluster** (`9kBVEfk`, `2YbEKjjT`, `HTQxEk`, …): possible operator
  wallet network. **Not pursued** — identity territory, out of scope.
- **`8Nerkdt` (~2.5% recipient):** whether it is launch tooling/referral or a second
  party — a small structural question, not identity.
- **Behavioural fingerprint:** whether the round-2 operator's active hours match the
  Central-European clock reported for round 1 — a weak signal at best, not identity.

## 9. How to verify (no trust required, script-independent)

1. **Foundation:** fetch creation sig `2WXTx543…` via `getTransaction`; confirm a
   Pump.fun `create` + Token-2022 `initializeMint2` signed by `GLf2`, 19:14:38 UTC.
2. **Fee split:** fetch each of the seven signatures in **Appendix A** via
   `getTransaction` and read `meta.preBalances`/`postBalances`; the per-account
   deltas must match the table. Their sums are the §4 totals.
3. **6ehREa single-token:** fetch its full history; confirm `GPx5…pump` is the only
   Pump.fun mint it touches.
4. **Linkage:** grep every round-2 dump for the round-1 address set; expect no hits.
5. **Labels / website:** treat entity tags and the website's claim as third-party
   metadata, verified independently — never blockchain-native facts.

## 10. Reproduce round 2 (from scratch)

Requires Python 3.9+ and `SOLANA_RPC` set to a Solana JSON-RPC endpoint.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SOLANA_RPC="https://mainnet.helius-rpc.com/?api-key=YOUR_KEY"

# 1) mint genesis: creation signer, time, authorities
python scripts/recon_token.py GPx5APBduaoYaG1jrqYNM81GDGgLyLWev9My4mmipump

# 2) verify any creator-fee distribution (Appendix A) — instructions + balance deltas
python scripts/gettx.py <SIGNATURE_FROM_APPENDIX_A>

# 3) confirm 6ehREa is a single-token wallet (only GPx5...pump appears)
python scripts/fetch_wallets.py --addresses 6ehREaVX9kKAqwhaAsecpgjSy45xCNjxCgMgwNaud781 \
  --start 2026-06-01 --end 2026-08-31 --out round2/data/6eh.json
grep -oE '[1-9A-HJ-NP-Za-km-z]{32,44}pump' round2/data/6eh.json | sort | uniq -c

# 4) fee tally across the fee-path wallets (forensic view, not auto-attribution)
python scripts/fetch_wallets.py --addresses-file round2/wallets.round2.txt \
  --start 2026-08-29 --end 2026-08-31 --out round2/data/r2.json
python scripts/tally_pump_fees.py --data "round2/data/*.json" \
  --addresses GLf2JhxRfSuDVnRRE7TssRN2LKDvW6Afoqfq3d1c9uCJ \
  6ehREaVX9kKAqwhaAsecpgjSy45xCNjxCgMgwNaud781 \
  8Nerkdt84Cq3AroU9319vBmC4iaJiEEGCxJRouWFSCcS

# 5) round-1 linkage test — expect no hits
grep -Eo 'Hok9nbV|Ec2qmcp|9Ve5Cgt|3YLNDXn|26sZDub|J4zoc1r|9WwEfdd|BmFdpra' \
  round2/data/r2.json | sort | uniq -c
```
---

## Appendix A — Creator-fee distributions (per-signature)

Each row is one `DistributeCreatorFees` transaction. Amounts are the on-chain
balance deltas (`postBalances − preBalances`) for each recipient, in SOL. Verify
any row by fetching the signature and reading its balance changes.

| # | Time (UTC) | Signature | GLf2 | 6ehREa | 8Nerkdt |
|---|---|---|---|---|---|
| 1 | 2026-08-29 19:20:21 | `5HVojiDrJoBgRyqfzs5peBAeD4Pjv6VDLR23NdQjEF8GovHN7VkGiof5jwG2Np3MdNNzKxUuQD4GafSheuWKsX27` | 39.588324184 | 41.672300856 | 2.083571532 |
| 2 | 2026-08-29 19:27:29 | `QFZjNiNx1oMDe9u53b6TmiQt44ahX4vSaFQcGeovEynRbUpPpTp1WaisfLe25wVrd1hWMadhSZvqv3JotjYR6af` | 5.371016922 | 5.654128486 | 0.282706424 |
| 3 | 2026-08-29 19:43:11 | `5aKzkAg9ZVpDNhUW2h1G9fmHCh9ckLW7FQqqcz53NvVakyzdgkrvYLeWeJ8yqtLQQKNvsegKnm2MeTzNWoWXaoBg` | 3.742965561 | 3.940390211 | 0.197019510 |
| 4 | 2026-08-29 19:55:50 | `4W3uDk7fiT81uHarK1Y3g6MEUUPaGfzf3LCn8XQKK9ZAAQggdoih5hKqRzJUcNVQwhP7AUMFri2mxvzD85KvkQA2` | 0.931475850 | 0.980927357 | 0.049046367 |
| 5 | 2026-08-29 20:02:37 | `Qo6oXZXKhfp96c3NF62N5vT3LMWafFF3CLEwzgv7oV7ZZ8WbExaWUqztF39JZV9uYAuG5YB94E4rEotZ5qLBhtK` | 0.717178284 | 0.755244308 | 0.037660884 |
| 6 | 2026-08-29 20:47:10 | `NvMZcFyXtob1s6Db3oCWYkeb28C5GM6EZpeawEF7oMBZx7iEP8vTXkb7KDGnwD2Ego2fbvM1Jq1FtwNcs2VQbhx` | 0.713096955 | 0.751054836 | 0.037552741 |
| 7 | 2026-08-30 02:43:39 | `56wNMNMEvfdF6WenKUsEeDsV2ruaHi4fJ4yREbG2Qj1FQc8KS5ehouC2YXK7CLPuDRunAzy7zXGNMZpQPWbnWBk3` | 0.223463610 | 0.235651315 | 0.011782565 |
| | | **Total** | **51.287521** | **53.989697** | **2.699340** |

(Full signatures are given un-truncated on purpose — do not shorten them when citing.)

---

*No identity attribution is made or implied. This document establishes financial
relationships between public addresses and stops at the launchpad/exchange
boundary. Corrections with reproducible evidence are welcome.*
