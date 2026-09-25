# V33 Repository Audit: Strategic Route Portfolio & Meta-Control

**Date:** 2026-09-24  
**Role:** Lead Research Engineer, Competition Scientist, and Implementation Owner  
**Program:** Kagriculture V33 Research Program  
**Competition Deadline:** September 30, 2026 at 11:59 PM UTC (~6 days remaining)  
**Target:** Materially improve competition win rate over A7 (stretch target ~3000+ leaderboard rating)

---

## 1. Protected Incumbents & Integrity Audit

Prior to any execution, all protected submission assets and baseline dependencies were verified:

| Asset | File Location | Expected SHA-256 | Actual Calculated SHA-256 | Verification Status |
| :--- | :--- | :--- | :--- | :---: |
| **Slot B (Incumbent)** | `candidates/v30_a7_standalone/main.py` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | **PASS (BIT-IDENTICAL)** |
| **Slot A (Protected)** | `submission_aec_v22r1.tar.gz` | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | **PASS (BIT-IDENTICAL)** |
| **Engine Version** | `kaggle_environments` | `1.32.7` | `1.32.7` | **PASS** |
| **Baseline Registry** | `scripts/v32_common.py` | 12 component digests | All 12 digests verified | **PASS** |

### Virgin Holdout Protection
The following holdout partitions are strictly protected and remain untouched:
- `214200–214249` (GATE0 virgin holdout)
- `340090–340199` (Protected remainder cohort)
- `249695–249734` (V32_CONFIRM single-touch holdout)

No route discovery, feature engineering, selector training, or hyperparameter search will touch these ranges.

---

## 2. Forensic Audit of V32 / P10 / P11 / P12 Research

The extensive V32 research program established crucial empirical facts that directly dictate the V33 architecture:

1. **Failure of Continuous Macro-RL (RL-X2):**
   - Attempted end-to-end PPO and offline-pre-trained macro controllers issuing decisions every $H=4$ ticks.
   - Result: Terminal cash collapsed from ~$104k down to ~$13.7k (win rate collapsed to 11.1%).
   - Causal Reason: Sequential open-loop desynchronization occurs whenever macro deviations exceed ~10% of game steps. Continuous intervention breaks A7's delicate, tick-exact worker pathing, feeding schedules, and inventory buffers.

2. **Physical Resynchronization Solved, But Economic Gap Remains (P12):**
   - P12 formulated isolated interventions as bounded $H=4$ options with mandatory return to A7.
   - P12 proved that physical resynchronization is achievable: $D_{\text{resync}} = 0.0$ at $t+28$ ticks (100% synced).
   - However, closed-loop league evaluation showed negative economic return:
     - A7 mean cash: **$104,332.17** (Win rate: 83.3%)
     - P12 Search-Gated: **$101,004.63** (Win rate: 56.7%, Paired delta: -$3,327.53, Worst tail: -$26,853.00)
     - P12 Supervised Selector: **$101,003.68** (Win rate: 56.7%, Paired delta: -$3,328.48)
     - P12 PPO Selector: collapsed to $a=0$ (`FOLLOW_A7`, 0 activations).

3. **Causal Attribution of the P12 Failure:**
   - The local +$11,179 counterfactual alpha discovered by exact search on Seed 249635 was regime-dependent: it occurred against `E8_DMITRII` (a pure livestock player who never touched the wheat seed market or bakery).
   - When facing crop-growing opponents (`V54`, `E0_V3`, `E1_V22R1`, `E2_A7`), land capex ($4,000) locked up liquidity while simultaneous harvest flooded the bakery, collapsing spot prices ($48 \to $22). The farm suffered delayed insolvency and missed late harvests.

4. **The Paradigm Shift for V33:**
   - **Do NOT build another controller that tries to "improve A7" via continuous low-level interventions or option splicing.**
   - **LOW-LEVEL EXECUTION REMAINS THE JOB OF THE EXPERT ROUTE.**
   - The expert route manages workers, movement, planting, harvesting, feeding, watering, purchases, production, sales, and liquidation coherently from start to finish.
   - The meta-controller operates at the strategic macro level: selecting an elite route, deciding whether to stay or safely switch at strategic boundaries.

---

## 3. Current Public Meta & External Benchmark Audit

Investigation of external public solutions, discussions, and repository artifacts reveals key insights:

### A. The 3090.1 Public Artifact (`public_3090` / `v27 Midgame Meta Reset`)
- **Source:** `external_repos/lixingtao123-Kaggriculture/public_3090/output/main.py`
- **Claimed Score:** Public Score = 3090.1.
- **Critical Distinction:** The notebook log explicitly documents `"25/27 strict-future Top-30 replay cases; not an official LB score"`. The 3090.1 figure is an offline sample metric over historical top-30 replays, not a verified live leaderboard rating.
- **Mechanism:** Dual-regime tape selection:
  - Selects `_REBALANCE_ACTIONS` if `townCenterSellInterval >= 24` (PR #1394 configuration), otherwise `_LEGACY_ACTIONS`.
  - Open-loop 719-step action tape combined with local weed repair and price-impact/demand-adjusted sell ranking.
  - Zero dynamic route switching or online reinforcement learning.

### B. The 3009.0 Public Artifact (`v48 Fast Routes` / `v44 Gold Floor`)
- **Source:** `forensic_verification/extracted_sources/v49_modules/v48_fast_route_router.py`
- **Reported Score:** Public Score = 3009.0 ("40/40 Early Floor | 39/46 Top-10 | v48 Fast Routes").
- **Mechanism:** Sparse closed-loop routing over 6 predefined routes based on 4 observable town shop events:
  - Route set: `default`, `yarn_fast`, `farm_fast`, `yarn_second`, `yarn_third`, `bakery_capital`.
  - Events: first shop `YARN_STORE` at step 88 $\to$ `yarn_fast`; first shop `FARMERS_MARKET` at step 120 $\to$ `farm_fast`; second shop `YARN_STORE` at step 153 $\to$ `yarn_second`; third shop `YARN_STORE` at step 216 $\to$ `yarn_third`.
  - Evaluates exactly one child policy per turn to avoid time limit violations.
  - Price-impact market timing overlay (`reorder_sell_slots`).

### C. Recent Discussion on Replay-based PPO Meta-Agents
- Identified structural failure modes:
  - Strong routes often share identical opening prefixes (e.g., initial worker hires, first crop bed), making them indistinguishable early on.
  - Selecting a route before opponent strategy reveals itself forces commitment under high uncertainty.
  - Once committed, switching routes later violates physical inventory and land layout constraints.
  - Online PPO meta-selectors plateau because state space representations fail to capture the long-term capex consequences of early commitments.

---

## 4. Replay Data & Population Asset Inventory

The repository contains extensive replay datasets and agent populations ready for extraction and benchmarking:

1. **Replay Archives:**
   - Root replays: `elo3000_test_replay.json` (11.2 MB), `episode-104820229-replay.json` (30.3 MB), `master_83k_replay.json` (12.6 MB), `master_fast_replay.json` (9.5 MB), `master_fixed_replay.json` (10.9 MB), `titan_day0_replay.json` (11.5 MB), `titan_test_replay.json` (12.6 MB), `titan_wheat_replay.json` (10.7 MB).
   - Dedicated folder `replays/`: 15 full match replay JSON files (`episode-92890298` through `92902361`).
   - Live telemetry: `live_data/episodes_v31r2/` containing `summary.jsonl`, `leaderboard.json`, and hundreds of logged matches.

2. **Candidate & Competitor Agent Pool:**
   - **`E2_A7` / `A7`:** The protected standalone incumbent (`candidates/v30_a7_standalone/main.py`).
   - **`E1_V22R1`:** Slot A champion (`submission_aec_v22r1.tar.gz`).
   - **`E8_DMITRII`:** Frontier competitor (~2800 LB) (`extracted_agents/dmitrii_lb2800/main.py`).
   - **`E0_V3`:** Frozen baseline (`submission_Vj_kc_v3.tar.gz`).
   - **`V54`:** Declarative crop specialist (`external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py`).
   - **`P3090`:** Public top-tape agent (`external_repos/lixingtao123-Kaggriculture/public_3090/output/main.py`).
   - **`V66`:** Public agent (`external_repos/kaggriculture-v66-agent/`).
   - **`SYN_AGG`:** Hostile synthetic market stressor (`candidates/v32_rlx2/opponents.py`).
   - **Opponents Library:** 35 specialized opponents in `opponents/` (melon, cow, sheep, market aggressors, replay clones).

---

## 5. Architectural & Research Mandate for V33

Following the master specification, V33 will be developed strictly inside `candidates/v33_meta_strategy/`:

1. **Phase A (Complete):** Repository audit, asset inventory, baseline hash verification, dependency map.
2. **Phase B:** Data discovery, cataloging (`V33_DATA_CATALOG.md`), and strict governance protocol (`V33_DATA_GOVERNANCE.md`).
3. **Phase C & D:** Replay normalization layer, trajectory schema, route extraction, and route clustering (`V33_ROUTE_CLUSTERING.md`).
4. **Phase E:** Construction of the elite route bank (`V33_ROUTE_BANK.md`) starting with $R_0 = \text{A7}$ plus 3–8 distinct experts.
5. **Phase F & G (The Critical Scientific Gate):** Full route-vs-route tournament matrix (`V33_ROUTE_MATCHUP_MATRIX.md`) and non-transitivity testing (`V33_NONTRANSITIVITY.md`).
   - **Gate Question:** *Do multiple elite routes actually contain complementary matchup strength?*
   - If NO: Terminate route portfolio expansion and confirm A7 as the universal expert.
   - If YES: Proceed into early information study and selector development.
6. **Phases H–N:** Early information study, exact counterfactual oracle, transition safety analysis, one-switch selector, midgame meta reset, and market overlay.
7. **Phases P–R:** Master benchmark on fresh DEV seeds, holdout audit, and promotion decision report.
