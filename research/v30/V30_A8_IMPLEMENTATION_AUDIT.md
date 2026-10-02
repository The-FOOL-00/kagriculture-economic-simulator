# V30 A8 IMPLEMENTATION AUDIT

Verdict: NOTHING TO AUDIT — no A8 code was written (no-build decision,
V30_A8_SPEC.md). This file audits the substitute deliverable and guards
the no-build boundary.

## Negative attestations

- No file matching `*a8*` (case-insensitive) exists outside this doc set:
  verified by construction (only A7-standalone `candidates/v30_a7_standalone/`
  was created; it contains zero A8 logic — it is A7).
- `aec/backbone/v27_ablation_adapters.py`: SHA UNCHANGED (A7 frozen).
- `submission_Vj_kc_v3.tar.gz`: SHA UNCHANGED (V3 frozen).
- `submission_aec_v22r1.tar.gz`: SHA UNCHANGED (V22R1 frozen).
- No V3/A7/V22R1 source file modified in V30 (git status check below).
- No tape copied, no replay transplanted, no post-hoc action mutation
  introduced anywhere. The only new agent code is the A7-standalone
  builder, which embeds V3 VERBATIM + the frozen A7 rewrite rule.

## A7-standalone construction audit

- Generator: scripts/v30_build_a7_standalone.py (asserts V3 + A7 SHAs
  before building; fails closed on drift).
- Output: candidates/v30_a7_standalone/main.py (373,891 bytes,
  sha256 51c1d2...9ce3f). Contains: V3 bytes verbatim + 11-line
  equivalent of the adapter's step-0 rewrite + safe-schema wrapper.
- Behavioral proof (not inspection): 24/24 tied legs, 8/8 identical
  action digests/money/struct vs the frozen adapter on virgin seeds.

## Boundary for future work

Any future A8 MUST present a new V3x_A8_SPEC naming the observed
mechanism + evidence + planner integration BEFORE code (V30 trigger
criteria: >60% H2H vs A7 over ≥16 mirrored legs, or >5% absolute
excess, same seeds, opponent-strength controlled).
