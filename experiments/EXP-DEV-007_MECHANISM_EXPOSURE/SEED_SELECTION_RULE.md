# SEED SELECTION RULE: EXP-DEV-007_MECHANISM_EXPOSURE

**Experiment**: `EXP-DEV-007_MECHANISM_EXPOSURE`
**Date**: 2026-09-15
**Status**: PRE-REGISTRATION FREEZE (rule fixed before any execution)
**Cohort size**: N = 500 (fixed by `POWER_PLANNING.md`)

---

## 1. The rule (deterministic, outcome-independent)

The cohort is the contiguous block **[B, B+499]** where:

- **B = 310000** (primary), defined as the smallest multiple of 10000 strictly
  above every seed range previously named as an experimental cohort, consumed
  partition, reserved alternative, or quarantine range in any experiment
  document (the maximum such named upper bound is 300049, from the
  `300000–300049` reserved alternative listed in the EXP-DEV-006 provenance
  audit).
- No game outcome, trigger likelihood, shop distribution, YARN history, or any
  other experimental result entered the choice of B. The rule uses only
  round-number anchoring at a high, distant location.

**Selected cohort: seeds 310000–310499 inclusive (N=500).**

## 2. Fallback chain (provenance-triggered only)

If the primary block fails ANY dimension of the provenance audit:

- Fallback 1: B = 410000 → 410000–410499.
- Fallback 2: B = 510000 → 510000–510499.
- Further: B += 100000 until a block passes the FULL audit.

The first block passing the full audit wins. Fallback is triggered **only** by
provenance failure (prior exposure of the block). It must never be triggered by
any experimental outcome, because no outcome may exist before the freeze.

Audit outcome for the primary block: see `SEED_PROVENANCE.md`.
(If the primary passes, no fallback block is audited or touched.)

## 3. Disjointness proof (integer arithmetic, verified at freeze)

Selected block: [310000, 310499].

| Protected range | Reason | Overlap |
|---|---|---|
| 214200–214249 | virgin final holdout | none (95,751 below) |
| 50050–50099 | consumed Qualification | none |
| 50000–50049 | consumed Discovery | none |
| 50100–50149 | benchmark partition | none |
| 50000–50499 | sweep/contaminated region | none |
| 50150–50199 | contaminated | none |
| 60000–60049 | sweep-contaminated | none |
| 245000–245049 | consumed DEV-003 | none |
| 246000–246049 | consumed DEV-004 | none |
| 247000–247049 | consumed DEV-005 | none |
| 248000–248049 | consumed DEV-006 Discovery | none |
| 1000–2683 | stride-reachable executions | none |
| 249000–249049 | named reserved alternative | none |
| 250000–250049 | named reserved alternative | none |
| 255000–255049 | named reserved alternative | none |
| 260000–260049 | named reserved alternative | none |
| 300000–300049 | named reserved alternative | none (9,951 below) |

Minimum distance to any protected range: 9,951 seeds (above 300000–300049);
95,751 seeds above the final holdout.

## 4. Simulator compatibility (static, no execution)

- Config accepts an integer seed; 310000–310499 fits with zero truncation.
- Deterministic RNG `(seed * 1000003) ^ day`: no modulo folding at this
  magnitude; 310499 is 0.014% of the 2^31 Kaggle seed space.
- Verified by static inspection of the port source only. No candidate seed was
  constructed, simulated, or smoke-tested.

## 5. Rule integrity statement

- The rule was written before the provenance audit completed and before any
  execution capability for this cohort exists (no runner has been written).
- The audit searched for prior *exposure*, never for *outcomes*.
- After this freeze, the cohort is immutable: no seed replacement, no resizing,
  no extension (see `PROTOCOL.md` §8).
