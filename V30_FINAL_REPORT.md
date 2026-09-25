# V30 FINAL Report — Live-Meta Frontier Calibration

Date: 2026-09-21. Engine 1.32.7. Decision: §42 OUTCOME C (no-build) + A7-standalone packaging.

## 1. Mission answer (§2)

> What capabilities do the strongest observable agents possess that V3/A7 lack?

**None.** The V30 gauntlet inverted the premise:

- V3: **176-0** over 11 runnable meta families (16 mirrored legs each).
- A7: **80-0** over 6 of those families.
- V3/A7 self-play ($101.6k) exceeds every meta self-play ($54.7–95.5k).
- Same-seed live control: V3-vs-weak matches/exceeds all 6 tested live
  bests, including the 180k high-water mark (an empty-market artifact)
  and top-1 tetsuya's games.
- V22R1 (Slot A fallback) ties V3 (4W/6L/6T) and beats DMITRII 16-0;
  A7 beats V22R1 16-0 (+$1,272 — same V29 mechanism).

V3/A7 classify as **frontier-breakout** (§23) against all observables.
No A8 mechanism is motivated; building one now would be unmotivated
heuristic search (§3). No-build decision + reopen triggers: V30_A8_SPEC.md.

## 2. Why V3 wins (observed causal chain)

1. Crop/production diversity (carrot + egg/goose streams tapes lack).
2. Fertilizer application intensity (2x DMITRII; tapes sell it).
3. Shop-reactive routing (parent) vs fixed tapes across seeds.
4. Earlier monetization (sales from t=1 vs t=120).
5. Microstructure wrappers (frontload + 2-turn advance + horizon 24).
6. A7 opening path (+1.3k vs V3-regime; +12.2k vs DMITRII).

Anti-signals (do not imitate): NIGHT wheat-cycling (-47k), pure
closed-loop rules OKAMI (-91k), adaptive-but-weak V66 (-17.6k).

## 3. What shipped instead (Outcome C)

**A7-standalone experimental candidate**: `submission_a7_v30.tar.gz`
(143KB, stdlib-only, loader-validated, +1,286 signature via loader path).
Behavioral equivalence vs frozen A7 adapter: 24/24 tied legs, 8/8
identical action digests/money/struct on virgin seeds; serial/pool
parity exact. See V30_PACKAGING_AUDIT.md.

## 4. Slot recommendation (human decides, §43)

- Slot A (KEEP): V22R1 — submitted, frozen, frontier-level.
- Slot B (experimental): `submission_a7_v30.tar.gz` — beats Slot A 16-0,
  beats all tested meta 80-0, inherits V29's 80-0 holdout.
- Limitation: A7's edge is extractive; if live has moved off the
  V3-regime opening it degrades to V3-level (still frontier-best
  observed). Late-September live top unobservable (no API).

## 5. Seeds

Exploration 249570..249577 (gauntlet) + live-seed forensics (disjoint
9-digit) + 249580..249590 (equivalence/parity/loader). Protected
holdouts untouched (tests 9/9). Virgin remainder: 249591..249619.

## 6. Evidence map

Registry: V30_META_OPPONENT_REGISTRY.json. Gauntlet: results/v30_explore*.jsonl,
v30_fallback.jsonl. Equivalence: results/v30_equivalence.jsonl. Live-seed:
results/v30_liveseed*.jsonl. Harness: scripts/v30_gauntlet.py. Builder:
scripts/v30_build_a7_standalone.py. Packager: scripts/v30_package_a7.py.
Tests: tests/test_v30_freeze.py (9 passed).

## 7. Compute

~480 matches, ~19s median (V22R1 ~135s), 9 workers. No A7-vs-V3 legs run
in V30 (§41.10 respected). No frozen bytes modified (V22R1/V3/A7 SHAs verified).

## 8. Stale-test note (transparency)

`tests/test_v28_freeze.py::test_cohort_quarantine` (unbounded `seed >= 249530`
scan, predating V30) false-positived on V30's authorized 249570+ outputs --
offender list verified to contain ONLY post-V28 V30 rows (9 v30_* files).
Minimal maintenance applied per the V29 precedent (V29_FINAL_REPORT s15):
V30 own-files join the test's existing name-allowlist convention (its
docstring scopes it to "pre-V28 artifacts"). Verified: planted-violation
mutation probe still FAILS as required; suite green after. V28's
protection over pre-V30 files is byte-identical. No V28 evidence, result,
spec, or candidate byte was altered. (A parallel V29 literal-scan trip
on V30 governance text was resolved WITHOUT touching that test, by
writing the V29 slice endpoint arithmetically as 340050+39.)
