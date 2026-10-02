# V32 EXP-4..EXP-9 — PRE-REGISTERED PROTOCOL STUBS (2026-09-22)

Per the mission ("start with EXP-1 through EXP-3; do not proceed to
large-scale training until feasibility evidence justifies it"), EXP-4..EXP-9
are PROTOCOLS, not executed experiments. Each runs only if its entry gate is
met. Full per-experiment reports (`V32_EXP4_CHAMPION.md` … `V32_EXP9_AEC_HYBRID.md`)
are written when — and only when — the experiment executes.

## EXP-4 Learned vs frozen champion

- Entry: EXP-3 shows positive DEV W/L/T slope at ≤10M agent-steps.
- Method: learner (deterministic eval) vs champion (= E2_A7 initially) on
  V32-DEV mirrored legs; suite = champion-suite minus CONFIRM.
- Report: `V32_EXP4_CHAMPION.md`. NOT a promotion test (promotion uses CONFIRM
  per `V32_PROMOTION_PROTOCOL.md`).

## EXP-5 Learned vs strong-opponent suite

- Entry: EXP-4 non-collapse (no family <40% WR).
- Method: learner vs E0/E1/E2/E3/E6/E7/E8 on DEV, mirrored; per-family matrix.
- Kill rule: a 95/45/42-style split (§20) FAILS the generalist claim even if
  mean delta is positive.

## EXP-6 Population-diversity ablation

- Entry: EXP-5 complete.
- Arms: train vs (a) full diverse population, (b) V3-clone-only population,
  (c) single-opponent (E2). Same budget. Compare DEV suite breadth.
- Decides whether diversity sampling (§V32_SAMPLING_PROTOCOL) earns its keep.

## EXP-7 Frozen-champion promotion test

- Entry: EXP-5 breadth gate passed on DEV.
- Method: EXACTLY `V32_PROMOTION_PROTOCOL.md` on V32-CONFIRM, single touch.
- Report: `V32_EXP7_PROMOTION.md` + `V32_PROMOTION_RECORD.json` entry.

## EXP-8 Targeted adversarial finetuning

- Entry: a promoted champion exists AND a strongest counter-family is identified.
- Method: single Learner-A vs Adversary-B cycle (§23), DEV only; re-test on
  the suite for forgetting (historical-champion league check).
- Full two-net alternation only if the single cycle improves strong-opponent WR.

## EXP-9 Learned + AEC safety layer

- Entry: a promoted learned generalist exists (Phase C complete).
- Method: learned policy + AEC supervisor vs learned policy alone vs best
  deterministic, DEV suite; attribution per §28–§30 (B0/B6/B7 comparison).
- AEC integration BEFORE this point is banned (attribution discipline).
