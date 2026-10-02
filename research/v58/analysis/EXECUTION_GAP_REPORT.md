# V58 Execution Gap Report

Question (§40): if an elite macro plan beats V49 but our executor cannot
reproduce it, the gap is execution, not strategy.

## Finding: no execution gap to investigate

1. No elite plan beats V49 anywhere measured (capture 0/40 legs across 10
   elites on discovery seeds; tournament in progress in
   [PLAN_TOURNAMENT.json](../counterfactuals/PLAN_TOURNAMENT.json)).
   The §40 trigger condition (elite macro > V49 macro, but transplant fails)
   has not fired.
2. Direction of the gap is reversed: the executable elites show execution
   *leaks* relative to V49 on identical lines —
   saiteja_3000 ends on 2 quads (misses SW), tetsutani_pasture liquidates its
   whole herd, kaitofukami_3009 under-produces wash volume on these seeds.
   V49's executor is the family ceiling, not the floor.
3. The transplant experiment (§15, V49 executor + elite portfolio) is therefore
   moot for every plan except thomastschinkel_2945: only t2945 shares V49's
   census closely enough that a portfolio-only delta (6C/6S vs 12C/5S) is
   definable. Transplant record:
   [PLAN_TRANSPLANT.json](../counterfactuals/PLAN_TRANSPLANT.json) (written
   after the tournament; currently: no qualifying transplant — t2945 loses
   its fixed matchup, so there is no winning macro to transplant).

## Worker-route spot check (V49 vs t2945, seed 10000)

Both run crew 11-12 end, hires 263/266, zero blocked-action evidence in
rewards (both DONE, full 720 steps). The $150 gap is economic calibration
(herd mix + sale timing), not route efficiency — no missed-milestone pattern
in the daily snapshots (identical quad sequence NW→NE→SW, identical first-sale
days for 7 of 9 commodities).

## Conclusion

V49's executor needs no replacement. If the tournament finds a t2945 regime
win, the follow-up is a *calibration* rule (herd mix), not an executor rewrite.
