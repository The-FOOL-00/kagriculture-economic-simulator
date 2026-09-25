import sys, os
sys.path.insert(0, os.path.abspath("."))
from candidates.v35_a7_opening.main import V35OpeningController
from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v32_rlx2.opponents import load_league_opponent
import numpy as np

SEEDS = [249685, 249686, 249687, 249688]
OPPS = ['E8_DMITRII', 'E2_A7', 'E0_V3', 'SYN_AGG']
opp_masters = {o: load_league_opponent(o) for o in OPPS}

def eval_candidate(wash_qty, t1, f1, t2, f2, t3):
    deltas = []
    cas = 0
    for s in SEEDS:
        for o in OPPS:
            # Baseline V35
            sim_b = FastKagricultureSim(seed=s)
            v35 = V35OpeningController(wash_buy=25, wash_sell=25)
            ob0, ob1 = sim_b.reset(seed=s)
            while not sim_b.done:
                [ob0, ob1], _, _, _ = sim_b.step([v35.act(ob0), opp_masters[o](ob1)])
            b_cash = ob0['farms'][0]['money']
            b_win = b_cash > ob1['farms'][1]['money']

            # Candidate
            sim_c = FastKagricultureSim(seed=s)
            v35_c = V35OpeningController(wash_buy=wash_qty, wash_sell=wash_qty)
            oc0, oc1 = sim_c.reset(seed=s)
            while not sim_c.done:
                step = int(oc0['step'])
                act = v35_c.act(oc0)
                mkt = act.setdefault('market', [])
                shed = oc0.get('private', {}).get('shed', {})

                if step == t1:
                    for item in ('STRAWBERRY', 'MILK', 'WOOL', 'MELON'):
                        q = shed.get(item, 0)
                        if q >= 2: mkt.append(['SELL', item, max(1, int(round(q * f1)))])
                elif step == t2:
                    for item in ('STRAWBERRY', 'MILK', 'WOOL', 'MELON'):
                        q = shed.get(item, 0)
                        if q >= 2: mkt.append(['SELL', item, max(1, int(round(q * f2)))])
                elif step >= t3:
                    for item in ('STRAWBERRY', 'MILK', 'WOOL', 'MELON'):
                        q = shed.get(item, 0)
                        if q > 0: mkt.append(['SELL', item, q])

                act['market'] = mkt[:10]
                [oc0, oc1], _, _, _ = sim_c.step([act, opp_masters[o](oc1)])
            c_cash = oc0['farms'][0]['money']
            c_win = c_cash > oc1['farms'][1]['money']
            if b_win and not c_win: cas += 1
            deltas.append(c_cash - b_cash)
    return float(np.mean(deltas)), float(np.median(deltas)), cas

print("Evaluating wash and timing variations...")
# Baseline V43: wash 25, 694 40%, 705 60%, 716 100%
m0, med0, c0 = eval_candidate(25, 694, 0.40, 705, 0.60, 716)
print(f"V43 Baseline (25, 694-40%, 705-60%, 716-100%): Mean +{m0:.2f} | Med +{med0:.2f} | Cas: {c0}")

# Variation 1: 50% at 694, 70% at 705
m1, med1, c1 = eval_candidate(25, 694, 0.50, 705, 0.70, 716)
print(f"Var 1 (25, 694-50%, 705-70%, 716-100%):        Mean +{m1:.2f} | Med +{med1:.2f} | Cas: {c1}")

# Variation 2: Wash 26
m2, med2, c2 = eval_candidate(26, 694, 0.50, 705, 0.70, 716)
print(f"Var 2 (26, 694-50%, 705-70%, 716-100%):        Mean +{m2:.2f} | Med +{med2:.2f} | Cas: {c2}")

# Variation 3: 50% at 694, 100% at 705 (V42 style flush)
m3, med3, c3 = eval_candidate(25, 694, 0.50, 705, 1.00, 716)
print(f"Var 3 (25, 694-50%, 705-100%, 716-100%):       Mean +{m3:.2f} | Med +{med3:.2f} | Cas: {c3}")
