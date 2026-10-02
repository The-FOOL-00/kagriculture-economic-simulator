#!/usr/bin/env python3
"""V58 elite strategy-family clustering (committed).

Method (interpretable first, per spec section 7):
  F1  hand buckets: stream_h100 exact match (identical actions thru turn 100)
  F2  hand buckets: stream_h200 exact match (identical actions thru turn 200)
  F3  numeric: k-means on standardized strategy features (crew, hires, land day,
      tiles, crop mix) over elite seats; k chosen by silhouette over k=2..10
  F4  nearest-neighbour: for each elite seat, fraction of 20 nearest feature
      neighbours sharing its h100 family (family coherence check)

Outputs:
  research/v58/analysis/ELITE_STRATEGY_CLUSTERS.json
  (ELITE_STRATEGY_CLUSTERS.md written after V49 comparison joins)
"""
import json
import os
import sys
from collections import Counter, defaultdict

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DB = os.path.join(REPO, "research", "v58", "data", "replay_database.jsonl")
OUT = os.path.join(REPO, "research", "v58", "analysis", "ELITE_STRATEGY_CLUSTERS.json")

sys.stdout.reconfigure(line_buffering=True)


def load():
    elite, control = [], []
    with open(DB) as f:
        for line in f:
            r = json.loads(line)
            rt = r.get("rating")
            if rt is None:
                continue
            if rt >= 2945:
                elite.append(r)
            elif 2500 <= rt < 2800:
                control.append(r)
    return elite, control


