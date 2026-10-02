# V55 Temporal Leakage and Oracle Analysis Report

## Executive Summary

The V55 research program investigates whether the sovereign incumbent **`V49_Meta_Fusion`** can be improved by making state-dependent continuation decisions *only after future shop demand is legally revealed* in `observation.town["unlocked_shops"]`.

This report evaluates three policy classes across the critical counterfactual pair `(250416, 250436)`:
1. **The Oracle Policy** (Upper-bound theoretical benchmark with access to future shop draws from Step 0),
2. **The Illegal Early Policy** (Branches prior to shop reveal using seed identification or future RNG leakage),
3. **The Legal Post-Reveal Policy** (Eligible candidate class acting strictly on callback observations at Step 216+).

**Key Findings:**
* **Pre-Reveal State Identity:** Through Step 215, the observable environments of Seed 250416 and Seed 250436 are mathematically identical ($obs_{250416}(t) \equiv obs_{250436}(t)$ for all $t \in [0, 215]$).
* **Illegal Early Leakage:** Any policy that branches at Step 150 (e.g., V54 COWSWAP) appears to generate +$5,000+ margin on 250436 only by exploiting temporal leakage. When evaluated without future information, an identical pre-reveal policy must treat 250416 and 250436 identically, resulting in severe -$1,400 to -$3,500 casualties on 250416.
* **The Legal Post-Reveal Bottleneck:** Once the shop is legally revealed at Step 216 (`PIZZA_SHOP` on 250436 vs `PET_CAFE` on 250416), physical and choreographic constraints prevent profitable adaptation. Post-reveal demand-aware selling gains modest margin on 250436 (+$627 to +$1,641) but causes a catastrophic **-$30,569 casualty** on 250416 due to shed capacity saturation and silent engine crop deletion.
* **Conclusion:** 100% of the apparent alpha from pre-reveal dairy specialization is unexploitable temporal leakage. Under strict legal observation gates, post-reveal adaptation fails the zero-casualty safety gate.

---

## 1. Mathematical Formalization of Policy Classes

Let $S_t$ be the true environment state at step $t$, and $O_t = \pi_{obs}(S_t)$ be the legally observable state available in the agent callback.
Let $W_{shop} = (\omega_{72}, \omega_{144}, \omega_{216}, \dots, \omega_{576})$ be the sequence of stochastic town shop draws, where each $\omega_t \sim \text{Uniform}(\mathcal{S}_{shops})$.

### Class 1: The Oracle Policy $\pi_{oracle}(O_t, W_{shop})$
* **Definition:** Has access to future shop realizations $W_{shop}$ at Step 0.
* **Mechanism:** Can construct specialized physical infrastructure from Day 0:
  - If $W_{shop}$ contains high milk demand (e.g. 250436 with 5 dairy shops), it builds coops/pastures tailored exclusively to dairy, hires specialized dairy hands, and skips strawberry/melon infrastructure.
  - If $W_{shop}$ contains low milk demand (e.g. 250416), it builds crop autarky and sheep pastures.
* **Theoretical Upper Bound:** Oracle alpha is +$8,000 to +$12,000 over static generalist policies, but is 100% non-implementable in competition.

### Class 2: The Illegal Early Policy $\pi_{illegal}(O_t, \text{SeedID})$
* **Definition:** Executes branch decisions before Step 216 based on seed lookups or hidden engine state.
* **Empirical Demonstration:** In V54, a Step-150 gate attempted to switch between Dairy and Wool based on observed prices. However, because $O_{150}(250416) \equiv O_{150}(250436)$, an honest observation-driven policy makes the exact same decision on both seeds.
* **Leakage Quantification:** If a policy selectively activates COWSWAP on 250436 but not on 250416, it is using 1 bit of illicit future information. That single bit accounts for +$7,120 of apparent margin, which instantly collapses into a -$1,410 casualty when applied honestly.

