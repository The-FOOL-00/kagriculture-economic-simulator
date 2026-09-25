# V32 PROMOTION PROTOCOL (pre-registered 2026-09-22)

No learner exists yet. This gate is frozen BEFORE any promotion test is run.
It governs every `learner vs champion` decision in V32 (EXP-4/EXP-7/EXP-8).

## 1. Evaluation suite (fixed, strong, small)

`V32_CHAMPION_SUITE` = E0_V3, E1_V22R1, E2_A7, E3_V25P3, E6_W72, E7_W2015,
E8_DMITRII + current champion. (E4/E5 dispatch lanes join if EXP-1 shows them
non-degenerate; E10_PASS never joins — it is a sanity anchor, not a gate.)

- Seeds: V32-CONFIRM (249695–249734), mirrored seats (both seats every seed).
- Loader: hermetic adapters / exec-isolated files, `max_tasks_per_child=1`.
- Eval policy mode: deterministic (argmax / temperature 0). Record model hash,
  checkpoint hash, env version, seed list, seat map, action digests.
- One touch: a checkpoint consumes V32-CONFIRM exactly once. Fail = `FAILED`,
  no retuning on the same cohort (holdout covenant applies).

## 2. Promotion gate (ALL must hold)

Let per-seed paired outcome `d_s = learner_cash - champion_cash` on the suite
mean per seed (both seats, all suite opponents averaged), plus per-family
win rates.

1. **Positive mean**: `mean(d) > 0` over V32-CONFIRM seeds.
2. **Positive median**: `median(d) > 0`.
3. **Win rate**: learner wins > 50% of suite legs (ties excluded from the
   denominator; ties reported separately).
4. **Wins > losses** strictly, counting all legs.
5. **No catastrophic tail**: no single leg worse than -$25,000 vs champion on
   the same seed/seat/opponent (a bigger blowout = automatic FAIL — the
   learner must not introduce a new collapse mode).
6. **No single-family collapse**: learner win rate vs EACH suite family ≥ 40%.
7. **Breadth**: strictly positive mean `d` vs at least 3 distinct suite
   families (a one-family exploit is not a promotion).
8. **Determinism**: full-suite rerun reproduces every leg's action digest
   (leaf-node equality, not just W/L).

No universal p-value threshold is imposed: with n=40 seeds × suite, clauses
1–7 jointly control the error; clause 8 controls harness flakiness.

## 3. Champion mechanics

- `champion_policy` starts as E2_A7 (validated live counter-policy; strongest
  deterministic generalist by live evidence).
- The champion stays frozen between promotion tests. Historical champions are
  kept frozen in the league (V32 league = champion + up to 3 challengers +
  E0/E1/E2 + strongest live-derived family).
- Promotion requires a `V32_PROMOTION_RECORD.json` entry: checkpoint hashes,
  config hash, population-manifest hash, seed list, per-leg results, gate
  clause checklist, rerun digests.
- Training reward, single tournaments, single-seed luck, or single-opponent
  dominance are NEVER promotion evidence.

## 4. Router/BC-only candidates

Supervised/router candidates (OUTCOME B/C) face the same gate with one
addition: the no-memorization probe (§38: seed-hash ablation — shuffling seed
IDs must not change decisions; decisions must be a function of observable
state only). Fail = no promotion regardless of W/L.

## 5. Amendments

Any change to this protocol requires a dated addendum stating the old rule,
the new rule, and the reason — and NEVER applies retroactively to an already
consumed V32-CONFIRM touch.
