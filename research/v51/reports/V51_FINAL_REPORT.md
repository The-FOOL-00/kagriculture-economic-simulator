# V51 Final Research Report: Blocked-Action Recovery & Current Top-Meta Transfer

## Executive Summary & Mandatory Governance Decision

The V51 research program set out to investigate whether value lost when a deterministic action tape encounters an unexpected legal blocker could be recovered locally without altering the rest of the choreography:
$$\text{blocked action} \longrightarrow \text{queue intended action} \longrightarrow \text{clear blocker (DIG)} \longrightarrow \text{replay intended action}$$
This hypothesis was drawn from high-performing public competition artifacts, most notably Kaito Fukami's **v27 Midgame Meta Reset** and **v48 Fast Routes** (LB 3009), both of which employ a delayed replay buffer (`_weed_repair_action` / `scripts.v22_weed_repair`).

Following a complete forensic audit, isolated mechanism reconstruction, comprehensive blocked-action instrumentation (128 discovery legs = 92,032 turns), counterfactual evaluation across five repair variants (C0–C5) and four midgame transfer variants (M1–M5), and a fresh 576-leg out-of-sample ladder (2,304 total 719-step simulation matches across 9 elite and adversarial opponents), our empirical findings are unequivocal:

1. **Weed Repair is Mathematically Inert on V49**:
   - In Kaggriculture, weeds spawn probabilistically during night phases on uncultivated dirt.
   - The 2945 base choreography (Yusuke Hayashi EXP240 / R42) tilled all active farming plots during the early game and maintains tight continuous crop rotations.
   - Weeds *did* spawn on uncultivated periphery dirt tiles (280 tile-turns observed across 719 steps), but the 2945 static action tape **already contains pre-scripted `DIG` actions** at those exact tile-turns (e.g. step 405 `hand_6` at `(9,0)` with `DIG`; step 547 `hand_6` at `(8,2)` with `DIG`).
   - Consequently, V49 units **never** attempt an intended `PLANT` or `BUILD_PASTURE` on a `WEED` tile. Weed-blocked actions occurred **0 times across 128 discovery legs** (0.000%) and **0 times across 576 fresh validation legs** (0.000%).
   - The Weed Repair mechanism produced **$0.00 paired cash delta** and **0 action divergences** (100% bit-exact parity with V49).

2. **Section 12 Fail-Safe Rule Invoked**:
   - The research protocol mandated: *"If V49 naturally generates essentially no relevant weed-blocked actions: STOP. Do not force the mechanism into the candidate. Move immediately to: Midgame Meta Reset Forensics."*

3. **Midgame & Top-Meta Transfer Forensics**:
   - **M3 (Early Route Re-evaluation at Step 72)**: Proved inert ($0.00 delta, 0 activations), as V49's existing step 144 adaptive branch switch already captures macro divergence optimally.
   - **M4 (Sell Slot Priority Reordering)**: Produced **-$199.17 mean delta** (95% CI [-$221.75, -$177.38]) and **12 casualties**, dropping overall win rate from 99.31% to 97.22%. Reordering sell priority to favor animal products over basic crops prematurely throttled early-game crop liquidity needed for farm-hand recruitment.
   - **M5 (Market Demand Adaptation)**: Produced **-$114.98 mean delta** by holding back inventory during temporary price dips, stranding dead stock at game end.

4. **Phase 14 Promotion Gate**:
   - V51 Blocked Repair achieves 0 casualties and 99.31% WR, but fails criteria 3 (positive paired delta: +$0.00), criteria 4 (non-no-op 95% CI: [+0.00, +0.00]), criteria 5 (natural activation: 0), and criteria 6 (loss rescues: 0).
   - In accordance with the non-negotiable governance protocol:

```text
================================================================================
MANDATORY GOVERNANCE DECISION:
V49_RETAIN
================================================================================
```

Frozen Champion V49 remains the authoritative competition candidate.
`candidates/v51_blocked_repair/main.py` is preserved strictly as an audited, verified research artifact.

---

## 1. Governance & SHA256 Verification

