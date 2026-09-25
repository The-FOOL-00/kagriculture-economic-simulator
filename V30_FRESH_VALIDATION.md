# V30 FRESH VALIDATION

No A8 confirmatory tournament was required (no-build). Fresh-seed
validation was spent on the shipped deliverable instead: A7-standalone
equivalence + packaging integrity on previously unused seeds.

## Fresh cohorts consumed (first use in V30)

| Seeds | Use | Result |
|---|---|---|
| 249580..249587 | AST↔A7-adapter equivalence (24 legs) + AST self-play | 24/24 dollar-tied; 8/8 digest/money/struct identical |
| 249588..249589 | serial/pool parity (AST:A7) | 2/2 exact (rewards + digests) |
| 249590 | competition-loader validation (fresh-dir import + full match) | AST 129,182 vs V3 127,896 (+1,286 signature) |

## Virginity status

- 249580..249590: consumed by V30 (recorded here; retired).
- 249591..249619: REMAINS VIRGIN (no seed-field executions; V30 never
  touched it). Available for any future confirmatory cycle.
- Protected holdouts untouched: 340090..340199, 214200..214249
  (hard-refused by harness; quarantine test passes).
- Live seeds (9-10 digit): exploratory forensics only, disjoint from all
  dev ranges by construction.

## Promotion criteria (§35) applied to A7-standalone

1. No integrity issue: PASS (frozen inputs verified, tests 9/9).
2. Deterministic: PASS (cross-process digest identity).
3. Serial/parallel parity: PASS (exact).
4. Meta gauntlet not a disaster: PASS (80-0 as A7; AST≡A7 proven).
5. Fresh seeds replicate: PASS (equivalence on 8 virgin seeds).
6. No catastrophic tail: PASS (A7 inherits V29 tail audit; AST identical).
7. Explainable mechanism: PASS (30-unit opening wash, V27/V28/V29).
8. Fits packaging constraints: PASS (143KB, stdlib-only, loader-validated).
