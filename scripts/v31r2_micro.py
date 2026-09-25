"""V31R2: market microstructure — inventory/price trajectories + sell events."""
import json, sys

def micro(path, focus=("WHEAT", "MELON", "MILK", "WOOL", "FERTILIZER")):
    d = json.load(open(path))
    teams = d["info"]["TeamNames"]
    ours = teams.index("Eldritch") if "Eldritch" in teams else 0
    steps = d["steps"]
    print(f"##### ep{d['info'].get('EpisodeId')} {teams}")
    # sample inventory/prices every 24 steps from agent0 view
    print("  t   " + "  ".join(f"{p:>14s}" for p in focus))
    for t in list(range(0, 721, 48)) + [719]:
        if t >= len(steps): continue
        o = steps[t][0]["observation"]
        inv = o["market"]["inventory"]; pr = o["market"]["prices"]
        print(f"  {t:3d} " + "  ".join(f"{inv.get(p,0):>6.0f}/{pr.get(p,0):>6.0f}" for p in focus))
    # realized revenue per product (money attributed): track money delta on steps where only sells happen is noisy;
    # instead: count fills = min(order, shed_before). Approximate with order qty (fills usually full for us).
    for i, tag in ((ours, "us"), (1 - ours, "op")):
        n_sell_steps = sum(1 for st in steps if any(isinstance(m, list) and m and m[0] == "SELL" for m in st[i]["action"].get("market", [])))
        print(f"  {tag}: steps-with-SELL={n_sell_steps}")
    # money curves every 48
    for i, tag in ((ours, "us"), (1 - ours, "op")):
        m = [steps[t][i]["observation"]["farms"][i if steps[t][i]["observation"]["player"] == i else steps[t][i]["observation"]["player"]]["money"] for t in range(0, len(steps), 48)]
        print(f"  money-{tag}: " + " ".join(f"{x:.0f}" for x in m))

if __name__ == "__main__":
    for p in sys.argv[1:]:
        micro(p)
