# SPDX-License-Identifier: MIT
"""V32 P7 trajectory-level prefix supervision (v32p7-a1).

Modules:
- prefix: deterministic prefix extraction from recorded demonstrations.
- metrics: prefix-exact-match, first-divergence, macro-survival (pure functions).
- state: normalized simulator-state distance (pure function).
- phase: deterministic state-derived macro-phase detector (no step labels).
- rollout: validated truncated/pair manual-loop rollouts (same observation path
  as env.run; equivalence covered by tests/test_v32_p7.py).
"""
