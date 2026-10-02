# Changelog

All notable milestones, architectural breakthroughs, and repository engineering events in the **Kagriculture** project are documented here.

---

## [Final Archival & Repository Finalization] - 2026-10-02
### Added
- Created formal historical Git branches: [`culture/v24`](file:///c:/Users/Sundareswaran/Kagriculture) and [`culture/v25`](file:///c:/Users/Sundareswaran/Kagriculture), fully encapsulating the Challenger suite and Coherent Planner research campaigns.
- Created canonical repository documentation:
  - [`docs/FINAL_ARTIFACTS.md`](file:///c:/Users/Sundareswaran/Kagriculture/docs/FINAL_ARTIFACTS.md): Full provenance, SHA256 checksums, and execution instructions for the Incumbent agent (V49 Meta Fusion) and teammate bundles.
  - [`docs/AGENTS.md`](file:///c:/Users/Sundareswaran/Kagriculture/docs/AGENTS.md): Master registry of all candidate agents, configurations, and benchmarks.
  - [`docs/RESEARCH_HISTORY.md`](file:///c:/Users/Sundareswaran/Kagriculture/docs/RESEARCH_HISTORY.md): Detailed chronicle of research hypotheses, methodology, and results from V40 through V60.
  - [`docs/DATASETS.md`](file:///c:/Users/Sundareswaran/Kagriculture/docs/DATASETS.md) & [`data/MANIFEST.csv`](file:///c:/Users/Sundareswaran/Kagriculture/data/MANIFEST.csv): External dataset registries and deterministic re-acquisition scripts.
  - [`research/repository_cleanup/`](file:///c:/Users/Sundareswaran/Kagriculture/research/repository_cleanup/): Comprehensive size audit, file classification, deletion manifest, and final cleanup report.
### Removed
- Safely detached and removed external worktrees `Kagriculture-v24` and `Kagriculture-v25`.
- Reclaimed ~18.1 GB of disk space by purging disposable Python virtual environments (`.venv`), temporary downloaded episode JSONs (`research/v60/data/tmp_ep_jsons/`), intermediate trajectory dumps (`results/*.jsonl`), and scratch telemetry dumps.
### Changed
- Hardened `.gitignore` to prevent future reintroduction of raw simulation replays, virtual environments, and intermediate neural network checkpoints.

---

## [V60] - September Elite Replay Acquisition & A100 Staging
- Automated match replay collection from top September ladder participants via Kaggle Episodes API.
- Packaged bit-exact A100 Recovery Staging Bundle (`Kagriculture_A100_V60_Recovery.zip`, SHA256: `8C80805B...`) with 17/17 automated verification passes.

## [V58] - August 3100+ Elite Replay Validation
- Benchmarked V49 against executable plans extracted from August 3100+ public replays.
- Achieved **400 / 400 wins (100% Win Rate)**, proving total obsolescence of legacy carrot-0 strategies against V49's modern wash/carrot economy.

## [V56 - V57] - V49 Forensic Autopsy & Queue Optimization
- Isolated V49's 4 historical loss worlds (seeds 250617 and 250621 vs V44) to step 697 lockstep market transaction queue collisions.
- Proved through 24 intervention variants that baseline transaction ordering is Pareto-optimal; locked V49 baseline.

## [V50 - V55] - Mechanism Falsification & Divergence Boundaries
- Falsified fertilizer buyback suppression (V50; starved late crop deliveries).
- Falsified weed blocked-action replay buffers (V51; 0 firings across 92k steps on 2945 chassis).
- Falsified dynamic cow swapping (V52; caused shed bottlenecks).
- Mapped mathematical boundary of opponent state observability (V54; prove irreconcilable divergence post-step 144).
- Falsified dynamic midgame shop route switching (V55; caused severe crop desynchronization).

## [V49] - Meta Fusion Incumbent (Final Competition Submission)
- Injected E402 late seed-cap overlay: strictly capped `BUY_SEED` for wheat and carrots after step 624 to remaining tile capacity.
- Achieved **99.31% Win Rate (572W / 4L / 0T / 0 casualties across 576 fresh validation legs)**.
- Locked and submitted as the official final competition agent (`v49_meta_fusion_20260929_2212.zip`, SHA256: `8CAFF630...`).

## [V47 - V48] - 2945 Elite Chassis Transfer & Route 105 Overrides
- Ported and deconstructed public 2945 benchmark chassis (Hayashi/Tschinkel lineage): ORDERPRI2 priority, cow->goose, shed-room guard.
- Discovered surgical Route 105 overrides for Brunch/Farmers, Bakery/Brunch, and PetCafe/Farmers shop combinations (+0.74 alpha, 4 rescues, 0 casualties).

## [V44] - CapEx Cutoff Rule Discovery
- Discovered hard constraint: forbidding `BUY_ANIMAL` and `BUY_LAND` after turn 520 preserves critical float and prevents stranded endgame capital.

## [V40 - V43] - High-Throughput Simulators & Compositional Alpha
- Developed `FastKagricultureSim` achieving 500+ steps/second with bit-exact Kaggle engine parity.
- Validated multi-step micro-alpha composition across production and terminal liquidation regimes.

## [V30 - V35] - A7 Standalone & Production Milestone
- Packaged A7 candidate with opening wash controller and standalone submission bundle (`final_submission/V35_FINAL_SUBMISSION.tar.gz`).

## [V24 - V25] - Culture Campaigns (Challengers & Coherent Planners)
- **V24**: Evaluated Challengers C1 (idle zeroing), C2 (livestock scale), and C3 (carrot compound); mapped competitive bottleneck matrix.
- **V25**: Developed coherent planner architecture (P1 macro, P2 options, P3 unified).

## [V22R1] - Base Competition Release
- Baseline competition release commit (`33763a8`).
