# V30 META DATA SOURCES

Date: 2026-09-21. No Kaggle API credentials available in this environment
(no `kaggle` CLI, no `~/.kaggle`); all meta evidence below is local and
independently re-executed in-engine (1.32.7). Nothing is trusted on labels.

## 1. Runnable public agents (primary evidence)

| ID | Path | Claimed band | Architecture |
|---|---|---|---|
| P3090 | `external_repos/lixingtao123-Kaggriculture/public_3090/output/main.py` | 3090 | 719-step tape + WEED repair + SELL ranking |
| P3000 | `.../opponents/public_3000/main.py` | 3000 | 720-step tape + WEED/FR repair |
| P2900 | `.../public_2900/main.py` | 2900 | tape (== P3000 tape bytes; older runtime) |
| NIGHT | `.../opponents/night_harvest/main.py` | — | 719-step tape, wheat-cycle variant |
| OKAMI | `external_repos/okami001-Kaggriculture/main.py` | — | reactive expert rules (closed loop) |
| DMITRII | `extracted_agents/dmitrii_lb2800/main.py` (+tarball `submission_dmitrii_lb2800.tar.gz`) | LB2800 | router + terminal planner + unit model |
| V66 | `external_repos/kaggriculture-v66-agent/main.py` | public agent | multi-route conditional (re-decides t=72/144, terminal 713–718) |

Retrieved into workspace 2026-09-08..09-10 (file dates); treated as
hypotheses and re-run locally. Ratings are source-directory labels, NOT
verified current leaderboard positions.

## 2. Local replay corpora (secondary evidence)

- `replays/live_tournament/episode_10751*.json` — 28 episodes, 2026-09-11.
- `episode-104820229-replay.json` (2026-09-19), `elo3000_test_replay.json`,
  `master_*_replay.json`, `titan_*_replay.json` — older references.
- `external_repos/lixingtao123-Kaggriculture/online_replays/` (A/B/C1/C2 +
  episode-104076314), `opponents/top1_tetsuya/replays/` (3 episodes).
- `external_repos/lixingtao123-Kaggriculture/results/*.json` — author's own
  local head-to-head logs (e.g. `a_vs_public_2900.json`: 24 games, 91.7% W,
  mean margin +$9.5k; rewards 60k–120k scale). Used only as priors.

## 3. Leaderboard snapshots

- `external_repos/lixingtao123-Kaggriculture/leaderboard_snapshots/kaggriculture.zip`
  (2026-09-08). Stale by definition; used for family names only.

## 4. What was NOT available

- Live Kaggle leaderboard / current ratings / recent episodes via API.
- Current top-10 cutoff: unknown; "3100+" is used ONLY as a research-band
  label for the strongest runnable public tape family (P3090), never as a
  claimed rank.

## 5. Governing rule

Every behavioral claim about a meta agent used in A8 design must be
reproduced in our engine on V30 seeds. Tape contents are evidence of
macro decisions, never transplanted.
