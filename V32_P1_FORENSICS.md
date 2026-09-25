# V32 P1 FORENSICS — expert-population routing analysis (2026-09-22)

Pure offline analysis of `results/v32_exp1.jsonl` (448 legs, 432 core).
No matches run. Machine-readable companion: `V32_P1_FORENSICS.json`.
Generator: `scripts/v32_p1_forensics.py` (deterministic, no matches).

Framing: each leg L-vs-R on seed s yields two directed rows,
`(seed s, opponent R) -> cash of L`, over router classes
{V3, A7, V25P3, W72, W2015}. n = 48 rows (6 seeds x 8 opponents;
opponent=A7 rows lack A7 data — EXP-1 has no self-play).

## 0. Competition-state integrity check (phase entry gate)

| Check | Result |
| :--- | :--- |
| Slot A `submission_aec_v22r1.tar.gz` SHA256 | `6b879b3e…fb3f5` MATCHES freeze |
| Slot B `submission_a7_v30.tar.gz` SHA256 | `4a076730…016619` MATCHES freeze |
| V3 `submission_Vj_kc_v3.tar.gz` SHA256 | `845e0d10…18943` MATCHES freeze |
| All 31 V32 QUAL_MANIFEST artifact hashes | MATCH (recomputed 2026-09-22) |
| Engine `kaggle_environments` | 1.32.7 MATCHES |
| Protected holdouts 214200-214249, 340090-340199 in EXP-1 records | 0 hits |
| V32-CONFIRM 249695-249734 in EXP-1 records | 0 hits |
| `check_seed_allowed` refuses holdouts/CONFIRM, allows 249643+ research | verified live |
| Fast V32 tests (`test_v32_freeze`, `test_v32_protocol`) | 14/14 pass |
| Competition artifacts modified/rebuilt/resubmitted | NONE |

## 1. V32 artifact inventory (authoritative inputs, frozen)

Manifests/registry: `V32_QUAL_MANIFEST.json`, `V32_BASELINE_FREEZE.md`,
`V32_EXPERT_POPULATION.json` (11 experts E0-E10), `V32_FINAL_REPORT.md`,
`V32_EXP1_EXPERT_BENCHMARK.md`, `V32_EXP2_IMITATION.md`,
`V32_EXP3_RL_FEASIBILITY.md`, `V32_STRATEGY_FINGERPRINTS.json`,
`V32_SAMPLING_PROTOCOL.md`, `V32_PROMOTION_PROTOCOL.md`,
`V32_STATE_ENCODER_SPEC.md` (+v1.1 prices correction), `V32_TRAINING_SPEC.md`,
`V32_COMPUTE_FEASIBILITY.md`, EXP-4-9 protocol stubs. Runners:
`scripts/v32_common.py` (quarantine/digests/loaders),
`scripts/v32_exp1_benchmark.py`, `scripts/v32_capture.py`,
`scripts/v32_encoder.py` (v32enc-v1.1, 90 floats), `scripts/v32_bc_probe.py`,
`scripts/v32_sample.py`, `scripts/v32_gate.py`. Seed ledger: TRAIN
249635-249674 (consumed 249635-249642 + commissioning 249673-249674;
free 249643-249672), DEV 249675-249694 untouched, CONFIRM 249695-249734
frozen untouched. Nothing in this list is modified by P1/R1.

## 2. Expert x opponent MEAN CASH (row expert vs column opponent, $)

```
          V3   V22R1      A7   V25P3      A1      A2     W72   W2015    DMIT
V3       ---   93384  106566  107458   93427   93891   92348  110064  111156
V22R1  93457     ---  106574  107466   93447   93910   92368  110082  111134
A7    107852  107828     ---   93891  107843  108744   92350   93666  112740
V25P3 106864  106839   92636     ---  106858  107950   91529   92848  112580
A1     93444   93391  106573  107467     ---   93901   92356  110071  111156
A2     92636   92583  105578  106664   92628     ---   91527  108694  110703
W72    92377   92326   92373   92841   92367   92845     ---   92375   98725
W2015 110305  110248   93702   94206  110295  111037   92351     ---   98495
DMIT  100101  100104   99389   99394  100101  100199   90202   89952     ---
```

