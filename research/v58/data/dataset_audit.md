# V58 Dataset Audit

Builder: [build_db.py](research/v58/data/build_db.py) (committed, reproducible).
Manifest: [replay_manifest.json](research/v58/data/replay_manifest.json).

## Sources

| ID | Content | Size | Elite content |
|----|---------|------|---------------|
| S1+S2+S3 | georgymamarin episodes/features/stream-hashes (2026-07-30..08-31) | 74,699 eps / 139,903 feats | 518 seats ≥2945, max rating 3138.9 |
| S4 | georgymamarin teams.csv (ladder snapshot) | 7,090 teams | top 2930.1 (tetsuya); snapshot predates Sept |
| S5 | live_data keep/ replays (our v22r1 live games) | 193 files | none (2× 2800-2945, rest <2800) |
| S6 | replays/live_tournament | 48 files | none (all <2500 bar 2 slots) |
| S7 | online_replays A/B/C1/C2 (LiXingtao games) | 48 files | none (all ≤2748) |
| S8 | replays/episode-* root replays | 27 files | none (all weak) |
| S9 | leaderboard CSV 2026-09-22 | 9,807 teams | top 3109.5 (DSM); join key only, no replays |
| S10 | executable elite agents | 11 agents | 3009/3000/2945/2880/2860/2800 + claimed 3090/3000 tapes |

Tapes `replays/Aethel_prime_v1` (101) and `replays/Apex_v4` (52) are our own
self-play action lists (list-JSON, no observations) — excluded from the elite
population, usable only as control-route references.

## Elite population (from S1+S2+S3, rating = per-seat match rating)

| Band | Seats | % of 149,398 |
|------|-------|--------------|
| 3100+ | 5 | 0.003% |
| 3050-3100 | 18 | 0.012% |
| 3000-3050 | 114 | 0.076% |
| 2945-3000 | 381 | 0.255% |
| 2800-2945 | 2,680 | 1.8% |
| 2500-2800 (control) | 14,229 | 9.5% |
| <2500 | 131,971 | 88.3% |

Elite (≥2945): 518 seats, 176 teams, 227 submissions, all `EPISODE_TYPE_PUBLIC`,
dates 2026-08-05..08-15.

## Caveats (binding on all V58 conclusions)

1. **No 3100+ full replays.** The public "top-10 archive" / Furina 148-episode
   slice are not available locally and public Kaggle sources are unreachable
   from this environment (web search returns no Kaggle content). Elite-A/B are
   (rating, features, hashes) only — no observations, no market actions.
2. **Engine skew.** Elite seats: 1.32.4 (30), 1.32.5 (106), 1.32.6 (381),
   1.32.7 (1). Family discovery is cross-patch; every causal claim is
   re-tested on engine 1.32.7.
3. **Historical window.** Elite dates Aug 05-15 predate the Sept leaderboard
   (S9 top 3109.5). Families are historical-evidence-first (§30); current-meta
   relevance requires the executable-elite (S10) cross-check on 1.32.7.
4. **Features lack animals/labour-trace/market-actions.** S2 has crops, crew
   peak, hires, land day, prices — but no cows/sheep/hands-trajectory/sales.
   Stream hashes (S3) compensate as exact route-lineage identifiers.
5. **Rating ≠ cash.** Preserved separately per §36 (rating, bank, outcome).

## Verification

- V49 frozen: `candidates/v49_meta_fusion/main.py` SHA256
  `8CAFF630...FBBD11` verified 2026-09-26; engine `kaggle-environments 1.32.7`.
- Protected holdouts never touched: 214200-249, 340090-199, 249695-734.
- Seed splits: discovery 10000-10099, tournament 10100-10199, fresh ≥10200
  (all from benchmarks/seeds/development.txt), V56 ladder range 250600-250632 avoided.
