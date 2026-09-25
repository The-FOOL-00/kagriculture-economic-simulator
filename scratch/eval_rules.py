import sys, os
sys.path.insert(0, os.path.abspath("."))
from candidates.v35_a7_opening.main import V35OpeningController
from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v32_rlx2.opponents import load_league_opponent
import numpy as np

SEEDS = [249685, 249686, 249687, 249688]
OPPS = ['E8_DMITRII', 'E2_A7', 'E0_V3', 'SYN_AGG']
opp_masters = {o: load_league_opponent(o) for o in OPPS}

def eval_policy(sell_rule):
    deltas = []
    for s in SEEDS:
        for o in OPPS:
            # Baseline V35
            sim_b = FastKagricultureSim(seed=s)
            v35 = V35OpeningController()
            ob0, ob1 = sim_b.reset(seed=s)
            while not sim_b.done:
                [ob0, ob1], _, _, _ = sim_b.step([v35.act(ob0), opp_masters[o](ob1)])
            b_cash = ob0['farms'][0]['money']

            # Candidate
            sim_c = FastKagricultureSim(seed=s)
            v35_c = V35OpeningController()
            oc0, oc1 = sim_c.reset(seed=s)
            while not sim_c.done:
                step = int(oc0['step'])
                act = v35_c.act(oc0)
                mkt = act.setdefault('market', [])
                shed = oc0.get('private', {}).get('shed', {})
                prices = oc0.get('market', {}).get('prices', {})

                sell_rule(step, shed, prices, mkt)
                act['market'] = mkt[:10]
                [oc0, oc1], _, _, _ = sim_c.step([act, opp_masters[o](oc1)])
            c_cash = oc0['farms'][0]['money']
            deltas.append(c_cash - b_cash)
    return float(np.mean(deltas)), float(np.median(deltas))

# Rule 1: Pure V43 Terminal Flush (40% @ 694, 60% @ 705, 100% @ 716)
def rule_v43(step, shed, prices, mkt):
    if step in (693, 694):
        for item in ('STRAWBERRY', 'MILK', 'WOOL', 'MELON'):
            q = shed.get(item, 0)
            if q >= 2: mkt.append(['SELL', item, max(1, int(round(q * 0.40)))])
    elif step in (704, 705):
        for item in ('STRAWBERRY', 'MILK', 'WOOL', 'MELON'):
            q = shed.get(item, 0)
            if q >= 2: mkt.append(['SELL', item, max(1, int(round(q * 0.60)))])
    elif step >= 716:
        for item in ('STRAWBERRY', 'MILK', 'WOOL', 'MELON'):
            q = shed.get(item, 0)
            if q > 0: mkt.append(['SELL', item, q])

# Rule 2: V43 + Extreme Price Spike Selling (> $200)
def rule_spike200(step, shed, prices, mkt):
    rule_v43(step, shed, prices, mkt)
    if step < 680 and step % 4 == 0:
        for item in ('STRAWBERRY', 'MILK', 'WOOL'):
            if float(prices.get(item, 0)) >= 200.0 and shed.get(item, 0) >= 3:
                mkt.append(['SELL', item, 1])

# Rule 3: V43 + Pre-Terminal (Steps 650-680) Scarcity Selling
def rule_late_scarcity(step, shed, prices, mkt):
    rule_v43(step, shed, prices, mkt)
    if 650 <= step < 680 and step % 4 == 0:
        for item in ('STRAWBERRY', 'MILK', 'WOOL'):
            if shed.get(item, 0) >= 4:
                mkt.append(['SELL', item, 1])

m_v43, med_v43 = eval_policy(rule_v43)
m_spk, med_spk = eval_policy(rule_spike200)
m_late, med_late = eval_policy(rule_late_scarcity)

print(f"Rule V43 (Staggered Flush):      Mean +{m_v43:.2f} | Med +{med_v43:.2f}")
print(f"Rule Spike > 200:                 Mean +{m_spk:.2f} | Med +{med_spk:.2f}")
print(f"Rule Late Scarcity (650-680):     Mean +{m_late:.2f} | Med +{med_late:.2f}")
