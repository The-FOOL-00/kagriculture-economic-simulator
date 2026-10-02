# V32 P2 ORACLE REGRET (BC floor; no PPO deltas exist)

R1 oracle lift on TEST: +$7,897 over A7 (robust, 40/40 seeds).

| Policy | Mean cash (SCREEN seat-0) | Oracle regret |
| :--- | ---: | ---: |
| A7 (reference) | ~$98,159 (gate) | ~$7,897 |
| Mixture-BC | $31 (median $0, n=138) | ~$106,000 |
| A7-BC | ~$2 (n=16) | ~$106,000 |
| PPO | — (never ran) | — |

BC regret ≈ $110k+: BC captures NONE of the oracle gap (it captures none
of A7 either). The §51 question ("does PPO reduce oracle regret") is
unanswerable in P2 — it awaits a competent init in the follow-up phase.