### Class 3: The Legal Post-Reveal Candidate $\pi_{legal}(O_t)$
* **Definition:** Strictly satisfies:
  $$\pi_{legal}(O_t) = \pi_{V49}(O_t) \quad \forall t < 216$$
  $$\pi_{legal}(O_t) = f(O_t) \quad \forall t \ge 216 \text{ where } O_t \text{ contains revealed shops}$$
* **Constraint:** Must decide future actions using only public information available at and after the reveal step.

---

## 2. Experimental Comparison on Critical Counterfactuals

We tested the policy classes on the critical seeds across identical opponent and seat configurations:

| Policy Class | Decision Step | Info Source | Seed 250416 Margin | Seed 250436 Margin | Paired Delta (250436) | Paired Delta (250416) | Casualties | Gate Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V49 Incumbent (Control)** | N/A | None | -$716 | -$1,405 | $0 | $0 | 0 | **PASS (Incumbent)** |
| **Oracle Upper Bound** | Step 0 | Full Future $W_{shop}$ | +$6,420 | +$8,150 | +$9,555 | +$7,136 | 0 | **ILLEGAL (Unimplementable)** |
| **Illegal Early (V54 Gate)** | Step 150 | Seed / Future Lookup | -$2,126 | +$5,715 | +$7,120 | -$1,410 | 1 | **REJECTED (Leakage)** |
| **Legal Post-Reveal (B_120)**| Step 216 | `unlocked_shops` | -$31,285 | -$778 | +$627 | **-$30,569** | 1 | **REJECTED (Catastrophic)** |
| **Legal Post-Reveal (B_140)**| Step 216 | `unlocked_shops` | -$31,839 | +$236 | +$1,641 | **-$31,123** | 1 | **REJECTED (Catastrophic)** |
| **Legal Post-Reveal (C_PROD)**| Step 216 | `unlocked_shops` | -$716 | -$1,816 | -$411 | $0 | 1 | **REJECTED (Negative Delta)** |

---

## 3. Why Legal Post-Reveal Adaptation Fails Mechanically

Why does legal post-reveal adaptation fail so decisively when the Oracle succeeds?

1. **Sunk Capital and Physical Path Dependency:**
   By Step 216, 30% of the game has elapsed. V49 has invested in 6 cows, 4 sheep, 2 geese, 1 empty pasture, 3 farm hands, and extensive plowed/planted crop fields.
   Unlike an Oracle that never built sheep or crops, a Step-216 agent cannot undo its infrastructure.
2. **Animal Delivery Disconnect:**
   If the post-reveal policy attempts to increase milk production at Step 216 by purchasing a cow (`BUY_ANIMAL COW 1`), the engine places the new cow inside the **shed**.
   In V49, worker schedules are rigidly optimized. No worker is allocated to pick up the cow from the shed and carry it to the pasture. The cow remains trapped in the shed, consuming $1,200 in liquid capital and producing zero milk (Family C delta: -$411).
3. **The Shed Saturation Trap (`del inv[item]`):**
   If the post-reveal policy attempts to hold milk to wait for town shop demand to drive up market prices (Family B), the milk sits in the player's shed.
   The shed has a maximum capacity of 100 items. When milk accumulates, `shed_used` reaches 100.
   When field workers harvest Strawberries, Melons, or Wheat and attempt `DROP` at the shed, the official engine executes:
   ```python
   room = max(0, shed_capacity - sum(shed.values()))
   take = min(n, room)
   if take > 0:
       shed[item] = shed.get(item, 0) + take
   del inv[item]
   ```
   Because `room == 0`, `take == 0`, and the engine immediately executes `del inv[item]`!
   The worker's harvested crops are deleted from existence with zero payment, creating an immediate -$30,000+ loss.

---

## 4. Conclusion and Promotion Ruling

* **Temporal Leakage Verdict:** Any apparent strategy that differentiates seeds before Step 216 is pure temporal leakage and cannot be executed in live competition.
* **Post-Reveal Adaptation Verdict:** At and after Step 216, the legal state of the farm is too physically constrained to pivot to a different commodity regime without breaking V49's shed capacity and choreographic synchronization.
* **Decision:** Retain V49. Post-reveal continuation candidate is unsafe and rejected.
