# V32 P2 TRAINING REPORT

## 1. BC training (the only training P2 ran)

Three BC runs, all on the LOCKED pointer-head architecture (545,705
params, frozen a1 `c8977778…`), Adam 3e-4, batch 1024:

| Run | Data | Epochs | val farmer/hands/mkt-nn | Replay |
| :--- | :--- | ---: | :--- | :--- |
| mixture-BC | 4 teachers, 138k steps | 30 | 0.438/0.443/0.300 | $560 (0-138) |
| A7-BC | A7 seats, 43k steps | 27* | 0.369/0.393/0.271 | $0–39 (0-16) |
| A7b-BC | same, 100-ep budget | 27* | identical plateau | — |

*early-stopped (patience 5 on val full-exact). Checkpoints:
`results/v32_p2_bc.npz`, `v32_p2_bc_a7.npz`, `v32_p2_bc_a7b.npz` (+reports).

## 2. PPO training: NOT LAUNCHED (STOP at §29 BC gate)

No competent BC initialization exists (best replay $560 vs A7 ~$100k).
PPO from a $0 policy has no reward signal (all terminal returns ≈ 0);
launching it would violate §5's BC-pipeline requirement and render G2
meaningless. Validated but unused: PPO driver + smoke test (2 episodes,
1 update, parity tripwire held), eval harness, preregistered config
(`V32_P2_PPO_SPEC.md`), Tier-1/2 screen design. All preserved for the
follow-up phase once a competent init exists.

## 3. Provenance

Git HEAD `d818fb1`; torch 2.14.0+cpu (`.venv`); CPU-only 12-core.
Run registries: `results/v32_p2_bc_report.json`,
`results/v32_p2_bc_a7_report.json` (+ `*_a7b_*`).
