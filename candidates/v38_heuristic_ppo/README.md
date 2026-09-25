# V38: Heuristic-Guided Hierarchical Residual PPO

**Candidate ID:** `V38`  
**Package:** `candidates/v38_heuristic_ppo/`  
**Status:** RESEARCH ONLY — NOT SUBMITTED  
**Production Incumbent:** V35 (`candidates/v35_a7_opening/main.py`)  

---

## Architecture Summary
1. **State Abstraction (`state_features.py`):** Separates physical state (spatial tiles, chore coordinates) from economic state (liquid cash, price trends, wage runway, balance sheet value).
2. **Deterministic Expert Heuristic (`heuristic.py`):** Unifies V35 opening wash (25/25 wheat) with A7 physical chore routing and reactive safety layers.
3. **Macro Action Vocabulary (`macro_options.py`):** 11 discrete macro options (`0: TRUST_HEURISTIC` through `10: RECOVERY`) with strict action masking.
4. **Safety Enforcer (`safety.py`):** Multi-tier guardrails (liquidity floor, intervention cooldown, bounded duration $H=4$, terminal protection).
5. **Macro Policy (`policy.py`):** Masked discrete actor-critic MLP operating on 64 normalized economic features.
6. **Counterfactual Engine (`counterfactual.py`):** Exact forward simulation to measure causal advantage $\hat{A}(s, a) = C_T(a) - C_T(\text{heuristic})$.
