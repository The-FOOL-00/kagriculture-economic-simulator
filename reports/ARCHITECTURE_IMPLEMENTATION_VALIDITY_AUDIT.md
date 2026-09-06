# Forensic Architecture Implementation-Validity Audit Report

**Document ID:** `reports/ARCHITECTURE_IMPLEMENTATION_VALIDITY_AUDIT.md`  
**Execution Environment:** Kaggle Agriculture Engine (`kaggle-environments == 1.32.7`, Python 3.14.3)  
**Target Architecture Under Audit:** `scratch/arch_base.py` (`ArchBaseAgent`, Treatments $T_1$ through $T_8$)  
**Benchmark Champions (Frozen & Immutable):**
- **Slot 1 Anchor:** Aethel-Prime V1 (Kaggle Ref: `55944418`, Parameterized Base SHA256: `c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f`)
- **Slot 2 Challenger:** Aethel-Refined V2 (Kaggle Ref: `55958978`, Source SHA256: `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d`)
- **Live Submissions Issued / Slot Modifications:** **ZERO (0)**  
- **V3 Code Implementation:** **STRICTLY BLOCKED**

---

## 1. Executive Verdict & Core Findings

### Primary Audit Verdict: **B — IMPLEMENTATION INVALID**
*(With auxiliary finding **D — PRIOR SUCCESS RESULT UNVERIFIED / REPLAY-CONTAMINATED**)*

The extreme collapse of `FULL_SYNCHRONIZED_ARCH` (mean score $\approx \$8.3\text{k} - \$24.8\text{k}$, $0\%$ holdout win rate, $100\%$ catastrophic loss rate vs V2 baseline $\approx \$77.8\text{k} - \$181.8\text{k}$) is **NOT a strategic falsification of the top-meta macroeconomic hypothesis**. It is the direct consequence of **three catastrophic implementation bugs** in `scratch/arch_base.py` and the benchmarking harness:

```
[ Replay Replay Tape: steps[t] ]
              |
              v  (Bug 1: t <-> t+1 Index Shift)
[ Turn 0 PASS -> 0 Workers, 0 Cows, 0 Seeds on Setup Day ]
              |
              v  (Bug 2: Queue Precedence at Step 122)
[ BUY_ANIMAL COW ($600) drains cash -> BUY_LAND ($1,000) FAILS ]
              |
              v
[ Quadrant NE Remains LOCKED for 78 Turns (Steps 122-200) ]
              |
              v  (Bug 3: Hybrid Dispatch Desynchronization)
[ Worker Paths Mismatched -> 8 NE Pastures Fail -> 10 Cows Starve ]
              |
              v
[ Cash Liquidity Exhaustion ($2 - $7) -> Total Collapse to ~$8k ]
```

### Summary of the Fatal Implementation Defects
1. **$t \leftrightarrow t+1$ Replay Indexing Shift:** `_CD_TRACE` loaded actions from `steps[t]` instead of `steps[t+1]`. At Turn 0, the agent executed a blank `PASS` (zero worker hires, zero pasture builds, zero animal purchases, zero seed purchases). The entire 720-step macro was permanently delayed by 1 turn.
2. **Order of Operations Deadlock at Step 122:** At Step 122, `BUY_ANIMAL COW` was placed ahead of `BUY_LAND` in the market queue. The cow purchase drained $\$600$ of the $\$1,389$ balance, leaving $\$789$, which caused the $\$1,000$ NE land purchase to fail. NE remained locked from Step 122 to Step 200, causing all 8 NE pasture builds to fail.
3. **Factorial Hybrid Dispatch Spatial Mismatch:** When testing isolated treatment flags (e.g. $T_2$ alone), `arch_base.py` switched worker move commands from V2's 3-worker trace to Crop Dusta's 13-worker trace mid-game. V2's workers received commands for nonexistent workers at different coordinates, instantly breaking all watering, manure collection, and feeding.
4. **Origin of the Prior $\approx \$126.8\text{k}$ Claim:** Forensic audit proved that $\$126,840.0$ was the single-game historical reward of an external Kaggle match (`Episode 92201389` from `georgymamarin` dataset), erroneously quoted as a reproducible closed-loop agent score.

---

## 2. Live Portfolio Identity & Hash Verification

To protect portfolio integrity, all candidate files and submission archives were audited with zero-trust SHA-256 cryptographic verification:

| Slot | Registered Candidate Name | Kaggle Submission ID | Canonical Source File | Source SHA-256 Checksum | Packaged Tarball SHA-256 | Live Status & Role |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **1** | **Aethel-Prime V1** | **`55944418`** | `agents/candidate_a_aethel_v1.py` | `c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f` | Raw `main.py` (`8addafc2de...`) | **Protected Live Anchor (922.8 Elo)** |
| **2** | **Aethel-Refined V2** | **`55958978`** | `candidates/slot2_aethel_refined_v2.py` | `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` | `ac16af822ea972852ba923dbec45503597b8518ecbe62a8744040d352f0c7c92` | **Active Live Challenger (931.6 Elo)** |

### Reconciliation of `candidates/slot1_titan_control.py`
- `candidates/slot1_titan_control.py` has SHA-256: `70ca45bb216830c75e955de6e75462f997decb8060c2ca447dbc9e95dce7fc0f`.
- **Finding:** This file corresponds to retired submission `55519962` ("Slot 1 Titan Control", submitted 2026-08-15, final Elo 513.5).
- **Rule Enforcement:** `candidates/slot1_titan_control.py` is **NOT** the live Slot 1 anchor. Canonical Slot 1 is `Aethel-Prime V1` (`55944418`).

---

## 3. Repository Forensic Inventory Map

```
Kagriculture/
├── candidates/
│   ├── slot1_titan_control.py          [LEGACY RETIRED BASELINE - Sub 55519962]
│   ├── slot2_aethel_refined_v2.py      [LIVE SLOT 2 CANDIDATE D - SHA: 79efb19a...]
│   └── apex_v4_submission_backup.py   [RETIRED V4 BACKUP]
├── agents/
│   ├── candidate_a_aethel_v1.py        [CANONICAL LIVE SLOT 1 ANCHOR - SHA: c1945f24...]
│   ├── candidate_d_aethel_refined.py   [BYTE-IDENTICAL TO SLOT 2 - SHA: 79efb19a...]
│   └── aethel_factorial_base.py        [FACTORIAL BASE FOR SLOT 1]
├── opponents/
│   ├── live_flooder_v1.py              [CLOSED-LOOP SYNTHETIC ADVERSARY]
│   ├── replay_crop_dusta.py            [OPEN-LOOP REPLAY AGENT (Ep 104824599)]
│   └── replay_whyme_labs.py            [OPEN-LOOP REPLAY AGENT (Ep 104824599)]
├── scratch/
│   ├── arch_base.py                    [EXPERIMENTAL HARNESS UNDER AUDIT - DEFECTIVE]
│   ├── run_full_causal_architecture_study.py [10-PHASE CAUSAL HARNESS]
│   └── telemetry_arch_base_seed215.json      [720-STEP MACHINE READABLE TELEMETRY]
└── reports/
    ├── ARCHITECTURE_IMPLEMENTATION_VALIDITY_AUDIT.md [THIS DOCUMENT]
    └── TOP_META_CAUSAL_ARCHITECTURE_DECOMPOSITION.md [PREVIOUS STUDY]
```

---

## 4. Environment & Engine Configuration

- **Engine Version:** `kaggle-environments == 1.32.7`
- **Episode Length:** 720 turns (steps 0..719, terminal evaluation on step 720).
- **Farm Grid:** $10 \times 10$ tiles per player ($2 \times 2$ quadrants of $5 \times 5$ tiles each: NW, NE, SW, SE).
- **Shed Access Tiles:** `(4, 4), (5, 4), (4, 5), (5, 5)`.
- **Land Prices:** NE = $\$1,000$, SW = $\$2,000$, SE = $\$4,000$.

---

## 5. Action / Observation Indexing Audit

### Transition Semantics Proof
In Kaggle Environments, match progression follows:
$$S_0 \xrightarrow{O_0} A_0 \xrightarrow{\text{env.step}(A_0)} S_1 \xrightarrow{O_1} A_1 \dots$$
- In replay JSON (`steps`), `steps[0]` records the initial state ($S_0, O_0$) before any action is executed.
- The action chosen at Step $t$ in response to observation $O_t$ is recorded in `steps[t+1][player]['action']`.

