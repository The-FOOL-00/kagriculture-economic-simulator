# V25 Backbone Preregistration

## 1. Experimental Objective
Test whether replacing V3's macro planning layer with a coherent planner (addressing capital velocity, labor utilization, crop composition, and livestock scaling prior to route compilation) can outperform standalone V3 in closed-loop CRN matches.

## 2. Tested Candidates
* **P1 — Capital/Labor Planner** (`candidates/v25_p1_macro.py`): Replaces opening cash lockup and worker dispatch logic; eliminates route padding `PASS`.
* **P2 — Production/Livestock Planner** (`candidates/v25_p2_production.py`): Dynamic crop composition (fast turnover Carrot/Tomato integration) + NPV livestock scaling.
* **P3 — Unified Macro Planner** (`candidates/v25_p3_unified.py`): Joint capital, labor, production, and livestock optimization.

## 3. Benchmark Protocol
* **Opponent**: Standalone V3 (`submission_Vj_kc_v3.tar.gz` unpacked payload).
* **Seating**: Common Random Numbers (CRN) with mirrored seating:
  - Match A: Candidate (Seat 0) vs V3 (Seat 1) on seed $S$.
  - Match B: V3 (Seat 0) vs Candidate (Seat 1) on seed $S$.
* **Discovery Cohort**: Seeds `249430..249449` (20 seeds $\times$ 2 seats = 40 matches per candidate).
* **Parallelism**: Process-level multiprocessing with `MAX_WORKERS = 9`.
* **Match Output**: Independent checkpointing to `results/v25_backbone_matches.jsonl`.

## 4. Endpoints & Success Metrics

### Primary Endpoint
* **Mean Paired Terminal Reward Delta**:
  $$\Delta_{mean} = \frac{1}{N} \sum_{i=1}^N (Reward_{Candidate, i} - Reward_{V3, i})$$

### Secondary Endpoints
* **Win / Loss / Tie Count**:
  - Win: $\Delta_i > +500$
  - Loss: $\Delta_i < -500$
  - Tie: $|\Delta_i| \le 500$
* **Median Paired Delta**: $\Delta_{median}$
* **Tail Loss Floor**: Minimum paired delta across all matches ($\Delta_{min}$).
* **Early Labor Efficiency**: Percentage of productive turns ($1 - \text{Idle Rate}$) for $t \in [0, 100]$.
* **Execution Safety**: 0 crashes, 0 illegal action exceptions, 100% completion across 720 turns.

## 5. Promotion Gate (Preregistered Decision Rules)

To earn promotion to the Confirmation Trial:
1. $\Delta_{mean} > 0.0$
2. Win Count $>$ Loss Count
3. Worst-case tail loss $\Delta_{min} > -50,000$ (no catastrophic system breakdowns)
4. Bit-exact determinism verified in serial vs. parallel equivalence audit.
5. Maximum **ONE** candidate promoted (the top performer).

If no candidate meets all criteria:
Conclude: **`V25 NO SUFFICIENT PLANNER IMPROVEMENT`** and freeze V22R1.
