# V34 Forensic Audit of V33 Methodology & Scientific Validity

**Program:** Kagriculture V34 Research Program  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Scope:** Forensic evaluation of V33's experimental design, data generation, route switching mechanisms, and leakage posture.  

---

## 1. Executive Summary of Audit Findings

The V33 research program attempted to build a meta-strategy selector over a portfolio of 6 expert routes (`R0_A7`, `R1_V22R1`, `R2_DMITRII`, `R3_P3090`, `R4_V54`, `R5_V25P3`). While V33 correctly concluded that A7 is universally dominant over other entire static routes, its implementation of route switching, counterfactuals, and selector training suffered from severe methodological flaws that prevent its quantitative selector conclusions from being accepted as final.

### Summary Classification of V33 Findings:
| Finding ID | V33 Claim / Finding | Forensic Audit Classification | Rationale & Evidence |
| :--- | :--- | :---: | :--- |
| **F-01** | Transitive dominance of A7 in round-robin match matrix | **VALID** | Evaluated via full, independent, 720-step matches between agents from clean initial states ($t=0$). Zero leakage. |
| **F-02** | Absence of rock-paper-scissors non-transitivity cycles | **VALID** | Cycle-finding over the round-robin tournament graph yielded zero cycles. Re-verified mathematically. |
| **F-03** | Market overlay sell-reordering degrades A7 cash and win rate | **VALID** | Evaluated in paired matches against league opponents; failure caused by intra-turn liquidity starvation when high-velocity wheat sales were delayed. |
| **F-04** | Route transition counterfactual headroom ($+\$4,613$ on Seed 249677) | **INVALID** | Evaluated by naively calling `R2_DMITRII` from an A7-initialized farm at $t=48$ against opponent `R2_DMITRII`. Dmitrii's internal state machine was desynchronized from the actual farm physical state. Furthermore, only one opponent family was tested. |
| **F-05** | Regime dataset classification labels | **INVALID** | Ground-truth opponent identities were used to assign regime categories, breaching the observable-only formulation. |
| **F-06** | Selector dataset oracle route labels | **INVALID** | Route superiority labels were derived using global seed and opponent knowledge rather than causal online information available at decision time. |
| **F-07** | Selector confidence-gated 100% abstention | **VALID_WITH_LIMITATIONS** | The selector correctly chose to abstain and default to A7, but this was a consequence of finding no complementary alternative in an invalidly constructed option pool. |
| **F-08** | Early information horizon (entropy drop between $t=4$ and $t=16$) | **VALID_WITH_LIMITATIONS** | Observable variance increases as opponent moves and hires are revealed, but observable price variations at $t \le 16$ have low mutual information with terminal market demand. |

---

## 2. Detailed Dimension-by-Dimension Audit

### Dimension A: Opponent Leakage
- **Audit Target:** Features in `candidates/v33_meta_strategy/selector.py` and `evaluate_meta_selector.py`.
- **Finding:** While the online feature extractor in `RouteSelector.extract_observable_features` correctly reads only observable properties (`opp_visible_hands`, `opp_claimed_quads`, spot market prices), the training datasets (`regime_dataset.jsonl` and `selector_dataset.jsonl`) generated during exploration explicitly indexed opponent IDs (`opp_id` in `task` parameters) and utilized opponent identities to partition regimes.
- **Classification:** **INVALID in dataset generation; VALID in runtime extraction.**

### Dimension B: Seed Leakage
- **Audit Target:** Label generation across `DEV_SEEDS = [249675..249679]`.
- **Finding:** In `candidates/v33_meta_strategy/test_route_transitions.py`, counterfactual evaluations were computed by hardcoding seeds `[249675, 249676, 249677]`. The observed $+\$4,613$ gain for Dmitrii was unique to Seed 249677. The selector's thresholding was post-hoc tuned to match the observed properties of that specific seed, creating severe risk of seed memorization.
- **Classification:** **INVALID.**

