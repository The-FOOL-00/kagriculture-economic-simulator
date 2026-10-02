# V32 P2 ENV BENCHMARK

Hardware: CPU-only, 12 cores, ~7 GB RAM. torch 2.14.0+cpu in `.venv`
(single interpreter for env + policy; frozen digests unaffected).
Machine-readable: `results/v32_p2_bench.json`.

| Quantity | Value |
| :--- | :--- |
| Params (locked arch) | 545,705 |
| Unit candidates | 101 |
| Market candidates/slot | 1,466 |
| Market slots | 10 (len-10 lists observed 704× — M=8 would truncate) |
| Hands observed | 0–14 (cap 16 assert) |
| Policy forward+sample (batch=1) | 5.5 ms → ~183 agent-steps/s single-process |
| Expert leg (V3-class) | ~13–16 s / ~720 steps / 2 seats ≈ 10 ms/agent-step |
| Projected PPO rollout (10 workers) | ~600 agent-steps/s → 1M ≈ 30 min + updates |

GPU: none available; all P2 compute is CPU. Bottleneck is environment
simulation + expert opponents, not candidate scoring (batched once per
step: 101 + 1466 encodings + matmuls). No optimization applied (§33:
semantics first; profiled, adequate for one 1M run).
