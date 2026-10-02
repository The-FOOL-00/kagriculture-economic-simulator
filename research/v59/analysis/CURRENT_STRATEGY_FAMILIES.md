# V59 — Current Strategy Families
**Generated:** 2026-09-28

---

## Data Limitation Statement

V59 Phase 12 (Current Strategy Family Discovery) requires September replay data  
with full action streams at turns 24/48/72/100.

**ZERO September replay files are available locally.**

The georgymamarin dataset (primary corpus) ends 2026-08-31.  
The Kaggle episode index ends 2026-08-31.  
The live_data/episodes_v31r2/ contains only outcome summaries (no actions).

---

## What CAN Be Said (from Aug corpus + Sep leaderboard context)

### August Strategy Families (V58 established)

From the georgymamarin corpus (Aug 05–15, 518 elite seats ≥2945):

| Family | Description | Aug Elite Share | Action |
|---|---|---|---|
| F1 | Carrot-0 heavy, 24/42/108 crop units, land-7 | ~50% of 3100+ | SUPERSEDED by V49 |
| F2 | night_harvest pattern (identified in V58) | — | SUPERSEDED |
| F3 | Alternative F1 variant (19/37/143, land-6) | ~30% | SUPERSEDED |
| F4 | P3000-style | rare | SUPERSEDED |
| F5 | P3090-style | rare | SUPERSEDED |

**ALL August families lost to V49** in V58's 400-leg tournament.

### Inferred September Strategy Landscape

From the Sep 22 leaderboard without replay data:

**HYPOTHETICAL Family S1 — Current Sep Meta (unconfirmed)**  
Teams: DSM (3109), Vadim Vasilenko (3099), Unknown Mother-Goose (3052), Kaggledew Valley (3038)  
Evidence: These 4 teams are NEW with zero Aug presence → submitted entirely new strategies  
Strategy signature: UNKNOWN — cannot fingerprint without replay

**HYPOTHETICAL Family S2 — Improved V49-Style (unconfirmed)**  
Teams: Majkel1337 (3070, was Aug 1201), THIRD FARM CLUB (3049, was 2264)  
Evidence: Massive Aug-Sep gains in teams that DO appear in Aug corpus  
Interpretation: Either found V49-style carrot/wash + better parameters, OR different strategy  
Strategy signature: UNKNOWN — cannot fingerprint without replay

**HYPOTHETICAL Family S3 — Execution-Optimized (unconfirmed)**  
Teams: Ryo Hasegawa (2920, was 2645 in Aug), SpaTaro (2921, was 2384)  
Evidence: Smaller gains, were already competitive in Aug  
Interpretation: Incremental improvement, likely execution optimization  
Strategy signature: UNKNOWN

---

## Clustering Results

**Not executable** — requires action stream data at turn 24/48/72/100.

Destbreso benchmark provides stream_hashes for Aug corpus:
- Turn 24: 462 distinct behaviours across 2400 seats
- Turn 50: 521 distinct behaviours
- Strong half (2000+): 112 distinct behaviours above 2000 rating

September equivalent: **not computable without Sep replay files**.

---

## Family Survival Analysis

**Not executable** — requires multi-date fingerprinting.

Cannot determine whether Sep families:
- Appeared Sep 1 (3+ weeks of data)
- Appeared Sep 15 (1 week)
- Appeared Sep 22 (day-of submission)

All 7 top-3000 teams show Sep 21–22 submission dates → confirms active,  
but does NOT tell us when their current strategy was first submitted.

---

## Conclusion

V59 Phase 12 concludes: **STRATEGY FAMILIES NOT DISCOVERABLE** with current data.

Failure class: **I — Current meta data insufficient**

The question "What are the strongest September agents doing?" cannot be answered  
from local replay data. The leaderboard confirms they exist and are active.  
The strategy content remains opaque.
