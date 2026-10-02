# V32 RL-X2 — SYSTEM DESIGN & ARCHITECTURAL SPECIFICATION
**Phase:** V32 RL-X2  
**Date:** 2026-09-23  
**Status:** ARCHITECTED, VERIFIED & CERTIFIED  
**Package:** `candidates/v32_rlx2/`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Executive Overview & Core Principle

Phase V32 RL-X2 supersedes the old low-level atomic action learning and teacher imitation paradigms (P2–P7), which failed due to step-level brittleness, and builds upon the structural findings of P8–P11:
- P8 proved the teacher's physical behavior is essentially an open-loop tape ($H(A_t \mid t) = 0.000$ bits).
- P9 showed that macro-economic hierarchical execution can match A7, but manual heuristic overrides are dangerous.
- P10 mapped reproducible mid-game economic opportunity classes but found sparse hand-crafted residuals had severe tail risks.
- P11 proved that terminal physical headroom is completely exhausted by A7 ($0.00 carried cargo, $0.00 in shed, $0.00 delta from physical search).

Therefore, the remaining frontier of competitive alpha lies strictly in:
```text
========================================================================================
STRATEGIC REINFORCEMENT LEARNING & EXACT SIMULATOR COUNTERFACTUAL SEARCH
LEARNING WHEN TO FOLLOW A7 AND WHEN TO DEVIATE BASED ON MACRO-ECONOMIC & OPPONENT SIGNALS
========================================================================================
```

RL owns **WHAT** (strategic decisions: crop focus, livestock expansion, preemptive selling, cash preservation).  
The Deterministic Executor owns **HOW** (spatial chore dispatch, pathing, order formatting, legal safety).

---

## 2. Mathematical System Architecture

```text
                           LEGAL OBSERVATION
                                   ↓
                       ECONOMIC STATE EXTRACTOR
                         (Tiers S0, S1, S2, S3)
                                   ↓
                   ┌───────────────┴───────────────┐
                   │                               │
                   ▼                               ▼
          PROTECTED INCUMBENT            STRATEGIC POLICY (PPO)
             (A7 Baseline)              OR EXACT MACRO SEARCH
                   │                               │
                   │                       Macro Action a ∈ {0..9}
                   │                       (Action 0 = FOLLOW_A7)
                   │                               │
                   └───────────────┬───────────────┘
                                   ↓
                        STRATEGIC EXECUTOR (HOW)
                                   ↓
                       LEGALITY & SAFETY ENFORCER
                         (Fail-Closed to A7)
                                   ↓
                          KAGGLE SIMULATOR
```

---

## 3. Economic State Spaces (§10, §11)

The observation is converted into a strongly typed, zero-leakage feature vector across four nested tiers:

1. **Tier S0 (Raw Essentials, Dim = 19):**
   - Current cash, liquid inventory value, total shed inventory, total planted crops, active workers, normalized game step, 9 spot prices, 4 shop unlock indicator flags.
2. **Tier S1 (Structured Economics, Dim = 63):**
   - S0 + cash runway (days of wages), committed wages today, next hire cost, chore backlog, idle hands, unwatered crops, vacant arable land, weed count, animal counts (cows, sheep, geese), unfed/uncared counts, empty pastures, feed reserve runway, wheat in shed, unlocked quadrants, next quadrant cost, town consumption phase ($step \pmod 4$), hour of day ($step \pmod{24}$), terminal flag, individual crop counts (5), individual shed inventory (9), price deltas (9).
3. **Tier S2 (S1 + Opponent Observables, Dim = 71) [Default]:**
   - S1 + opponent cash, cash delta ($p\_cash - opp\_cash$), opponent visible workers, opponent visible crops, opponent visible cows/sheep/geese, opponent unlocked quadrants.
4. **Tier S3 (S2 + Derived Opportunities & Stress Signals, Dim = 80):**
   - S2 + liquidity stress index ($runway < 1.5$ days), preempt sell signals for MILK, WOOL, MELON, STRAWBERRY, and market glut saturation flags.

---

## 4. Macro Action Space & Intent Mappings (§12, §14, §39)

The policy acts in a discrete 10-dimensional macro action space. Action 0 is mandatory `FOLLOW_A7`:

