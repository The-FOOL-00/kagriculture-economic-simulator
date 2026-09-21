# V27 — ABLATION PLAN (single-factor, planner-level, coherent)

## 1. Scope reduction (evidence-driven)

The V27 brief (§15) assumes six P3 mechanisms. Source forensics shows
the 125-line `candidates/v25_p3_unified.py` contains exactly TWO
behavioral deltas vs V3: (1) step-0 bypass with a 30/30 wash (V3: call
through with 50/50 + frontload), (2) PASS→WATER/DIG dispatch. There is
no livestock, sales, or "macro coupling" code in P3 (pasture/crop/sell-
structure gaps all 0; ledger §4). Ablating non-existent code is
impossible; the brief's A4/A5/A6 are therefore RESOLVED, not run:

| Brief ID | Specified target | Disposition |
| :--- | :--- | :--- |
| A1 | opening capital → V3 | RUN (variant calls V3 at step 0; keeps dispatch) |
| A2 | wheat-wash 30 → V3 qty | RUN (variant bypasses with 50/50; keeps dispatch) |
| A3 | labor dispatch → V3 | RUN (variant keeps 30/30 bypass; no dispatch) |
| A4 | livestock coupling | NOT APPLICABLE — no such P3 code (evidence: ledger §4) |
| A5 | macro coupling | NOT APPLICABLE as distinct — A1+A3 jointly remove all P3 deltas (= V3 sanity control) |
| A6 | sales/velocity | NOT APPLICABLE — no P3 sales code (all selling is V3-reactive) |

A1−A2 isolates the bypass-vs-call effect from the quantity effect;
A2−P3 isolates quantity; A3−P3 isolates dispatch. A1+A3 must
reproduce V3 exactly (harness-validating sanity control).

## 2. Coherence (§16)

Variants subclass `V25P3BackboneAdapter` (`aec/backbone/
v27_ablation_adapters.py`; P3 source and V26 adapters untouched):
step-0 branch flag (`call_v3_at_step0`, `open_units`) + dispatch flag.
No tape mutation, no action splicing, no planner-state inconsistency:
A3 emits V3's own actions unmodified; A1 feeds V3 its natural step-0
input. Continuation policies mirror the flags.

## 3. Design (exploratory mechanism work; non-gating)

- Seeds: consumed 60 (A/B/C ranges) × seats {0,1} = 120 matches per
  config. Firewall: never 249490+.
- Primary (brief-literal): variant-vs-V3 (common baseline; A1/A2/A3/
  V3-sanity = 480 matches). Variant−P3 read via shared V3 anchor.
- Secondary (tighter pairing): variant-vs-P3 direct, same game
  (A1/A2/A3 = 360 matches). NOTE: market regime differs from primary
  (30/30-symmetric vs 30/50); both reported, primary governs.
- Hermetic adapters throughout; engine 1.32.7; MAX_WORKERS=9.
- Compact capture per match (money/hands/pasture/plant/quad series +
  finals + digests + market-order counts; ~30KB/match) for emergence/
  divergence approximation. Rewards + digests exact.

## 4. Sanity gate (must pass before interpreting A1–A3)

V3-sanity (A1+A3) vs V3 must reproduce `results/v27_farm_gaps.jsonl`
60/60 EXACTLY (rewards; same program, same seeds, hermetic). On
failure: STOP, diagnose loader (STOP condition 6/7 analogue). On
success: the variant harness is validated and A1–A3 reads are causal
for their flags.

## 5. Readout per ablation (vs frozen V25, paired by seed/seat)

Mean/median paired Δ vs V3 AND vs P3-direct; W/L/T; win rate; tail
floor; money-gap emergence shift; first-divergence shift (money
series); final composition; 249463-tip dependence (does the tip
survive each ablation? — the single most informative cell); 249450
invariance (farm event should not move). Full table, no cherry-pick
(§29). All ablation claims labeled EXPLORATORY (consumed seeds).
