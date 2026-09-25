"""V31R2: download all live replays for A7 + V22R1, summarize, keep non-wins."""
import json, os, shutil, subprocess, sys, time

KAGGLE = ".venv/bin/kaggle"
TOKEN = open("/mnt/c/Users/Sundareswaran/.kaggle/access_token").read().strip()
ENV = dict(os.environ, KAGGLE_API_TOKEN=TOKEN)
TMP = "/tmp/v31r2_dl"
KEEP = "live_data/episodes_v31r2/keep"
os.makedirs(TMP, exist_ok=True)
os.makedirs(KEEP, exist_ok=True)

OUR_TEAM = "Eldritch"

def summarize(ep_id, sub_label, create_time, ep_type):
    path = os.path.join(TMP, f"episode-{ep_id}-replay.json")
    if not os.path.exists(path):
        r = subprocess.run([KAGGLE, "competitions", "replay", str(ep_id),
                            "-p", TMP, "-q"], capture_output=True, text=True, env=ENV)
        if r.returncode != 0 or not os.path.exists(path):
            return {"episode_id": ep_id, "sub": sub_label, "error": (r.stderr or "")[:300]}
    try:
        with open(path) as f:
            d = json.load(f)
        teams = d["info"]["TeamNames"]
        ours = teams.index(OUR_TEAM) if OUR_TEAM in teams else None
        if ours is None:
            out = {"episode_id": ep_id, "sub": sub_label, "error": f"our team not in {teams}"}
        else:
            ours_r = d["rewards"][ours]
            opp_r = d["rewards"][1 - ours]
            res = "W" if ours_r > opp_r else ("L" if ours_r < opp_r else "T")
            out = {"episode_id": ep_id, "sub": sub_label, "createTime": create_time,
                   "type": ep_type, "our_idx": ours, "opp_team": teams[1 - ours],
                   "our_reward": ours_r, "opp_reward": opp_r, "delta": ours_r - opp_r,
                   "result": res, "statuses": d["statuses"], "seed": d["info"].get("seed"),
                   "steps": len(d["steps"]), "module": d.get("module_version"),
                   "version": d.get("version")}
            if res != "W":
                keep = os.path.join(KEEP, f"{sub_label}-episode-{ep_id}-replay.json")
                if not os.path.exists(keep):
                    shutil.move(path, keep)
                    out["kept"] = keep
                elif os.path.exists(path):
                    os.remove(path)
            elif os.path.exists(path):
                os.remove(path)
        return out
    except Exception as e:
        return {"episode_id": ep_id, "sub": sub_label, "error": f"parse: {e}"}

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    shard = sys.argv[2] if len(sys.argv) > 2 else None  # e.g. "0/4"
    out_path = sys.argv[3] if len(sys.argv) > 3 else "live_data/episodes_v31r2/summary.jsonl"
    jobs = []
    if which in ("a7", "both"):
        eps = json.load(open("live_data/episodes_v31r2/a7_episodes.json"))
        jobs += [("a7", e) for e in eps]
    if which in ("v22r1", "both"):
        eps = json.load(open("live_data/episodes_v31r2/v22r1_episodes.json"))
        jobs += [("v22r1", e) for e in eps]
    if shard:
        k, n = map(int, shard.split("/"))
        jobs = [j for i, j in enumerate(jobs) if i % n == k]
    done_ids = set()
    for p in [out_path, "live_data/episodes_v31r2/summary.jsonl"]:
        if os.path.exists(p):
            for line in open(p):
                try:
                    done_ids.add(json.loads(line)["episode_id"])
                except Exception:
                    pass
    n_new = 0
    with open(out_path, "a") as out:
        for i, (sub, e) in enumerate(jobs):
            if e["id"] in done_ids:
                continue
            s = summarize(e["id"], sub, e["createTime"], e["type"])
            out.write(json.dumps(s) + "\n")
            out.flush()
            n_new += 1
            if n_new % 10 == 0:
                print(f"{n_new} done, last ep {e['id']} -> {s.get('result', s.get('error','?')[:60])}", flush=True)
    print(f"ALL DONE: {n_new} new summaries")

if __name__ == "__main__":
    main()