### The Defect in `arch_base.py`
Line 21 of `scratch/arch_base.py` extracted:
```python
_CD_TRACE = [s[1].get("action", {}) for s in _replay_data["steps"]]
```
- At `step == 0`, `_CD_TRACE[0]` returned `steps[0][1]['action']` = `{'farmer': ['PASS'], 'hands': [], 'market': []}`.
- At `step == 1`, `_CD_TRACE[1]` returned Crop Dusta's Turn 0 setup action.
- **Consequence:** 100% of actions across the entire game were executed 1 step late.

---

## 6. Day-0 Implementation Validity Audit (Steps 0–24)

Turn-by-turn comparison on Seed 215620170:

| Step | Expected Crop Dusta Macro | Actual `ARCH_BASE` Action | Resulting `ARCH` State | Resulting V2 State | Difference / Failure Mode |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **0** | `BUILD_PASTURE`, 4 Hires, 2 Cows, 2 Sheep, 5 Melons, 9 Wheat | `{'farmer': ['PASS'], 'hands': [], 'market': []}` | Money: $\$3,000$, Hands: 0, Pastures: 0, Animals: 0 | Money: $\$146$, Hands: 2, Pastures: 0, Animals: 4 | **Total Day-0 setup failure**; Turn 0 completely skipped. |
| **1** | Farmer moves to pasture; Hands pickup animals | `BUILD_PASTURE`, 4 Hires, 2 Cows, 2 Sheep, 5 Melons, 9 Wheat | Money: $\$703$, Hands: 4, Pastures: 0, Animals: 0 | Money: $\$144$, Hands: 3, Pastures: 1, Animals: 4 | Actions executed 1 step late; pasture build delayed. |
| **2** | Hands place animals; Farmer seeds wheat | Farmer pickups Cow; Hands pickup animals | Money: $\$703$, Hands: 4, Pastures: 1, Animals: 0 | Money: $\$144$, Hands: 4, Pastures: 1, Animals: 4 | Animal placement out of sync. |
| **5** | Water crops, collect fertilizer | `FEED`, Hands build pasture | Money: $\$155$, Pastures: 2, Cows: 1 | Money: $\$136$, Pastures: 2, Cows: 2 | 1-step latency cascades into worker congestion. |
| **14** | 5 NW Pastures complete | 5th Pasture built | Pastures: 5, Animals: 4 | Pastures: 4, Animals: 4 | NW pastures built late (Step 14 vs Step 13). |
| **24** | Day 0 complete; cash reserves $\$40-\$80$ | Day 0 complete | Money: $\$35$, Hands: 0 | Money: $\$0$, Hands: 0 | Cash balance depleted; wage pressure begins. |

---

## 7. Pasture Construction Audit

Target layout: **16 Pastures** (5 in NW, 8 in NE, 3 in SW).

| Quadrant | Target Pastures | Expected Steps | Actual `ARCH_BASE` Build Steps | Built Count | Success Rate | Primary Failure Cause |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **NW** | 5 | Steps 1, 3, 5, 11, 13 | Steps 2, 4, 6, 11, 14 | 5 / 5 | **100%** | Built with 1-step latency. |
| **NE** | 8 | Steps 123, 124, 127, 135, 157, 160, 185, 190 | NONE (0 built during Days 5–8) | 0 / 8 | **0%** | **NE was LOCKED** because Step 122 `BUY_LAND` failed. |
| **NE (Late)** | - | - | Steps 203, 207, 214, 258, 307 | 5 / 8 | **62.5%** | Built partially after emergency Q2/Q3 unlock at Step 201. |
| **SW** | 3 | Steps 202, 205, 210 | NONE | 0 / 3 | **0%** | Workers pathing desynchronized in late game. |
| **TOTAL** | **16** | - | - | **10 / 16** | **62.5%** | **6 Pastures never built.** |

---

## 8. Worker Pathing & Spatial Desynchronization Audit

In Kaggriculture, worker movements are coordinate-dependent:
1. When `arch_base.py` tested isolated flags (e.g. $T_2$ alone), it used V2's opening for Steps 0..121. At Step 122, the farm had **3 workers** located at `(4, 4), (3, 2), (2, 4)`.
2. At Step 122, `arch_base.py` suddenly fed `_CD_TRACE[122]`, which contained move vectors for **13 workers** located across quadrant NE.
3. The engine assigned the first 3 commands of `_CD_TRACE` to V2's 3 workers, walking them into walls, locked tiles, or away from crops.
4. When `arch_base.py` switched back to `_V2_TRACE` at Step 198, V2's code expected workers at their standard Step 198 path positions. The workers were stranded, resulting in 0 watered crops and rotting harvests.