## 3. Expert x opponent W-L-T (row expert vs column opponent, 12 legs each)

```
          V3   V22R1      A7   V25P3      A1      A2     W72   W2015    DMIT
V3       ---   1-10-1   0-12-0   8-4-0   0-4-8  12-0-0  0-12-0  0-12-0  12-0-0
V22R1 10-1-1     ---   0-12-0   8-4-0  10-1-1  12-0-0   8-4-0  0-12-0  12-0-0
A7    12-0-0  12-0-0     ---  12-0-0  12-0-0  12-0-0  0-12-0  0-12-0  12-0-0
V25P3  4-8-0   4-8-0   0-12-0    ---   4-8-0  12-0-0  0-12-0  0-12-0  12-0-0
A1     4-0-8  1-10-1   0-12-0   8-4-0    ---  12-0-0   4-8-0  0-12-0  12-0-0
A2    0-12-0  0-12-0  0-12-0  0-12-0  0-12-0    ---  0-12-0  0-12-0  12-0-0
W72   12-0-0   4-8-0  12-0-0  12-0-0   8-4-0  12-0-0    ---  12-0-0  12-0-0
W2015 12-0-0  12-0-0  12-0-0  12-0-0  12-0-0  12-0-0  0-12-0    ---  12-0-0
DMIT  0-12-0  0-12-0  0-12-0  0-12-0  0-12-0  0-12-0  0-12-0  0-12-0   ---
```

Wash ladder margins (row minus column): W72-W2015 +24, W72-A7 +23,
W2015-A7 +36, W2015-V3 +241, A7-V3 +1286. All reproduce EXP-1 §2.

## 4. OBSERVED FACTS (routing-relevant)

F1. Oracle-cash minus fixed A7 over 48 rows: mean +$10,545, median +$1,638,
max +$50,655, positive on 42/48 rows. A7 is itself the oracle on 6/48 rows.
F2. Fixed-expert regret vs oracle-cash (mean/median): V3 12813/7673,
A7 10546/1638, V25P3 10839/1640, W72 23296/20264, W2015 9828/0. Best fixed
class by cash is W2015 (median regret 0), not A7; A7 is close-or-best on
most rows but catastrophic on a tail (max 50655).
F3. Oracle-cash minus fixed W72: mean +$23,296, median +$20,264. W72 is the
worst fixed choice by cash and joint-best by W/L (0.875, §6) — decoupling.
F4. Oracle-W/L minus A7-W/L: mean +0.125 win-score, positive on 6/48 rows
only (the vs-W2015 rows, where W72 is the unique 12-0 answer). With these
5 classes, W/L routing adds value almost nowhere else.
F5. TARGET A and TARGET B give OPPOSITE answers vs W2015: W72 wins (+$24)
at $92,375 own cash; V3 loses (-$241) at $110,064. Delta: winning costs
~$17.7k of own cash. Cash and W/L routing are different tasks.
F6. Per-(seed, expert) cash spread across opponents: median $21,743, max
$54,017 (A7 on 249639). The pair-economy is near-DISCRETE: on 249639 all
36 directed cash values cluster at ~$74.9k (19x) / ~$103k (9x) / ~$125k
(8x). Same-expert-same-seed swings of $30-50k are level switches.
F7. Per-opponent best-fixed (post-hoc fit) captures 47% of the oracle-A7
gap ($4,947 of $10,545). Rule: vs {V25P3, W2015} play V3; vs DMIT play A7;
else W2015 (vs W72 is flat: all classes within ~$800 — unstable argmax).
About half the oracle gap is opponent-driven, half seed-driven.
F8. Best-by-cash varies by BOTH axes: by opponent (vs V3 -> W2015 4/6; vs
V25P3 -> V3 5/6; vs W2015 -> V3 4/6; vs DMIT -> split) and by seed (249637
-> V25P3 7/8 rows; other seeds -> W2015/V3 mixes). Routing is non-degenerate
on both axes.
F9. CROSS-vs-WITHIN pair-cash gaps (post-hoc G1/G2): +$15.2k, +$1.8k,
+$18.1k, +$62.9k, +$70.9k, +$8.3k — same sign 6/6, descriptive only (n=6).
Pre-registered confirmation on fresh TRAIN seeds (see preregistration).
F10. Step-0 observation is BIT-IDENTICAL across all 6 EXP-1 seeds: 0/90
encoder features differ (empty tiles, zero shed/seeds, identical prices
and farmer). The seed expresses ONLY through in-episode RNG.
F11. Seat symmetry holds for 416/416 non-V22R1 core legs, but FAILS for
16 legs: all V22R1-involved pairs on seed 249640 (8 pairs x 2 seats).
CORRECTION to V32_EXP1 §4/V32_FINAL_REPORT §2.6 ("byte-identical"): true
except V22R1-on-249640. Follow-up 1-leg rerun (V22R1-vs-V3, seed 249640,
same spec) reproduces rewards AND action digest exactly: V22R1 is
deterministic per (seed, seat-assignment) but seat-SENSITIVE on 249640
(a seat-dependent code path fires in that seed's economy), not
nondeterministic. R1 addendum: a second V22R1-asymmetry seed found in
the R1 probe (W2015-vs-V22R1 on 249653: +$108 vs +$683 across mirror;
winners agree). Single-seat labels remain valid for the V22R1-free grid;
V22R1 stays evaluation-only (and out of the main grid).
F12. Adapter audit: all router-class adapters key step-0 logic off
`obs['step']`; internal state is call bookkeeping only. V3-family experts
are tape-plus-reactive-layer policies indexed by step: a FRESH adapter
starting mid-episode is coherent (no crash, tape-indexed) but not
identical to continuous play (1-step reactive memory resets). Continuation
legs are therefore valid labels for a continue-policy; continuation
equivalence vs full-episode play is diagnostic, not assumed.

## 5. INTERPRETATION

The pair, not the expert, sets the economy level (2-3 discrete levels per
seed, F6); within a level, wash-ladder crumbs ($10-1.3k) decide W/L. The
router's economic value is catastrophe avoidance (dodge A7's suppressed
levels, +$30-50k each) plus crumb collection, NOT picking a universally
strong expert. F7 splits the oracle gap about evenly between
opponent-driven (reachable by opponent-conditioned static routing) and
seed-driven (needs early-episode RNG expression). F10 kills state-only
pre-episode routing (see §6). F5 forces separate cash and W/L heads.