### Dimension C: Future Leakage
- **Audit Target:** Step $t$ observable feature dictionary.
- **Finding:** No direct temporal future leakage was detected in `extract_observable_features`. The features inspected are strictly current prices, inventories, and farm status at step $t$. However, market moving averages were not causal (some exploratory notebooks computed trajectory-wide statistics).
- **Classification:** **VALID (clean runtime features).**

### Dimension D: Replay Transplantation Validity
- **Audit Target:** Route execution in `RouteBank`.
- **Finding:** A route is an open-loop or semi-closed-loop action tape compiled under specific environment assumptions. When an agent like `R3_P3090` or `R2_DMITRII` is executed against an active opponent that buys or sells differently than the training replay, the environment deviates. `R3_P3090` completely collapsed (0% win rate across all 50 matches) because its tape actions depended on public shop state that was consumed by opponents.
- **Classification:** **VALID (confirms open-loop route fragility).**

### Dimension E: Route-Prefix Fairness
- **Audit Target:** Comparison of routes in `route_tournament.py` vs `test_route_transitions.py`.
- **Finding:** In `route_tournament.py`, all 6 routes were compared fairly from identical $t=0$ initial states. This confirmed that A7 is globally superior to other static agents.
- **Classification:** **VALID.**

### Dimension F: Route Transition Validity (Physical Coherence)
- **Audit Target:** Implementation in `test_route_transitions.py`:
  ```python
  def hybrid(obs, configuration=None):
      step = int(obs.get("step", 0) or 0)
      if step < t_switch:
          return r0_agent(obs, configuration)
      else:
          return target_agent(obs, configuration)
  ```
- **Finding:** This is catastrophic. At $t=t_{\text{switch}}$, `target_agent` is suddenly called on a farm state that was developed under A7's crop-heavy, single-quadrant opening.
  - If `target_agent` is `R2_DMITRII`, Dmitrii's internal logic assumes pastures, cows, sheep, and specific worker roles already exist. None exist on an A7 farm at $t=48$.
  - Dmitrii tries to feed non-existent cows or place animals into non-existent coops, generating invalid/no-op actions and causing rapid economic collapse.
  - Splicing wholesale route controllers midgame is physically incoherent and invalidates any causal conclusion about route switching.
- **Classification:** **INVALID.**

### Dimension G: A7 Baseline Parity
- **Audit Target:** In all paired evaluations, A7 standalone was executed using `candidates/v30_a7_standalone/main.py` and `E9_AST`.
- **Finding:** The A7 baseline execution is bit-identical to the protected incumbent. Hash verification confirmed 100% parity.
- **Classification:** **VALID.**

---

## 3. Preserved Scientific Facts for V34

The following empirical facts established during V33 survive audit and form key design constraints for V34:

1. **A7 is Globally Dominant Over Static Alternative Routes:**
   No other standalone expert (V22R1, Dmitrii, P3090, V54, V25P3) outperforms A7 in a full match starting from $t=0$. Therefore, V34 must keep A7 as the default backbone.
2. **Wholesale Switching Midgame Destroys Physical Choreography:**
   One cannot simply swap agent code mid-match. Interventions must be localized, tactical, and explicitly A7-compatible.
3. **Naive Market Reordering Starves Intra-Turn Liquidity:**
   A7's open-loop action tapes rely on selling wheat first to fund intra-turn purchases. Any market order adjustment must be strictly guarded by an exact liquidity verifier.
4. **Counterfactual Headroom Must Be Measured Across the League:**
   Measuring counterfactuals against only a single opponent (e.g. Dmitrii) produces regime-specific illusions that collapse against other opponents.

---

## 4. Audit Sign-off & Transition to V34

V33's route-portfolio switching is permanently retired due to physical incoherence and dataset leakage.
V34 will proceed with exact, localized, A7-compatible tactical forward search.
