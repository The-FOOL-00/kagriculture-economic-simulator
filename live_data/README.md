# Live Replay & Data Pipeline

This directory stores live leaderboard episodes, download traces, logs, and reverse-engineered opponent strategies.

## Directory Structure
- `submissions/`: Metadata snapshots of submitted agents.
- `episodes/`: Raw episode JSON data downloaded via Kaggle API.
- `replays/`: Formatted match replays for forensic visual inspection.
- `logs/`: Runtime standard output and error traces.
- `analysis/`: Extracted opponent behavior patterns and strategic clusters.

## Workflow
```
Kaggle Submission -> Matchmaking Episodes -> Episode Download -> Replay Analysis -> Loss Forensics -> Opponent Mining -> Next Iteration
```
