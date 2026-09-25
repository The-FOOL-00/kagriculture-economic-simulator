# V30 A8 SPEC — NO-BUILD DECISION

Status: PREREGISTERED NO-BUILD. This spec exists to satisfy §17's
"spec before implementing" gate in the negative: NO A8 SHALL BE CODED
in V30 because no §12 missing capability was observed.

## 1. Missing capability: NONE FOUND

256-0 head-to-head legs (V3 176-0 + A7 80-0) over 11 meta families;
V3/A7 self-play (101.6k) exceeds every meta self-play (54.7-95.5k);
same-seed live control matches/exceeds all live bests. See
V30_FRONTIER_GAP_ANALYSIS.md.

## 2. Replay evidence: INVERSION, not gap

Live absolutes are opponent-strength artifacts (180k vs collapsed 43k
opponent). Strongest live opponents (xxxxyt 145k, ORiginators 126k,
tetsuya ≤138k) fall at or below V3's same-seed capability.

## 3. Economic rationale for no-build

Any A8 mechanism now would be invented, not observed. Invented mechanisms
cannot pass §16 (A8vA8 > V3vV3 by construction) without unmotivated
tuning, which §3 bans. Expected value of building < expected value of
qualifying A7 for the experimental slot + preserving deadline slack.

## 4-7. Policy rule / state / thresholds / A7 interaction: N/A (no build)

## 8. Planner changes: NONE. A7 frozen bytes untouched. V3 tarball untouched.

## 9-10. Expected mechanism/benefit: N/A (no build)

## 11. Risks of building anyway (why we stop)

- Deadline burn on zero-signal tuning (§26, §41.9).
- Breaking A7's validated 80-0 V29 edge with unmotivated edits.
- Contaminating confirmation seeds with exploratory A8 variants.
- Inventing "frontier-positive" claims from proxy metrics (§3).

## 12. Falsification criteria (what reopens A8)

A future cycle may reopen A8 iff it presents a runnable/live agent with,
on same seeds, opponent-strength controlled:
(a) reproducible >60% head-to-head vs A7 over ≥16 mirrored legs, or
(b) >5% absolute self-play excess over A7 with a coherent mechanism.
The new spec must name the mechanism, the evidence, and the planner
integration point before any code.

## Substitute deliverable (Outcome C)

A7-standalone packaging + equivalence + loader validation + V22R1
calibration + submission recommendation. See V30_PACKAGING_AUDIT.md,
V30_FINAL_REPORT.md.
