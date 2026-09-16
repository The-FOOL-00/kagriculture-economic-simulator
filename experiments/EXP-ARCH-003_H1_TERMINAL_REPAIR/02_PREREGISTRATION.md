# EXP-ARCH-003_H1_TERMINAL_REPAIR — Preregistration Document

**Experiment ID:** EXP-ARCH-003_H1_TERMINAL_REPAIR  
**Successor To:** EXP-ARCH-002_H1_DOMINANCE_TERMINAL (frozen, flawed terminal design)  
**Date Frozen:** 2026-09-16  
**Status:** FROZEN PRIOR TO PROSPECTIVE EXECUTION  
**Hypothesis:** H1-ACT (Repaired terminal reap-and-ferry optimizer achieves non-zero activation and net-positive economic gain without violating safety or intermediate solvency)  

---

## 1. Executive Summary & Design Rationale

In ARCH-002 (`EXP-ARCH-002_H1_DOMINANCE_TERMINAL`), the H1 terminal optimizer exhibited 0% activation across all 500 seeds (1000 CRN games) due to two structural defects identified during the ARCH-002 forensic audit:
1. **Market Asynchrony (Defect 1):** The shadow simulator forced market orders on steps 712–718 to match baseline market orders verbatim. Because the baseline schedules terminal sales at step 718 based on inventory deposited by baseline worker paths, any candidate worker plan that deposited crops or fertilizer at step 718 produced unsold inventory sitting idle in the shed, yielding $0.00 money gain.
2. **Pathological Prefix Dominance (Defect 2):** Invariant D5 previously enforced step-by-step per-actor cumulative deposit dominance ($\forall t, \forall i: \text{cand\_dep}[t][i] \ge \text{base\_dep}[t][i]$), immediately rejecting optimal worker re-routing that temporarily deferred an intermediate deposit by 1 step even when no baseline market order was pending.

ARCH-003 repairs both defects while strictly maintaining economic safety, intermediate market solvency, deterministic execution, and zero state leakage.

---

## 2. Definitive Separation of Invariants: D5 vs. Acceptance

Before implementation, the separation between safety/dominance and economic adoption was frozen:

### D5: Safety and Dominance Invariant
D5 specifies the non-negotiable safety conditions that guarantee a candidate plan cannot damage the agent relative to baseline execution:
1. **Zero Overflow:** Candidate simulated overflow must equal 0 at all steps $t \in [712, 718]$.
2. **Intermediate Market Solvency (Steps 712–717):** For every step $t \in [712, 717]$ and product $p \in \text{PRODUCTS\_9}$, candidate pre-market shed inventory must satisfy all executable baseline SELL orders:
   $$\text{cand\_pre\_shed}[t][p] \ge \min(\text{base\_scheduled\_qty}[t][p], \text{base\_pre\_shed}[t][p])$$
   Additionally, the candidate must satisfy all baseline BUY obligations without insolvency.
3. **Terminal Weak Dominance (Step 718):** At the terminal step 718:
   - Candidate pre-market shed $\ge$ baseline pre-market shed for every product $p \in \text{PRODUCTS\_9}$.
   - Candidate total cumulative deposits across all actors $\ge$ baseline total cumulative deposits for every product $p \in \text{PRODUCTS\_9}$.
   - Candidate cumulative sold units $\ge$ baseline cumulative sold units for every product $p \in \text{PRODUCTS\_9}$.
4. **No-Steal Invariant:** The candidate plan must satisfy `no_steal_pass` (no theft of opponent crops or mutual collisions on contested resource tiles).

### Acceptance: Economic Adoption Criterion
Acceptance specifies whether an already-safe (D5-passing) candidate generates genuine net economic improvement on the real game objective:
1. **Worker Changed:** Candidate worker actions must differ from baseline worker actions (`worker_changed == True`).
2. **Terminal Money Delta Positive:** Real terminal money from exact simulation must exceed baseline terminal money:
   $$\Delta_{\text{money}} = \text{cand\_final\_money} - \text{base\_final\_money} > 0$$
3. **Non-Negative Sold Unit Deltas:** For every product $p \in \text{PRODUCTS\_9}$, $\Delta_{\text{sold}}(p) \ge 0$.
4. **Strictly Positive Sales Improvement:** There exists at least one product $p$ such that $\Delta_{\text{sold}}(p) > 0$.
5. **Zero Overflow:** `candidate_overflow == 0`.

*Note:* `stock_value` is retained as an internal heuristic ranking metric in candidate search, but cannot trigger acceptance unless exact money and sold unit criteria are met.

---

## 3. Treatment and Baseline Specifications

