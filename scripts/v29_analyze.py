# SPDX-License-Identifier: MIT
"""V29 Phases 8-11: lock raw results, emit paired CSV, compute six gates
and the absolute-level decomposition.

Reads results/v29_raw_results.jsonl (frozen tournament output, 160 rows).
Writes results/v29_paired_results.csv, results/v29_gate_stats.json,
results/v29_decomposition.csv, results/v29_decomposition_stats.json.
Gate math EXACTLY per V29_PREREGISTRATION.md s2 (copied from V28);
decomposition EXACTLY per V29_ABSOLUTE_LEVEL_SPEC.md.
"""

import csv
import hashlib
import json
import os
import statistics
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(REPO_ROOT, "results", "v29_raw_results.jsonl")
CSV = os.path.join(REPO_ROOT, "results", "v29_paired_results.csv")
STATS = os.path.join(REPO_ROOT, "results", "v29_gate_stats.json")
DECOMP_CSV = os.path.join(REPO_ROOT, "results", "v29_decomposition.csv")
DECOMP_STATS = os.path.join(REPO_ROOT, "results", "v29_decomposition_stats.json")

A7_SHA = "18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9"
V3_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
SIM = {"p3_adapter": "ce8169e95e86bd338b32dada48ba3fa0216bdeea4cebdd34a0264fe18a9f5195",
       "v3_adapter": "a0a9fd2c2ce1abe2de7e871e7fd9deec647df9863179c19cf1b94fc5ed2e3135",
       "interface": "1a1c5ec7cbc097c13d60eeed98ed98749f11cad7456c368366513dc7eeda4091",
       "utils": "53f9277406162cf1789d5dceb944f147ead85d65d52647350533a1c1c7684404",
       "config": "14c3a22c0141b770efe43244afe77f7ed27064e0256bdb9f8b40750e3b2eabae"}
A7_FLAGS = {"call_v3_at_step0": True, "open_units": 30,
            "dispatch": False, "rewrite_step0_wash": True}
SEEDS = list(range(340050, 340090))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tcrit95(df=39):
    try:
        from scipy.stats import t as tdist
        return float(tdist.ppf(0.975, df))
    except ImportError:
        return 2.0227  # t(0.975, df=39)


