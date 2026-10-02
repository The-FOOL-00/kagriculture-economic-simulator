# V29 — INDEPENDENT RERUN AUDIT (preregistered 14-instance subset)

Subset (frozen in preregistration §11 BEFORE the tournament): seeds
340050..340054 × Arms 1+2 (10 matches) PLUS seeds 340050..340051 × Arms
3+4 (4 matches) = 14 instances. Each re-executed after the main run in
a fully fresh `sys.executable` interpreter via independently
reconstructed invocation commands (`run_one_subprocess`), with no
access to the tournament result cache. Compared on (cand_reward,
base_reward, action_digest, money_digest, state_digest).

| Instance | Verdict | Fresh PID |
| :--- | :--- | ---: |
| A1:340050 | EXACT | 14800 |
| A2:340050 | EXACT | 14812 |
| A1:340051 | EXACT | 14824 |
| A2:340051 | EXACT | 14838 |
| A1:340052 | EXACT | 14852 |
| A2:340052 | EXACT | 14864 |
| A1:340053 | EXACT | 14876 |
| A2:340053 | EXACT | 14888 |
| A1:340054 | EXACT | 14902 |
| A2:340054 | EXACT | 14914 |
| A3:340050 | EXACT | 14928 |
| A4:340050 | EXACT | 14940 |
| A3:340051 | EXACT | 14954 |
| A4:340051 | EXACT | 14966 |

**14/14 exact.** All 14 ran in distinct fresh processes (distinct PIDs).
Preregistration §11(c) satisfied; no OUTCOME-C integrity failure.
Tournament reproduceability is independently confirmed on both the
primary arms and the self-play arms.
