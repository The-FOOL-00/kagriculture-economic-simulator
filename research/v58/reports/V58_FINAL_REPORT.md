# V58 — Elite Meta Reconstruction + Safe Macro Strategy Selector: Final Report

Decision: **V58_RETAIN_V49** · Classification: **NEGATIVE** (on the breakthrough
question) with INTERESTING historical findings · V49 retained: **true**

## 1. Executive Summary

V58 asked whether the 3100+ population hides strategic structures above V49
that a safe macro selector could exploit. Answer: **no**. The August 3100+
population (518 seats ≥2945, max 3138.9) plays two carrot-0 macro routes that
the September carrot/wash meta — which V49 already leads — has superseded.
All 10 executable elite plans lose to V49 (0/400 tournament legs, 20 ties);
the sole boundary plan (thomastschinkel_2945) never beats V49 strategically
(0/60 pair sums positive; 2 nominal wins = seat artifacts). No static elite,
no selector, no executor change. The smallest adaptive decision-making
required to move beyond V49 is: none exists in the observed elite population.

## 2. Public Replay Data Audit

No 3100+ full-replay archive exists locally; public Kaggle sources are
unreachable from this environment. Local corpora audited: georgymamarin
(74,699 eps, the elite-bearing source), keep/ (193), live_tournament (48),
online_replays A/B/C1/C2 (48), root replays (27) — all sub-2800 opponents.
Full audit: [dataset_audit.md](../data/dataset_audit.md).

## 3. Elite Population Definition

Elite = S1+S2+S3 seats ≥2945 (518 seats / 176 teams / 227 subs, Aug 05-15,
engines 1.32.4-6). Bands: 3100+ (5), 3050-3100 (18), 3000-3050 (114),
2945-3000 (381). Control 2500-2800 (14,233). Executable cross-check: 11 agents
(3009→2800 + claimed-3090/3000 tapes + V44/V49).

## 4. Strategy Family Discovery

64 h100 / 113 h200 exact route families; F1 holds 50% of elite seats incl. 4/5
of 3100+. Two macro crop routes only: (24/42/108@land7) vs (19/37/143@land6).
NN coherence 70.5%. Local capture hashes match S3: night_harvest=F2,
P3000=F4, P3090=F5 — validating cross-source comparability.
See [ELITE_STRATEGY_CLUSTERS.md](../analysis/ELITE_STRATEGY_CLUSTERS.md).

## 5. V49 vs Elite Comparison

V49 (M12/S33/W163/C49, 12C/5S, land d6, wash engine) matches NO August family —
it is a September-route agent. Closest relative t2945 (same census, 6C/6S).
See [V49_VS_ELITE.md](../analysis/V49_VS_ELITE.md) and the difference matrix in
[V49_VS_ELITE.json](../analysis/V49_VS_ELITE.json).

## 6. Macro Lever Discovery

Only live lever: end-herd mix within the Sept wash route (12C/5S vs 6C/6S).
All August levers superseded; kaito-3009 regime tape unproven (0/40, -26k).
See [MISSING_LEVERS.md](../analysis/MISSING_LEVERS.md).

## 7. Fixed Elite Plan Tournament

0/400 elite wins (Stage B, seeds 10100-10119, engine 1.32.7).
t2945 0/20/20 at -79 mean — the boundary. See
[V58_FINAL_LADDER.md](V58_FINAL_LADDER.md) and
[PLAN_TOURNAMENT.json](../counterfactuals/PLAN_TOURNAMENT.json).

## 8. Plan Transplant Results

NO_QUALIFYING_TRANSPLANT. t2945's 2/120 scan wins decompose exactly into
seat premium + strategy deficit ≤ 0 (self-play controls identical under both
agents). See [PLAN_TRANSPLANT.json](../counterfactuals/PLAN_TRANSPLANT.json).

## 9. Meta Drift

The carrot revolution (melon 24→12, carrot 3.5k→21k seats) happened Aug-W3/W4,
AFTER the elite window. V49 is post-revolution; the August 3100s are
pre-revolution. The premise inverts: V49 is newer than the elite data.
See [META_DRIFT.md](../analysis/META_DRIFT.md).

## 10. Selector Construction

Not built — hierarchy step 1 failed (no fixed winner), so steps 4-5 are
unreachable. Design pre-registered (day-0 lock, turn-100 boundary, V49
fallback) in case future data qualifies plans.

## 11. Leakage Audit

Closed NOT-APPLICABLE: zero adaptive components, zero trained parameters,
fresh split untouched. See
[SELECTOR_LEAKAGE_AUDIT.md](../analysis/SELECTOR_LEAKAGE_AUDIT.md).

## 12. Fresh Benchmark

Not run: no candidate survived (running fresh legs without a candidate is
theater). Tournament + scan + V56 ladder constitute 400 + 120 + 576 legs of
evidence against promotion.

## 13. Per-Opponent Results

[per_opponent_results.json](../benchmarks/per_opponent_results.json). Worst
deficits: v44 (-163k, off-regime no-op), saiteja (-90k), night_harvest (-45k).
Smallest: t2945 (-79), dmitrii (-10k).

## 14. Per-Seed Results

Tournament: 20/20 seeds swept by V49 (all matchups). Scan: 58/60 seeds swept;
10134/10153 split by seat premium (pair sums -240, 0 — both ≤ 0 for t2945).

## 15. Per-Seat Results

Capture + tournament legs are seat-mirrored (deterministic tapes, identical
scores both seats) except the two seat-premium scan seeds, where the premium
(±~1000, flat from step 600) decides the nominal winner under BOTH agents.

## 16. Rescue/Casualty Analysis

Rescues 0, casualties 0 — no candidate exists to rescue or casualty. V49's own
tournament record: 380W/20T/0L (100% unbeaten).

## 17. Why the Candidate Works / Fails

There is no candidate because the elite population offers no alpha: August
routes are stale (no carrot/wash, lower throughput), September routes are
V49's family with weaker calibration or execution leaks (2-quad end, herd
liquidation, off-regime no-op). Failure class (§39): **A — elite routes are
not actually superior to V49**, with a V56-analogous seat/queue artifact
footnote for the 2 nominal t2945 wins.

## 18. 3000+ Path Assessment

Does the elite population contain families V49 does not represent? **Yes**
(August F1-F6) — but they are weaker, not higher. Does one causally beat V49?
**No** (0/400). Family-general macro beat V49? **No**. Adaptive selection beat
best fixed? **No** (nothing to select). Survive fresh seeds / unseen opponents?
**Moot**. Credible 3000+ path from this population? **No — EVIDENCE_SUPPORTS
stale-meta conclusion, not a 3000+ path.**

## 19. Promotion Decision

**V58_RETAIN_V49.** Gates: A fail (no improvement), B vacuous, C fail, D
pass (mechanism understood: V49 leads the post-revolution meta), E/G fail.
Default retained.

## 20. Reproducibility / Governance

- V49 frozen: true (SHA re-verified; file untouched).
- Protected holdouts accessed: 0 (asserted in all runners).
- Kaggle submissions: 0. Future info / seed-as-feature / opp-private-state: false.
- Engine: kaggle-environments 1.32.7; parity: capture hashes match S3
  normalization on 3/3 fossil lines (F2/F4/F5).
- Reproduce: build_db.py → cluster_families.py → capture_trajectories.py →
  compare_v49_elite.py → run_plan_tournament.py → t2945_regime_scan.py.
