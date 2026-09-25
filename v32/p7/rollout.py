# SPDX-License-Identifier: MIT
"""V32 P7 rollout helpers: truncated + full episodes on the validated path.

env.run is the validated full-episode path (manual stepping with raw step
returns leaves seat-1 observations stale). This module drives truncated
rollouts through the SAME observation builder env.run uses internally
(Environment._Environment__get_shared_state), so truncated rollouts are
exactly env.run's first H steps for BOTH seats. Equivalence is verified by
tests/test_v32_p7.py::test_05 against env.run traces.

No teacher-state overwrite, no action splicing, no future-state inputs: each
agent sees only its own current observation; all states are simulator-generated.
"""

import copy


def shared_obs(env, seat):
    """Current observation for `seat` via env.run's own observation builder."""
    return copy.deepcopy(
        env._Environment__get_shared_state(seat)["observation"])


def truncated_rollout(make_fn, seed, seat_agents, H, trace_seat=0,
                      ess_fn=None):
    """Run H+1 steps (0..H) of a 2-agent game. Returns trace + env.

    make_fn(seed) -> env; seat_agents = [agent0, agent1] with .act(obs, cfg).
    trace: list of {"step", "obs", "ess", "actions"} where actions = [a0, a1]
    and ess is ess_fn(obs, trace_seat) when ess_fn is given.
    """
    env = make_fn(seed)
    env.reset(2)
    trace = []
    for _ in range(H + 1):
        obs = [shared_obs(env, 0), shared_obs(env, 1)]
        acts = [seat_agents[0].act(obs[0]), seat_agents[1].act(obs[1])]
        rec = {"step": int(obs[trace_seat].get("step", 0)),
               "obs": copy.deepcopy(obs[trace_seat]),
               "actions": copy.deepcopy(acts)}
        if ess_fn is not None:
            rec["ess"] = ess_fn(obs[trace_seat], trace_seat)
        trace.append(rec)
        if getattr(env, "done", False):
            break
        env.step(acts)
    return trace, env


def full_episode_trace(make_fn, seed, seat_agents, trace_seat=0, ess_fn=None):
    """Full episode via env.run with per-step trace recording."""
    env = make_fn(seed)
    trace = []

    def make_rec(i):
        def _act(obs, cfg=None):
            a = seat_agents[i].act(obs, cfg)
            if i == trace_seat:
                rec = {"step": int(obs.get("step", 0)),
                       "obs": copy.deepcopy(obs),
                       "action": copy.deepcopy(a)}
                if ess_fn is not None:
                    rec["ess"] = ess_fn(obs, trace_seat)
                trace.append(rec)
            return a
        return _act

    env.run([make_rec(0), make_rec(1)])
    return trace, env
