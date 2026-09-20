# PHASE019 COMMIT PATH AUDIT

**Phase**: PHASE019 — Uncertainty-Aware Commit Selection & Robust Economic Decision Audit  
**Date**: 2026-09-20  
**Scope**: Complete end-to-end trace of candidate generation, funneling, exact simulation, economic scoring, WinModel ranking, safety certification, and commit/abstention decision logic.

---

## 1. End-to-End Commit Pipeline Architecture

The AEC compiler decision pipeline in `aec/integration/executor.py` executes each turn via the following sequence:

```text
1. OBSERVE & IR BUILD
   └─ build_economic_state() → EconomicState
2. BACKBONE BASELINE
   └─ BackboneAdapter.plan() → baseline_action, future_trajectory
3. OPPORTUNITY & EVENT DETECTION
   └─ OpportunityEngine.detect() + detect_events()
4. PATCH GENERATION
   └─ PatchGenerator.generate_patches() → raw_patches
5. CANDIDATE FUNNEL & PRUNING
   ├─ 5A: OpportunityCandidateFunnel.filter_candidates() [with FunnelReservationPolicy]
   ├─ 5B: MacroController.validate_tactical_compatibility()
   ├─ 5C: MetaOrchestrator.prioritize_candidates()
   └─ 5D: prune_patches(max_candidates=8) → candidate_patches
6. COUNTERFACTUAL SIMULATION & EVALUATION (Loop over active_patches[:8])
   ├─ 6A: MacroRegimeTransitionDetector.probe_candidate()
   ├─ 6B: select_adaptive_horizon()
   ├─ 6C: CounterfactualSimulator.evaluate() → SimulationOutcome
   ├─ 6D: WinModel.evaluate() → EvaluationResult
   ├─ 6E: SafetyChecker.verify() → passed_safety, checks, abstain_reason
   ├─ 6F: Governance/Quarantine Filter
   └─ 6G: CandidateTelemetry & SafetyCertificate generation
7. COMMIT SELECTION (Within-loop greedy replacement)
   └─ if cert.commit_decision:
         if best_eval_result is None or eval_res.expected_p_win > best_eval_result.expected_p_win:
             best_candidate = patch
             best_certificate = cert
             best_eval_result = eval_res
8. COMMIT OR ABSTAIN
   └─ if best_candidate is not None:
         apply patch to baseline_action → return committed_action
      else:
         return baseline_action (ABSTAIN / BACKBONE fallback)
```

---

## 2. Step-by-Step Mechanism Audit

### 2.1 Where Candidate Scores are Produced
- Candidate counterfactual wealth is computed in `aec/counterfactual/simulator.py` lines 631–642:
  ```python
  cand_margin = cand_total_wealth - candidate_rollout.opp_money
  base_margin = base_total_wealth - baseline_rollout.opp_money
  delta_terminal_margin = cand_margin - base_margin
  ```
- This accounts for all cash and commodity shed inventory at current market prices across both rollouts.
- Crucially, this score is a **deterministic point estimate** from a single forward simulation.

### 2.2 Where the $15 Hurdle Enters
- In `aec/evaluation/win_model.py` lines 341–354 (the fallback lexicographic branch applicable to general/tranche patches):
  ```python
  if delta_margin > 0.0 and p_win_gain > 0.005:
      is_superior = True
  elif outcome.delta_terminal_margin > 15.0:
      is_superior = True
  elif outcome.delta_our_money > 20.0 and outcome.delta_terminal_margin >= 0.0:
      is_superior = True
  else:
      is_superior = False
  ```
- Because $\frac{d}{dx} \text{sigmoid}(x/1000) \le 0.00025$, `p_win_gain > 0.005` requires $\Delta \text{margin} \ge \$20.0$ at parity and higher when ahead/behind.
- Thus, the active operational hurdle is strictly **$\Delta \text{margin} > \$15.0$**. Any candidate with margin delta $\le \$15.0$ is marked `is_superior = False` unless money gain $> \$20.0$.

### 2.3 WinModel Application & Scoring
- In `aec/evaluation/win_model.py`:
  ```python
  def estimate_p_win(self, current_gap: float, margin_delta: float) -> float:
      projected_margin = current_gap + margin_delta
      scale = 1000.0
      return 1.0 / (1.0 + math.exp(-projected_margin / scale))
  ```