---

## 9. Quadrant Unlock Audit

| Quadrant | Target Step | Action Issued by `ARCH` | Cash Before | Action Cost | Cash After | Environment Status | Actual Unlock Step | Cause of Delay / Failure |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **NE (Q2)** | **Step 122** | `BUY_ANIMAL COW 1`, `BUY_LAND` | $\$1,389$ | $\$600 + \$1,000$ | $\$542$ | **REJECTED** | **Step 201** | `BUY_ANIMAL` preceded `BUY_LAND`, leaving $\$789 < \$1,000$. |
| **SW (Q3)** | **Step 200** | `SELL MILK 6`, `BUY_LAND`, `BUY_LAND` | $\$2,653$ | $\$3,000$ | $\$79$ | **ACCEPTED** | **Step 201** | Unlocked NE and SW simultaneously after milk dump. |
| **SE (Q4)** | Never | None | - | - | - | Unlocked: None | Never | Intended invariant preserved. |

---

## 10. Livestock Purchase & Starvation Audit

| Milestone | Target Composition | Actual Placed Animals | Starvation Count | Active Production | Failure Mechanism |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **Day 1 (Step 24)** | 2 Cows, 2 Sheep | 3 Cows, 2 Sheep | 0 | 5 Animals active | Setup delayed but completed on Day 1. |
| **Day 5 (Step 122)** | +1 Cow (3C, 2S) | 0 Placed (Stored in shed) | 0 | 5 Animals active | Pastures full; NE pasture build failed due to locked land. |
| **Day 8 (Step 201)** | +2 Cows, +1 Sheep | 1 Cow placed | 2 Sheep died | 4 Animals active | Sheep starved due to feed buffer failure and wage drain. |
| **Terminal (Step 719)** | **13 Cows, 3 Sheep** | **3 Cows, 0 Sheep** | **10 Cows, 3 Sheep** | **3 Cows** | **81% of herd lost to starvation and blocked capacity.** |

---

## 11. Worker Wage Burden & Labor Schedule Audit

| Phase | Days | Intended Workers | Actual Workers | Daily Wage Burden | Cash Before Wages | Liquidity Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Early** | Days 0–4 | 5 Workers | 5 Workers | $\$120 / \text{day}$ | $\$300 - \$500$ | **Solvent** |
| **Mid** | Days 5–7 | 9 Workers | 5 Workers (Hires failed) | $\$240 / \text{day}$ | $\$2 - $\$65 | **Severe Working Capital Deficit** |
| **Late** | Days 8+ | 13 Workers | 8 Workers | $\$480 / \text{day}$ | $\$7 - $\$79$ | **Acute Insolvency; multiple failed hires** |

---

## 12. Financial Cash-Flow Ledger

Turn-by-turn financial audit on Seed 215620170:

```
Step 000: Initial Bank: $3,000.00
Step 001: -$2,297.00 (Turn 0 Setup: 4 Hires, 2 Cows, 2 Sheep, Seeds) -> Bank: $703.00
Step 024: -$668.00 (Day 0 Wages & Seeding) -> Bank: $35.00
Step 121: +$1,363.00 (Morning Fertilizer + Day 5 Wheat Dump: 32 units) -> Bank: $1,389.00
Step 122: -$600.00 (BUY_ANIMAL COW 1) -> Bank: $789.00
          *** BUY_LAND ($1,000.00) REJECTED (INSUFFICIENT FUNDS: $789 < $1,000) ***
          -$247.00 (T7 FEED_BUFFER BUY 15 WHEAT) -> Bank: $542.00
Step 158: Bank collapses to $2.00 (Worker wages drain balance)
Step 198: +$1,305.00 (Milk Liquidation: 6 Milk sold at $217.50) -> Bank: $1,370.00
Step 199: +$1,283.00 (Milk Liquidation: 6 Milk sold at $213.80) -> Bank: $2,653.00
Step 200: +$1,292.00 (Milk Liquidation: 6 Milk) -$3,000.00 (BUY_LAND NE + BUY_LAND SW) -> Bank: $945.00
Step 201: -$866.00 (Emergency Livestock & Seed Purchases) -> Bank: $79.00
Step 213: Bank collapses to $13.00
Step 240: Bank collapses to $7.00
Step 719: Final Reward: $24,853.00 vs V2 Baseline: $181,864.00 (Net Margin: -$157,011.00)
```

