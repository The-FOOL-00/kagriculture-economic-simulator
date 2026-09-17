# EXP-AEC-001: Adaptive Economic Compiler (AEC) Foundation Validation
## Formal Prospective Preregistration Protocol

**Document Identifier**: `EXP-AEC-001_AEC_V1_PREREGISTRATION`  
**Experiment Name**: `EXP-AEC-001`  
**Author**: Senior Research Engineer & Adversarial Reviewer  
**Date**: 2026-09-17  
**Status**: **PREREGISTERED — PENDING EXECUTION AUTHORIZATION**  
**Execution Covenant**: **NO PROSPECTIVE EXPERIMENT HAS BEEN EXECUTED. EXECUTION IS BLOCKED PENDING EXPLICIT USER APPROVAL.**

---

### 1. Objective
To empirically evaluate whether the Adaptive Economic Compiler (AEC) framework—operating as an event-triggered, counterfactually certified tactical patch compiler over the frozen V3 macro backbone—maintains baseline stability, eliminates tactical execution bottlenecks, and produces a non-negative win-rate and terminal margin delta under paired Common Random Number (CRN) evaluation without introducing negative tail variance.

---

### 2. Primary Hypothesis
$$\mathcal{H}_1: \mathbb{E}[\Delta \text{Margin}(\text{AEC}_{\text{frozen\_foundation}} - \text{V3}_{\text{control}})] > 0 \quad \text{and} \quad \Delta \text{WinRate} \ge 0$$
Operating AEC over the frozen V3 backbone with verified foundation transformations (Market Front-Loading, Terminal Liquidation, Phase-Boundary Shutdown, Route Weed Clearing) produces a statistically significant non-negative paired terminal margin delta and non-negative win delta compared to the raw V3 backbone alone.

---

### 3. Secondary Hypotheses
1. **$\mathcal{H}_{2a}$ (Dormant Parity)**: On turns where no event is detected, AEC produces zero divergence from the baseline action ($0.0\%$ mutation rate, $<0.1\text{ ms}$ overhead).
2. **$\mathcal{H}_{2b}$ (Safety Invariant Integrity)**: AEC incurs zero runtime exceptions, zero invalid game engine actions, zero shed inventory overflows ($>100$ units), and zero solvency breaches across all simulated turns.
3. **$\mathcal{H}_{2c}$ (Downside Tail Protection)**: The 5th percentile of paired score delta ($\Delta P_{05}$) does not deteriorate by more than $\$250.00$ relative to control.

---

