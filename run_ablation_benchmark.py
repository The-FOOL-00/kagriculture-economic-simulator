"""
=============================================================================
CAUSAL ABLATION BENCHMARK — runs ALL component ablations using the existing
tournament_engine.run_paired_tournament infrastructure.
=============================================================================
This uses FILE PATHS (not callables) to avoid the kaggle_environments
agents/ package scan issue.

Candidates:
  A = Control (slot4_control_frozen_v2.py)
  B = Emergency Liquidity Only
  C = Batch 8 Only
  D = Frontrun Only  (from ablation_variants.py helper)
  F = Emergency + Batch 8  (from ablation_variants.py helper)
  G = Emergency + Frontrun  (from ablation_variants.py helper)
  H = Emergency + Dynamic Batch  (from ablation_variants.py helper)
  I = Full Predictive (hybrid_predictive_market.py)

Batch sweep: batches 4, 8, 12, 14, 18, 24 vs Control and vs Titan.
=============================================================================
"""
import sys, os, json, time, argparse, math, importlib.util as ilu
ROOT = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, ROOT)

from tournament_engine import run_paired_tournament

# ─── agent file registry ─────────────────────────────────────────────────────
def apath(filename):
    return os.path.join(ROOT, "agents", filename)

CANDIDATES = {
    "A_Control":        apath("slot4_control_frozen_v2.py"),
    "B_Emergency":      apath("ablation_b_emergency_only.py"),
    "C_Batch8":         apath("ablation_c_batch8_only.py"),
    "I_FullPredictive": apath("hybrid_predictive_market.py"),
}

# Batch sweep — generate standalone files for batches 4, 12, 18, 24
# (Batch 8 = C above, Batch 14 = A above)
def generate_batch_agent_file(batch_size):
    """Generate a batch-N standalone agent file from ablation_c_batch8_only.py template."""
    template_path = apath("ablation_c_batch8_only.py")
    out_path = apath(f"ablation_batch_{batch_size}.py")
    if os.path.exists(out_path): return out_path
    with open(template_path) as f: src = f.read()
    src = src.replace("SELL_BATCH = 8", f"SELL_BATCH = {batch_size}")
    src = src.replace("AblationC_Batch8Only", f"AblationBatch{batch_size}")
    src = src.replace("# === ONLY CHANGE: batch size = 8 ===", f"# === ONLY CHANGE: batch size = {batch_size} ===")
    with open(out_path, "w") as f: f.write(src)
    return out_path

BATCH_SIZES = [4, 8, 12, 14, 18, 24]

# ─── opponent registry ────────────────────────────────────────────────────────
def load_opponent_ecosystem():
    spec = ilu.spec_from_file_location("opp_eco", apath("opponent_ecosystem.py"))
    mod = ilu.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.OPPONENT_ECOSYSTEM