def fam_stats(members):
    ratings = sorted(m["rating"] for m in members)
    banks = sorted((m["features"] or {}).get("final_money") or 0 for m in members)
    n = len(members)
    med = lambda v: v[n // 2] if n else None  # noqa: E731
    return {
        "size": n,
        "rating_med": med(ratings), "rating_min": ratings[0] if n else None,
        "rating_max": ratings[-1] if n else None,
        "bank_med": med(banks),
        "teams": len(set(m["team_id"] for m in members)),
        "subs": len(set(f'{m["episode_id"]}/{m["seat"]}' for m in members)),
        "dates": [min(m["date"] for m in members), max(m["date"] for m in members)],
        "wins": sum(1 for m in members if m["outcome"] == "W"),
        "bands": dict(Counter("3100+" if m["rating"] >= 3100 else
                              "3050+" if m["rating"] >= 3050 else
                              "3000+" if m["rating"] >= 3000 else "2945+"
                              for m in members)),
        "engines": dict(Counter((m["features"] or {}).get("engine_version") for m in members)),
    }


def feat_med(members):
    cols = ["peak_crew", "total_hires", "tiles_planted", "plants_carrot",
            "plants_melon", "plants_strawberry", "plants_tomato", "plants_wheat"]
    out = {}
    for c in cols:
        vals = sorted((m["features"] or {}).get(c) for m in members)
        vals = [v for v in vals if v is not None]
        out[c] = vals[len(vals) // 2] if vals else None
    fld = Counter((m["features"] or {}).get("first_land_day") for m in members)
    out["first_land_day_mode"] = fld.most_common(1)[0][0] if fld else None
    out["first_land_day_dist"] = {str(k): v for k, v in fld.most_common(5)}
    return out


def main():
    elite, control = load()
    print(f"elite={len(elite)} control={len(control)}")
    result = {"population": {"elite_ge2945": len(elite), "control_2500_2800": len(control)}}

    # F1/F2: exact stream-hash families
    for cut in ("stream_h100", "stream_h200"):
        fams = defaultdict(list)
        for m in elite:
            fams[(m["hashes"] or {}).get(cut)].append(m)
        # control overlap per family hash
        ctrl_by_hash = Counter((m["hashes"] or {}).get(cut) for m in control)
        fam_list = []
        for h, members in sorted(fams.items(), key=lambda kv: -len(kv[1])):
            s = fam_stats(members)
            s["hash"] = h
            s["control_sharing_route"] = ctrl_by_hash.get(h, 0)
            s["feature_med"] = feat_med(members)
            fam_list.append(s)
        result[f"families_{cut}"] = {
            "n_families": len(fam_list),
            "singletons": sum(1 for f in fam_list if f["size"] == 1),
            "top": fam_list[:25],
            "size_hist": dict(Counter(f["size"] for f in fam_list)),
        }
        print(f"{cut}: {len(fam_list)} families, "
              f"singletons={result[f'families_{cut}']['singletons']}, "
              f"top sizes={[f['size'] for f in fam_list[:8]]}")

    # F3: k-means on features
    try:
        import numpy as np
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
        from sklearn.preprocessing import StandardScaler

        cols = ["peak_crew", "total_hires", "tiles_planted", "plants_melon",
                "plants_strawberry", "plants_wheat", "plants_carrot", "plants_tomato"]

        def vec(m):
            f = m["features"] or {}
            v = [f.get(c) if f.get(c) is not None else 0.0 for c in cols]
            fld = f.get("first_land_day")
            v.append(float(fld) if fld is not None else 15.0)
            return v

        X = np.array([vec(m) for m in elite], dtype=float)
        Xs = StandardScaler().fit_transform(X)
        best = None
        for k in range(2, 11):
            km = KMeans(n_clusters=k, n_init=10, random_state=7).fit(Xs)
            sil = silhouette_score(Xs, km.labels_)
            print(f"kmeans k={k} silhouette={sil:.3f}")
            if best is None or sil > best[0]:
                best = (sil, k, km.labels_)
        sil, k, labels = best
        clusters = []
        for c in range(k):
            members = [m for m, lab in zip(elite, labels) if lab == c]
            s = fam_stats(members)
            s["cluster"] = c
            s["feature_med"] = feat_med(members)
            # dominant h100 families inside
            s["h100_mix"] = {str(h): n for h, n in
                             Counter((m["hashes"] or {}).get("stream_h100") for m in members).most_common(5)}
            clusters.append(s)
        result["kmeans"] = {"k": k, "silhouette": round(sil, 4), "features": cols + ["first_land_day"],
                            "clusters": sorted(clusters, key=lambda c: -c["size"])}
    except ImportError as e:
        result["kmeans"] = {"error": f"sklearn unavailable: {e}"}
        print("sklearn unavailable, skipping k-means")

    # F4: NN coherence of h100 families in feature space
    try:
        import numpy as np

        cols = ["peak_crew", "total_hires", "tiles_planted", "plants_melon",
                "plants_strawberry", "plants_wheat"]
        X = np.array([[((m["features"] or {}).get(c) or 0.0) for c in cols] for m in elite], float)
        mu, sd = X.mean(0), X.std(0) + 1e-9
        Xn = (X - mu) / sd
        fams = [(m["hashes"] or {}).get("stream_h100") for m in elite]
        coh = []
        for i in range(len(elite)):
            d = ((Xn - Xn[i]) ** 2).sum(1)
            nn = np.argsort(d)[1:21]
            coh.append(float(np.mean([fams[j] == fams[i] for j in nn])))
        result["nn_coherence"] = {"k": 20, "mean_same_family": round(float(np.mean(coh)), 4)}
        print(f"NN coherence: {result['nn_coherence']}")
    except ImportError:
        result["nn_coherence"] = {"error": "numpy unavailable"}

    # Meta drift: elite family share + bank by date
    by_date = defaultdict(list)
    for m in elite:
        by_date[m["date"]].append(m)
    drift = {}
    for d in sorted(by_date):
        ms = by_date[d]
        top_h = Counter((m["hashes"] or {}).get("stream_h100") for m in ms).most_common(3)
        drift[d] = {"seats": len(ms),
                    "rating_med": sorted(m["rating"] for m in ms)[len(ms) // 2],
                    "top_h100": [[h, n] for h, n in top_h]}
    result["elite_drift_daily"] = drift

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(result, f, indent=1)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