| Component | Target File | SHA256 Checksum | Status |
| :--- | :--- | :--- | :--- |
| **Incumbent Champion** | `candidates/v49_meta_fusion/main.py` | `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11` | **FROZEN / UNTOUCHED** |
| **Frozen Baseline V48** | `candidates/v48_challenger/main.py` | `F8D13866C1204DA04D5B8E7B73477D714F031F00C637B5B557FE8E2A45299BA1` | **FROZEN / UNTOUCHED** |
| **Frozen Baseline V47** | `candidates/v47_elite_transfer/main.py` | `8872E99186A19266E3A595A96FE0D3C10433EBE8782E78C20202F52909C2C318` | **FROZEN / UNTOUCHED** |
| **Frozen Baseline V44** | `candidates/v44_economic_portfolio/main.py`| `58FDE865A1CD0890DFE204E639A4FFDAF99F440F6F50B62C7CCFBE18617D5F76` | **FROZEN / UNTOUCHED** |
| **V50 Research Artifact**| `candidates/v50_dead_action_guard/main.py` | `E3DC43B55EB0C7450CBE14A9EF212AE67B8E37E5C286B757834F259E66F1C80E` | **FROZEN / UNTOUCHED** |
| **V51 Research Candidate**| `candidates/v51_blocked_repair/main.py` | `1F0E92228642578CBF50885EA307707D317C826616498AF36ABF5EFE41A6795C` | **VERIFIED ARTIFACT** |

### Holdout Integrity Verification
All protected virgin holdout ranges were strictly quarantined throughout the entire V51 research lifecycle:
- `214200–214249` (Protected Virgin Holdout Range 1): **0 accesses**
- `340090–340199` (Protected Virgin Holdout Range 2): **0 accesses**
- `249695–249734` (Protected Virgin Holdout Range 3): **0 accesses**
- Submissions to Kaggle during V51 research: **EXACTLY 0**

---

## 2. Forensic Audit of Public Blocked-Action Leads

Our investigation audited three core public leads and one public discussion:
1. **Kaito Fukami: v27 Midgame Meta Reset (Score: 25/27 Strict-Future)**
   - Decompiled in `research/v51/external/KAITO_V27_FORENSICS.md`.
   - Identified mechanism: `_weed_repair_action(actor_idx, intended_action)`.
   - Trigger: Intended action is `PLANT` or `BUILD_PASTURE`, and actor's current tile is `WEED`.
   - Action: Issues `DIG`, stores intended action in `delayed_action_buffer[actor_idx]`, and re-evaluates next turn.
   - Scope: Strictly single-actor local. Does not rewind other actors or regenerate route tape.

2. **Kaito Fukami: v48 Fast Routes (LB 3009, 39/46 Top-10)**
   - Decompiled in `research/v51/external/KAITO_V48_FORENSICS.md`.
   - Packaging: Extracted into standalone module `scripts/v22_weed_repair.py`.
   - Integration: Called inside `FastRouteFollower._get_action_for_actor()`.
   - Key finding: Kaito's routes are generated dynamically using `a_star_planner` on partially cleared maps where weeds frequently spawn on intended planting routes.

3. **Rayk Kretzschmar & Public Discussion ("What actually predicted the ladder")**
   - Documented in `research/v51/external/BLOCKED_ACTION_PUBLIC_EVIDENCE.md`.
   - Consensus: Local repair loops prevent catastrophic choreographic stalls when static planners encounter dynamic obstacles.
   - Caveat: Static pre-compiled choreographies (such as 2945) that already include dirt cultivation routes have a fundamentally different obstacle profile than dynamic A* planners.

Full details preserved in [public_mechanisms.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v51/external/public_mechanisms.json).

---

## 3. Isolated Mechanism Reconstruction & Unit Testing

Before modifying V49, Kaito's weed repair mechanism was reconstructed cleanly in isolation:
- File: `research/v51/mechanisms/weed_repair_engine.py`
- Test Suite: `research/v51/mechanisms/test_weed_repair_engine.py`