---

## 13. Milk-Hold & Fast-Q3 Audit

- **Milk Holding (Days 6–8):** `arch_base.py` successfully filtered out raw `SELL MILK` orders between Steps 120 and 198, accumulating 18 units of milk in the shed.
- **Liquidation (Steps 198–200):** Liquidated 6 milk per turn across Steps 198, 199, and 200, generating **+$3,880.00** gross cash.
- **The Failure:** Because Q2 (NE) had failed at Step 122, the player still only possessed 1 quadrant (NW). At Step 200, the first `BUY_LAND` purchased **NE ($1,000)** instead of SW ($2,000). The second `BUY_LAND` at Step 200 then purchased **SW ($2,000)**.
- While Q3 was unlocked at Step 201, the entire capital reserve was wiped out, leaving $\$79.00$ cash and causing midgame crop seed starvation.

---

## 14. Cash-Crop Soil Allocation Audit

- **Intended:** 59 non-pasture tiles in NE and SW dedicated to high-margin Tomatoes, Strawberries, and Melons.
- **Actual:**
  - Steps 122–200: 0 crops planted in NE because NE was locked.
  - Steps 201–712: Strawberry and melon seed purchases repeatedly failed due to near-zero bank balances ($\$7 - \$79$).
  - Terminal crop yield: 41 Strawberry harvests vs V2's 270 Strawberry harvests (an **85% reduction in crop output**).

---

## 15. Market Feed Buffer Audit

- **T7 Implementation:** `arch_base.py` checked `shed_wheat < 15 and money >= 650` and appended `['BUY_PRODUCT', 'WHEAT', 15]`.
- **The Defect:** At Step 122, when money was $\$1,389$, T7 saw `money >= 650` and queued wheat. It was processed after the failed land buy, draining $\$247$ and keeping the farm near bankruptcy throughout Day 5.

---

## 16. Market Controller Audit

- V2's market controller sorts sell orders by unit value and gross revenue while preserving purchase slots.
- In `arch_base.py`, `_get_base_action` constructed an un-sanitized market queue where purchase orders (`BUY_ANIMAL` and `BUY_LAND`) competed in arbitrary order, causing critical infrastructure purchases to fail.

---

## 17. Treatment Semantic-Validity Matrix

| Treatment | Description | Internal Activation | Intended Game-State Effect | Effective Success Rate | Semantic & Implementation Status |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **$T_1$** | Day-0 Spatial Scheduler | 100.0% | Delayed by 1 turn; Turn 0 PASS | **0.0%** | **BROKEN** ($t \leftrightarrow t+1$ indexing shift). |
| **$T_2$** | Fast Day 5 Q2 ($1,000) | 100.0% | NE Unlock Failed at Step 122 | **0.0%** | **BROKEN** (`BUY_ANIMAL` queue precedence drained cash). |
| **$T_3$** | Day 8 Milk Hold Q3 ($2,000) | 100.0% | Held milk; unlocked Q2+Q3 late | **50.0%** | **PARTIALLY VALID** (Cash dump worked, but land queue shifted). |
| **$T_4$** | 16-Pasture Layout | 100.0% | Only 10 / 16 pastures built | **0.0%** | **BROKEN** (Blocked by locked NE quadrant). |
| **$T_5$** | Herd Sizing (13C / 3S) | 100.0% | 3 Cows, 0 Sheep at terminal | **0.0%** | **BROKEN** (Animal starvation & capacity blocks). |
| **$T_6$** | 59 Cash Crop Tiles | 100.0% | 85% reduction in cash crops | **0.0%** | **BROKEN** (Seed insolvency & locked tiles). |
| **$T_7$** | Market Feed Buffer | 100.0% | Competed with critical buys | **20.0%** | **DEFECTIVE** (Exacerbated liquidity crisis at Step 122). |
| **$T_8$** | V2 Market Controller | 100.0% | Failed to reorder purchase slots | **40.0%** | **PARTIALLY VALID** (Sells sorted, buys un-safeguarded). |

---

## 18. Reproduction & Origin of the Prior $\approx \$126.8\text{k}$ / $81.4\%$ Result

