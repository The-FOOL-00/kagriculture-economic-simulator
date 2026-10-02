# V32 REWARD SPEC (v1, 2026-09-22)

## 1. Primary objective (frozen)

Head-to-head competition outcome on mirrored seeds. Terminal cash difference
is the SCORE; W/L/T is the DECISION. Every reward variant below is judged by
whether optimizing it improves actual W/L/T on DEV/CONFIRM — never by the
shaped value itself (§13–§14 of the brief).

## 2. Candidate rewards

- **R-A terminal cash**: `r = own_terminal_cash / 1e5`. Simple, dense-at-end,
  but opponent-agnostic (a rich loss still scores well).
- **R-B win/loss/tie**: `r ∈ {+1, 0, -1}` from the leg outcome (mirror-aware:
  computed on the seed's seat-sum, not the single leg, to kill seat bias).
- **R-C hybrid (default)**: `r = sign(d) * (1 + log(1+|d|/1000))` where
  `d` = mirrored cash delta (learner − opponent, both seats). Win-signal
  dominant, margin-aware, log-compressed so $50k blowouts don't drown $1k
  mechanism edges (the +$1,286 A7 edge must remain visible to the optimizer).

## 3. Shaping ban (default) + exception process

No intermediate-cash shaping by default: V31R2/PHASE016 showed local-vs-global
pathologies (tranche overblocking, shed-clog destruction) when intermediate
signals disagreed with terminal outcome. Any shaping proposal must (a) state
the hypothesized credit-assignment gap, (b) run an ablation (shaped vs
unshaped, same budget), (c) win on W/L/T, not on shaped return.

## 4. Value head target

Expected R-C under the current opponent mixture. Opponent identity is NOT a
value input (would leak test-regime info); the value conditions on state only.

## 5. Router labels (not a reward, but the fallback's supervision)

Per-tick label = argmax over experts of counterfactual mirrored outcome from
that tick's state (exact-simulator rollouts, TRAIN seeds only, both seats).
Ties → keep incumbent (hysteresis; prevents router thrash).
