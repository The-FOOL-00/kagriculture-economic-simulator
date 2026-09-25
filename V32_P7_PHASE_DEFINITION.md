# V32 P7 — PHASE DEFINITION (H2, STATE-DERIVED ONLY)

## 1. STATUS: DEFINITION COMPLETE, CONDITIONING GATED

This document defines the macro-phase variable for H2. Phase CONDITIONING
(a phase embedding added to the policy) is gated behind the H1 prefix result
(prereg §8): it is trained only after Prefix-only behavior is measured, and
only if prefix supervision shows partial benefit that phase context could
extend. Definition and validation of the detector itself are complete.

## 2. DETECTOR (`v32/p7/phase.py::detect_phase`)

Deterministic function of CURRENT OBSERVABLE STATE ONLY:

```text
0 OPENING_CAPITAL:        no hired hands
1 WORKFORCE_SETUP:        hands hired, but zero secured livestock
2 LIVESTOCK_SETUP:        livestock secured (shed + carried + stocked-on-tiles),
                          but no pasture/coop structures yet
3 PRODUCTION_SETUP:       structures exist, but no stocked animals on tiles yet
4 ECONOMIC_CONTINUATION:  stocked animals present
```

Inputs used (all physical/economic `ess` fields): `hands`, `shed`, `inv`,
`thist[5]` (pastures), `thist[7]` (coops), `thist[8]` (stocked animals).
Inputs NEVER used: step index, day/hour clock, teacher tape/route, seed ID,
future knowledge, expert state. Same `ess` → same phase, always
(`tests/test_v32_p7.py::test_07/08` enforce this structurally via AST: the
module contains no `step`/`teacher`/`seed`/`future` references).

The stocked-on-tiles term (`thist[8]`) in the livestock count is load-bearing:
without it the detector regresses to WORKFORCE_SETUP mid-production once shed
and carried inventories empty into placed pastures (found during validation on
the recorded teacher trace, fixed before dataset construction).

## 3. VALIDATION ON RECORDED TEACHER TRACES (240/240 SEATS)

Phase trajectory over steps 0–24 is single-variant (60/60) within every teacher
and identical across all four teachers:

```text
Step 0–1:  OPENING_CAPITAL        (no hands; wash + hire setup)
Step 2–3:  LIVESTOCK_SETUP        (5 hands + shed livestock; farmer SOUTH + PICKUP)
Step 4:    PRODUCTION_SETUP       (hand-built pastures exist; farmer PICKUP WHEAT)
Step 5–24: ECONOMIC_CONTINUATION  (stocked pastures; farmer builds/places/tends)
```

WORKFORCE_SETUP (hands but no animals) is SKIPPED on the teacher trace because
hiring and livestock purchase co-execute at step 1 — but it is exactly the phase
of the P6 failure state (5 hired hands idling, no livestock secured, capital
drained by wages). The detector therefore DISCRIMINATES the failure mode from
the nominal macro using only observable state, which is the precondition H2
requires.

## 4. CONDITIONING ARCHITECTURE (IF GATED IN)

```text
structured temporal features (157-dim, frozen)
        +
state-derived phase embedding (small: 5-way embedding, dim ≤ 8)
        ↓
shared MLP (3×256, P6 warm-start)
        ↓
native action heads (unchanged)
```

The phase embedding is the ONLY architecture delta; trunk/heads/codec/mask stay
frozen in shape. Training: same prefix objective as the best Prefix arm +
phase input; ablation A (P6 baseline) vs B (prefix only) vs C (prefix + phase)
on first divergence, prefix-exact-match, state divergence, terminal economics.

## 5. REJECTION CRITERIA

H2 is rejected without training if: (a) prefix supervision fully solves the
macro (no headroom for phase context); (b) prefix supervision fails so
completely that no phase signal could plausibly bridge the gap AND the failure
is representational (P7-D); or (c) the phase detector cannot discriminate
policy failure states from nominal states in closed loop (checked on Arm 0/Arm 1
traces before any conditioning run).