## 6. INFORMATION-BOUNDARY CONCLUSION (E)

REGIME A (pre-episode state only): PROVABLY UNINFORMATIVE. Step-0 state is
a constant (F10), so any state-only pre-episode router is a constant
function = best-fixed-expert. Value over fixed: exactly zero. Implemented
as the global best-fixed baseline + a constancy test, not as a model.
REGIME A+ID (state + opponent identity): diagnostic static router. Captures
at most the opponent-driven half of the gap (~47%, F7). Deployable only
where the opponent is known (rematch/ladder); in blind matches identity is
unavailable pre-episode.
REGIME B (fixed V3 opening of N=24 steps, then routed continuation):
the deployable router. Observes opponent wash behavior + early price-path
RNG expression through legal public channels (market prices/inventory,
public farm fields) and selects the continuation expert. Primary bet:
early price-path predicts the pair-economy level (F6).
REGIME C (periodic re-routing): NOT implemented in R1 (deferred per §14
until static/early routing shows benefit).

## 7. IMPLICATIONS FOR ROUTER DESIGN

1. Five router classes {V3, A7, V25P3, W72, W2015}; self-play legs included
to complete the oracle (EXP-1 lacks them). A1/A2 excluded (dispatch lanes:
A1 ~= V3 parity, A2 weak — redundant/dead classes add label noise, not
signal); DMITRII excluded as a class (weak lane) but kept as an opponent;
V22R1 excluded (eval-only cost + F11 asymmetry), small opponent probe only.
2. Soft/admissible-set labels required: vs-W72 rows are flat within ~$800
(F7); hard argmax there invents winners from noise.
3. Separate cash and W/L prediction heads (F5); primary metric economic
regret (TARGET A), W/L regret secondary.
4. Opponent panel {V3, A7, V25P3, W72, W2015, DMITRII}; wash-micro
{W72, W2015} held out as the unseen opponent family in a secondary split.
5. Seeds, not legs, are the sample unit (F11 + EXP-1 §4); splits by seed.