# ─── frontrun trigger distribution (diagnostic tool) ────────────────────────
def analyze_frontrun_distribution(n_seeds=50):
    """Count how often frontrun trigger fires across matches."""
    print("\n" + "="*60)
    print("FRONTRUN TRIGGER DISTRIBUTION ANALYSIS")
    print("="*60)

    spec = ilu.spec_from_file_location("ablation_d", apath("ablation_variants.py"))
    mod = ilu.module_from_spec(spec); spec.loader.exec_module(mod)
    _ControlBase = mod._ControlBase

    instance = _ControlBase(batch=14, emergency=False, frontrun=True, dynamic_batch=False)

    from kaggle_environments import make
    ctrl_spec = ilu.spec_from_file_location("ctrl", apath("slot4_control_frozen_v2.py"))
    ctrl_mod = ilu.module_from_spec(ctrl_spec); ctrl_spec.loader.exec_module(ctrl_mod)
    ctrl_fn = ctrl_mod.agent

    def challenger_fn(obs, cfg=None): return instance(obs, cfg)

    for seed in range(50000, 50000 + n_seeds):
        for swap in [False, True]:
            players = [challenger_fn, ctrl_fn] if not swap else [ctrl_fn, challenger_fn]
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
            try: env.run(players)
            except: pass

    dt = instance.dump_threat_log
    pd = instance.price_drop_log
    ft = instance.frontrun_trigger_count

    dt_nz = [x for x in dt if x > 0]
    pd_nz = [x for x in pd if x > 0]

    def pct(data, p):
        if not data: return 0
        s = sorted(data); return s[min(int(len(s)*p/100), len(s)-1)]

    print(f"\n  Turns logged: {len(dt)} | Non-zero dump threats: {len(dt_nz)} ({100*len(dt_nz)/max(1,len(dt)):.1f}%)")
    print(f"\n  DUMP THREAT DISTRIBUTION (when > 0):")
    for t in [2, 4, 6, 8, 12, 16]:
        ct = sum(1 for x in dt_nz if x >= t)
        print(f"    >= {t:2d}: {ct:5d} turns  ({100*ct/max(1,len(dt_nz)):.1f}%)")

    print(f"\n  PRICE DROP DISTRIBUTION (when > 0):")
    for t in [3, 5, 8, 10, 15, 20]:
        ct = sum(1 for x in pd_nz if x >= t)
        print(f"    >= ${t:2d}: {ct:5d} turns  ({100*ct/max(1,len(pd_nz)):.1f}%)")

    print(f"\n  P50 dump_threat={pct(dt_nz,50):.0f}  P75={pct(dt_nz,75):.0f}  P95={pct(dt_nz,95):.0f}")
    print(f"  P50 price_drop ={pct(pd_nz,50):.1f}  P75={pct(pd_nz,75):.1f}  P95={pct(pd_nz,95):.1f}")
    print(f"\n  CURRENT FRONTRUN FIRES: {ft} (threshold: >=12 units AND >=$15)")
    if ft == 0:
        print("  *** CONFIRMED: threshold never fires ***")
        print("  Estimated fires at alternative thresholds:")
        for dt_t, pd_t in [(4,8),(4,5),(6,10),(8,12)]:
            fires_est = sum(1 for i,x in enumerate(dt_nz) if x>=dt_t and i<len(pd_nz) and pd_nz[i]>=pd_t)
            print(f"    >= {dt_t} units AND >= ${pd_t}: ~{fires_est} fires")

    return {"dump_threat_log": dt[:300], "price_drop_log": pd[:300],
            "frontrun_triggers": ft, "dt_nz_count": len(dt_nz), "pd_nz_count": len(pd_nz)}

# ─── forecast baseline comparison ────────────────────────────────────────────
def analyze_forecast_baseline(n_seeds=30):
    """Compare naive (last price) vs analytical (reversion) forecast MAE."""
    print("\n" + "="*60)
    print("FORECAST BASELINE COMPARISON")
    print("="*60)

    from kaggle_environments import make
    spec = ilu.spec_from_file_location("ctrl", apath("slot4_control_frozen_v2.py"))
    mod = ilu.module_from_spec(spec); spec.loader.exec_module(mod)
    ctrl_fn = mod.agent

    PRODUCTS = ["MELON", "CARROT", "MILK", "WOOL"]
    BASE = {"MELON": 250, "CARROT": 35, "MILK": 160, "WOOL": 200}

    history = {p: [] for p in PRODUCTS}

    def tracker(obs, cfg=None):
        mkt = obs.get("market", {}) or {}
        prices = dict(mkt.get("prices", {}))
        s = obs.get("step", 0)
        for prod in PRODUCTS:
            p = prices.get(prod, 0)
            if p > 0: history[prod].append((s, p))
        return ctrl_fn(obs, cfg)

    for seed in range(50000, 50000 + n_seeds):
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        try: env.run([tracker, ctrl_fn])
        except: pass

    print(f"\n  {'Product':<12} {'N':>5} {'Naive MAE':>12} {'Analytic MAE':>14} {'Improv':>8}")
    print(f"  {'-'*55}")
    results = {}
    for prod in PRODUCTS:
        hist = history[prod]
        if len(hist) < 4: continue
        naive_e = []; analytic_e = []
        for i in range(1, len(hist)):
            actual = hist[i][1]; prev = hist[i-1][1]
            naive_e.append(abs(actual - prev))
            analytic_pred = prev * 0.92 + BASE[prod] * 0.08
            analytic_e.append(abs(actual - analytic_pred))
        nm = sum(naive_e)/len(naive_e); am = sum(analytic_e)/len(analytic_e)
        imp = (nm - am) / nm * 100
        sign = "✅" if imp > 5 else "—"
        print(f"  {prod:<12} {len(naive_e):>5} {nm:>12.2f} {am:>14.2f} {imp:>+7.1f}% {sign}")
        results[prod] = {"naive_mae": nm, "analytic_mae": am, "n": len(naive_e)}
    return results

