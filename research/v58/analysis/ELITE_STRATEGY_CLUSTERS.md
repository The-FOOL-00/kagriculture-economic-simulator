# V58 Elite Strategy Clusters

Data: [replay_database.jsonl](../data/replay_database.jsonl) (149,398 seats),
method: [cluster_families.py](cluster_families.py).
Full numbers: [ELITE_STRATEGY_CLUSTERS.json](ELITE_STRATEGY_CLUSTERS.json).

## Population

Elite = rating ≥2945: **518 seats / 176 teams / 227 submissions**,
2026-08-05..08-15, engines 1.32.4-6 (only one 1.32.7 seat).
Control = 2500-2800: 14,233 seats.

## F1/F2: exact route families (stream-hash identity)

| Cut | Families | Singletons | Top sizes |
|-----|----------|------------|-----------|
| h100 (actions thru turn 100) | 64 | 36 | 258, 80, 40, 15, 13, 10, 6, 6 |
| h200 (actions thru turn 200) | 113 | 85 | 243, 67, 39, 9, 8, 8, 6, 4 |

Top h100 families (M/S/W = melon/strawberry/wheat plantings, medians):

| Fam | n | teams | r_med | r_max | W/L | M/S/W/C | land | bank_med |
|-----|---|-------|-------|-------|-----|---------|------|----------|
| F1 | 258 | 78 | 2990 | 3139 | 136/122 | 24/42/108/0 | 7 | 88,142 |
| F2 | 80 | 26 | 2974 | 3059 | 27/53 | 24/42/92/0 | 7 | 121,617 |
| F3 | 40 | 1 | 2958 | 2976 | 22/18 | 19/37/143/0 | 6 | 76,680 |
| F4 | 15 | 15 | 2964 | 3001 | 14/1 | 19/37/143/0 | 6 | 81,646 |
| F5 | 13 | 12 | 2954 | 2971 | 7/6 | 19/37/143/0 | 6 | 76,488 |
| F6 | 10 | 9 | 2996 | 3024 | 6/4 | 19/37/143/0 | 6 | 78,879 |

All families: peak crew 14, no carrot, no tomato. Only **two macro crop routes**
exist in the August elite: **(24/42/108 @ land-day-7)** and
**(19/37/143 @ land-day-6)**. F1 holds 4 of 5 3100+ seats.

Control overlap: F1's exact turn-100 route is shared by 2,940 control seats —
same opening line, lower rating. Rating separates *within* route, not just
between routes (opponent strength, later divergence, patch).

## F3: numeric clustering

sklearn is unavailable in the offline venv, so k-means was not run; the exact
hash families (F1/F2) plus the NN-coherence check below carry the clustering
weight. The two macro routes are linearly separable in (wheat, melon, land-day)
alone, so a k-means rerun is not expected to add families.

## F4: nearest-neighbour coherence

20-NN in standardized (crew, hires, tiles, M/S/W) space: **70.5%** of an elite
seat's neighbours share its h100 family. Families are feature-coherent, not
hash accidents.

## Executable-agent placement (in-sim capture, engine 1.32.7)

Local capture hashes use identical normalization and **do match** S3 families:

| Agent | h100 elite match | Family | Note |
|-------|-----------------|--------|------|
| night_harvest | n=80, max 3058.8 | **F2** | historical tape route, live in Aug elite |
| P3000_claimed | n=15, max 3000.9 | **F4** | public tape = F4 line |
| P3090_claimed | n=13, max 2971.1 | **F5** | public tape = F5 line |
| V49 | none | novel (Sept) | carrot route, outside Aug population |
| kaitofukami_3009 | none | novel (Sept) | sheep-only day-0, distinct line |
| thomastschinkel_2945 | none | novel (Sept) | closest V49 relative (see below) |
| saiteja_3000 | none | novel (Sept) | 2-quad end, distinct line |
| tetsutani_pasture | none | novel (Sept) | liquidates herd by end |
| indarkarhana_top10 | none | novel (Sept) | 10C/4S end |
| dmitrii_lb2800 | none | novel (Sept) | V49-family market census |
| v44 | none | conditional | **no-ops off-regime** (see V49_VS_ELITE) |

## Verdict on multiplicity (§44)

Multiple elite families coexist, but they collapse to **two August macro routes**
plus a **September carrot-route cluster** (V49 + Sept executables). The decision
boundary is not "which August family" — it is August-route vs September-route,
and the September cluster already contains V49 as its strongest member.
