import os, sys
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import copy
import numpy as np
from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v44_economic_portfolio.main import V44CandidateController
from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v32_rlx2.opponents import load_league_opponent
from research.v45.counterfactual.market_search import SEARCH_SEEDS, OPPONENTS, _act

BASE_PRICES = {"STRAWBERRY": 120, "MILK": 160, "WOOL": 200, "MELON": 250}

class V45AdaptiveScarcityController:
    """Adaptive market intelligence controller.
    Uses observable town shops and spot prices to adaptively size sell tranches:
    - If price >= base price (high value): sell 60%
    - If price < base price (depressed): sell 40% (preserving stock for recovery)
    - Fallback: exactly 50% (identical to V44)
    """
    def __init__(self):
        self.v35 = V35OpeningController()

    def reset(self):
        self.v35.reset()

    def act(self, obs, cfg=None):
        base_act = self.v35.act(obs, cfg)
        step = int(obs.get("step", 0) or 0)
        if step < 520:
            return base_act

        try:
            private = obs.get("private", {}) or {}
            shed = dict(private.get("shed", {}) or {})
            act = copy.deepcopy(base_act)
            mkt = act.setdefault("market", [])

            if step >= 520:
                mkt = [o for o in mkt if not (len(o) > 0 and o[0] in ("BUY_ANIMAL", "BUY_LAND"))]

            if step < 690:
                act["market"] = mkt[:10]
                return act

            marketable = ("STRAWBERRY", "MILK", "WOOL", "MELON")
            already = {o[1] for o in mkt if len(o) > 1 and o[0] == "SELL"}
            prices = obs.get("market", {}).get("prices", {}) or {}

            # Window 1: Step 693-694 Pre-emption
            if step in (693, 694):
                for item in marketable:
                    qty = shed.get(item, 0)
                    if qty >= 2 and item not in already and len(mkt) < 10:
                        cur_p = prices.get(item, BASE_PRICES[item])
                        base_p = BASE_PRICES[item]
                        if cur_p >= base_p:
                            pct = 0.55
                        else:
                            pct = 0.45
                        sell_qty = max(1, int(round(qty * pct)))
                        mkt.append(["SELL", item, sell_qty])
                        already.add(item)

            # Window 2: Step 704-705 Secondary Recovery
            elif step in (704, 705):
                for item in marketable:
                    qty = shed.get(item, 0)
                    if qty >= 2 and item not in already and len(mkt) < 10:
                        sell_qty = max(1, qty // 2)
                        mkt.append(["SELL", item, sell_qty])
                        already.add(item)

            # Window 3: Step >= 716 Final Flush
            elif step >= 716:
                for item in marketable:
                    qty = shed.get(item, 0)
                    if qty > 0 and item not in already and len(mkt) < 10:
                        mkt.append(["SELL", item, qty])
                        already.add(item)

            act["market"] = mkt[:10]
            return act
        except Exception:
            return base_act

opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}

deltas = []
margin_deltas = []
cas = 0
res = 0

for seed in SEARCH_SEEDS:
    for opp_id in OPPONENTS:
        for seat in [0, 1]:
            # V44
            sim_v = FastKagricultureSim(seed=seed)
            v44 = V44CandidateController()
            opp_v = copy.deepcopy(opp_masters[opp_id])
            ov0, ov1 = sim_v.reset(seed=seed)
            while not sim_v.done:
                [ov0, ov1], _, _, _ = sim_v.step([_act(v44, ov0), opp_v(ov1)] if seat == 0 else [opp_v(ov0), _act(v44, ov1)])
            v_cash = float(ov0['farms'][0]['money'] if seat == 0 else ov1['farms'][1]['money'])
            vo_cash = float(ov1['farms'][1]['money'] if seat == 0 else ov0['farms'][0]['money'])
            v_win = v_cash > vo_cash

            # Adaptive
            sim_c = FastKagricultureSim(seed=seed)
            cand = V45AdaptiveScarcityController()
            opp_c = copy.deepcopy(opp_masters[opp_id])
            oc0, oc1 = sim_c.reset(seed=seed)
            while not sim_c.done:
                [oc0, oc1], _, _, _ = sim_c.step([_act(cand, oc0), opp_c(oc1)] if seat == 0 else [opp_c(oc0), _act(cand, oc1)])
            c_cash = float(oc0['farms'][0]['money'] if seat == 0 else oc1['farms'][1]['money'])
            co_cash = float(oc1['farms'][1]['money'] if seat == 0 else oc0['farms'][0]['money'])
            c_win = c_cash > co_cash

            cd = c_cash - v_cash
            md = (c_cash - co_cash) - (v_cash - vo_cash)
            deltas.append(cd)
            margin_deltas.append(md)
            if v_win and not c_win:
                cas += 1
                print(f"CASUALTY on Seed {seed} vs {opp_id} Seat {seat}: V44 {v_cash} vs opp {vo_cash} | Cand {c_cash}")
            if not v_win and c_win:
                res += 1
                print(f"RESCUE on Seed {seed} vs {opp_id} Seat {seat}!")

print(f"Adaptive vs V44 across {len(deltas)} legs:")
print(f"Mean Cash Delta: ${np.mean(deltas):>+7.2f}")
print(f"Median Cash Delta: ${np.median(deltas):>+7.2f}")
print(f"Mean Margin Delta: ${np.mean(margin_deltas):>+7.2f}")
print(f"Casualties: {cas} | Rescues: {res}")
print(f"Positive Hit Rate: {np.mean(np.array(deltas) > 0)*100:.1f}%")
print(f"Min Delta: ${np.min(deltas):>+7.2f} | Max Delta: ${np.max(deltas):>+7.2f}")