- `expected_p_win` is strictly monotonic with `margin_delta` for all candidates in the same turn (since `current_gap` is constant across candidates in turn $t$).
- Therefore, ranking candidates by `expected_p_win` is mathematically identical to ranking candidates by `delta_terminal_margin`.

### 2.4 Absolute vs Relative Comparison
- **Absolute vs Baseline**: Every candidate is evaluated solely as $\Delta = \text{CandidateRollout} - \text{BaselineRollout}$.
- **Absence of Relative Comparison**: Candidates are **NEVER** evaluated directly against each other ($\Delta_{\text{cand1}} - \Delta_{\text{cand2}}$).
- There is no margin gap requirement between the winner and the runner-up: a candidate with $\Delta = +\$15.05$ defeats a candidate with $\Delta = +\$15.00$, and a tranche candidate with $\Delta = +\$16.0$ defeats a foundation candidate with $\Delta = +\$15.5$.

### 2.5 Tie Resolution
- In `executor.py` line 727:
  `if best_eval_result is None or eval_res.expected_p_win > best_eval_result.expected_p_win:`
- Because strict inequality `>` is used, an exact tie retains the *earlier* simulated candidate. If strictly greater, the new candidate overwrites the previous leader.

### 2.6 Competition with Foundation Mechanisms
- Foundation mechanisms (`DEPENDENCY_AWARE_MARKET_TIMING`, `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN`) enter `candidate_patches` alongside experimental mechanisms.
- Under Phase018 Repair A (`enable_funnel_reservation`), foundation mechanisms are guaranteed reserved seats in the top-$K$ prune list so they are not crowded out before simulation.
- However, at the commit selection point (line 727), foundation candidates receive **NO preferential margin or stability weighting**. If an experimental tranche candidate has $\Delta = +\$32.0$ and the foundation candidate has $\Delta = +\$25.0$, the tranche candidate commits and displaces the foundation candidate.

### 2.7 Runner-Up Availability & Information Loss
- Up to `max_simulations = 8` candidates are simulated and evaluated.
- However, the compiler retains ONLY `best_candidate`, `best_certificate`, and `best_eval_result`.
- The delta and properties of the runner-up candidates are recorded in telemetry but are **completely discarded** by the decision policy. The compiler does not verify whether the winning candidate's advantage over the runner-up is fragile, noise-level, or robust.

### 2.8 Local vs Long-Horizon Ranking
- Funnel screening (pre-simulation) uses local heuristic rankings (e.g. priority stamping, revenue estimates).
- Exact simulation uses the long-horizon adaptive horizon ($\approx 5$ to $40$ steps, macro-escalated).
- Commit selection uses the terminal margin point estimate, with **zero measurement of perturbation sensitivity or neighborhood stability**.

### 2.9 Conditions for Abstention
- The compiler abstains (falling back to baseline backbone action) if and only if:
  1. No candidate patches are generated or survive pruning.
  2. All simulated candidates fail safety checks (`passed_safety == False`).
  3. All simulated candidates fail the economic hurdle (`is_superior == False`).
  4. The candidate that passed is in scientific quarantine.
- The compiler CANNOT abstain because a candidate is "fragile", "unstable across neighbor actions", or "marginally superior to a much safer alternative".

---

## 3. Structural Vulnerabilities Identified

1. **Max-Selection Winner's Curse**:
   When evaluating multiple candidate variants or speculative sales, picking the maximum single-point rollout estimate systematically selects upward-biased estimation noise.
2. **Missing Neighborhood Robustness**:
   A tranche order selling $q=5$ units is committed if its point rollout yields $+\$16.0$, even if $q=4$ yields $-\$50.0$ and $q=6$ yields $-\$80.0$.
3. **Zero-Margin Foundation Displacement**:
   An experimental tranche candidate with $+\$16.0$ displaces a proven foundation candidate with $+\$15.5$, absorbing high tail risk for an unverified $\$0.50$ point advantage.
4. **Binary Commit vs Abstain**:
   There is no concept of abstaining when the candidate advantage is within the noise floor of the simulation trajectory.
