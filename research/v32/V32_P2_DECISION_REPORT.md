# V32 P2 DECISION REPORT — STOP AT §29 BC GATE (no PPO run)

## 1. Classification: pre-PPO STOP (§65 tree: "BC representation failure → STOP + fix action representation")

P2 never reached the 1M slope gate (G1–G7 unopened — no PPO outcomes
exist). The slope gate did not pass or fail; it was never armed, because
its mandatory precondition (a competent BC initialization, §5/§27–§29)
could not be built with the locked action head. Nearest §61 branch: F,
REFINED — not a fidelity bug (T1–T11 + parity + execution identity all
pass; simulator semantics proven faithful), but an OPTIMIZATION
INFEASIBILITY of the locked pointer head for this candidate space.

## 2. Evidence summary (OBSERVED FACT)

- Mixture-BC: 138k steps, val farmer 0.438 / mkt-nonnoop 0.300; replay
  $31 mean (median $0, 0-138 vs panel).
- A7-BC (+100-ep A7b): val 0.369/0.271, plateaued (early-stop ep27
  twice); replay $0–39 (0-16).
- Closed-loop probe: 0.343 ≈ val → NO eval-time bug; genuine compounding.
- Step-0 wash: never memorized (argmax all-NO-OP over 60 identical
  samples) → optimization failure.
- Linear head control: 100% by ep75 on identical features → features
  SUFFICIENT; the head is the blocker.
- Pointer head: 55% at ep300 (50–100× sample-efficiency gap); frozen-keys
  42%; big-init/rescale/log-scaling all equivalent-or-worse.
- Key geometry: 41,800 market + 169 unit pairs at cosine > 0.99 —
  content-shared encoder collapses qty/item variants to near-identical
  keys; queries cannot separate them. Structural, not tunable.
- Consequence for PPO: every init earns ≈$0 → terminal-only rewards are
  all ≈0 → zero advantages → PPO-from-BC ≡ PPO-from-random ≡ no signal.
  Launching the 1M run would violate §5 and render G2 meaningless.

## 3. What P2 delivered (negative result, preserved capital)

- Validated infrastructure: env+torch single interpreter; capture (120
  legs, 172k steps, TEST-11-clean vocab 101+1466); online temporal
  features; PPO driver + eval harness (smoke-tested, parity-held);
  15-test suite green; frozen a1 manifest (hash stable).
- Representation result (§13): pair-level predictability 0.41→0.96
  through the R1 window — the adaptive signal is real and exposed.
- Precise failure attribution (head optimization, not features/fidelity/
  data) + rejected-fix record (a1.1) so the follow-up doesn't repeat it.

## 4. Fix specification for the follow-up phase (NOT authorized here)

Any ONE of: (a) per-candidate learned key embeddings (drop content-shared
encoder; keeps formula/scoring/masking semantics); (b) LayerNorm + scaled
init on q/k with a memorization gate (≥95% on 400 samples before BC);
(c) two-stage key pretraining (spread objective, then CE). Each needs its
own design doc, tests, and prereg — this is new authorization, not P2.

## 5. Required answers (§63, abridged — full NO-PPO record above)

1–7,9: unanswerable (no PPO). 8: BC tails = total loss ($0). 10: slope
gate NEVER ARMED (precondition failed). 11–12: no scale-up review; the
blocking mechanism is pointer-head key collapse + bilinear
sample-inefficiency. 13: YES — head preserved exact semantics (T1–T11).
14: falsifier = a locked-head BC that replays economically (disproven
twice) or a PPO run with nonzero reward variance from this init.

## 6. Competition-state re-verification (phase exit)

Slot A `6b879b3e…` / Slot B `4a076730…` re-verified byte-identical;
no submission touched; no protected/CONFIRM seed executed (all work on
P2-TRAIN 249635–249649 + P2-SCREEN 249650–249672 + commissioning-free
probes on consumed TRAIN seed 249635); full suite green at exit.
