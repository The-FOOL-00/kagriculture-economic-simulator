import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v41.training.train_online_ppo import V41OnlinePPOTrainer
import torch

if __name__ == "__main__":
    ckpt_init = os.path.join(REPO_ROOT, "research", "v41", "checkpoints", "v41_offline_model.pt")
    out_ckpt = os.path.join(REPO_ROOT, "research", "v41", "checkpoints", "v41_ppo_champion.pt")

    trainer = V41OnlinePPOTrainer(
        checkpoint_path=ckpt_init,
        lr=3e-4,
        teacher_kl_coeff=0.08
    )

    seeds = [249635, 249636, 249637]
    opps = ["E8_DMITRII", "E2_A7"]

    print(f"Starting V41 Online Recurrent PPO Training (3 iterations)...")
    t0 = time.perf_counter()

    for it in range(1, 4):
        t_it = time.perf_counter()
        res = trainer.train_iteration(seeds=seeds, opponents=opps, ppo_epochs=2)
        dur = time.perf_counter() - t_it
        print(f"Iter {it:02d} | Mean Reward: ${res['mean_reward']:.1f} | Interventions: {res['total_interventions']} | Loss: {res['loss']:.4f} | Time: {dur:.1f}s")

    torch.save(trainer.policy.state_dict(), out_ckpt)
    print(f"Online PPO completed in {time.perf_counter()-t0:.1f}s. Saved: {out_ckpt}")
