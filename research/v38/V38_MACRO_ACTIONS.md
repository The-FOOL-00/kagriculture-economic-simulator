# V38 Macro Action Taxonomy, Preconditions, and Execution Semantics

**Document ID:** `V38_MACRO_ACTIONS.md`  
**Date:** 2026-09-25  
**Candidate:** `candidates/v38_heuristic_ppo/`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Macro Action Space Design

To avoid the action-space collapse and step-level brittleness of low-level continuous/discrete RL, V38 structures its policy around a discrete 11-dimensional macro action vocabulary:

$$\mathcal{A}_{\text{macro}} = \{0, 1, 2, \dots, 10\}$$

Action 0 (`TRUST_HEURISTIC`) is mandatory and unconditionally legal at every step.

---

## 2. Action Catalog & Legality Preconditions

| Index | Name | Semantic Intent | Preconditions (Action Mask) | Execution Mechanism | Duration ($H$) |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **0** | **`TRUST_HEURISTIC`** | **Delegate turn to expert heuristic** | **Always True (Unconditional)** | Pure V35/A7 expert action | 1 |
| **1** | `EXPAND_LAND` | Unlock next $5 \times 5$ quadrant | Quads $< 4$, Step $< 480$, Cash $\ge \text{Cost} + \$150$ | Injects `BUY_LAND` with sell-prioritization | 4 |
| **2** | `HIRE_WORKER` | Hire additional farm hand | Hands $< 7$, Step $< 500$, Hour 0, Chores $> 2 \times N$ | Injects `HIRE` order | 4 |
| **3** | `ANIMAL_EXPANSION` | Acquire Cow + Pasture | Empty pastures $> 0$, Feed runway $\ge 3$ d, Cash $\ge \$550$ | Injects `BUY_ANIMAL COW` | 4 |
| **4** | `CROP_EXPANSION` | Buy & plant Melon seeds | Empty arable plots $> 0$, Step $< 450$, Cash $\ge \$230$ | Injects `BUY_SEED MELON` | 4 |
| **5** | `SHOP_SUPPLY` | Town consumption front-run | Step $\equiv 0 \pmod 4$, Stock $\ge 2$ Milk/Wool/Melon, $P \ge 20$ | Front-runs town consumption cycle | 4 |
| **6** | `SELL_INVENTORY` | Liquidate surplus shed goods | Non-wheat stock $\ge 4$, Spot price $\ge 15.0$ | Sells surplus non-feed goods | 4 |
| **7** | `HOLD_INVENTORY` | Suppress sales during market glut | Shed volume $< 75$, Price delta $< -2.0$, Step $< 650$ | Filters out planned low-price sales | 4 |
| **8** | `MARKET_OPPORTUNITY` | Capture temporary price spike | Stock $\ge 1$, Spot price $\ge 35.0$ | Injects high-priority SELL order | 4 |
| **9** | `LIQUIDITY_PROTECT` | Emergency working capital recovery| Wage runway $< 2.0$ days, Step $< 680$ | Cancels non-vital buys, liquidates high-value goods | 4 |
| **10** | `RECOVERY` | Extreme distress recovery | Cash $< \$50$ or starving animals | Sells all surplus, purchases feed WHEAT | 4 |

---

## 3. Strict Precondition Masking

Before PPO evaluates policy logits, an action mask $\mathbf{m} \in \{0, 1\}^{11}$ is generated from current observable features. If an action's preconditions are not met, its logit is masked with $-\infty$:

$$\pi_\theta(a \mid s) = \frac{\exp(z_a + (1 - m_a) \cdot (-10^8))}{\sum_{a'} \exp(z_{a'} + (1 - m_{a'}) \cdot (-10^8))}$$

This guarantees that:
1. PPO can never select an invalid action (e.g. buying land when already owning all quadrants or buying animals when cash is below safety thresholds).
2. Exploration is strictly confined to economically viable candidates.
3. `TRUST_HEURISTIC` ($a=0$) is always available as a safe default.