# ─── catastrophic loss forensics ─────────────────────────────────────────────
def investigate_catastrophic_loss(seed=50040):
    print("\n" + "="*60)
    print(f"CATASTROPHIC LOSS FORENSICS — Seed {seed}")
    print("="*60)

    from kaggle_environments import make

    def load_fn(filename):
        spec = ilu.spec_from_file_location("_agent", apath(filename))
        mod = ilu.module_from_spec(spec); spec.loader.exec_module(mod)
        return mod.agent

    ctrl_fn  = load_fn("slot4_control_frozen_v2.py")
    emerg_fn = load_fn("ablation_b_emergency_only.py")
    full_fn  = load_fn("hybrid_predictive_market.py")
    batch8_fn = load_fn("ablation_c_batch8_only.py")

    scenarios = [
        ("Control (P0 vs ctrl)",  ctrl_fn,  ctrl_fn,  False),
        ("Control (P1 vs ctrl)",  ctrl_fn,  ctrl_fn,  True),
        ("Emergency (P0)",        emerg_fn, ctrl_fn,  False),
        ("Emergency (P1)",        emerg_fn, ctrl_fn,  True),
        ("Batch8 (P0)",           batch8_fn,ctrl_fn,  False),
        ("Batch8 (P1)",           batch8_fn,ctrl_fn,  True),
        ("Full Pred (P0)",        full_fn,  ctrl_fn,  False),
        ("Full Pred (P1)",        full_fn,  ctrl_fn,  True),
    ]

    print(f"\n  {'Scenario':<26} {'Cand $':>9} {'Ctrl $':>9} {'Margin':>9} {'Res':>5}")
    print(f"  {'-'*64}")

    cash_traces = {}
    for label, ch_fn, ct_fn, swap in scenarios:
        cfg = {"episodeSteps": 720, "seed": seed}
        env = make("kaggriculture", configuration=cfg, debug=False)
        players = [ch_fn, ct_fn] if not swap else [ct_fn, ch_fn]
        try:
            env.run(players)
            final = env.steps[-1]
            r0 = float(final[0].reward or 0); r1 = float(final[1].reward or 0)
            ch_cash = r0 if not swap else r1
            ct_cash = r1 if not swap else r0
            margin = ch_cash - ct_cash
            res = "WIN" if ch_cash > ct_cash else "LOSS"
            print(f"  {label:<26} {ch_cash:>9.0f} {ct_cash:>9.0f} {margin:>+9.0f} {res:>5}")
        except Exception as e:
            print(f"  {label:<26} ERROR: {str(e)[:30]}")

    # Cash trajectory for deepest forensics (Full Pred as P1)
    print(f"\n  CASH TRAJECTORY — Ctrl P0 vs Full Pred P1 (Seed {seed}):")
    print(f"  {'Step':>5}  {'Ctrl P0 $':>10}  {'Pred P1 $':>10}  {'Gap':>9}")
    ctrl_cash = []; pred_cash = []
    def t_ctrl(obs, cfg=None):
        p = obs.get("player", 0); farms = obs.get("farms", [])
        if farms and p < len(farms): ctrl_cash.append((obs.get("step",0), float(farms[p].get("money",0))))
        return ctrl_fn(obs, cfg)
    def t_pred(obs, cfg=None):
        p = obs.get("player", 0); farms = obs.get("farms", [])
        if farms and p < len(farms): pred_cash.append((obs.get("step",0), float(farms[p].get("money",0))))
        return full_fn(obs, cfg)
    env2 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    try:
        env2.run([t_ctrl, t_pred])
        paired = list(zip(ctrl_cash[::24], pred_cash[::24]))
        for (s0,c0),(s1,c1) in paired:
            print(f"  {s0:>5}  ${c0:>9.0f}  ${c1:>9.0f}  {c0-c1:>+9.0f}")
        # Find divergence point
        for i, ((s0,c0),(s1,c1)) in enumerate(zip(ctrl_cash, pred_cash)):
            if abs(c0-c1) > 300:
                print(f"\n  DIVERGENCE: step={s0}, gap=${c0-c1:+.0f}  (ctrl=${c0:.0f}, pred=${c1:.0f})")
                break
    except Exception as e:
        print(f"  Cash trace failed: {e}")