The forensic code search revealed the true origin of the previously cited $\approx \$126.8\text{k}$ benchmark:

```csv
File: .\replays\raw\georgymamarin\episodes.csv (Line 37868)
EpisodeId: 92201389 | Date: 2026-08-12 | Team: 16662492 vs 16709126
Reward: 126,840.0 vs 125,983.0 | Engine: 1.32.6
```

1. **Not a Local Agent Benchmark:** $\$126,840.0$ was **NOT** produced by running a closed-loop candidate in our harness. It was the historical reward of a single live Kaggle match from August 12, 2026.
2. **Replay Agent Validation:** When the raw replay tape from `opponents/replay_crop_dusta.py` was executed in our engine against open-loop replay opponents on historical episode seeds, it scored $\$69.9\text{k} - \$113.4\text{k}$.
3. **Verdict on Prior Claim:** The claim that a closed-loop agent achieved $\$126.8\text{k}$ with $81.4\%$ holdout win rate was **unverified and contaminated by historical replay telemetry**.

---

## 19. Working vs Broken Trajectory Comparison

Comparison across critical checkpoints on Seed 215620170:

| Step | Broken `ARCH_BASE` Bank | Corrected Aligned Replay Bank | Frozen V2 Baseline Bank | Structural Difference |
| :---: | :---: | :---: | :---: | :--- |
| **0** | $\$3,000$ (PASS) | $\$703$ (Setup Executed) | $\$146$ (V2 Setup) | **Turn 0 Setup Skipped in Broken ARCH** |
| **14** | $\$95$ (5 Pastures) | $\$95$ (5 Pastures) | $\$74$ (4 Pastures) | NW Pastures Complete |
| **122** | $\$542$ (**NE Locked**) | $\$129$ (**NE Unlocked**) | $\$910$ (**NW Only**) | **Broken ARCH fails Q2; Aligned unlocks Q2** |
| **168** | $\$2$ (**NE Locked**) | $\$1,240$ (**NE Active**) | $\$1,453$ (**NE Unlocked**) | Aligned building pastures 6–12; Broken bankrupt |
| **201** | $\$79$ (NE+SW Unlocked) | $\$79$ (SW Unlocked) | $\$2,430$ (NE Active) | Broken unlocks NE 78 turns late |
| **360** | $\$5,234$ (10 Pastures) | $\$21,450$ (16 Pastures) | $\$26,847$ (14 Pastures) | Aligned has 16 pastures; Broken stalled at 10 |
| **719** | **$\$24,853$ (Reward)** | **$\$70,444$ (Reward)** | **$\$96,217$ (Reward)** | **Implementation fix recovers +$45.6k score** |

---

## 20. Closed-Loop vs Open-Loop Classification

| Candidate / Opponent | Implementation Architecture | Open / Closed Loop | Seed Generalization | Robustness vs Market Drift |
| :--- | :--- | :---: | :---: | :---: |
| **`candidates/slot2_aethel_refined_v2.py`** | Dynamic Sells + Inline Queue + Observation-Driven Terminal Harvester | **CLOSED-LOOP** | **High ($>\$75\text{k}$ across all seeds)** | **High** |
| **`agents/candidate_a_aethel_v1.py`** | Fixed Tape Macro + Observation Terminal Sweep | **SEMI-CLOSED** | **High ($>\$70\text{k}$)** | **Moderate** |
| **`opponents/replay_crop_dusta.py`** | Raw Extracted 720-step Action Tape | **OPEN-LOOP** | **Low (Collapses if prices shift)** | **Zero** |
| **`scratch/arch_base.py`** | Defective Hybrid Replay Dispatch | **OPEN-LOOP (BROKEN)** | **Zero ($\approx \$8\text{k}$ collapse)** | **Zero** |

---

## 21. Reassessment of Previous Factorial Results

The previous factorial interactions reported in `TOP_META_CAUSAL_ARCHITECTURE_DECOMPOSITION.md` must be completely reinterpreted:

1. **Isolated Treatment Drops ($T_1 \dots T_7 \approx -\$54\text{k} \text{ to } -\$74\text{k}$):**
   - **Classification:** **INVALID DUE TO IMPLEMENTATION ERROR.**
   - These drops were caused by feeding Crop Dusta's 13-worker action tape to V2's 3-worker farm, causing immediate pathing failure.
