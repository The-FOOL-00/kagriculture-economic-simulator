# V26 — AEC TRANSFER PREREGISTRATION

## 1. Governance & Protocol Anchor
* **Campaign**: V26 — Backbone-Aware AEC Re-Architecture & Transfer to V25
* **Date**: 2026-09-21
* **Branch**: `research/v26-backbone-aware-aec`
* **Base Tag**: `v22r1` (Commit `33763a8`)
* **Registry Cohort**: `249470..249489` (20 virgin seeds × 2 seats = 40 matches per arm)
* **Opponent**: Standalone V3 (Mirrored seating, Seat 0 and Seat 1)

---

## 2. Hypotheses

### Primary Hypothesis ($H_1$)
> `V25_MARKET_TIMING` (ARM 3) achieves a positive paired terminal economic delta relative to `V25_STANDALONE` (ARM 1) when evaluated using a V25-native exact continuation model:
> $$\Delta \mu = \mathbb{E}[\text{Reward}(\text{ARM 3}) - \text{Reward}(\text{ARM 1})] > +\$0.00$$

### Secondary Hypotheses ($H_2$ to $H_5$)
1. **$H_2$ (Infrastructure Neutrality)**: `V25_AEC_INFRA_ONLY` (ARM 2) produces identical behavior to `V25_STANDALONE` (ARM 1) with zero unintended action deviations ($\Delta \mu \equiv \$0.00$).
2. **$H_3$ (Reference Reproducibility)**: Under the generic backbone architecture, `V3_MARKET_TIMING_REFERENCE` (ARM 4) replicates historical non-negative market-timing performance vs standalone V3.
3. **$H_4$ (Safety Integrity)**: No committed intervention in ARM 3 triggers catastrophic tail collapse (worst loss $\ge -\$1,500.00$) or animal escape/feed starvation.
4. **$H_5$ (Counterfactual Reproducibility)**: Counterfactual predictions for committed interventions are independently verifiable without circular self-referencing.

---

## 3. Arm Definitions & Configuration

| Arm Identifier | Backbone Policy | AEC Active? | Enabled Mechanisms | Purpose |
| :--- | :--- | :---: | :---: | :--- |
| **ARM 1: `V25_STANDALONE`** | `V25P3BackboneAdapter` | No | None | Clean Control |
| **ARM 2: `V25_AEC_INFRA_ONLY`** | `V25P3BackboneAdapter` | Yes | `()` | Null Infrastructure Parity Check |
| **ARM 3: `V25_MARKET_TIMING`** | `V25P3BackboneAdapter` | Yes | `("DEPENDENCY_AWARE_MARKET_TIMING",)` | Primary Experimental Treatment |
| **ARM 4: `V3_MARKET_TIMING_REFERENCE`** | `V3BackboneAdapter` | Yes | `("DEPENDENCY_AWARE_MARKET_TIMING",)` | Contemporary Historical Reference |

---

## 4. Primary Endpoints & Statistical Decision Criteria

1. **Primary Metric**: Paired terminal reward delta $(\text{Candidate} - \text{Baseline})$.
2. **Key Comparison**:
   $$\Delta \text{Transfer} = \text{Mean}(\text{ARM 3}) - \text{Mean}(\text{ARM 1})$$
3. **Decision States (Section 33)**:
   - **`V26 MARKET TIMING TRANSFERRED`**:
     $\Delta \text{Transfer} > +\$0.00$, bootstrap 95% CI lower bound $\ge -\$50.00$, win rate $> 50\%$, and zero safety breaches.
   - **`V26 TRANSFER FAILED — MECHANISM`**:
     Infrastructure operates without error, but realized economic delta is zero or negative ($\Delta \le \$0.00$).
   - **`V26 TRANSFER FAILED — BACKBONE-SPECIFIC ECONOMICS`**:
     Market-timing opportunities do not fire or have no economic leverage on V25 P3's superior liquidity profile.
   - **`V26 TRANSFER FAILED — INFRASTRUCTURE`**:
     Continuation model desynchronizes, mutates live state, or fails null parity.

---

## 5. Stop Conditions (Mandatory Halt)
Execution must halt immediately if:
1. V25 AEC infrastructure changes V25 actions without commits.
2. Continuation fails exact replay.
3. Hidden P3 state is lost across clones.
4. Action divergence appears on null turns.
5. Candidate evaluation uses V3 state or hardcoded V3 cash.
6. Safety becomes fail-open.
7. Any protected holdout seed is touched.
8. Result-dependent tuning is attempted mid-study.