# ─── side asymmetry analysis ──────────────────────────────────────────────────
def analyze_side_asymmetry(n_seeds=60):
    print("\n" + "="*60)
    print("PLAYER-SIDE ASYMMETRY ANALYSIS")
    print("="*60)

    ctrl_path = apath("slot4_control_frozen_v2.py")
    full_path = apath("hybrid_predictive_market.py")

    p0_res = run_paired_tournament(full_path, ctrl_path, seeds=list(range(50000, 50000+n_seeds)), num_pairs=n_seeds, max_workers=4)
    all_results = p0_res.get("results", [])
    p0_wins = [r for r in all_results if not r["swapped"] and r["win"] == 1.0]
    p1_wins = [r for r in all_results if r["swapped"] and r["win"] == 1.0]
    p0_total = [r for r in all_results if not r["swapped"]]
    p1_total = [r for r in all_results if r["swapped"]]

    p0_wr = len(p0_wins) / max(1, len(p0_total))
    p1_wr = len(p1_wins) / max(1, len(p1_total))
    p0_margins = [r["margin"] for r in p0_total]
    p1_margins = [r["margin"] for r in p1_total]
    p0_mean = sum(p0_margins)/max(1,len(p0_margins))
    p1_mean = sum(p1_margins)/max(1,len(p1_margins))
    p0_worst = min(p0_margins) if p0_margins else 0
    p1_worst = min(p1_margins) if p1_margins else 0

    print(f"\n  P0 (Predictive as Player 0): WR={p0_wr*100:.1f}%  Mean=${p0_mean:+.0f}  Worst=${p0_worst:+.0f}")
    print(f"  P1 (Predictive as Player 1): WR={p1_wr*100:.1f}%  Mean=${p1_mean:+.0f}  Worst=${p1_worst:+.0f}")
    print(f"  Asymmetry Delta:             {(p0_wr-p1_wr)*100:+.1f}pp  Mean gap: ${p0_mean-p1_mean:+.0f}")
    if abs(p0_wr-p1_wr) > 0.10:
        print(f"  *** STRONG ASYMMETRY: {abs(p0_wr-p1_wr)*100:.1f}pp — investigate farm layout ***")
    else:
        print(f"  Side asymmetry is within normal range.")

    return {"p0_wr": p0_wr, "p1_wr": p1_wr, "p0_mean": p0_mean, "p1_mean": p1_mean,
            "p0_worst": p0_worst, "p1_worst": p1_worst, "asymmetry_pp": (p0_wr-p1_wr)*100}

# ─── main ablation suite ──────────────────────────────────────────────────────
def run_main_ablation(seeds, workers=4):
    print("\n" + "="*70)
    print("MAIN ABLATION SUITE — All Candidates vs Control V2 (paired)")
    print("="*70)

    ctrl_path = apath("slot4_control_frozen_v2.py")
    all_stats = {}

    for name, cpath in CANDIDATES.items():
        if name == "A_Control": continue
        print(f"\n>>> {name}")
        stats = run_paired_tournament(cpath, ctrl_path, seeds=seeds, num_pairs=len(seeds), max_workers=workers)
        all_stats[name] = stats
        r = stats; rr = r.get("results", [])
        p0 = [x for x in rr if not x["swapped"]]; p1 = [x for x in rr if x["swapped"]]
        p0_wr = sum(1 for x in p0 if x["win"]==1.0)/max(1,len(p0))
        p1_wr = sum(1 for x in p1 if x["win"]==1.0)/max(1,len(p1))
        sign = "✅" if r["win_rate"] > 50 else "⚠️" if r["win_rate"] > 45 else "❌"
        print(f"  {sign} WR: {r['win_rate']:.1f}%  CI:[{r['ci_95'][0]:.1f}%,{r['ci_95'][1]:.1f}%]"
              f"  P0={p0_wr*100:.1f}%  P1={p1_wr*100:.1f}%"
              f"  Margin:{r['margin']:+.0f}  Worst:{r['worst_drawdown']:+.0f}"
              f"  Catas:{r['catastrophic_losses']}")

    return all_stats

# ─── batch sweep ──────────────────────────────────────────────────────────────
def run_batch_sweep(seeds, workers=4):
    print("\n" + "="*70)
    print("BATCH SIZE SWEEP (paired) — vs Control and vs Titan")
    print("="*70)

    ctrl_path = apath("slot4_control_frozen_v2.py")
    eco = load_opponent_ecosystem()
    titan_key = next((k for k in eco if "titan" in k.lower() or "Titan" in k), None)
    titan_path = eco.get(titan_key) if titan_key else None

    batch_stats = {}
    for b in BATCH_SIZES:
        bpath = generate_batch_agent_file(b)
        stats_ctrl = run_paired_tournament(bpath, ctrl_path, seeds=seeds, num_pairs=len(seeds), max_workers=workers)
        r = stats_ctrl
        sign = "✅" if r["win_rate"] > 50 else "⚠️"
        print(f"  Batch {b:2d} vs Ctrl: WR={r['win_rate']:5.1f}%  CI:[{r['ci_95'][0]:.1f},{r['ci_95'][1]:.1f}]  Margin:{r['margin']:+.0f}")
        batch_stats[f"batch_{b}_vs_ctrl"] = {k:v for k,v in r.items() if k != "results"}

        if titan_path:
            stats_titan = run_paired_tournament(bpath, titan_path, seeds=seeds[:40], num_pairs=40, max_workers=workers)
            r2 = stats_titan
            print(f"  Batch {b:2d} vs Titan: WR={r2['win_rate']:5.1f}%  CI:[{r2['ci_95'][0]:.1f},{r2['ci_95'][1]:.1f}]  Margin:{r2['margin']:+.0f}")
            batch_stats[f"batch_{b}_vs_titan"] = {k:v for k,v in r2.items() if k != "results"}

    return batch_stats