### Test Suite Results (6/6 Passed):
1. **Farmer Blocker**: When farmer at `(5,5)` planned `PLANT WHEAT` on a `WEED` tile, engine substituted `DIG`, recorded buffer, and replayed `PLANT WHEAT` at step 10 when the tile was cleared.
2. **Farm Hand Blocker**: Identical local behavior verified for `hand_1` through `hand_6`.
3. **Simultaneous Multi-Actor Collisions**: Farmer and `hand_1` simultaneously blocked on weeds; both issued `DIG` independently without cross-talk.
4. **Consecutive Blockers**: Actor landing on two consecutive weeds properly cleared both before resuming route.
5. **Episode Reset**: State cleanly wiped across match boundaries.
6. **Seat Independence**: Seat 0 and Seat 1 coordinate frames and player state fully isolated.

---

## 4. Empirical Discovery: Blocked Action Corpus on V49

To determine whether V49 actually suffers from blocked actions, we instrumented the full simulation engine across 128 discovery matches (92,032 individual turns) against V44.

### Observed Blocker Taxonomy & Frequencies:
| Blocker Category | Description | Intended Action | Observed Events | Frequency |
| :--- | :--- | :---: | :---: | :---: |
| **B1 — WEED Blocker** | Tile is `WEED` on planting or pasture | `PLANT` / `BUILD_PASTURE` | **0** | **0.000%** |
| **B2 — PATH/Occupancy** | Unit movement blocked by coworker | `MOVE` | 0 | 0.000% |
| **B3 — Resource Blocker** | Insufficient seeds or money | `PLANT` / `BUY` | 0 | 0.000% |
| **B4 — Timing Blocker** | Nightfall / market closure | Market orders | 0 | 0.000% |
| **B5 — Route-State Divergence**| Dynamic market divergence vs tape | Route macro | 11 matches | 8.59% |
| **B6 — Storage/Shed Blocker** | Inventory full | `HARVEST` | 0 | 0.000% |
| **B7 — Terminal Window** | Late-game investment stranded | Late planting | 0 | 0.000% |

### Why B1 Weed Blockers Never Occur in V49:
1. **Active Cultivation**: The 2945 choreography cultivates all internal agricultural plots during the early game. In Kaggriculture, weeds never spawn on cultivated farmland.
2. **Pre-Scripted Dig Actions**: Weeds that spawned on uncultivated periphery dirt tiles (e.g. `(9,0)` and `(8,2)`) were already accounted for in the original tape:
   - Step 405: `hand_6` at `(9,0)` has pre-scripted `DIG`.
   - Step 547: `hand_6` at `(8,2)` has pre-scripted `DIG`.
3. V49 units never attempt `PLANT` or `BUILD_PASTURE` on an uncultivated dirt tile.

