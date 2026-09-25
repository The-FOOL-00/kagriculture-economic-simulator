import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v41.shadow.shadow_evaluator import run_shadow_audit

if __name__ == "__main__":
    ckpt = os.path.join(REPO_ROOT, "research", "v41", "checkpoints", "v41_offline_model.pt")
    # Clean DEV seeds (quarantine checked: not in 214200-214249, 340090-340199, 249695-249734)
    seeds = [249675, 249676]
    opps = ["E8_DMITRII", "E2_A7"]

    print("Running Shadow Mode Audit across clean DEV seeds...")
    metrics = run_shadow_audit(
        model_checkpoint_path=ckpt,
        seeds=seeds,
        opponents=opps
    )