# ─── attribution table ────────────────────────────────────────────────────────
def print_attribution_table(all_stats):
    print("\n" + "="*80)
    print("COMPONENT ATTRIBUTION TABLE")
    print("="*80)
    print(f"  {'Candidate':<24} {'WR%':>6} {'CI Low':>7} {'CI Hi':>7} {'Margin':>9} {'Worst':>9} {'Catas':>6}")
    print(f"  {'-'*76}")
    for name, s in all_stats.items():
        if "win_rate" not in s: continue
        wr  = s["win_rate"]
        lo, hi = s.get("ci_95", (0,0))
        mm  = s.get("margin", s.get("mean_margin", 0))
        wl  = s.get("worst_drawdown", s.get("worst_loss", 0))
        cat = s.get("catastrophic_losses", 0)
        sign = "✅" if wr > 52 else "⚠️" if wr > 48 else "❌"
        print(f"  {sign} {name:<22} {wr:>5.1f}% {lo:>6.1f}% {hi:>6.1f}% {mm:>+9.0f} {wl:>+9.0f} {cat:>5}")

# ─── main entry ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick",     action="store_true", help="50 seeds (fast)")
    parser.add_argument("--forensics", action="store_true", help="Catastrophic seed only")
    parser.add_argument("--frontrun",  action="store_true", help="Frontrun distribution only")
    parser.add_argument("--forecast",  action="store_true", help="Forecast baseline only")
    parser.add_argument("--batch",     action="store_true", help="Batch sweep only")
    parser.add_argument("--asymmetry", action="store_true", help="Side asymmetry only")
    parser.add_argument("--full",      action="store_true", help="Run all experiments")
    parser.add_argument("--seeds",     type=int, default=100)
    parser.add_argument("--workers",   type=int, default=4)
    args = parser.parse_args()

    seeds = list(range(50000, 50000 + args.seeds))
    if args.quick: seeds = seeds[:50]

    print("="*70)
    print("CAUSAL ABLATION BENCHMARK — Kaggriculture Component Attribution")
    print("="*70)
    print(f"Seeds: {len(seeds)} ({seeds[0]}-{seeds[-1]}) | Workers: {args.workers}")

    all_stats = {}
    run_all = args.full or not any([args.forensics, args.frontrun, args.forecast, args.batch, args.asymmetry])

    if args.forensics or run_all:
        investigate_catastrophic_loss()

    if args.frontrun or run_all:
        fr = analyze_frontrun_distribution(n_seeds=min(50, len(seeds)))
        all_stats["frontrun"] = fr

    if args.forecast or run_all:
        fc = analyze_forecast_baseline(n_seeds=min(30, len(seeds)))
        all_stats["forecast"] = fc

    if args.asymmetry or run_all:
        asy = analyze_side_asymmetry(n_seeds=min(60, len(seeds)))
        all_stats["side_asymmetry"] = asy

    if run_all or not any([args.forensics, args.frontrun, args.forecast, args.batch, args.asymmetry]):
        main_stats = run_main_ablation(seeds, workers=args.workers)
        all_stats.update(main_stats)

    if args.batch or run_all:
        batch_stats = run_batch_sweep(seeds, workers=args.workers)
        all_stats["batch_sweep"] = batch_stats

    if all_stats:
        print_attribution_table(all_stats)

    # Save
    out = os.path.join(ROOT, "ablation_results.json")
    safe = {}
    for k, v in all_stats.items():
        if isinstance(v, dict):
            safe[k] = {kk: vv for kk, vv in v.items() if kk not in ("results",) and not isinstance(vv, list)}
        else:
            safe[k] = v
    with open(out, "w") as f: json.dump(safe, f, indent=2, default=str)
    print(f"\nResults saved: {out}")

if __name__ == "__main__":
    main()
