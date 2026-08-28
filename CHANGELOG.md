# Changelog

All notable changes to this analysis are documented here.

## [1.1.0] — 2026-08-28
### Added
- **Section 14b — Cash-out (27 Aug 2026):** reconstruction of the ~3,210 SOL
  cash-out from the deployer `Hok9` through a peel chain of fresh single-purpose
  wallets, terminating at two labeled exchange endpoints — **KuCoin** and
  **CCE.Cash**.
- Timeline (§10) and "What is proven" (§11) entries for the cash-out.

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
