# V58 Selector Leakage Audit

Status: PRE-REGISTERED (selector not yet built — see decision hierarchy §50:
no selector may be constructed unless Stage B shows multiple winning plans).

## Boundaries the selector must obey (if built)

1. Decision boundaries: day 0 only, with optional re-evaluation at turn-100
   (day 4) — the earliest cut where macro routes separate (see
   [MACRO_BOUNDARIES.md](MACRO_BOUNDARIES.md)). No per-step decisions.
2. Legal features only: cash, day/hour, own animals/crops/hands/land, current
   market prices/inventory, already-revealed town shops, own production,
   opponent PUBLIC board state (per PUBLIC_OPPONENT_STATE_SCHEMA.md).
3. Forbidden: future shops, seed/RNG, opponent pending actions, opponent
   private state, future cash/reward, terminal outcome, replay strategy labels
   as targets without counterfactual validation.
4. Training/eval split: grouped by seed (discovery 10000-10099 / tournament
   10100-10199 / fresh ≥10200) AND leave-one-agent-out over executable elites
   (proxy for leave-one-player-out: no plan may be selected on seeds used to
   discover it). Time split: August-hash families are discovery-only; September
   executables are validation.
5. V49 fallback mandatory with learned abstention threshold (§22).

## Audit verdict — CLOSED AS NOT-APPLICABLE

- Selector built? **No.** Tournament ended 0/400; t2945 follow-up 2/120
  nominal wins proven seat artifacts (0/60 pair sums positive).
- Shipped adaptive components: **zero**. No selector code exists under
  research/v58/candidates/ (both dirs intentionally empty).
- Leakage surface: **none** — nothing trained, no features consumed, no test
  worlds touched by any policy (all V58 legs used discovery/tournament splits;
  fresh split ≥10200 never used).
- Split integrity: discovery 10000-10001 (capture), tournament 10100-10119
  (plan tournament) + 10120-10179 (t2945 scan); holdouts and V56 range
  asserted out in every runner script.
- Future information used: **false**. Seed as policy feature: **false**
  (no policy). Opponent-private-state: **false**.