Full corpus archived in [v49_blocked_action_corpus.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v51/blocked_actions/v49_blocked_action_corpus.json) and [v49_blocked_action_report.md](file:///c:/Users/Sundareswaran/Kagriculture/research/v51/blocked_actions/v49_blocked_action_report.md).

---

## 5. Loss-Rescue Forensics on Historical V49 Losses

We audited all 11 historical V49 losses against elite opponents to evaluate whether any loss was caused by blocked actions:
- Artifact: [V49_BLOCKED_ACTION_LOSS_TABLE.md](file:///c:/Users/Sundareswaran/Kagriculture/research/v51/losses/V49_BLOCKED_ACTION_LOSS_TABLE.md)

### Audit Findings:
- **Weed Blockers in Any Loss Game**: **EXACTLY 0**.
- **Root Cause of Losses**:
  - **7 / 11 Losses**: V44 Step 36 Goose Arbitrage (V44 opens with an early Goose buy at Step 36, banking an immediate +$1,400 liquidity float that snowballs into earlier farm-hand purchases).
  - **2 / 11 Losses**: Step 144 Animal Scaling Delay (Sheep price divergence).
  - **2 / 11 Losses**: Worker congestion bottlenecks at shared barn entrances.
- **Rescue Count with Weed Repair**: **0 / 11 (0.0%)**.

---

## 6. Counterfactual Experimentation (C0–C5 & M1–M5)

We evaluated 5 Blocked-Repair variants and 4 Midgame/Top-Meta variants across 64 paired legs each (128 runs per variant) against V44 on discovery seeds `[250400..250431]`:

### Part 1: Blocked-Repair Counterfactuals
| Variant | Mechanism Description | Mean Delta vs V49 ($) | 95% Bootstrap CI | Cand WR (%) | Rescues | Casualties | Active Legs |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **C0** | Raw V49 Baseline | +$0.00 | [+$0.00, +$0.00] | 93.75% | 0 | 0 | 0 / 64 (0%) |
| **C1** | Standard Weed Repair (8 replays) | +$0.00 | [+$0.00, +$0.00] | 93.75% | 0 | 0 | 0 / 64 (0%) |
| **C2** | Weed Repair (0 replays, DIG only)| +$0.00 | [+$0.00, +$0.00] | 93.75% | 0 | 0 | 0 / 64 (0%) |
| **C4** | Generalized Blocker Repair | +$0.00 | [+$0.00, +$0.00] | 93.75% | 0 | 0 | 0 / 64 (0%) |
| **C5** | Conservative Value-Preserving | +$0.00 | [+$0.00, +$0.00] | 93.75% | 0 | 0 | 0 / 64 (0%) |

*Conclusion*: Across all C-variants, active legs = 0, delta = $0.00. Weed repair is 100% inert on V49.

### Part 2: Midgame & Top-Meta Counterfactuals
| Variant | Mechanism Description | Mean Delta vs V49 ($) | 95% Bootstrap CI | Cand WR (%) | Rescues | Casualties | Active Legs |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **M1** | Weed Repair (Re-test) | +$0.00 | [+$0.00, +$0.00] | 93.75% | 0 | 0 | 0 / 64 (0%) |
| **M3** | Midgame Reset (Step 72) | +$0.00 | [+$0.00, +$0.00] | 93.75% | 0 | 0 | 0 / 64 (0%) |
| **M4** | Sell Slot Reordering | -$634.98 | [-$734.77, -$547.17] | 76.56% | 0 | **11** | 64 / 64 (100%) |
| **M5** | Market Demand Adaptation | -$114.98 | [-$179.50, -$59.37] | 93.75% | 0 | 0 | 56 / 64 (87.5%) |

*Conclusion*:
- M3 is inert because Step 72 wheat prices do not diverge sufficiently to trigger branch changes.
- M4 causes severe capital starvation (11 casualties against V44).
- M5 strands unsold inventory at game end.

Full data preserved in [v51_blocked_repair_results.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v51/counterfactuals/v51_blocked_repair_results.json) and [v51_midgame_mechanism_results.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v51/counterfactuals/v51_midgame_mechanism_results.json).

---

## 7. Fresh Validation Benchmark (Phases 11 & 13)

Conducted across **576 fresh paired legs per candidate** (32 fresh seeds $\times$ 2 seats $\times$ 9 opponents = 2,304 total simulation matches):
- Elite Opponents: `V44`, `dmitrii_lb2800`, `tetsutani_pasture`, `kaitofukami_v48_3009`, `indarkarhana_top10`, `saiteja_mega_3000`
- Adversarial Opponents: `DAIRY_FLOOD`, `WOOL_FLOOD`, `TERMINAL_DUMPER`

### Grand Results Summary:
| Candidate | Elite Delta ($) | Adv Delta ($) | Overall Mean Delta ($) | 95% Bootstrap CI | Overall WR (%) | Rescues | Casualties | Active Legs |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V49_Meta_Fusion** | +$0.00 | +$0.00 | **+$0.00** | [+$0.00, +$0.00] | **99.31%** | — | — | 0 / 576 |
| **V51_Blocked_Repair** | +$0.00 | +$0.00 | **+$0.00** | [+$0.00, +$0.00] | **99.31%** | 0 | 0 | **0 / 576** |
| **V51_Midgame_Reset_Variant** | +$0.00 | +$0.00 | **+$0.00** | [+$0.00, +$0.00] | **99.31%** | 0 | 0 | **0 / 576** |
| **V51_Sell_Reorder_Variant** | -$296.71 | -$4.09 | **-$199.17** | [-$221.75, -$177.38] | **97.22%** | 0 | **12** | 394 / 576 |

Full data preserved in [v51_fresh_ladder.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v51/benchmarks/v51_fresh_ladder.json) and [V51_FINAL_LADDER.md](file:///c:/Users/Sundareswaran/Kagriculture/research/v51/reports/V51_FINAL_LADDER.md).

---

## 8. Compliance with Promotion Gate (Phase 14)

| Gate Condition | Requirement | Empirical Result | Gate Status |
| :--- | :--- | :--- | :---: |
| **1. Casualties** | Exactly 0 casualties | 0 casualties observed | **PASS** |
| **2. Fresh Win Rate** | WR $\ge$ V49 | 99.31% == 99.31% | **PASS** |
| **3. Economic Delta** | Positive paired cash delta | +$0.00 (Exact zero) | **FAIL** |
| **4. Confidence Interval**| 95% CI supports non-no-op | 95% CI: [+0.00, +0.00] | **FAIL** |
| **5. Natural Activation**| Activates in fresh matches | 0 activations / 576 legs | **FAIL** |
| **6. Loss Rescues** | $\ge 1$ failure/near-tie rescued | 0 rescues | **FAIL** |
| **7. Generalization** | Effect across multiple opps | Inert across all 9 opps | **FAIL** |
| **8. Terminal Liquidation**| No negative interaction | Verified safe | **PASS** |
| **9. Choreography Drift**| 0 unexplained drift | Exact parity (0 drift) | **PASS** |
| **10. Runtime Safety** | Safe execution | <0.5 ms per turn | **PASS** |

### Scientific Verdict:
Because Criteria 3, 4, 5, 6, and 7 failed, V51 cannot be promoted over V49.
In accordance with Section 17 (*"If V51 produces no robust alpha: V49_RETAIN is the correct scientific result. Do not manufacture a candidate merely because the version number advanced."*):

**FINAL VERDICT**: `V49_RETAIN`

---

## 9. Artifact Manifest

| Category | Artifact Path | Description |
| :--- | :--- | :--- |
| **External Forensics** | `research/v51/external/KAITO_V27_FORENSICS.md` | Audit of Kaito v27 Midgame Meta Reset |
| **External Forensics** | `research/v51/external/KAITO_V48_FORENSICS.md` | Audit of Kaito v48 Fast Routes (LB 3009) |
| **External Forensics** | `research/v51/external/BLOCKED_ACTION_PUBLIC_EVIDENCE.md`| Audit of public discussion & ladder leads |
| **External Forensics** | `research/v51/external/public_mechanisms.json` | Extracted public mechanism catalog |
| **Isolated Engine** | `research/v51/mechanisms/weed_repair_engine.py` | Isolated WeedRepairEngine implementation |
| **Unit Test Suite** | `research/v51/mechanisms/test_weed_repair_engine.py`| 6 unit tests verifying blocker state machine |
| **Corpus** | `research/v51/blocked_actions/v49_blocked_action_corpus.json`| 128-leg full-terminal blocker audit |
| **Corpus Report** | `research/v51/blocked_actions/v49_blocked_action_report.md` | Analysis of V49 blocker immunity |
| **Loss Forensics** | `research/v51/losses/V49_BLOCKED_ACTION_LOSS_TABLE.md` | Forensic audit of all 11 V49 losses |
| **Counterfactuals** | `research/v51/counterfactuals/v51_blocked_repair_results.json`| C0–C5 counterfactual results |
| **Counterfactuals** | `research/v51/counterfactuals/v51_midgame_mechanism_results.json`| M1–M5 top-meta transfer results |
| **Fresh Ladder Data** | `research/v51/benchmarks/v51_fresh_ladder.json` | 576-leg raw fresh validation metrics |
| **Ladder Report** | `research/v51/reports/V51_FINAL_LADDER.md` | Complete fresh validation ladder |
| **Final Report** | `research/v51/reports/V51_FINAL_REPORT.md` | This document |
| **Candidate Artifact** | `candidates/v51_blocked_repair/main.py` | Assembled V51 research artifact |
| **Completion Marker** | `research/v51/COMPLETE` | Formal cycle completion marker |
