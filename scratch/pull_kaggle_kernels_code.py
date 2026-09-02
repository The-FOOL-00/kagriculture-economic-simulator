import os
import sys
from kaggle.api.kaggle_api_extended import KaggleApi

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

api = KaggleApi()
api.authenticate()

target_kernels = [
    "kaitofukami/238-238-known-streams-v58-minimax-closed-loop",
    "busyaprime/what-actually-wins-on-the-kaggriculture-ladder",
    "premaananda108/economics-driven-rule-agent-ecobot-v7-arena",
    "boatlee/v21-r1-public-state-route-portfolio",
    "georgymamarin/kaggriculture-daily-replays-the-live-meta-report",
    "yamakawanin/kaggriculture-adaptive-public-state-multi-route",
    "yhay81/fieldbook-commit-for-three-days",
    "lynnsakurai/farming-score-v3-replay-revised",
    "destbreso/a-dna-test-for-agents",
    "ameythakur20/kaggriculture-premium-first-market-agent",
    "llccqq624/kaggriculture-adaptive-counterbook",
    "saitejabandaruin/kaggriculture-pure-architecture-2600-elo-v3"
]

os.makedirs("scratch/kernels", exist_ok=True)

for k_slug in target_kernels:
    folder_name = k_slug.replace("/", "__")
    dest = os.path.join("scratch/kernels", folder_name)
    os.makedirs(dest, exist_ok=True)
    print(f"Pulling kernel: {k_slug} -> {dest}")
    try:
        api.kernels_pull(k_slug, path=dest)
        print(f"  Successfully pulled {k_slug}: files={os.listdir(dest)}")
    except Exception as e:
        print(f"  Failed {k_slug}: {e}")

print("Done pulling kernels!")
