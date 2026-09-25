# V32 P2 LEARNING CURVE (BC only; no PPO curve exists)

## Mixture-BC val (30 epochs, no early stop)

full-exact 0.019→0.022 (slow creep); farmer 0.42→0.44; hands 0.43→0.45;
mkt-nonnoop 0.29→0.30; NLL 1.05→1.00. Still improving microscopically at
ep29 — but 100-epoch A7b proved the plateau is architectural, not budget.

## A7-BC val (early-stopped ep27)

full-exact flat 0.013 from ep22; farmer 0.35→0.37; mkt-nonnoop 0.26→0.27.

## PPO slope: NO DATA (run never launched — STOP at §29 BC gate)

The slope-gate question (G1–G7) was never reached. PPO smoke test
(random init, 2 episodes, 1 update) validated the loop mechanically
(parity held, loss finite) but carries no scientific signal.
