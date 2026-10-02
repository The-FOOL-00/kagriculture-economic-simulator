# V22R1 — RELEASE FINAL

**Note**: this file and `V22R1_RELEASE_MANIFEST.json` were created after
tagging per the release order (exactly one release commit); they pin the
release commit by hash and remain worktree files.

## Release Status

`FINAL SUBMISSION FROZEN`

## Submission Archive

`submission_aec_v22r1.tar.gz`
SHA256: `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5`
(549,911 bytes, 130 members; hash stable across smoke, commit, and tag.)

Retired: `submission_aec_v22.tar.gz`
(`2b23bc228366e7df5fbe4ecdd38bd3c26d3fd1c0da58e5b97f745c979075df23`,
unchanged, kept for audit history, never submitted.)

## Git

- Commit: `33763a8f58b17bc3a32735c2a322883b78ed3778`
  (`release: v22r1 final competition submission`; 48 files, +5202/-0)
- Tag: `v22r1` (annotated; dereferences to the release commit)
- No push performed; release is local-only unless a human requests
  publication.

## V3

Frozen SHA256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`
(worktree tarball, packaged payload, and config constant all verified.)

## Active Foundation

Exactly: `V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION +
PHASE_SHUTDOWN` (verified programmatically in worktree and packaged
configs; `frozen_mode=True`; tranche/multiworker/funnel/boundary-safe/
uncertainty mechanisms all disabled).

## Loader Verification

PASS across competition-style loader (`exec`, no `__file__`, KE 1.32.7):
source loads, agent initializes, real AEC actions execute (719 decisions,
commits > 0, foundation mechanisms only), no all-PASS degradation, full
720-step game DONE/DONE, V3-scale output, deterministic repeats.
(`PHASE022R1_FINAL_LOADER_SMOKE.md`; 3/3 loader regression tests green.)

## Semantic Equivalence

40/40 EXACT — 0 differences across 28,800 step records × 10 fields
(dev vs repaired package; control 4/4 identical).
(`PHASE022R1_SEMANTIC_EQUIVALENCE.md`.)

## Safety

Corrected safety instrumentation present; adversarial safety regression
passes (7/7); every commit gated by ~20 evaluated predicates; the two
certificate-only placeholders documented as unevaluated with the
freeze-mandated document-don't-claim disposition.
(`PHASE022R1_SAFETY_AUDIT.md`.)

## Determinism

Per-turn determinism verified: every action, V3 base action, decision,
commit/abstain, mechanism, and terminal reward identical across all
repeated executions (processes, loader modes, load conditions; packaged
repeats bit-identical). No "720/720" phrasing: 719 decisions per
720-step game. (`PHASE022R1_DETERMINISM_AUDIT.md`.)

## Performance

Median/tail wording only: median decision latency approximately 51 ms;
tail materially higher; config's own 100 ms limit breached
(`within_limit=false`); no blanket sub-100 ms claim.
(`PHASE022R1_PERFORMANCE_AUDIT.md`.)

## Scientific Scope

All evidence is cohort-scoped and does not establish global optimality:
on the fresh 40-match development cohort the foundation produced a mean
paired terminal-margin delta of approximately +$33.35 vs pure V3 with
substantial uncertainty (CI [-$335.08, +$401.78], d = 0.03); no
preregistration exists; no universal or optimal effect is claimed.

## Holdout Status

- `340050..340199`: UNTOUCHED (retained)
- `214200..214249`: UNTOUCHED (retained)
- `340300..340349`: CONSUMED / RETIRED (EXP-AEC-004; never reuse;
  never again described as untouched)

## Known Residual Uncertainties

- Live LIQ/SHUT mechanisms did not fire during the headline cohort
  (protective value unproven).
- V22 per-arm ledgers / per-step telemetry were not fully exported where
  applicable (aggregates trusted via reviewed code).
- kagsim-bound tests are environment constrained on Linux (5 modules
  uncollectable; runnable suite 759/759 green).

## Freeze Decision

`NO FURTHER RESEARCH CHANGES AUTHORIZED WITHOUT EXPLICIT HUMAN APPROVAL`
