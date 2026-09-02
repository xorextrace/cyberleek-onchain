# Changelog

All notable changes to this analysis are documented here.

## [1.4.0] — 2026-09-02
### Fixed — **corrected cash-out total**
- The 27 August cash-out was previously reported as **3,210.80 SOL**. This was an
  error: the fourth exit (to `8hypa8…`) was recorded as 1,011.411 SOL when the
  wallet actually received a single transfer of **505.681 SOL**. The wallet's
  inbound and outbound transfers of the same amount had been summed together.
- **Corrected total: 2,705.07 SOL.** This now reconciles with the 2,676.67 SOL the
  deployer obtained by selling its creator-fee allocation minutes earlier
  (1,442.43 + 1,234.23 SOL), plus ~28 SOL of pre-existing balance. The previous
  figure did not reconcile — it implied more SOL leaving the wallet than ever
  entered it.
- `scripts/tally_cashout.py`: `SEED_OUT` corrected accordingly.
- Endpoint figures are **unchanged** (~1,336.67 SOL to CCE.Cash, ~543.90 SOL to the
  KuCoin deposit address) because they were measured directly. Only the
  denominator changes: cleanly-attributed share rises from ~59% to ~70%.
- A visible correction notice has been added to §14b.
### Added
- **Reconciliation rule** in the methodology (§1): every aggregate figure is now
  checked against the wallet's actual balance delta, and inflows must reconcile
  with outflows. This is the check that surfaced the error above — the previous
  total failed it and that was not noticed at the time.
### Verified
- Refetched the deployer wallet across 27 Aug – 1 Sep: **no further movements**.
  The cash-out is a single closed event, and the full mechanic is visible on-chain
  (fee collection 07:27 → sale 07:28 → four outbound transfers 07:29–07:32).

## [1.3.0] — 2026-08-30
### Added
- **Round 2 observations.** A second token launched under CyberLeek branding
  ("Grand Theft Leek" / $CYBER, mint `GPx5…pump`, creator `GLf2J…9uCJ`) was
  examined on-chain. Observed creator-fee distributions of **107.977 SOL**.
### Notes
- The branding and website/Telegram links show clear continuity with the
  CyberLeek ecosystem, but **no wallet reuse from the first token was observed**:
  none of the round-1 addresses (deployer, aggregation hub, exchange endpoints)
  appear among the second token's funding or distribution counterparties.
- On-chain data therefore does **not** establish whether the same operator is
  behind both rounds. Brand continuity is not operator continuity.

## [1.2.0] — 2026-08-28
### Added
- **Cash-out verification scripts:** `scripts/trace_cashout.py` (follows the
  27 Aug peel chain to its terminal endpoints) and `scripts/tally_cashout.py`
  (sums SOL reaching each labeled endpoint, counting only transfers from the
  known cash-out relays).
- `wallets.cashout.txt` — the cash-out wallet set for the fetcher.
- "Reproducing §14b" steps in the report, plus a cash-out step in §16.
### Changed
- §14b split now distinguishes **cleanly attributable** flows (~1,337 SOL to
  CCE.Cash, ~544 SOL to the KuCoin deposit address) from a **shared-aggregator
  lump** (`GPscf → BmFdp` KuCoin hot wallet) that is reported for context but not
  summed into any endpoint total, because the CyberLeek portion cannot be cleanly
  separated from third-party funds on-chain (SOL is fungible).
### Fixed
- Added a separate, correctly-windowed fetch command for the 27 Aug cash-out
  (`--end 2026-08-28`); the earlier docs only covered the funding trail, so the
  cash-out could not be reproduced.
- `wallets.cashout.txt` no longer lists the KuCoin hot wallet (BmFdp): fetching
  that high-volume wallet in full is unnecessary and slow; the relevant flow is
  captured via GPscf.
### Notes
- `trace_cashout.py` surfaces endpoints but does not name exchanges; the
  KuCoin / CCE.Cash labels are read on Solscan and treated as third-party
  metadata, never as a code output.

## [1.1.0] — 2026-08-28
### Added
- **Section 14b — Cash-out (27 Aug 2026):** reconstruction of the cash-out
  (stated as ~3,210 SOL at the time; corrected to 2,705.07 SOL in v1.4.0)
  cash-out from the deployer `Hok9` through a peel chain of fresh single-purpose
  wallets, terminating at two labeled exchange endpoints — **KuCoin** and
  **CCE.Cash**.
- Timeline (§10) and "What is proven" (§11) entries for the cash-out.
- Italian translation of the full report (`CYBERLEEK_ONCHAIN_ANALYSIS_REPORT_IT`).

### Changed
- Section 9 (mixer / obfuscation): added a note that the cash-out routed part of
  the proceeds through **CCE.Cash**, a non-custodial swap service — a concrete
  instance of the off-chain mechanism §9 declined to exclude.

### Notes
- The KuCoin branch of the cash-out terminates at the same `BmFdp` KuCoin Hot
  Wallet seen in the upstream funding genealogy (§8) — the same infrastructure
  appears at both ends (funding and cash-out).
- Split figures are approximate; the cash-out was still in progress at capture.
- No identity attribution is made or implied. See the disclaimer in the report.

## [1.0.0] — 2026-08-27
### Added
- Initial on-chain funding-trail analysis of the `$CYBERLEEK` token.
- Verification scripts: `fetch_wallets.py`, `verify.py`, `analyze_flows.py`,
  `check_mixer.py`.
- Confidence model, methodology, reproducibility and disclaimer sections.
