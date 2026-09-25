# V30 SANITY RESULTS

No A8 was built (no-build decision, V30_A8_SPEC.md). Sanity scope below
covers the substitute deliverable (A7-standalone) + gauntlet integrity.

## Loader smoke (all meta agents)

V3 vs {P3090, V66, DMITRII, OKAMI} on seed 249570: all loaded, all played
full 720-step games, all produced substantial economies (42k-141k). No
loader failures, no zero-output agents, no regime crashes.

## Engine-fact corrections during sanity

1. `hands==0` artifact: farm hands reset EVERY dawn (engine source line
   ~880). All agents re-hire daily (~10/day). Not a bug in any agent.
2. Tape agents execute fixed 719/720-step tapes + WEED repair + SELL
   ranking; verified coherent play (money curves rise monotonically,
   expansion at t=240, terminal liquidation at t=708).
3. Live config == local config (townCenterSellInterval 24). No regime
   confound for tape agents' "rebalance" path.

## A7-standalone sanity

- Step-0 market on probe seed: 30/30 wash present; all other steps V3.
- Loader-path match (fresh dir, import main): AST 129,182 vs V3 127,896
  (+1,286 — exact A7 signature).
- 24/24 equivalence legs dollar-tied; 8/8 cross-bout action digests,
  money trajectories, and structure traces identical.
- Serial/pool parity: 2/2 exact (rewards + digests).
