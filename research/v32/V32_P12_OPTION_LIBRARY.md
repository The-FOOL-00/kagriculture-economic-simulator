# V32 P12: Discrete Option Library & Governance (V32_P12_OPTION_LIBRARY)

**Phase:** V32 P12 (Sparse Options & Resynchronization)  
**Date:** 2026-09-24  
**Status:** QUALIFIED & LOCKED FOR EVALUATION  
**Incumbent Protection:** Default policy is strictly A7 (`candidates/v30_a7_standalone/main.py`). Options are temporary, bounded interventions ($H=4$ ticks) that must earn the right to override A7.

---

## 1. Option Architecture & Invariants

Each option is governed by an explicit `OptionContract`:
1. **Strict Horizon ($H = 4$ ticks):** An option executes for at most 4 simulator ticks, then terminates.
2. **Hard Return Invariant:** Return to A7 is unconditional and mandatory upon completion or early exit.
3. **Non-Stacking:** At most 1 option may be active at any given moment ($F_{\max} \le 1$). No nesting or recursion.
4. **Resynchronization Gate:** After an option terminates, the controller requires physical synchronization (`SYNCED`) and a minimum cooldown interval ($T_{\text{cooldown}} \ge 24$ ticks) before any new option can be considered.
5. **Fail-Closed Default:** If confidence is low, conditions are ambiguous, or desynchronization is detected, the controller reverts unconditionally to A7.

---

## 2. Option Registry & Specifications

| Option ID | Name | Candidate Action | Duration | Governance Status | Trigger Condition | Validated Alpha (Peak) | Post-Resync Status |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: | :---: |
| **O01** | `EXPAND_LAND` | 9 | 4 ticks | **QUALIFIED** | Step $\in [216, 360]$, Cash $\ge \text{NextLandCost} + \$1000$, Runway $\ge 2.5\text{d}$ | **+$11,179.00** | `SYNCED` (100%) |
| **O02** | `CROP_EXPANSION_MELON` | 4 | 4 ticks | **QUALIFIED** | Step $\in [72, 216]$, Arable $\ge 2$, Cash $\ge \$320$, Runway $\ge 2.0\text{d}$ | **+$2,128.00** | `SYNCED` (100%) |
| **O03** | `LIQUIDATE_SURPLUS` | 3 | 4 ticks | **QUALIFIED** | Step $\in [120, 360]$, Non-wheat shed units $\ge 6$ | **+$3,924.00** | `SYNCED` (100%) |
| **O04** | `OPPORTUNISTIC_SELL` | 1 | 4 ticks | **QUALIFIED** | Step $\in [200, 600]$, High-value shed inventory $\ge 4$ @ Spot Price $\ge \$15$ | **+$3,420.00** | `SYNCED` (100%) |
| **O05** | `PRESERVE_CASH` | 8 | 4 ticks | **SCREENED** | Runway $< 1.8\text{d}$ or Cash $< \$400$ | +$93.00 | `SYNCED` (100%) |
| **O06** | `SELECTIVE_PREEMPT_SELL`| 2 | 4 ticks | **SCREENED** | Step $\in [144, 650]$, Volatile shed inventory $\ge 2$ @ Spot Price $\ge \$25$ | +$25.00 | `SYNCED` (100%) |

---

## 3. Detailed Option Profiles

### Option O01: `EXPAND_LAND` (Quadrant Unlock)
* **Action Index:** 9 (`EXPAND_LAND`)
* **Underlying Mechanism:** A7 operates on an open-loop, conservative land allocation (typically 1 quadrant). On seeds with strong early liquidity (e.g. Seed 249635), farm cash reaches $15,000+ by Step 288 (Day 12). Purchasing quadrant 2 unlocks 25 arable tiles. Because A7's route continues farming existing plots while clearing new land on slack ticks, the expanded arable base allows subsequent melon plantings to mature before Day 27, yielding an enormous terminal payout.
* **Local vs Final Delta:**
  * At $t+4$: Cash is -$4,000.00 (land purchase expense).
  * At $t+28$: Cash is -$4,000.00 (crops actively growing).
  * At $t=719$: Cash is **+$11,179.00** (harvest liquidated).
* **Early Termination Rule:** If cash drops below $500 before land purchase completes, abort to A7.

### Option O02: `CROP_EXPANSION_MELON` (High-Value Seed Ramp)
* **Action Index:** 4 (`CROP_EXPANSION_MELON`)
* **Underlying Mechanism:** Accelerates the acquisition of high-margin melon seeds at Day 3 (Step 72) when initial shop reveals show favorable fruit pricing.
* **Peak Validated Delta:** +$2,128.00 (Seed 249636 Step 72).
* **Early Termination Rule:** Abort if vacant arable tiles $< 2$.

### Option O03: `LIQUIDATE_SURPLUS` (Working Capital Monetization)
* **Action Index:** 3 (`LIQUIDATE_SURPLUS`)
* **Underlying Mechanism:** Converts accumulated non-wheat vegetables and fruit into immediate cash, clearing shed space and funding scheduled high-tier chore investments.
* **Peak Validated Delta:** +$3,924.00 (Seed 249637 Step 144).

### Option O04: `OPPORTUNISTIC_SELL` (Spot Price Monetization)
* **Action Index:** 1 (`OPPORTUNISTIC_SELL`)
* **Underlying Mechanism:** A7 holds inventory until pre-planned 72-step release boundaries. O04 detects spot price spikes on Milk, Wool, and Melons and sells fractional lots before price decay occurs.
* **Peak Validated Delta:** +$3,420.00 (Seed 249636 Step 216).

---

## 4. Governance & Promotion Lifecycle

```
[ DISCOVERED ]
      │ (P12-01: Exact reproduction + 100% resync)
      ▼
  [ SCREENED ]
      │ (P12-02: Closed-loop positive final delta)
      ▼
 [ QUALIFIED ]
      │ (P12-05: Fresh-seed generalization + Tail safety)
      ▼
  [ PROMOTED ]
```

* **Current Status:** Options O01, O02, O03, O04 are **QUALIFIED** for closed-loop evaluation under Experiment P12-02.
* **Options O05, O06** remain **SCREENED** (small positive alpha, low activation priority).
