# V39 Rule Distillation — Minimal Deterministic Intervention

## 1. Executive Summary
Following turn-by-turn loss forensics on all 29 live V35 competition replays (Phase 3) and counterfactual simulation (Phases 10–12), the dominant, fixable failure mode was isolated to **terminal liquidation omission** (`TERMINAL_LIQUIDATION_OMISSION`).

In 100% of analyzed losses, V35 held mature, perishable, high-value goods (`MILK`, `STRAWBERRY`, `WOOL`) in its farm shed at Step 693/694, while its static route tape omitted them in favor of selling wheat and carrots. Opponents dumped their sheds at Step 694, crashing market prices from peak values ($37/strawberry, $19/milk) to floor values ($1/unit), costing V35 between $600 and $1,500 in price slippage.

V39 distills this insight into a **single, minimal, deterministic, legally observable rule**.

---

## 2. Canonical Specification

```text
================================================================================
RULE: TARGETED_ENDGAME_LIQUIDATION_GUARD (FLUSH_694)
================================================================================
TRIGGER PREDICATE:
  1. step in (693, 694)                     [Final hours of Day 28 before turn boundary]
  2. shed contains qty > 0 of:
     - 'STRAWBERRY' OR
     - 'MILK' OR
     - 'WOOL'
  3. item NOT ALREADY in market sell queue
  4. len(market_orders) < 10                [Kaggle market buffer constraint]

ACTION:
  Append market order:
    ['SELL', item, qty]

DURATION:
  Active only during steps 693 and 694 (2 steps total out of 720).

SAFETY CONSTRAINTS:
  - Preserves 100% of V35 farmer trajectory (zero route divergence).
  - Preserves 100% of V35 worker choreography (zero hand divergence).
  - Preserves 100% of existing market orders.
  - Enforces len(market) <= 10 to guarantee zero order bounce.
  - Strict try/except fallback to exact base V35 action on any exception.
================================================================================
```

---

## 3. Legality and Cleanroom Compliance

| Constraint | Status | Proof |
| :--- | :---: | :--- |
| **No Seed Dependence** | **Compliant** | Evaluates only live `observation['step']` and `observation['private']['shed']`. |
| **No Opponent Identification** | **Compliant** | Zero opponent ID, name, or metadata inspected. |
| **No Future Replay Lookahead** | **Compliant** | Action is strictly causal based on current step inventory. |
| **No Outcome Labeling** | **Compliant** | Evaluates current physical state. |
| **No Neural Network Weights** | **Compliant** | Pure symbolic Python logic; zero weight files or checkpoints. |
| **No Hidden Runtime State** | **Compliant** | Stateless predicate evaluated on the observation. |
| **Execution Time** | **< 0.1 ms** | Single dictionary lookup; zero impact on Kaggle per-turn timeout. |

---

## 4. Why A Learned Model Is Unnecessary (Phase 21 Audit)

Question: *Is the live failure boundary too complex for a deterministic predicate?*

**Verdict: NO.**

1. **Information Sufficiency**: The physical condition is binary and complete: either perishable high-value goods exist in the shed at Day 28 hour 21–22, or they do not.
2. **Economic Unimodality**: In Kaggriculture, strawberries, milk, and wool have zero utility in endgame other than selling for cash. There are no crafting recipes that convert them into higher-margin items.
3. **Price Monotonicity**: Endgame prices only decrease as agents dump inventory. Selling earlier is strictly dominant or price-neutral.
4. **Generalization Guarantee**: A deterministic rule has zero sample variance, zero parameter drift, and zero overfitting risk compared to a learned policy.