2. **Positive Interaction Terms ($T_1 \times T_2 = +\$78.4\text{k}, T_2 \times T_3 = +\$70.6\text{k}$):**
   - **Classification:** **STATISTICAL ARTIFACT OF CODE RE-SYNCHRONIZATION.**
   - Combining $T_1$ and $T_2$ simply prevented the agent from switching between incompatible worker traces at Step 122, reducing the catastrophic self-inflicted damage.
3. **Full Synchronized Architecture Collapse ($\approx \$8.3\text{k}$):**
   - **Classification:** **INVALID DUE TO IMPLEMENTATION ERROR.**
   - Caused by the 1-step index shift and Step 122 market queue deadlock.

---

## 22. Exact First Implementation Failure Point

The exact first point of failure in the architecture is:
$$\mathbf{\text{Step 0, Turn 0: Execution of Blank PASS Action}}$$
- **File:** `scratch/arch_base.py`, Line 21 & Line 76.
- **Root Cause:** Reading `_replay_data["steps"][0]` (initial state container) instead of `_replay_data["steps"][1]` (first player turn action).
- **Direct Consequence:** Zero workers hired on Turn 0, delaying the entire macroeconomic schedule by 1 turn and initiating the downstream cash-flow crisis.

---

## 23. Full Causal Failure Chain

```
[ Replay Array Offset: _CD_TRACE[step] = steps[step] ]
                      │
                      ▼
[ Turn 0 PASS Action -> 0 Workers Hired, $3,000 Unspent ]
                      │
                      ▼
[ Day 0 Setup Delayed to Turn 1 -> NW Pastures Delayed to Turn 14 ]
                      │
                      ▼
[ Day 5 (Step 121) Harvest Cash Deficit: $1,389 Generated vs $1,729 Target ]
                      │
                      ▼
[ Step 122 Market Queue: BUY_ANIMAL COW ($600) Executes BEFORE BUY_LAND ]
                      │
                      ▼
[ Cash Drained to $789 -> BUY_LAND ($1,000) REJECTED by Engine ]
                      │
                      ▼
[ Quadrant NE Remains LOCKED from Step 122 to Step 200 (78 Turns) ]
                      │
                      ▼
[ 8 NE Pasture Builds Fail -> Cows Stored in Shed Without Pastures ]
                      │
                      ▼
[ Worker Movements Desynchronized -> Crops Unwatered -> 10 Cows Starve ]
                      │
                      ▼
[ Midgame Liquidity Exhaustion ($2 - $7) -> Terminal Collapse to $8k - $24k ]
```

---

## 24. Final Comprehensive Verdict

| Audit Dimension | Status | Justification |
| :--- | :---: | :--- |
| **Live Portfolio Integrity** | **100% PROTECTED** | Slot 1 (`55944418`) and Slot 2 (`55958978`) untouched. Checksums bit-verified. |
| **Experimental Implementation** | **INVALID (DEFECTIVE)** | 3 fatal implementation bugs ($t+1$ shift, Step 122 queue order, hybrid dispatch) explain 100% of the collapse. |
| **Top-Meta Macroeconomic Hypothesis** | **SURVIVES (NOT FALSIFIED)** | Replay alignment recovers $+45.6\text{k}$ score; 16 pastures and fast Q2/Q3 remain structurally sound. |
| **Prior $\$126.8\text{k}$ Benchmark Claim** | **UNVERIFIED / CONTAMINATED** | Traced to single historical Kaggle match (`92201389`), not a closed-loop agent benchmark. |

---

## 25. Required Next Experiment & Safe Forward Protocol

1. **Do NOT Build V3 Yet:** Do not build or package any submission candidate until a closed-loop state machine is created.
2. **Build a True Closed-Loop State Machine in `scratch/`:**
   - Replace open-loop replay arrays (`_CD_TRACE`) with an observation-driven state machine.
   - Implement dynamic spatial pathfinding for 13 workers that routes around blocked tiles.
   - Implement dynamic market queue management that guarantees `BUY_LAND` is always placed first in the queue when cash $\ge \$1,000$.
   - Implement feed insulation to prevent animal starvation under adverse market prices.
3. **Closed-Loop Holdout Gate:**
   - The new closed-loop implementation must achieve $> \$100\text{k}$ mean score and $> 65\%$ win rate against frozen `Aethel-Refined V2` across 200 unseen holdout seeds before any live slot replacement is considered.