| Action Index | Name | Semantic Intent | Legality Constraint (Mask) |
| :---: | :--- | :--- | :--- |
| **0** | **`FOLLOW_A7`** | **Replay A7 baseline bit-identically** | **Unconditionally True (Bedrock)** |
| **1** | `OPPORTUNISTIC_SELL` | Sell shed stock if spot price $\ge 15.0$ and stock $\ge 4$ | Has sellable stock and step $< 712$ |
| **2** | `SELECTIVE_PREEMPT_SELL` | Front-run opponent dumps on volatile goods | Has $\ge 2$ Milk/Wool/Melon/Straw & px $\ge 25$ |
| **3** | `LIQUIDATE_SURPLUS` | Liquidate all non-wheat shed goods | Has surplus stock and step $< 712$ |
| **4** | `CROP_EXPANSION_MELON` | Buy melon seeds & prioritize planting | Cash $\ge \$80$, arable land $> 0$, step $< 450$ |
| **5** | `CROP_EXPANSION_WHEAT` | Replenish livestock feed reserve | Cash $\ge \$10$, arable land $> 0$, step $< 550$ |
| **6** | `LIVESTOCK_EXPANSION_COW`| Acquire Cow + pasture | Cash $\ge \$700$, runway $\ge 3$ d, step $< 450$ |
| **7** | `LIVESTOCK_EXPANSION_SHEEP`| Acquire Sheep + pasture | Cash $\ge \$600$, runway $\ge 3$ d, step $< 450$ |
| **8** | `PRESERVE_CASH` | Throttle optional hiring & land purchases | Workers $> 1$ or hires today $> 0$ |
| **9** | `EXPAND_LAND` | Unlock next farm quadrant | Cash $\ge LandCost + \$100$, quads $< 4$ |

---

## 5. PPO Mathematical Formulation (§15, §16)

The policy optimization optimizes the clipped surrogate objective with Generalized Advantage Estimation:

$$\mathcal{L}^{CLIP}(\theta) = \hat{\mathbb{E}}_t \left[ \min\left( r_t(\theta) \hat{A}_t, \, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) \hat{A}_t \right) \right]$$

where probability ratio $r_t(\theta) = \frac{\pi_\theta(a_t \mid s_t)}{\pi_{\theta_{old}}(a_t \mid s_t)}$ and GAE advantages:

$$\hat{A}_t = \sum_{l=0}^{\infty} (\gamma \lambda)^l \delta_{t+l}^V, \quad \delta_t^V = r_t + \gamma V_\phi(s_{t+1}) - V_\phi(s_t)$$

The joint optimization objective incorporates value loss clipping and entropy regularization:

$$\max_{\theta, \phi} \mathcal{L}(\theta, \phi) = \mathcal{L}^{CLIP}(\theta) - c_1 \frac{1}{2} \hat{\mathbb{E}}_t \left[ (V_\phi(s_t) - \hat{R}_t)^2 \right] + c_2 \mathcal{H}(\pi_\theta(\cdot \mid s_t))$$

---

## 6. Exact Simulator Strategic Search Engine (§20–§26)

Because the Kagriculture simulator is exact, deterministic, and fast (455 SPS), we formulate exact macro counterfactual valuation:

$$V(s_t, a) = \text{TerminalCash}(s_t, \, a \xrightarrow{H=4} \text{resume } A7)$$

At any consequential state $s_t$:
1. The search engine evaluates all legal macro actions $a \in \mathcal{A}(s_t)$.
2. Actions are ranked by paired delta vs A7: $\Delta(s_t, a) = V(s_t, a) - V(s_t, 0)$.
3. High-consequence states where $\Delta(s_t, a) > 0$ and $V(s_t, \text{best}) - V(s_t, \text{second}) > \delta_{min}$ form the supervised strategic pretraining dataset.

---

## 7. Opponent League & Tournament Framework (§27–§30)

Training and evaluation execute against the frozen 6-opponent panel:
1. `E2_A7` (Protected Incumbent Baseline)
2. `E1_V22R1` (Slot A Portfolio Live Champion)
3. `E0_V3` (Base Open-Loop Route Baseline)
4. `E8_DMITRII` (Frontier 2800+ Competitor)
5. `V54` (Declarative Macro Reference)
6. `SYN_AGG` (Hostile Market Stressor)

All matches execute under Common Random Number (CRN) pairs in both Seat 0 and Seat 1, eliminating seat bias and seed variance.

---

## 8. Fail-Closed Safety & Promotion Invariants (§69, §70)

1. **A7 Freeze**: `candidates/v30_a7_standalone/main.py` is read-only; SHA-256 is checked before and after all runs.
2. **Holdout Quarantine**: Holdout cohorts `214200–214249`, `340090–340199`, and `249695–249734` are protected by automated runtime assertions.
3. **Fail-Closed Runtime**: Any exception, timeout, or invalid action generation instantly falls back to A7 baseline bit-identically.
4. **Promotion Threshold**: A candidate must beat A7 on held-out development with statistically significant paired margin ($p < 0.01$), zero crashes, zero illegal moves, and non-negative worst-case tail risk before any live consideration.
