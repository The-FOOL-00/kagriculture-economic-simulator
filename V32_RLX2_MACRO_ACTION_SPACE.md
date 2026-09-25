# V32 RL-X2 — MACRO ACTION SPACE & INTENT SPECIFICATION
**Phase:** V32 RL-X2  
**Date:** 2026-09-23  
**Status:** SPECIFIED, IMPLEMENTED & VERIFIED  
**Package:** `candidates/v32_rlx2/action_space.py`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Executive Summary & Design Rationale (§6, §7, §12, §14)

Previous phases (P2–P7) proved that atomic, per-worker physical action learning suffers from catastrophic credit assignment failure and step-level brittleness. RL-X2 resolves this by operating at the macroeconomic intent level.

### Key Architectural Decisions:
1. **Action 0 is Mandatorily `FOLLOW_A7`:** The protected incumbent A7 is directly available as action index 0. If the strategic policy has no statistically superior deviation in a given state, it outputs action 0, executing A7 bit-identically ($0.00 delta, zero degradation).
2. **Deterministic Chore Executor Owns Execution:** The strategic policy dictates high-level resource allocations; the deterministic spatial dispatcher handles tile routing, hand alignment, and legal order assembly.
3. **Discrete 10-Action Formulation:** Compact, interpretable, and verifiable.

---

## 2. Master Action Space Dictionary

| Index | Identifier | Category | Semantic Intent & Economic Objective | Hard Legality Mask Condition |
| :---: | :--- | :--- | :--- | :--- |
| **0** | **`FOLLOW_A7`** | Baseline | **Passthrough**: Replay protected incumbent A7 route and reactive layers exactly. | **Unconditionally True** |
| **1** | `OPPORTUNISTIC_SELL` | Market | **Spot Monetization**: Liquidate shed inventory immediately if spot price $\ge 15.0$ and quantity $\ge 4$, avoiding holding stock until scheduled batch. | Shed has $\ge 4$ units of any product with spot price $\ge 10.0$; $step < 712$. |
| **2** | `SELECTIVE_PREEMPT_SELL`| Market | **Anti-Front-Running**: Front-run opponent dumps on volatile commodities (Milk, Wool, Melon, Strawberry) when opponent exhibits selling pressure. | Shed has $\ge 2$ units of volatile commodities & price $\ge 25.0$; $step < 712$. |
| **3** | `LIQUIDATE_SURPLUS` | Capital | **Emergency Cash**: Liquidate all non-wheat shed goods and excess wheat ($>15$ units) to fund capital expansion or avert wage insolvency. | Shed has non-wheat inventory or excess wheat $> 20$; $step < 712$. |
| **4** | `CROP_EXPANSION_MELON` | Production | **Cash Compounding**: Purchase Melon seeds and allocate arable tiles for planting during peak growth windows (Days 3–15). | Cash $\ge \$80$, vacant arable tiles $> 0$, wage runway $\ge 2.0$ days, $step < 450$. |
| **5** | `CROP_EXPANSION_WHEAT` | Production | **Feed Security**: Purchase Wheat seeds and plant when livestock feed runway drops below comfortable thresholds. | Cash $\ge \$10$, vacant arable tiles $> 0$, $step < 550$. |
| **6** | `LIVESTOCK_EXPANSION_COW`| Production | **High-Yield Milk**: Purchase Cow and construct/stock pasture when cash runway is robust ($\ge 3.0$ days). | Cash $\ge \$700$, vacant arable tiles $\ge 1$, runway $\ge 3.0$ days, $step < 450$. |
| **7** | `LIVESTOCK_EXPANSION_SHEEP`| Production | **Wool Compounding**: Purchase Sheep and construct/stock pasture when cash runway is robust. | Cash $\ge \$600$, vacant arable tiles $\ge 1$, runway $\ge 3.0$ days, $step < 450$. |
| **8** | `PRESERVE_CASH` | Capital | **Liquidity Defense**: Suppress optional worker hiring and land purchases to defend cash buffer during market downturns. | Active workers $> 1$ or hires today $> 0$. |
| **9** | `EXPAND_LAND` | Land | **Territorial Growth**: Purchase next available farm quadrant ($1 \to 2$, $2 \to 3$, $3 \to 4$) when cash buffer exceeds land price $+ \$100$. | Quadrants $< 4$, next land cost $> 0$, cash $\ge LandCost + \$100$, $step < 500$. |

---

## 3. Decision Horizon & Option Frequency (§13)

- **Default Interval:** $H = 4$ game steps.
- **Economic Justification:** In Kagriculture, town consumption events occur strictly every 4 turns ($step \pmod 4 == 0$). At each town consumption tick, market inventories decrease and spot prices recalculate. Aligning macro decisions to $H = 4$ synchronizes strategic policy actions with market equilibrium shifts, yielding exactly 180 decision steps per 720-step game.

---

## 4. Legality, Sanitization & Fail-Closed Guarantee (§38, §39, §69)

Every action emitted by the policy passes through `candidates/v32_rlx2/safety.py`:
1. **Order Clamping:** Clamps total market orders to $\le 10$, and clamps SELL order quantities to available shed stock.
2. **Hand Padding:** Ensures hand action lists match the exact number of active hired hands.
3. **Fail-Closed Fallback:** In the event of any runtime error or illegal state transition, the enforcer discards the candidate action and executes A7's baseline action bit-identically.
4. **Verification:** Verified via automated pytest test suite (`test_action_0_bit_identical_to_a7`), achieving 100% exact numerical match with A7 ($0.00 delta).
