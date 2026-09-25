# V39 Live Competition Monitoring & Observability Protocol

## 1. Objective
Per Phase 25, maintain a lightweight, non-invasive monitoring framework to observe production candidate V35 without polling spam, automated continuous loops, or any mutation commands.

---

## 2. Monitored Production Reference

| Parameter | Production Value |
| :--- | :--- |
| **Candidate Name** | `V35_FINAL_SUBMISSION.tar.gz` |
| **Kaggle Submission ID** | `56540535` |
| **Live Rating (Elo)** | `1642.5` |
| **Cataloged Episodes** | `29` (23 Wins, 6 Losses, 0 Ties | 79.31% Win Rate) |
| **Opening Signature** | Step 1: `[['BUY_PRODUCT', 'WHEAT', 25], ['SELL', 'WHEAT', 25]]` |
| **Status** | Active, Frozen, Protected |

---

## 3. Read-Only Monitoring Utility

A standalone script is maintained at [`scripts/v39_monitor_live.py`](file:///c:/Users/Sundareswaran/Kagriculture/scripts/v39_monitor_live.py).

### Capabilities
1. Verifies the integrity of local cataloged games in `scratch/v39/live/episodes.jsonl`.
2. Inspects read-only competition submissions via `kaggle competitions submissions -c kaggriculture`.
3. Detects newly completed matches and records them into the forensics pipeline.
4. Identifies rating drift versus empirical match results.

### Invariants
* **NEVER** calls `kaggle competitions submit`.
* **NEVER** modifies live submission parameters or active state.
* **NEVER** runs continuously as a high-frequency polling loop.
* Manual invocation or low-frequency batch execution only.

---

## 4. Rating Noise Discipline (Phase 27 Audit)

A core tenet of the V39 protocol:
> *A temporary rating drop is NOT automatically evidence of a strategy defect. Do not change V35 merely because its live rating moves.*

### Empirical Justification
* Matchmaking on the Kaggle ladder is stochastic with wide variance in opponent skill (from unrated baselines to 2800+ Elo bots).
* In our live dataset, V35 faced `Adhiraj Jagtap` on seed `203942858` where the opponent hit an unusually fast SE unlock, resulting in a -$11.6k deficit. Rating dropped temporarily, but rebounded to 1642.5 over the subsequent 10 matches.
* Strategy modifications are strictly prohibited unless a failure mode is:
  1. Observed across multiple matches,
  2. Reconstructed to a deterministic causal divergence,
  3. Verified via exact local counterfactual search,
  4. Demonstrated to produce **zero casualties** across baseline wins.
