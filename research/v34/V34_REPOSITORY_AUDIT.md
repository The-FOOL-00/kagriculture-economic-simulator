# V34 Repository Audit & Baseline Verification

**Program:** Kagriculture V34 Research Program (A7 Tactical Forward Search)  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Competition Deadline:** September 30, 2026 at 11:59 PM UTC  
**Primary Strategic Objective:** Improve competition matchup win rate over protected incumbent A7 while preserving A7's long-horizon physical choreography.  
**Stretch Target:** ~3000+ leaderboard rating region.  

---

## 1. Protected Incumbents & Governance Verification

Prior to any experimentation, code development, or dataset creation, all baseline dependencies, protected files, and governance partitions were verified:

| Component | File Path | Expected Digest / Range | Actual Verified Digest | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Slot B Incumbent (A7 Standalone)** | `candidates/v30_a7_standalone/main.py` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | **PASS (BIT-IDENTICAL)** |
| **Slot A Protected (V22R1 Archive)** | `submission_aec_v22r1.tar.gz` | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | **PASS (BIT-IDENTICAL)** |
| **Simulation Engine** | `kaggle_environments` | Version `1.32.7` | Version `1.32.7` | **PASS** |
| **V32 Dependency Registry** | `scripts/v32_common.py` | 12 component SHA-256 hashes | All 12 digests verified | **PASS** |

### Virgin Holdout Quarantine
The following partitions are strictly locked and quarantined. No discovery, model fitting, parameter tuning, or threshold selection will access them:
1. `214200–214249` (GATE0 virgin holdout)
2. `340090–340199` (Protected remainder cohort)
3. `249695–249734` (V32_CONFIRM single-touch holdout)

Authorized development and training seeds:
- `V32_TRAIN`: `249635..249674` (40 seeds)
- `V32_DEV`: `249675..249694` (20 seeds)

---

## 2. Comprehensive Audit of Predecessor Architectures

### A. V30 Standalone A7 (`candidates/v30_a7_standalone/main.py`)
- **Structure:** Standalone, pure-Python submission embedding the complete frozen V3 route-replay chassis (`_V3_SRC`), modifying only Step 0 market wash from 50/50 down to 30/30 (`_WASH30`).
- **Chassis Capabilities:** Contains 9 deterministic reactive layers:
  - `hand_align`: pads/truncates worker actions to actual hand count.
  - `weed_repair`: converts blocked actions to `DIG` and replays them when clear.
  - `sell_lead`: sells next step's scheduled lots 1 step early on off-cycle turns.
  - `front_run`: pre-empts opponent scheduled sales for premium goods.
  - `budget_guard`: checks 72-turn block funding and liquidates buffer stock if required.
  - `room_guard`: ensures shed inventory does not exceed 99 at day boundaries.
  - `clamp_sells`: trims `SELL` volume to projected shed inventory.
  - `dead_stock`: liquidates goods never referenced by the remainder tape.
  - `terminal_liquidation`: dumps remaining shed inventory at $t \ge 718$.
- **Strengths:** Produces unmatched open-loop physical coordination (~$104,332 mean cash in self-play), zero weed contamination, and robust baseline cash accumulation.
- **Weaknesses:** Highly rigid; unable to adjust land, worker allocation, or crop choice in response to hostile market saturations or unexpected opponent dumping.

### B. V32 RL-X2 (`candidates/v32_rlx2/`)
- **Concept:** Attempted continuous macro-RL (PPO and offline Q-learning) issuing macro actions every $H=4$ ticks.
- **Outcome:** Severe negative result. Mean cash collapsed from ~$104k to ~$13.7k; win rate dropped from 83.3% to 11.1%.
- **Diagnosis:** Continuous low-level intervention disrupts the tick-exact synchronization of A7's workers, breaking plant-water chains, feeding cycles, and cash accumulation schedules.

### C. V32 P12 Options (`candidates/v32_p12_options/`)
- **Concept:** Formulated interventions as discrete, bounded macroeconomic options (O01..O06) over $H=4$ ticks, requiring mandatory resynchronization and return to A7.
- **Outcome:** Proved that physical resynchronization is achievable ($D_{\text{resync}} = 0.0$ by $t+28$ ticks). However, closed-loop evaluation showed that the discovered options (e.g. land expansion O01) failed across different opponent regimes:
  - Mean cash dropped from $104,332 to $101,004 (-$3,328 delta vs A7).
  - Downside tail: worst-case loss of -$26,853.
  - Win rate dropped from 83.3% to 56.7%.
- **Diagnosis:** Generic macro options (such as buying a 4th quadrant of land) locked up liquid capital ($4,000 capex) and exposed the farm to spot price crashes when facing crop competitors, leading to delayed wage/feed insolvency.

### D. V33 Meta-Strategy (`candidates/v33_meta_strategy/`)
- **Concept:** Meta-selection among 6 elite routes (`R0_A7`, `R1_V22R1`, `R2_DMITRII`, `R3_P3090`, `R4_V54`, `R5_V25P3`), with early observable regime classification and market sell-reordering overlays.
- **Outcome:** A7 demonstrated strict transitive dominance (96.0% round-robin win rate, 88.3% league win rate). Unconditional switching produced an catastrophic -$8,433 downside tail, and market sell-reordering degraded league win rate by -5.0% absolute. The selective controller abstained 100% of the time, resulting in +0.0% incremental win rate.
- **Methodological Flaw Identified:** V33's experimental datasets (`regime_dataset.jsonl` and `selector_dataset.jsonl`) used ground-truth opponent identities and seed parameters to generate labels, and route transition tests spliced incompatible agent state machines into an A7 farm state.

---

## 3. The V34 Architectural Paradigm

V34 addresses the fundamental insight discovered through V30, V32, and V33:

```
A7 is an expert trajectory with near-optimal macro and micro physical choreography.
Wholesale route switching or continuous macro replacement is destructive.
However, A7 executes open-loop actions that are occasionally suboptimal under specific,
observable local market and opponent conditions.
```

Instead of replacing A7:
1. **Preserve A7 as the universal default backbone.**
2. **Identify sparse, high-information tactical decision points** (e.g., sale ordering, purchase timing, resource reservation).
3. **Evaluate localized, A7-compatible tactical actions** using exact forward lookahead in the simulator.
4. **Enforce multi-horizon evaluation** (+4, +8, +16, +32, +64, +128, terminal) to verify that short-term gains compound rather than reverse.
5. **Enforce fail-closed liquidity and physical synchronization guards.**
6. **Distill validated tactical opportunities into a sparse online detector**, falling back to A7 100% of the time whenever conditions are ordinary or uncertain.

---

## 4. Repository Verification Sign-off

- [x] A7 Standalone SHA-256 verified bit-identical.
- [x] V22R1 Tarball SHA-256 verified bit-identical.
- [x] Virgin holdout ranges locked.
- [x] Simulation environment version 1.32.7 confirmed.
- [x] Six-opponent league loader verified.
- [x] Repository audit approved for V34 execution.