### 4. Control Specification
- **Agent**: Frozen Teammate V3 macro policy.
- **Source Artifact**: `submission_Vj_kc_v3.tar.gz` (workspace root).
- **Cryptographic SHA-256**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`.
- **Runtime Mode**: Raw uncompiled backbone execution via direct submission agent callable. Zero AEC wrappers or interceptors.

---

### 5. Treatment Specification
- **Agent**: Frozen Teammate V3 macro policy wrapped by `AECExecutor`.
- **Backbone Adapter**: `aec.integration.BackboneAdapter` loading the identical V3 tarball in memory and enforcing the exactly-one-live-call invariant.
- **Compiler Configuration**: `AECConfig` frozen as declared in Section 6.

---

### 6. Exact AEC Configuration
```python
AECConfig(
    short_horizon=6,
    normal_horizon=18,
    extended_horizon=36,
    max_opportunities=16,
    max_candidates=8,
    max_simulations=8,
    cash_deviation_threshold=200.0,
    shed_alarm_threshold=95,
    price_shock_relative=0.25,
    opponent_supply_shock_qty=4,
    per_step_latency_limit_ms=100.0,
    fail_closed=True,
    backbone_type="v3",
    v3_tarball_path="submission_Vj_kc_v3.tar.gz",
    v3_tarball_sha256="845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943",
)
```

---

### 7. Exact Mechanism Set (Enabled Foundation)
The treatment for EXP-AEC-001 enables ONLY verified, structurally grounded mechanisms:
1. **Event Detection**:
   - `E1_FARM_OBSTRUCTION`: Immediate worker standing on weed.
   - `E3_SHED_CAPACITY_RISK`: Shed total $\ge 95$ or late-hour overflow risk.
   - `E4_MARKET_REGIME_SHIFT`: Product price liquidity ratio deviation $\ge 25\%$.
   - `E6_SHOP_INFORMATION_REVEAL`: Step $72 \times k$ town shop reveal.
   - `E7_PRODUCTION_DEADLINE`: Crop biological maturity cutoffs (steps 574, 622, 670).
   - `E8_TERMINAL_TRANSITION`: Step $\ge 670$ endgame and step 718 liquidation.
2. **Opportunity Analyzers**:
   - `RouteOpportunityAnalyzer`: Local weed dig.
   - `MarketOpportunityAnalyzer`: Market order front-loading.
   - `TerminalOpportunityAnalyzer`: Terminal liquidation and phase shutdown.
3. **Patch Families**:
   - `LOCAL_WEED_DIG` (`VERIFIED_SOURCE`): Convert PASS/blocked step to DIG.
   - `FRONTLOAD_ORDERS` (`VERIFIED_SOURCE`): Partition market orders into SELL -> BUY_PRODUCT -> Capital.
   - `TERMINAL_LIQUIDATION` (`REUSED_SAFETY`): Authoritative step-718 shed liquidation sorted by total value descending.
   - `PHASE_SHUTDOWN` (`VERIFIED_SOURCE`): Prune seed purchases for crops that cannot mature before step 718.
4. **Safety & Evaluation**:
   - `SafetyChecker`: Legality, physical bounds, zero overflow discard, solvency.
   - `WinModel`: Lexicographic evaluation with temporary sacrifice permission.

---

### 8. Disabled / Quarantined Mechanisms
To guarantee mechanism isolation and avoid confounding unproven heuristics with compiler validity, the following mechanisms are **EXPLICITLY DISABLED** in EXP-AEC-001:
- `DYNAMIC_SHADOW_HARVEST` (`PLAUSIBLE_UNPROVEN`): Disabled. (Heuristic distance ratio; passive continuation lookahead defect).
- `CARGO_FERRY_PRIORITY` (`PLAUSIBLE_UNPROVEN`): Disabled. (Missing generator support).
- `OPPONENT_PREEMPT_SELL` (`PLAUSIBLE_UNPROVEN`): Disabled. (Preemption price model uncalibrated).
- `EMERGENCY_FEED_PURCHASE` (`VERIFIED_SOURCE`): Disabled. (Missing generator support).
- `TERMINAL_HARVEST_SWEEP` (`REUSED_SAFETY`): Disabled. (Missing generator support).
- `evaluate_town_cycle_signal` (`PLAUSIBLE_UNPROVEN`): Disconnected / Disabled.

---

### 9. Candidate and Search Limits
- Max opportunities proposed per turn: 16
- Max candidate patches after static pruning: 8
- Max forward counterfactual simulations: 8
- Pruning rule: Rejects off-board moves, invalid order ops, non-positive quantities.

---

### 10. Horizon Configuration & Continuation Semantics
- `short_horizon`: 6 steps (used for `LOCAL_WEED_DIG`, `FRONTLOAD_ORDERS`).
- `normal_horizon`: 18 steps.
- `extended_horizon`: 36 steps (used for `PHASE_SHUTDOWN`).
- `terminal_horizon`: $\min(\text{remaining}, 2)$ for `TERMINAL_LIQUIDATION`.
- **Continuation Semantics**: Counterfactual H-step rollout uses deterministic continuous backbone-compatible continuation and does not default to PASS after offset 0. Future offsets propagate planned macro actions directly from the backbone route tape via read-only lookahead without additional live agent invocations, faithfully modeling multi-step worker positioning, shed inventory, and market order dynamics across all $H$ simulated offsets.

---

### 11. Event Configuration
- Fast-path bypass active: When 0 events fire, return baseline action immediately.

---

### 12. Opponent Pressure Configuration
- `OpponentPressureModel`: Active in counterfactual simulation to provide realistic market absorption resistance during order evaluation.

---

### 13. Evaluation Hierarchy
Lexicographic ordering:
1. Hard Safety Certification ($100\%$ required: overflow $= 0$, legal $= \text{True}$, cash $\ge 0$).
2. Expected $P(\text{WIN})$ delta $> +0.005$ ($+0.5\%$).
3. Expected Terminal Margin Delta $> +\$15.00$.
4. Net Own Money Delta $> +\$20.00$ with non-negative margin delta ($\ge \$0.00$).

---

### 14. Safety Rules
- Complete fail-closed boundary: If any unhandled exception occurs in AEC IR, detectors, search, simulation, or safety verification, fallback to baseline action immediately.
- If backbone raises an exception: emit safe emergency pass `{"farmer": ["PASS"], "hands": [], "market": []}`.

---

### 15. Cohort Selection & Governance
- **Selected Cohort**: Seeds `340000` to `340049` ($N=50$ contiguous seeds).
- **Match Design**: Paired Common Random Numbers (CRN).
  - Match 1: Treatment = Player 0, Control = Player 1.
  - Match 2: Treatment = Player 1, Control = Player 0.
  - Total games: $50 \times 2 = 100$ games.
- **Virginity Audit**:
  - $0$ historical executions in Git history or result files.
  - Distance to Final Holdout (`214200–214249`): **125,751 seeds**.
  - Completely disjoint from DEV-001 through DEV-007 and ARCH-002/003.

---

### 16. Sample Size and Power
- Sample size: $N = 50$ paired seed pairs ($100$ matches).
- Standard development sample size matching Gate 0.3 governance.
- Adequate to detect large tactical regressions ($\Delta M < -\$100$) or catastrophic tail failures with $>95\%$ power.

---

### 17. Primary Metrics
1. **Paired Terminal Margin Delta ($\Delta M$)**:
   $$\Delta M_s = \frac{1}{2} \left[ (M_{\text{treat}, P0} - M_{\text{ctrl}, P1}) + (M_{\text{treat}, P1} - M_{\text{ctrl}, P0}) \right]$$
2. **Paired Win Delta ($\Delta W$)**:
   $$\Delta W = W_{\text{treatment}} - W_{\text{control}}$$

---

### 18. Secondary Metrics
1. Mean Treatment Score vs Mean Control Score ($\mu_{\text{treat}} - \mu_{\text{ctrl}}$).
2. 5th Percentile Delta ($\Delta P_{05}$).
3. Interventions per Game ($N_{\text{commits}}$).
4. Abstain Rate ($N_{\text{abstain}} / N_{\text{events}}$).
5. Average turn latency (ms) and 99th percentile turn latency (ms).

---

### 19. Acceptance Criteria
All of the following must hold simultaneously:
1. **Non-Inferiority of Win Rate**: $\Delta W \ge 0$ (Treatment wins $\ge$ Control wins).
2. **Non-Negative Mean Margin Delta**: $\bar{\Delta M} \ge \$0.00$.
3. **Median Margin Delta**: $\text{Median}(\Delta M) \ge \$0.00$.
4. **Tail Protection**: $\Delta P_{05} \ge -\$250.00$.
5. **Zero Safety Regressions**: 0 engine rule violations, 0 shed overflows, 0 fatal unhandled crashes.
6. **Dormant Zero-Leakage**: Exactly 0 action differences on no-event turns.

---

### 20. Falsification Criteria
The hypothesis $\mathcal{H}_1$ is formally **REJECTED / FALSIFIED** if ANY of the following occur:
1. $\Delta W < -2.0\%$ (Treatment loses more games than Control).
2. $\bar{\Delta M} < -\$50.00$ with $p < 0.05$ (Statistically significant margin degradation).
3. Any game ends in disqualification or illegal action rejection by the Kaggle simulator.
4. Any candidate commit causes shed overflow discard ($>100$ units) in live play.
5. Max turn latency exceeds $1,000\text{ ms}$ on any turn.

---

### 21. Exclusion & Invalid-Run Rules
- No seed may be discarded, excluded, or rerun due to unfavorable economic outcomes.
- An execution is valid only if all 50 seeds complete both Player 0 and Player 1 matches (100 total matches).
- Any run halted by an infrastructure failure (e.g., power loss, OS kill) must be audited and resumed exactly at the interrupted seed without altering completed records.

---

### 22. Stopping Rules
- **Early Stop for Safety Failure**: If within the first 10 seeds, $\ge 2$ live engine exceptions occur, the experiment is terminated immediately and marked `ABORT_SAFETY_DEFECT`.
- No early stopping for positive or negative variance.

---

### 23. No-Tuning Rule
- Parameters in `AECConfig`, event detector thresholds, and opportunity relevance formulas are strictly frozen prior to execution.
- No tuning, threshold modification, or coefficient tweaking is permitted during or after inspecting experimental output.

---

### 24. Holdout Protection Covenant
- Seeds `214200–214249` (`HOLDOUT-COHORT-V1`) are strictly quarantined and touchless. Zero access, zero simulation.

---

### 25. Randomization & Pairing Procedure
- Seed list: `list(range(340000, 340050))`.
- Each seed is simulated twice:
  - Match A: `Game(seed, [Treatment, Control])`
  - Match B: `Game(seed, [Control, Treatment])`
- Completely eliminates role and map bias.

---

### 26. Reproducibility Information
- Python Version: 3.14.3
- Platform: Windows AMD64
- Simulator: `kagsim` C++ extension (`sim.hpp`)
- Commit: Pinned to git HEAD at execution launch.

---

### 27. Expected Runtime
- 100 matches $\times \sim 10-15\text{ seconds/match} \approx 15-25\text{ minutes}$ total runtime.

---

### 28. Output Artifact Specification
The experiment execution must produce:
1. `EXECUTION_MANIFEST.json`: Cryptographic hashes, start/end timestamps, git commit, seed range.
2. `CONFIG.json`: Serialized `AECConfig` and treatment parameters.
3. `RAW_RESULTS.json`: Match-level results (scores, winner, steps, player roles).
4. `PAIRED_DELTAS.csv`: Seed-level paired deltas ($\Delta M_s$, $\Delta S_s$, win indicator).
5. `TELEMETRY_EVENTS.csv`: Step-level compiler telemetry for all commits, abstains, latencies.
6. `SUMMARY.json`: Formal hypothesis evaluation statistics and decision verdict.
