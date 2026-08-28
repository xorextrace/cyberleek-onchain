# Changelog

All notable changes to this analysis are documented here.

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
- Example fetch window in §15/§16 no longer ends on 2026-08-21 (which predated
  the cash-out).
- `wallets.cashout.txt` no longer lists the KuCoin hot wallet (BmFdp): fetching
  that high-volume wallet in full is unnecessary and slow; the relevant flow is
  captured via GPscf.
### Notes
- `trace_cashout.py` surfaces endpoints but does not name exchanges; the
  KuCoin / CCE.Cash labels are read on Solscan and treated as third-party
  metadata, never as a code output.

## [1.1.0] — 2026-08-28
### Added
- **Section 14b — Cash-out (27 Aug 2026):** reconstruction of the ~3,210 SOL
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
