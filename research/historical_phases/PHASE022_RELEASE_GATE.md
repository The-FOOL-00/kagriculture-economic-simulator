# PHASE022 RELEASE GATE (Independent Adversarial Audit)

**Date**: 2026-09-20
**Candidate**: V3 (`845e0d10...`) + DEPENDENCY_AWARE_MARKET_TIMING +
TERMINAL_LIQUIDATION + PHASE_SHUTDOWN, packaged as `submission_aec_v22.tar.gz`
(`2b23bc22...`).

## Area classifications

| Area | Status | Reason |
| --- | --- | --- |
| V3 immutability | PASS | SHA exact; bundled payload bit-identical; packaged code == working tree; SHA verified on every backbone load |
| Cohort integrity | REQUIRES CORRECTION | Fresh cohort materially pristine (reservation-only pre-use); 340050..199 and 214200..249 clean; but 340300..349 was consumed by EXP-AEC-004 and falsely re-certified "untouched" |
| Statistical validity | REQUIRES CORRECTION | All numbers bit-exact; inference overstates (no prereg, primary-test convention fails, seed-level Wilcoxon p=0.051, d=0.03 spun, CI spans zero) |
| Attribution | PASS WITH CAVEAT | 3-layer ablation enforcement verified; identical arms explained; per-arm ledgers missing; causal headline must be cohort-scoped |
| Counterfactual fidelity | FAIL | MAE=$0.00 is tautological (realized copied from predicted; zero independent simulation); empirical claim must be withdrawn |
| Safety | PASS WITH CAVEAT | Fail-closed structure verified by inspection; suite weak in parts + macro test misreported; safety counter vacuous; LIQ/SHUT live paths unexercised; 2 vacuous cert predicates |
| Determinism | PASS WITH CAVEAT | Aggregate equality verified (10/10 + FULL re-execution); "720/720 steps" trajectory claim unsupported; packaged check void (dead agent) |
| Autonomy | PASS WITH CAVEAT | Honest supervisory-layer demarcation verified in code; "proven/Pareto-optimal/optimal" adjectives overclaim |
| Performance | REQUIRES CORRECTION | Aggregates as computed but `within_limit=false`; "sub-100ms" false as blanket; 9-stage table unsourced; 719 not 720 steps/match; step-0/fast-path figures unverified |
| Package integrity | FAIL | Static package perfect (hash, members, payload, deps, secrets); behavioral execution fails -- entrypoint `NameError: __file__` under the KE loader makes the submission a silent all-PASS agent ($3,000) |
| Reproducibility | REQUIRES CORRECTION | Fresh rows + traces + scripts persist; per-arm ledgers, per-step telemetry/latency, non-commit decisions unexported; release uncommitted (no pinned commit) |
| Documentation | REQUIRES CORRECTION | Extensive superlatives exceed evidence (optimum/ceiling/proven/decisive/robust); P20-vs-V22 timing contradiction unreconciled; registry/prose governance mismatch; historical table unit error |

## Release status

### RELEASE BLOCKED -- ENGINEERING ISSUE

The packaged submission does not execute its own code in the competition
environment (KE `exec` without `__file__` -> `NameError` on every step ->
all actions coerced to PASS -> $3,000.00, certified by vacuous QA assertions).
No release is possible from archive `2b23bc22...`; it must be retired,
repaired, rebuilt, and re-verified end-to-end (including a V3-scale reward
check and packaged determinism) before any further gate can pass.

Secondary (non-blocking once A1/A2 are fixed, but mandatory before release):
withdraw the fidelity validation claim; re-designate the 340300..349 cohort;
correct the statistical framing, performance wording, determinism scope,
safety metrics, and superlatives per `PHASE022_REQUIRED_CORRECTIONS.md`;
commit and tag the release.

## Gate logic note

Two areas carry FAIL. The fidelity FAIL is a *claim* failure (withdrawable by
documentation correction; the underlying simulator design is untouched). The
package FAIL is a *behavioral* failure (the artifact cannot perform its sole
function). Either the engineering repair succeeds (then: documentation
corrections + re-verification + release) or it does not (then: blocked). No
new science (no Phase 023, no mechanisms, no tuning) is proposed or needed:
verify -> correct wording -> correct release engineering -> freeze.
