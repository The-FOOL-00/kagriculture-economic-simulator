#!/usr/bin/env bash
# V60 Acquisition Commands — Shell (for Linux/WSL context)
# Generated: 2026-09-28

# METHOD 1: Download replay from public CDN (no auth)
curl -o ep_111851139.json "https://www.kaggleusercontent.com/episodes/111851139.json"

# METHOD 2: ListEpisodes API
curl -X POST "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes" \
  -H "Content-Type: application/json" \
  -d '{"submissionId": 55903635}'

# METHOD 3: Dataset list (auth required)
KAGGLE_USER=$(python3 -c "import json; print(json.load(open('/root/.kaggle/kaggle.json'))['username'])")
KAGGLE_KEY=$(python3 -c "import json; print(json.load(open('/root/.kaggle/kaggle.json'))['key'])")
curl -u "$KAGGLE_USER:$KAGGLE_KEY" \
  "https://www.kaggle.com/api/v1/datasets/list?search=kaggriculture-episodes"

# Run scan script
python3 -X utf8 research/v60/data/scan_sep_subs.py

# Required user action:
# kaggle datasets download ashok205/kaggriculture-top10-replay-archive -p research/v60/data/kaggle_downloads/
# kaggle datasets download kaggle/kaggriculture-episodes-2026-09-26    -p research/v60/data/kaggle_downloads/
# (These require OAuth browser session; API key alone is insufficient for download)
