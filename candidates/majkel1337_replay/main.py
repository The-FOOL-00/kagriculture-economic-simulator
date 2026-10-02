"""
Majkel1337 Replay Agent — reconstructed from Sep 2026 replay data.
Replays the action sequence from the most recent Majkel1337 game,
cycling through episodes when steps run out.
"""
import json, gzip, random
from pathlib import Path

_REPLAY_DIR = Path(__file__).parent.parent.parent.parent / 'research' / 'v60' / 'data' / 'sep_replays'
_MAJKEL_EPISODES = []
_episode_idx = 0
_step_idx = 0

def _load_episodes():
    global _MAJKEL_EPISODES
    TARGET = 'Majkel1337'
    for f in sorted(_REPLAY_DIR.glob('*.json.gz'), reverse=True):
        try:
            d = json.loads(gzip.open(f).read())
            teams = d.get('info', {}).get('TeamNames', [])
            if TARGET in teams:
                seat = teams.index(TARGET)
                steps = d.get('steps', [])
                actions = []
                for step in steps:
                    if seat < len(step):
                        act = step[seat].get('action')
                        if act is not None:
                            actions.append(act)
                if actions:
                    _MAJKEL_EPISODES.append(actions)
        except Exception:
            pass
    print(f'[MajkelReplay] Loaded {len(_MAJKEL_EPISODES)} Majkel1337 episodes')

_load_episodes()

def agent(obs, config=None):
    global _episode_idx, _step_idx
    if not _MAJKEL_EPISODES:
        return {}
    ep = _MAJKEL_EPISODES[_episode_idx % len(_MAJKEL_EPISODES)]
    if _step_idx >= len(ep):
        _episode_idx = (_episode_idx + 1) % len(_MAJKEL_EPISODES)
        _step_idx = 0
        ep = _MAJKEL_EPISODES[_episode_idx]
    act = ep[_step_idx]
    _step_idx += 1
    return act
