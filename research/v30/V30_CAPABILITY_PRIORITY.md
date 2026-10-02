# V30 CAPABILITY PRIORITY — DECISION MATRIX

## Candidates scored (§13)

| Capability | Meta prevalence | Est. terminal impact | Impl. difficulty | Break-A7 risk | Testability | H2H benefit | Time to validate |
|---|---|---|---|---|---|---|---|
| Capital recycling | none observed above V3 | 0 (V3 already fastest: sales from t=1) | — | — | — | 0 | — |
| Livestock scaling | tapes run FEWER animals; DMITRII == V3 | 0 | — | — | — | 0 | — |
| Fertilizer economy | V3 already leads 2x; tapes sell it | 0 observed (V3 is the frontier) | medium | medium | medium | unknown | days |
| Land expansion | all 2x land, same timing | 0 | — | — | — | 0 | — |
| Labor throughput | all ~10/day | 0 | — | — | — | 0 | — |
| Route efficiency | V3 parent ≥ all | 0 | — | — | — | 0 | — |
| Adaptive route selection (V66 idea) | 1 instance, loses by 17k | negative in only instance | high | high | low | 0 | weeks |
| Wheat cycling (NIGHT) | 1 instance, weakest (62k) | NEGATIVE (-47k) | low | high | done | negative | — |
| Terminal conversion | all liquidate similarly | 0 | — | — | — | 0 | — |

## Decision: NO A8 BUILD (§42 Outcome C)

Every candidate scores zero-or-negative observed benefit. The decision
matrix is degenerate because the frontier gap is degenerate: V3/A7 are
already above all observables on both head-to-head (256-0) and absolute
levels. Building "A8 = A7 + heuristic" now would violate §3 (no random
heuristic search) and §12 (choose from OBSERVED gap).

## What V30 ships instead

1. **A7-standalone packaging**: A7 exists only as a lab adapter wrapping
   V3 bytes. Make it a submittable `main.py` with dollar-identical
   behavioral equivalence, then qualify it as the experimental-slot
   candidate (Outcome C: "A7 may be the experimental live candidate").
2. **V22R1 fallback calibration**: confirm Slot A strength (in progress).
3. **Submission recommendation** with slot assignment for the human.

## Trigger criteria that WOULD justify a future A8 (post-V30)

Build A8 iff fresh evidence shows a runnable or live agent that, on
same seeds with opponent-strength controlled:
(a) beats A7 head-to-head reproducibly (>60% over ≥16 mirrored legs), OR
(b) exceeds A7's absolute self-play by >5% with a coherent mechanism.
Then A8 = A7 base + the single observed mechanism, per §§14-18.