def main():
    recs = [json.loads(l) for l in open(RAW) if l.strip()]
    assert len(recs) == 160, len(recs)
    assert len({r["key"] for r in recs}) == 160, "duplicate keys!"
    seeds = sorted({r["seed"] for r in recs})
    assert seeds == SEEDS, (seeds[:3], seeds[-3:])
    assert all(r["seed"] < 340090 for r in recs), "remainder touched!"
    arms = {}
    for r in recs:
        arms.setdefault(r["arm"], []).append(r)
        assert r["a7_digest"] == A7_SHA, r["key"]
        assert r["v3_digest"] == V3_SHA, r["key"]
        assert r["sim_digest"] == SIM, r["key"]
        assert r["engine_version"] == "1.32.7", r["key"]
    assert sorted(arms) == ["A1", "A2", "A3", "A4"], sorted(arms)
    for a in arms:
        assert len(arms[a]) == 40, (a, len(arms[a]))
        assert sorted(r["seed"] for r in arms[a]) == SEEDS
    # Rewrite integrity: A7 instances in A1/A2/A3 all deployed.
    for a in ("A1", "A2", "A3"):
        for r in arms[a]:
            assert r["cand_flags"] == A7_FLAGS, r["key"]
            assert all(r["step0_rewritten"]), r["key"]
            assert not any(r["step0_unexpected_shape"]), r["key"]
    pids = {r["pid"] for r in recs}
    nonces = {r["worker_nonce"] for r in recs}
    print("integrity: n=160 rewrite OK pids=%d nonces=%d" % (len(pids), len(nonces)))

    # ---- Primary: Arms 1+2 (80 paired deltas) ----
    prim = sorted(arms["A1"] + arms["A2"], key=lambda r: (r["seed"], r["arm"]))
    ds = [r["delta"] for r in prim]
    mean = statistics.mean(ds)
    median = statistics.median(ds)
    sd = statistics.stdev(ds)
    w = sum(1 for d in ds if d > 0)
    l = sum(1 for d in ds if d < 0)
    t = sum(1 for d in ds if d == 0)
    posrate = w / len(ds)
    by_seed = {}
    for r in prim:
        by_seed.setdefault(r["seed"], []).append(r["delta"])
    ms = [statistics.mean(v) for v in by_seed.values()]
    assert len(ms) == 40
    mse_mean = statistics.mean(ms)
    mse_sd = statistics.stdev(ms)
    se = mse_sd / (40 ** 0.5)
    tc = tcrit95(39)
    ci_lo, ci_hi = mse_mean - tc * se, mse_mean + tc * se
    seed_pos = sum(1 for m in ms if m > 0)
    mn, mx = min(ds), max(ds)
    qs = statistics.quantiles(ds, n=100)
    q05, q25, q75, q95 = qs[4], qs[24], qs[74], qs[94]
    s0 = [r["delta"] for r in prim if r["arm"] == "A1"]
    s1 = [r["delta"] for r in prim if r["arm"] == "A2"]
    seat_diff = [by_seed[s][0] - by_seed[s][1] for s in by_seed]
    tot = sum(ds)
    contrib = sorted(((abs(sum(v)), s) for s, v in by_seed.items()), reverse=True)
    top1_share = contrib[0][0] / abs(tot) if tot else float("nan")
    top3_share = sum(c[0] for c in contrib[:3]) / abs(tot) if tot else float("nan")
    top5_share = sum(c[0] for c in contrib[:5]) / abs(tot) if tot else float("nan")
    no_max = (tot - mx) / (len(ds) - 1)
    no_min = (tot - mn) / (len(ds) - 1)
    trimmed = statistics.mean(sorted(ds)[4:-4])
    import random
    rng = random.Random(29)
    boots = sorted(statistics.mean([rng.choice(ms) for _ in range(40)])
                   for _ in range(10000))
    boot_ci = [boots[250], boots[9749]]
    try:
        from scipy.stats import wilcoxon
        wil_p = float(wilcoxon(ds).pvalue)
    except ImportError:
        wil_p = None
    w500 = sum(1 for d in ds if d > 500)
    l500 = sum(1 for d in ds if d < -500)
    t500 = 80 - w500 - l500

    gates = {
        "gate1_mean_gt_0": {"value": mean, "pass": mean > 0},
        "gate2_median_gt_0": {"value": median, "pass": median > 0},
        "gate3_posrate_gt_50": {"value": posrate, "wins": w, "n": 80,
                                "pass": posrate > 0.50},
        "gate4_wins_gt_losses": {"wins": w, "losses": l, "ties": t,
                                 "pass": w > l},
        "gate5_seed_ci_positive": {"ci": [ci_lo, ci_hi], "tcrit": tc,
                                   "seed_mean": mse_mean, "seed_sd": mse_sd,
                                   "pass": ci_lo > 0},
        "gate6_tail_floor": {"min": mn, "pass": mn > -10000},
    }
    stats = {
        "n_matches": 80, "n_seeds": 40, "mean": mean, "median": median,
        "sd": sd, "se_match": sd / (80 ** 0.5), "min": mn, "max": mx,
        "q05": q05, "q25": q25, "q75": q75, "q95": q95,
        "wlt_exact": [w, l, t], "wlt_500": [w500, l500, t500],
        "posrate_match": posrate, "seed_pos_rate": seed_pos / 40,
        "seed_pos_count": seed_pos, "seed_ci95": [ci_lo, ci_hi],
        "seed_mean": mse_mean, "seed_sd": mse_sd,
        "seat0_mean": statistics.mean(s0), "seat1_mean": statistics.mean(s1),
        "seat0_median": statistics.median(s0),
        "seat1_median": statistics.median(s1),
        "seat_diff_max_abs": max(abs(d) for d in seat_diff),
        "seat_identical": sum(1 for d in seat_diff if d == 0),
        "top1_seed_share": top1_share, "top3_seed_share": top3_share,
        "top5_seed_share": top5_share,
        "top_contributors": [(s, c) for c, s in contrib[:5]],
        "tail_dependent_overlay": top1_share > 0.50,
        "mean_excl_max": no_max, "mean_excl_min": no_min,
        "trimmed_mean_5pct": trimmed,
        "bootstrap_ci95_secondary": boot_ci, "wilcoxon_p_secondary": wil_p,
        "gates": gates, "all_gates_pass": all(g["pass"] for g in gates.values()),
        "raw_sha256": sha256_file(RAW),
    }
    with open(CSV, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["seed", "arm", "seat", "cand", "base", "cand_reward",
                     "base_reward", "delta", "winner", "action_digest",
                     "money_digest", "state_digest", "step0_rewritten",
                     "pid", "mode"])
        for r in sorted(recs, key=lambda r: (r["seed"], r["arm"])):
            wr.writerow([r["seed"], r["arm"], r["seat"], r["cand"], r["base"],
                         r["cand_reward"], r["base_reward"], r["delta"],
                         r["winner"], r["action_digest"], r["money_digest"],
                         r["state_digest"], r["step0_rewritten"], r["pid"],
                         r["mode"]])
    stats["csv_sha256"] = sha256_file(CSV)
    with open(STATS, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    # ---- Decomposition: all four arms (spec s2-s5) ----
    a1 = {r["seed"]: r for r in arms["A1"]}
    a2 = {r["seed"]: r for r in arms["A2"]}
    a3 = {r["seed"]: r for r in arms["A3"]}
    a4 = {r["seed"]: r for r in arms["A4"]}
    rows = []
    for s in SEEDS:
        a0, v1p = a1[s]["seat0_reward"], a1[s]["seat1_reward"]
        v0p, a1c = a2[s]["seat0_reward"], a2[s]["seat1_reward"]
        A0, A1c = a3[s]["seat0_reward"], a3[s]["seat1_reward"]
        V0, V1 = a4[s]["seat0_reward"], a4[s]["seat1_reward"]
        d0, d1 = a0 - v1p, a1c - v0p
        m = (d0 + d1) / 2
        LA, LV = (A0 + A1c) / 2, (V0 + V1) / 2
        C = LA - LV
        E = m - C
        assert abs((C + E) - m) < 1e-6
        Abar = (a0 + a1c) / 2
        Vbar = (v0p + v1p) / 2
        OA, OV = Abar - LA, LV - Vbar
        assert abs((OA + OV) - E) < 1e-6
        C0, C1 = A0 - V0, A1c - V1
        assert abs(((C0 + C1) / 2) - C) < 1e-6
        rows.append({"seed": s, "d0": d0, "d1": d1, "m": m,
                     "A0": A0, "A1": A1c, "V0": V0, "V1": V1,
                     "L_A": LA, "L_V": LV, "CREATE": C, "EXTRACT": E,
                     "O_A": OA, "O_V": OV, "C_0": C0, "C_1": C1,
                     "G_V": V0 - V1, "G_A": A0 - A1c,
                     "P_AA": A0 + A1c, "P_VV": V0 + V1,
                     "P_AV0": a0 + v1p, "P_AV1": a1c + v0p})
    Cs = [r["CREATE"] for r in rows]
    Es = [r["EXTRACT"] for r in rows]
    LAs = [r["L_A"] for r in rows]
    LVs = [r["L_V"] for r in rows]
    Cbar = statistics.mean(Cs)
    Csd = statistics.stdev(Cs)
    Cse = Csd / (40 ** 0.5)
    C_ci = [Cbar - tc * Cse, Cbar + tc * Cse]
    Ebar = statistics.mean(Es)
    Esd = statistics.stdev(Es)
    Ese = Esd / (40 ** 0.5)
    E_ci = [Ebar - tc * Ese, Ebar + tc * Ese]
    C0s = [r["C_0"] for r in rows]
    C1s = [r["C_1"] for r in rows]

    def q(v):
        x = statistics.quantiles(v, n=100)
        return {"min": min(v), "q05": x[4], "q25": x[24],
                "median": statistics.median(v), "q75": x[74],
                "q95": x[94], "max": max(v)}

    dstats = {
        "n_seeds": 40,
        "M_head_to_head": mse_mean,
        "Cbar_create": Cbar, "C_sd": Csd, "C_ci95": C_ci,
        "C_median": statistics.median(Cs),
        "C_seed_positive": sum(1 for c in Cs if c > 0),
        "C_quantiles": q(Cs),
        "Ebar_extract": Ebar, "E_sd": Esd, "E_ci95": E_ci,
        "E_median": statistics.median(Es),
        "extract_share": (Ebar / mse_mean) if mse_mean > 0 else None,
        "create_share": (Cbar / mse_mean) if mse_mean > 0 else None,
        "catastrophic_weakness_veto": bool(Cbar < 0 and C_ci[1] < 0),
        "outcome_b_pattern": bool(Cbar <= 0 or (mse_mean > 0 and Ebar / mse_mean >= 0.50)),
        "L_A": {"mean": statistics.mean(LAs), "sd": statistics.stdev(LAs),
                "quantiles": q(LAs)},
        "L_V": {"mean": statistics.mean(LVs), "sd": statistics.stdev(LVs),
                "quantiles": q(LVs)},
        "C0_mean": statistics.mean(C0s), "C1_mean": statistics.mean(C1s),
        "C0_median": statistics.median(C0s), "C1_median": statistics.median(C1s),
        "G_V_nonzero": sum(1 for r in rows if r["G_V"] != 0),
        "G_A_nonzero": sum(1 for r in rows if r["G_A"] != 0),
    }
    with open(DECOMP_CSV, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    dstats["decomp_csv_sha256"] = sha256_file(DECOMP_CSV)
    with open(DECOMP_STATS, "w", encoding="utf-8") as f:
        json.dump(dstats, f, indent=1)
    print(json.dumps({k: v for k, v in stats.items()
                      if k not in ("gates", "top_contributors")}, indent=1))
    print("GATES:", {k: (v["pass"], v.get("value", v.get("ci", v.get("min"))))
                     for k, v in gates.items()})
    print("DECOMP: Cbar=%+.2f CI=[%+.1f,%+.1f] Ebar=%+.2f share=%s veto=%s" % (
        Cbar, C_ci[0], C_ci[1], Ebar, dstats["extract_share"],
        dstats["catastrophic_weakness_veto"]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
