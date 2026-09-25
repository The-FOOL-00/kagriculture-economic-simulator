import os
import sys
import time
import torch
import numpy as np

REPO_ROOT = os.path.abspath(".")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "candidates", "v38_heuristic_ppo"))

from evaluate import NeuralCandidateWrapper
from policy import MacroActorCritic

# 1. Parameter count and model size
checkpoint_path = "scratch/v38/ppo_policy.pt"
net = MacroActorCritic(obs_dim=64, act_dim=11)
if os.path.exists(checkpoint_path):
    ckpt = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
    net.load_state_dict(ckpt)
total_params = sum(p.numel() for p in net.parameters())
trainable_params = sum(p.numel() for p in net.parameters() if p.requires_grad)
file_size_bytes = os.path.getsize(checkpoint_path) if os.path.exists(checkpoint_path) else 0

print(f"Total Parameters: {total_params:,}")
print(f"Trainable Parameters: {trainable_params:,}")
print(f"Checkpoint File Size: {file_size_bytes / 1024:.2f} KB")

# 2. Benchmark PyTorch forward pass latency
dummy_input = torch.randn(1, 64)
dummy_mask = torch.ones(1, 11)

# warm up
for _ in range(50):
    _ = net(dummy_input, dummy_mask)

times = []
for _ in range(1000):
    t0 = time.perf_counter()
    _ = net(dummy_input, dummy_mask)
    t1 = time.perf_counter()
    times.append((t1 - t0) * 1000.0) # ms

arr = np.array(times)
print(f"MLP Forward Pass Latency: Mean={np.mean(arr):.3f}ms, p50={np.percentile(arr, 50):.3f}ms, p95={np.percentile(arr, 95):.3f}ms, Max={np.max(arr):.3f}ms")