- **Baseline Agent:**
  - Frozen `V54++` agent (`candidates/compiled_v54_plus_residual.py`).
  - Baseline SHA-256: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`.
  - Unadorned, read-only baseline policy with frozen routes (`backbone`, `yarn`, `bakery`).
- **Treatment Agent:**
  - `h1_agent.py:build_agent(load_baseline())`.
  - Step 0–711: Exact baseline pass-through.
  - Step 712: Handshake verification (G0–G5), clone ledgers, execute 128 shadow simulations, evaluate D5 and Acceptance. If a candidate is accepted, adopt plan; otherwise, pass through live baseline action.
  - Steps 712–717: Emit candidate worker commands; emit live baseline market orders verbatim.
  - Step 718: Emit candidate worker commands; emit candidate deterministic terminal liquidation market orders.
  - Step 719: Exact baseline termination.
  - Verification: Stepwise re-verification of physical state at steps 713–718. Any mismatch triggers immediate fail-closed abandonment to baseline.

---

## 4. Search and Simulation Parameters

All search parameters remain strictly frozen to the ARCH-002 budget:
- **Search Simulations:** Exactly 128 forward rollouts (`PIN_SIMULATIONS = 128`).
- **Optimization Passes:** Exactly 1 pass (`PIN_PASSES = 1`).
- **Proposals per Worker:** $\le 8$ proposals per actor (`PIN_MAX_PROPOSALS = 8`).
- **Proposal Generator:** Identical deterministic proposal generator (PASS, step moves, reaps, drop routes).
- **Proposal Ordering:** Lexicographic tie-breaking, unchanged.
- **Entry Prices:** Unchanged integer entry prices.
- **Worker Whitelist:** Farmer and all hired hands.
- **No BUY modifications:** No BUY orders injected; G4 coverage gate enforced.

---

## 5. Authoritative Step-718 Liquidation Market

At step 718, candidate market orders are computed deterministically by:
`compute_terminal_liquidation_market(obs_E, post_worker_cand_state)`
Which applies the frozen baseline liquidation logic:
`terminal_market(obs_sim, action, rule="collision", replace=True)`
Operating under strict restrictions:
- SELL orders only.
- `PRODUCTS_9` items only (`WHEAT`, `CARROT`, `TOMATO`, `STRAWBERRY`, `WATERMELON`, `POTATO`, `PUMPKIN`, `MELON`, `FERTILIZER`).
- Quantities are positive integers bounded by available post-worker candidate shed inventory.
- Maximum market orders $\le 10$ (`PIN_MAX_ORDERS = 10`).
- No BUY orders.
- No speculative pricing.
- Bit-identical implementation used across shadow search, live emission, and validation.

---

## 6. Common Random Numbers (CRN) Protocol

- **Cohort Range:** Seeds `330000` to `330499` inclusive.
- **Seed Count:** 500 fresh, unconsumed seeds.
- **CRN Structure:** 1000 total games:
  - Game A: Seed $s$, Player 0 = Treatment (ARCH-003), Player 1 = Baseline (V54++)
  - Game B: Seed $s$, Player 0 = Baseline (V54++), Player 1 = Treatment (ARCH-003)
- **Evaluation Engine:** Engine version 1.32.7 (pure deterministic Kagriculture environment).
- **Max Steps per Game:** 720.

---

## 7. Hypotheses and Success / Failure Criteria

### Primary Hypothesis (H1-ACT)
- **Null Hypothesis ($H_0$):** Activation rate $\text{Act} = 0\%$.
- **Alternative Hypothesis ($H_1$):** Activation rate $\text{Act} > 0\%$, with positive net monetary contribution $\Delta_{\text{money}} > 0$ on activated games.

### Success Criteria (Strict Gate)
1. **Activation:** Treatment activates on $\ge 1$ game out of 1000 ($\text{Act} > 0\%$).
2. **Economic Viability:** Mean net score delta across cohort is non-negative:
   $$\bar{\Delta} = \frac{1}{500} \sum_{s=330000}^{330499} \frac{(\text{Score}_{T0, s} - \text{Score}_{B1, s}) + (\text{Score}_{T1, s} - \text{Score}_{B0, s})}{2} \ge 0$$
3. **Activated Gain:** On the subset of games where treatment activates, mean $\Delta_{\text{money}} > 0$.
4. **Safety & Invariant Zero-Defect:**
   - 0 overflow events in treatment games.
   - 0 intermediate market insolvency events on steps 712–717.
   - 0 unhandled exceptions or crashes.
   - 0 state corruption or non-deterministic replays.

### Failure Criteria
- If $\text{Act} = 0\%$, hypothesis H1-ACT is rejected.
- If $\text{Act} > 0\%$ but $\bar{\Delta} < 0$, treatment is rejected due to net degradation.
- Any overflow or safety violation invalidates the run immediately.

---

## 8. Quarantine and Anti-Pollution Safeguards

1. **Cohort Quarantine:**
   - Cohort `330000–330499` is strictly forbidden from being executed during design, implementation, and micro-validation.
   - Any execution prior to formal preregistration freeze invalidates the cohort.
2. **Holdout Protection:**
   - Holdout seeds `214200–214249` remain strictly off-limits.
3. **Runner Enforced Guardrails:**
   - `run_arch003_execution.py` strictly validates seed bounds (`330000 <= seed <= 330499`).
   - Runner verifies baseline hash against `V54_PLUS_PLUS_SHA256` before opening any game.
   - Runner requires clean destination directory (no overwrite of existing records).

---

## 9. Preregistered File Hashes

The exact file hashes of all implementation and verification artifacts are frozen in `04_FREEZE_RECORD.md`.
