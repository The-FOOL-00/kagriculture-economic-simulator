import sys
import os
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

def audit_shed_trapping(seed):
    cfg = {"episodeSteps": 720, "seed": seed}

    class InstrumentedQ50(ParameterizedQuotaAgent):
        def __init__(self):
            super().__init__(50)
            self.history = []

        def __call__(self, obs, config=None):
            step = int(obs.get("step", 0) or 0)
            p = int(obs.get("player", 0) or 0)
            farms = obs.get("farms") or [{}, {}]
            farm = farms[p] if p < len(farms) else {}
            priv = obs.get("private") or {}
            shed = dict(priv.get("shed") or {})

            act = super().__call__(obs, config)
            w_acts = [act.get("farmer", ["PASS"])] + act.get("hands", [])
            w_pos = [tuple(farm.get("farmer", [4, 4]))] + [tuple(h) for h in farm.get("hands", [])]

            self.history.append({
                "step": step,
                "day": step // 24,
                "hour": step % 24,
                "shed": shed,
                "w_pos": w_pos,
                "w_acts": w_acts,
                "worker_targets": dict(self._worker_targets)
            })
            return act

    agent = InstrumentedQ50()
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    
    print(f"=== SHED ANIMAL TRAPPING AUDIT FOR SEED {seed} ===")
    for d in range(9, 17):
        h0 = [x for x in agent.history if x["day"] == d and x["hour"] == 0][0]
        shed_sheep = h0["shed"].get("SHEEP", 0)
        shed_cow = h0["shed"].get("COW", 0)
        print(f"\n--- Day {d}: Shed Sheep={shed_sheep}, Shed Cow={shed_cow}, Workers={len(h0['w_pos'])} ---")
        if shed_sheep > 0 or shed_cow > 0:
            for hr in range(6):
                h = [x for x in agent.history if x["day"] == d and x["hour"] == hr][0]
                line = f"  Hr {hr:2d} | Shed Sheep={h['shed'].get('SHEEP', 0)} | "
                for w in range(min(4, len(h["w_pos"]))):
                    pos = h["w_pos"][w]
                    act = h["w_acts"][w]
                    t = h["worker_targets"].get(w)
                    line += f"W{w}@{pos}: {act} (tgt={t}) | "
                print(line)

if __name__ == "__main__":
    audit_shed_trapping(1060)
