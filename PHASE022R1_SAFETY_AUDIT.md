# PHASE022R1 — SAFETY AUDIT (repair of the V22 safety instrumentation)

**Date**: 2026-09-20
**Status**: instrumented honestly; commit-gate policy unchanged (frozen).
No safety-policy semantics were altered: the same candidates commit or abstain
as in V22. What changed is measurement only (counter repair in
`scripts/run_phase022_consolidation.py`, which is not packaged).

## 1. The two predicates (identified)

| # | Predicate | Where referenced | Actually evaluated? |
| --- | --- | --- | --- |
| 1 | `purchase_ok` → certificate `purchase_check` | `executor.py:722` (`.get("purchase_ok", True)`); `certificate.py:27` (default True) | **NO — key absent from `SafetyChecker.verify()`; always the default `True`** |
| 2 | `market_collision_ok` → certificate `market_collision_check` | `checks.py:36` (init True); `executor.py:725` | **NO — initialized `True`, never assigned `False` anywhere in `verify()`** |

Both are always-true placeholders. They were not genuinely evaluated during
V22, and no V22R1 claim states that they were.

## 2. Are they required / dead / enforced elsewhere?

- Predicate 1 (purchase affordability): **enforced elsewhere**. An
  unaffordable purchase produces `candidate_final_money < 0` and is rejected
  by `solvency_ok` + `cash_liquidity_ok` (`checks.py:118-122`), proven by
  `test_predicate1_purchase_ok_unevaluated_but_affordability_enforced`. The
  named key itself is dead. (Corroborating reporting error:
  `PHASE022_AEC_DECISION_TRACE.md` Case 1 lists "`purchase_ok`: True" among
  `SafetyChecker` results — a value `verify()` never produces; it can only be
  the certificate's default. Corrected in the §22 rewrite.)
- Predicate 2 (market collision): **not enforced anywhere, but unreachable
  for novel collisions under the qualified config**. The
  `DEPENDENCY_AWARE_MARKET_TIMING` transform (`aec/market/transformations.py:13-70`)
  partitions V3's own basket into A/B/C and concatenates (truncated to 10): a
  sub-multiset / pure reorder, so the generator cannot introduce a duplicate
  that was not already in V3's native basket. A synthetic duplicate-order patch
  passes `verify()` with `market_collision_ok=True`
  (`test_predicate2_market_collision_ok_unevaluated_placeholder`) — fail-open
  for that input class at the predicate level, unreachable through the
  qualified mechanism. Implementing a new rejection here would change commit
  behavior and is prohibited by the freeze; the honest correction is
  documentation, applied here.

The real commit gate (`executor.py:603-619`) is
`candidate_otherwise_attractive = passed_safety and eval_res.is_superior`,
where `passed_safety` comes from ~20 genuinely evaluated predicates
(legality, feasibility, overflow, solvency, obligation, terminal, spatial,
fidelity, feed-security, inventory, conservation, capacity, liquidity,
conversion, temporal, reservation, terminal-resource/purpose, coordination).
The `SafetyCertificate` is telemetry: its `commit_decision` (`executor.py:729`)
does not consult the two placeholder fields.

## 3. Counter repair (instrumentation, not policy)

V22 counted candidates whose rejection reason contained `"SAFETY_FAIL"`
(`run_phase022_consolidation.py`, old line 178). No rejection string produced
by `SafetyChecker` or the executor contains that substring (the only writer is
the unused diagnostic `aec/audit/attribution_engine.py:330`), so the V22
"safety_violations = 0" was structurally zero and could not have detected a
fail-open even if one occurred.

Repaired semantics (`count_safety_outcomes`, same script):

- `safety_rejections` = candidates with `safety_pass is False`
  (fail-closed rejections — the system working as designed);
- `safety_violations` = candidates with `safety_pass is False` AND
  `commit_decision` (unsafe patches reaching COMMIT — true failures).

Verified by `test_repaired_counter_measures_observable_safety_outcomes`
(synthetic telemetry: 2 rejections, 1 violation; legacy logic yields 0).
The script change is dev-only (not packaged); economics untouched.

Honest restatement of the V22 safety record: across the 40 fresh-cohort
matches there were 0 illegal actions, 0 solvency breaches, 0 disqualifications
and 0 runtime crashes (directly observed game outcomes), and every committed
candidate in the 34 exported traces has `safety_pass=True`. The old
"`safety_violations = 0`" figure is retired as vacuous-by-construction; the
repaired counters will measure real events on future runs.

## 4. Adversarial coverage (added tests)

`tests/aec/test_phase022r1_safety_predicates.py` (7 tests, all passing):

- unsafe candidates (overflow, negative cash, illegal op, oversized basket,
  failed fidelity) rejected by the real predicates, each with its reason;
- predicate 1: placeholder status asserted + affordability-via-solvency proven;
- predicate 2: placeholder status asserted + reorder-multiset property proven;
- safe candidate passes every check;
- backbone failure → all-PASS `_SAFE` with `FAIL_SAFE` (fail-closed);
- AEC mid-pipeline exception → baseline action with `ABSTAIN_EXCEPTION`.

## 5. Residual disclosures (unchanged from audit, still true)

- LIQUIDATION/SHUTDOWN live paths never fired in validation (pure-function
  tests only); their live protective value is unproven.
- The macro stress test (`test_phase022_adversarial_stress.py:169`) constructs
  no livestock/feed deficit and asserts a tautology (decision in all three
  outcomes); its report description is corrected, not its code.
- The in-flight continuation path skips re-verification (unreachable under the
  qualified config; latent otherwise).
