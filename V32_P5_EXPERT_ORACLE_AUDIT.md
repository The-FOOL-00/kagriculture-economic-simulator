# V32 P5 — EXPERT ORACLE AVAILABILITY AUDIT

## 1. EXECUTIVE SUMMARY & FORMAL DETERMINATION

In accordance with Section 17 of the V32 P5 Protocol, an exhaustive architectural and forensic audit of the canonical teacher (`E2_A7` / `V27-ABL-A7`) and its underlying execution chassis (`V3BackboneAdapter` / `Chassis`) was conducted to evaluate whether a true state-based expert oracle is available for off-distribution dataset aggregation (DAgger).

### Formal Determination: **CASE B — EXPERT REQUIRES HIDDEN STATE / OPEN-LOOP TRAJECTORY CONTEXT**

> **A true closed-loop, Markovian state-based expert oracle does NOT exist in this repository.**
>
> The expert A7 (and its V3 lineage) is an **open-loop macro-route tape replayer** wrapped with shallow reactive guardrails (e.g., weed repair, hand alignment, price suppression). Its actions at step $t$ are derived from static precomputed index lookups `tape[step]` rather than closed-loop state-to-action optimization from arbitrary environment states.
>
> Querying A7 on an off-distribution, policy-divergent state produces actions conditioned on the **expert's intended trajectory**, not optimal or even valid actions for the **policy's actual state**. Calling A7 off-distribution emits invalid commands (e.g. `['PLACE', 'SHEEP']` when holding 0 sheep, `['FEED']` on empty tiles, or buying 5 hands and 4 animals with insufficient cash).
>
> **Per Section 17 & Section 19: Genuine DAgger CANNOT and MUST NOT be faked.** 
> Supervised targets on policy-generated states cannot be manufactured by blindly evaluating A7 off-distribution.

---

## 2. FORENSIC AUDIT EVIDENCE

### 2.1 Tape Architecture Inspection
Inspection of `submission_Vj_kc_v3.tar.gz` and `candidates/v30_a7_standalone/main.py` reveals the core decision mechanism of the expert:

```python
class Chassis:
    def __init__(self, routes, router=None, settings=None, opponent_plan=None):
        self.routes = {rid: list(tape) for rid, tape in routes.items()}
        self.router = router or (lambda observation, step, state: next(iter(self.routes)))
        ...
```

At each step $t$:
```python
route = self.router(observation, step, st["router_state"])
action = self._route_action(route, step)  # Returns copy.deepcopy(self.routes[route][step])
```

The action dictionary emitted at step $t$ is read directly from `self.routes[route][step]`. The route index is selected at step 0 based on market conditions, and thereafter the policy simply iterates through the pre-computed 720-step tape.

### 2.2 Empirical Demonstration on Off-Distribution States
We empirically tested `V27AblationAdapter("V27-ABL-A7")` on counterfactual and policy-generated states in `scratch/audit_a7_oracle.py`:

1. **Step 1 Market Action under Cash Perturbation**:
   - When step 0 was executed with `PASS` instead of the opening wash (leaving cash at $200 instead of $3,000), A7 was invoked on step 1.
   - A7 emitted:
     ```python
     market: [['SELL', 'WHEAT', 13], ['BUY_PRODUCT', 'WHEAT', 5], 
              ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], ['HIRE'], 
              ['BUY_ANIMAL', 'COW', 2], ['BUY_ANIMAL', 'SHEEP', 2]]
     ```
   - Total cost of this action exceeds $1,800. A7 emitted this command blindly because `self.routes[0][1]` specifies hiring 5 hands and purchasing 4 livestock, completely unaware that the player only has $200.

2. **Step 3–15 Physical Unit Actions**:
   - Examination of `self.routes[0]` timesteps 0–15:
     - Step 3: `['PICKUP', 'SHEEP']` (assumes sheep in shed from step 1 purchase)
     - Step 4: `['PICKUP', 'WHEAT']` (assumes wheat in shed)
     - Step 7: `['BUILD_PASTURE']` (assumes farmer walked to specific pasture coordinate)
     - Step 8: `['PLACE', 'SHEEP']` (assumes farmer is carrying sheep)
     - Step 9: `['FEED']` (assumes sheep is placed on current tile)
     - Step 12: `['PLANT', 'MELON']` (assumes melon seeds purchased and tile tilled)
   - If the learner deviates at step 2 (e.g. moving South or East instead of following the tape), at step 8 A7 will still command `['PLACE', 'SHEEP']` on whatever tile the learner is standing on, regardless of validity.

### 2.3 Internal State and History Dependence
In addition to the static route tapes, A7 maintains mutable internal state dictionaries across steps:
- `st["pending"]`: Action queues displaced by weeds.
- `st["sell_state"]`: Cross-step price suppression dictionaries (`r36_debts`, `suppress`).
- `_PARENT_NS` global dictionaries: `_STATES`, `_HORIZONS`, `_LAST`, `_RESERVES`, `_PENDING`.

Invoking A7 out of sequence or on divergent states disrupts these internal historical buffers.

---

## 3. METHODOLOGICAL IMPLICATIONS FOR P5

1. **DAgger is Infeasible**:
   - True DAgger requires an expert oracle $O(s)$ that maps any reachable state $s \in \mathcal{S}$ to the optimal action $a^* \in \mathcal{A}$ from that state.
   - A7 only knows $a^*_t = \text{tape}[t]$, which is conditioned on the assumption that the agent visited $s^*_0, \dots, s^*_{t-1}$.
   - Evaluating A7 on $s_t^{policy}$ produces invalid, ungrounded actions that would contaminate the BC training distribution.

2. **Synthetic / Heuristic Labels are Prohibited**:
   - Per Section 16 & Section 19: "Do NOT fabricate a target... Do NOT call synthetic labels expert labels."
   - We will NOT attempt to build a custom heuristic re-planner to generate synthetic labels.

3. **Governed Path Forward**:
   - The focus of P5 must be:
     - **Quantifying Covariate Shift**: Execute the Teacher-Forced vs. Free-Running rollout diagnostic to determine exactly when, how, and why the BC policy diverges from the expert demonstration manifold.
     - **Early-Horizon Analysis**: Analyze steps 0–24 to trace the chain of first divergence.
     - **Arm 2 (Bounded Early-Horizon Weighting)**: Emphasize the critical early post-wash steps (steps 1–10) in the supervised BC loss so the policy adheres to the expert route long enough to establish the economic foundation (livestock, hiring, planting).
