# V24 — Matchup Matrix

Diagnostic Matchup Matrix comparing V22R1, V3 baseline, and Live Cluster archetypes.

> [!NOTE]
> **EVALUATION LABEL**: `OPEN-LOOP DIAGNOSTIC`
> The matches below evaluate policies on exact recorded public game configurations and replay traces.

## Cross-Family Diagnostic Matchup Performance

| Candidate Policy | vs Target Archetype | Recorded Match Win Rate | Mean Terminal Delta | Primary Divergence Subsystem |
| :--- | :--- | :--- | :--- | :--- |
| **V22R1** | Cluster A (DSM, Vadim, Majkel) | **18.2%** (2W / 9L / 0T) | -$8,850 | `WORKER_STRATEGY` + `LIVESTOCK` |
| **V22R1** | Cluster B (THIRD FARM CLUB, Kaggledew) | **33.3%** (3W / 6L / 0T) | -$3,420 | `CROP_STRATEGY` + `CAPITAL_VELOCITY` |
| **V22R1** | Cluster C (QQ, Otter Vibe, Orbital) | **45.5%** (5W / 6L / 0T) | -$1,120 | `LABOR_IDLE_RATE` |
| **Pure V3** | Cluster A (DSM, Vadim, Majkel) | **14.3%** (1W / 6L / 0T) | -$9,400 | `LIVESTOCK_COUNT` + `WORKER_DEADLOCK` |
| **Pure V3** | Cluster B (THIRD FARM CLUB, Kaggledew) | **28.6%** (2W / 5L / 0T) | -$4,100 | `LABOR_TIMING` |
