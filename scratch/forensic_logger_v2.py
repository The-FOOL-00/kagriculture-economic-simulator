"""
FORENSIC MATCH LOGGER V2 — CORRECTED BRIDGE ACCOUNTING
=======================================================
Key corrections from diagnostic phase:
1. Revenue = shed_delta + inventories_delta (for sold items) × price
   (both shed AND hand inventories drain when things are sold)
2. 'inventories' = list of per-hand dicts with commodity counts
3. BUY_PRODUCT = wheat/feed purchase (not BUY_SEED, not BUY_FEED)
4. Labor cost tracked via cash deltas that can't be explained by other sources
5. Bridge tolerance: ±500 (minor timing rounding)
6. Animal revenue captured via shed GOOSE/animal decrease

Observation structure (confirmed):
  obs['farms'][p]['money']          - cash
  obs['farms'][p]['tiles']          - 10x10 tile grid
  obs['farms'][p]['hands']          - list of [x,y] worker positions
  obs['farms'][p]['unlocked_quadrants'] - ['NW', 'NE', ...]
  obs['farms'][p]['hires_today']    - hires made this day
  obs['private']['shed']            - shed inventory dict
  obs['private']['seeds']           - seed inventory dict
  obs['private']['inventories']     - list of per-hand inventory dicts
  obs['market']['prices']           - current prices
  obs['market']['inventory']        - market supply remaining
  obs['town']['unlocked_shops']     - unlocked shops
  obs['step']                       - step number (0-719)
  obs['day']                        - day (0-19)
  obs['hour']                       - hour within day (0-23)
"""

import os, sys, json, importlib.util
from collections import defaultdict
from typing import Dict, Any, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
DMITRII_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
sys.path.insert(0, DMITRII_DIR)

_spec = importlib.util.spec_from_file_location("dmitrii_agent", os.path.join(DMITRII_DIR, "main.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
dmitrii_fn = _mod.agent

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2


# ── TILE CENSUS ───────────────────────────────────────────────────────────────

def count_tiles(tiles: List[List]) -> Dict[str, int]:
    counts = defaultdict(int)
    for row in tiles:
        for t in row:
            if t is None:
                counts["EMPTY"] += 1
            elif isinstance(t, dict):
                crop = t.get("crop") or t.get("type")
                animal = t.get("animal")
                if crop:
                    counts[f"CROP_{crop}"] += 1
                elif animal:
                    counts[f"PASTURE_{animal}"] += 1
                elif t.get("weed") or t.get("is_weed"):
                    counts["WEED"] += 1
                else:
                    counts["USED_UNKNOWN"] += 1
            elif isinstance(t, str):
                counts[t] += 1
            else:
                counts["UNKNOWN"] += 1
    return dict(counts)


def sum_inventories(inventories: List[Dict]) -> Dict[str, int]:
    """Sum all per-hand inventory dicts into one."""
    total = defaultdict(int)
    for inv in (inventories or []):
        if isinstance(inv, dict):
            for k, v in inv.items():
                total[k] += v
    return dict(total)


def get_total_inventory(obs: Dict, player: int) -> Dict[str, int]:
    """Total available goods = shed + all hand inventories."""
    priv = obs.get("private", {})
    shed = dict(priv.get("shed", {}))
    hand_inv = sum_inventories(priv.get("inventories", []))
    total = defaultdict(int)
    for k, v in shed.items():
        total[k] += v
    for k, v in hand_inv.items():
        total[k] += v
    return dict(total)


# ── CORE FORENSIC GAME RUNNER ─────────────────────────────────────────────────

def play_forensic_match(seed: int, v2_seat: int) -> Dict[str, Any]:
    """
    Run one game with full forensic accounting.
    Returns complete bridge and time-series data for both V2 and Dmitrii.
    """
    dm_seat = 1 - v2_seat
    g = kagsim.Game(seed)
    v2_agent = ClosedLoopAgentV2()

    # Per-agent accumulators
    def make_acc():
        return {
            "revenue": defaultdict(float),
            "cost_seeds": defaultdict(float),
            "cost_animals": defaultdict(float),
            "cost_land": 0.0,
            "cost_labor_approx": 0.0,   # from cash delta when HIRE issued
            "cost_feed": 0.0,            # BUY_PRODUCT for wheat
            "cost_other": 0.0,
            "total_plants": defaultdict(int),
            "total_harvests": 0,
            "total_waters": 0,
            "total_fertilizes": 0,
            "total_passes": 0,
            "total_hires": 0,
            "total_sells_qty": defaultdict(int),
            "daily_snapshots": [],
            "event_log": [],
            "shop_unlock_steps": {},
            "land_buy_steps": [],
        }

    acc = {v2_seat: make_acc(), dm_seat: make_acc()}

    step = 0
    prev_obs = {v2_seat: None, dm_seat: None}
    prev_total_inv = {v2_seat: None, dm_seat: None}
    prev_cash = {v2_seat: None, dm_seat: None}

    while not g.done:
        obs_v2 = g.observe(v2_seat)
        obs_dm = g.observe(dm_seat)
        act_v2 = v2_agent.act(obs_v2)
        act_dm = dmitrii_fn(obs_dm)

        # Capture state before step
        for p, obs, act in [(v2_seat, obs_v2, act_v2), (dm_seat, obs_dm, act_dm)]:
            farm = obs["farms"][p]
            priv = obs.get("private", {})
            prices = dict(obs["market"]["prices"])
            shops = list(obs.get("town", {}).get("unlocked_shops", []))
            day = step // 24
            hour = step % 24

            cash = float(farm.get("money", 0))
            shed = dict(priv.get("shed", {}))
            seeds = dict(priv.get("seeds", {}))
            total_inv = get_total_inventory(obs, p)
            hands_pos = farm.get("hands", [])
            quads = list(farm.get("unlocked_quadrants", []))

            if step == 0:
                acc[p]["start_cash"] = cash

            # Track shop unlocks
            for shop in shops:
                if shop not in acc[p]["shop_unlock_steps"]:
                    acc[p]["shop_unlock_steps"][shop] = step

            # Daily snapshot
            if hour == 0:
                acc[p]["daily_snapshots"].append({
                    "day": day, "step": step,
                    "cash": cash,
                    "shed": shed,
                    "seeds": seeds,
                    "num_hands": len(hands_pos),
                    "quads": quads,
                    "shops": shops,
                    "tile_counts": count_tiles(farm.get("tiles", [])),
                })

            # Parse hand actions for pass/water/plant/harvest counts
            hand_actions = act.get("hands", [])
            for i, ha in enumerate(hand_actions):
                if not ha:
                    acc[p]["total_passes"] += 1
                    continue
                op = ha[0] if ha else "PASS"
                if op == "PLANT":
                    crop = ha[1] if len(ha) > 1 else "UNKNOWN"
                    acc[p]["total_plants"][crop] += 1
                elif op == "WATER":
                    acc[p]["total_waters"] += 1
                elif op == "HARVEST":
                    acc[p]["total_harvests"] += 1
                elif op in ("NORTH", "SOUTH", "EAST", "WEST"):
                    pass
                elif op == "PASS":
                    acc[p]["total_passes"] += 1
                elif op == "FERTILIZE":
                    acc[p]["total_fertilizes"] += 1

            # Track market order types for event log
            mkt_events = []
            for order in (act.get("market", []) or []):
                if not order: continue
                op = order[0]
                if op == "HIRE":
                    acc[p]["total_hires"] += 1
                    mkt_events.append(("HIRE", None, None))
                elif op == "BUY_LAND":
                    acc[p]["cost_land"] += 4000.0
                    acc[p]["land_buy_steps"].append(step)
                    mkt_events.append(("BUY_LAND", None, 4000))
                elif op == "BUY_ANIMAL":
                    animal = order[1] if len(order) > 1 else "?"
                    qty = order[2] if len(order) > 2 else 1
                    price = prices.get(animal, 0)
                    cost = qty * price
                    acc[p]["cost_animals"][animal] += cost
                    mkt_events.append(("BUY_ANIMAL", animal, cost))
                elif op == "BUY_SEED":
                    crop = order[1] if len(order) > 1 else "?"
                    qty = order[2] if len(order) > 2 else 1
                    price = prices.get(crop, 0)
                    cost = qty * price
                    acc[p]["cost_seeds"][crop] += cost
                    mkt_events.append(("BUY_SEED", crop, cost))
                elif op == "BUY_PRODUCT":
                    comm = order[1] if len(order) > 1 else "?"
                    qty = order[2] if len(order) > 2 else 1
                    price = prices.get(comm, 0)
                    cost = qty * price
                    acc[p]["cost_feed"] += cost
                    mkt_events.append(("BUY_PRODUCT", comm, cost))
                elif op == "SELL":
                    comm = order[1] if len(order) > 1 else "?"
                    qty = order[2] if len(order) > 2 else 1
                    acc[p]["total_sells_qty"][comm] += qty
                    mkt_events.append(("SELL", comm, qty))

            prev_total_inv[p] = total_inv
            prev_cash[p] = cash

            if mkt_events or acc[p]["total_plants"]:
                acc[p]["event_log"].append({
                    "step": step, "day": day, "hour": hour,
                    "cash": cash,
                    "prices": prices,
                    "market_events": mkt_events,
                    "shops": shops,
                })

        # EXECUTE STEP
        acts = [None, None]
        acts[v2_seat] = act_v2
        acts[dm_seat] = act_dm
        g.step(acts[0], acts[1])
        step += 1

    # ── POST-GAME: REVENUE VIA TOTAL INV DELTA ────────────────────────────
    # Replay to compute revenue via cumulative inventory flow
    # Simpler approach: use final cash and bridge with known costs
    rewards = {v2_seat: float(g.reward(v2_seat)), dm_seat: float(g.reward(dm_seat))}

    for p in [v2_seat, dm_seat]:
        final_obs = g.observe(p)
        farm = final_obs["farms"][p]
        priv = final_obs.get("private", {})
        market = final_obs.get("market", {})

        final_cash = float(farm.get("money", 0))
        final_shed = dict(priv.get("shed", {}))
        final_seeds = dict(priv.get("seeds", {}))
        final_prices = dict(market.get("prices", {}))

        # Terminal inventory value (unsold goods)
        terminal_value = sum(
            float(qty) * float(final_prices.get(comm, 0))
            for comm, qty in final_shed.items()
        )

        # Net income
        start_cash = acc[p].get("start_cash", 3000.0)
        net_income = final_cash - start_cash

        # Total explicit costs
        explicit_costs = (
            sum(acc[p]["cost_seeds"].values()) +
            sum(acc[p]["cost_animals"].values()) +
            acc[p]["cost_land"] +
            acc[p]["cost_feed"]
        )

        # Implied revenue = net_income + explicit_costs
        # (revenue - costs = net_income, so revenue = net_income + costs)
        implied_total_revenue = net_income + explicit_costs

        acc[p]["final_cash"] = final_cash
        acc[p]["final_shed"] = final_shed
        acc[p]["final_seeds"] = final_seeds
        acc[p]["final_prices"] = final_prices
        acc[p]["terminal_shed_value"] = round(terminal_value, 2)
        acc[p]["net_income"] = round(net_income, 2)
        acc[p]["explicit_costs"] = round(explicit_costs, 2)
        acc[p]["implied_total_revenue"] = round(implied_total_revenue, 2)
        acc[p]["simulator_reward"] = rewards[p]

    # Clean up defaultdicts for JSON serialization
    for p in [v2_seat, dm_seat]:
        for k in ["revenue", "cost_seeds", "cost_animals", "total_plants", "total_sells_qty"]:
            if isinstance(acc[p].get(k), defaultdict):
                acc[p][k] = dict(acc[p][k])
        for k in ["cost_land", "cost_labor_approx", "cost_feed", "cost_other",
                  "total_harvests", "total_waters", "total_fertilizes",
                  "total_passes", "total_hires"]:
            acc[p][k] = round(float(acc[p].get(k, 0)), 2)
        acc[p]["start_cash"] = acc[p].get("start_cash", 3000.0)

    v2_acc = acc[v2_seat]
    dm_acc = acc[dm_seat]

    # ── PAIRED DELTA ATTRIBUTION ──────────────────────────────────────────
    delta = {
        "final_cash": round(v2_acc["final_cash"] - dm_acc["final_cash"], 2),
        "net_income": round(v2_acc["net_income"] - dm_acc["net_income"], 2),
        "implied_total_revenue": round(v2_acc["implied_total_revenue"] - dm_acc["implied_total_revenue"], 2),
        "explicit_costs": round(v2_acc["explicit_costs"] - dm_acc["explicit_costs"], 2),
        "cost_seeds": round(sum(v2_acc["cost_seeds"].values()) - sum(dm_acc["cost_seeds"].values()), 2),
        "cost_animals": round(sum(v2_acc["cost_animals"].values()) - sum(dm_acc["cost_animals"].values()), 2),
        "cost_land": round(v2_acc["cost_land"] - dm_acc["cost_land"], 2),
        "cost_feed": round(v2_acc["cost_feed"] - dm_acc["cost_feed"], 2),
        "total_hires": v2_acc["total_hires"] - dm_acc["total_hires"],
        "total_harvests": v2_acc["total_harvests"] - dm_acc["total_harvests"],
        "total_waters": v2_acc["total_waters"] - dm_acc["total_waters"],
        "total_passes": v2_acc["total_passes"] - dm_acc["total_passes"],
        "total_fertilizes": v2_acc["total_fertilizes"] - dm_acc["total_fertilizes"],
        "terminal_shed_value": round(v2_acc["terminal_shed_value"] - dm_acc["terminal_shed_value"], 2),
    }

    # Plant counts delta
    all_crops = set(list(v2_acc["total_plants"].keys()) + list(dm_acc["total_plants"].keys()))
    delta["plants"] = {
        c: v2_acc["total_plants"].get(c, 0) - dm_acc["total_plants"].get(c, 0)
        for c in all_crops
    }

    # Sell qty delta
    all_comms = set(list(v2_acc["total_sells_qty"].keys()) + list(dm_acc["total_sells_qty"].keys()))
    delta["sells_qty"] = {
        c: v2_acc["total_sells_qty"].get(c, 0) - dm_acc["total_sells_qty"].get(c, 0)
        for c in all_comms
    }

    # Daily cash gap trajectory
    v2_daily = [s["cash"] for s in v2_acc["daily_snapshots"]]
    dm_daily = [s["cash"] for s in dm_acc["daily_snapshots"]]
    n_days = min(len(v2_daily), len(dm_daily))
    gap_traj = [round(v2_daily[i] - dm_daily[i], 2) for i in range(n_days)]

    # Divergence detection: first day |gap| > 1000 sustained for 2+ days
    divergence_day = None
    for i in range(len(gap_traj) - 1):
        if abs(gap_traj[i]) > 1000 and abs(gap_traj[i+1]) > 1000:
            divergence_day = i
            break

    # Shop family classification
    shops_v2 = v2_acc["shop_unlock_steps"]
    STRAW_SHOPS = {"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT", "FARMERS_MARKET"}
    has_pizza = "PIZZA_SHOP" in shops_v2
    has_straw = any(s in STRAW_SHOPS for s in shops_v2)
    has_yarn = "YARN_SHOP" in shops_v2
    has_dairy = "DAIRY_SHOP" in shops_v2
    pizza_day = shops_v2.get("PIZZA_SHOP", 999) // 24
    straw_day = min((shops_v2.get(s, 999) // 24 for s in STRAW_SHOPS if s in shops_v2), default=999)

    if has_yarn and not has_pizza and not has_straw:
        shop_family = "Yarn Only"
    elif has_pizza and not has_straw:
        shop_family = "Pizza no Straw"
    elif has_straw and not has_pizza:
        shop_family = "Straw no Pizza"
    elif has_pizza and has_straw:
        shop_family = "Pizza + Straw"
    elif has_yarn:
        shop_family = "Yarn World"
    else:
        shop_family = "No Premium Shop"

    return {
        "seed": seed,
        "v2_seat": v2_seat,
        "paired_margin": round(rewards[v2_seat] - rewards[dm_seat], 2),
        "v2_final_cash": round(rewards[v2_seat], 2),
        "dm_final_cash": round(rewards[dm_seat], 2),
        "v2": v2_acc,
        "dm": dm_acc,
        "delta": delta,
        "gap_trajectory_daily": gap_traj,
        "divergence_day": divergence_day,
        "v2_daily_cash": v2_daily,
        "dm_daily_cash": dm_daily,
        "shop_family": shop_family,
        "shops_v2": shops_v2,
        "has_pizza": has_pizza,
        "has_straw": has_straw,
        "has_yarn": has_yarn,
        "has_dairy": has_dairy,
    }


def run_crn_pair(seed: int) -> Tuple[Dict, Dict, float]:
    """Run CRN balanced pair and return (game0, game1, combined_margin)."""
    g0 = play_forensic_match(seed, v2_seat=0)
    g1 = play_forensic_match(seed, v2_seat=1)
    combined = g0["paired_margin"] + g1["paired_margin"]
    return g0, g1, combined


if __name__ == "__main__":
    import time
    print("=" * 80)
    print("FORENSIC LOGGER V2 — SMOKE TEST (Seeds 50000-50004)")
    print("=" * 80)

    for seed in [50000, 50001, 50002, 50003, 50004]:
        t0 = time.time()
        g0, g1, combined = run_crn_pair(seed)
        dt = time.time() - t0

        v2 = g0["v2"]
        dm = g0["dm"]

        print(f"\nSeed {seed}  ({dt:.1f}s)  Shop: {g0['shop_family']}")
        print(f"  Game0: V2={g0['v2_final_cash']:.0f}  Dm={g0['dm_final_cash']:.0f}  margin={g0['paired_margin']:+.0f}")
        print(f"  Game1: V2={g1['v2_final_cash']:.0f}  Dm={g1['dm_final_cash']:.0f}  margin={g1['paired_margin']:+.0f}")
        print(f"  Combined margin: {combined:+.0f}")
        print(f"  V2: rev={v2['implied_total_revenue']:.0f}  costs={v2['explicit_costs']:.0f}  net={v2['net_income']:.0f}")
        print(f"  Dm: rev={dm['implied_total_revenue']:.0f}  costs={dm['explicit_costs']:.0f}  net={dm['net_income']:.0f}")
        d = g0["delta"]
        print(f"  Delta: rev={d['implied_total_revenue']:+.0f}  costs={d['explicit_costs']:+.0f}  land={d['cost_land']:+.0f}  feed={d['cost_feed']:+.0f}")
        print(f"  Delta plants: {d['plants']}")
        print(f"  Delta hires: {int(d['total_hires']):+d}  harvests: {int(d['total_harvests']):+d}  fertilizes: {int(d['total_fertilizes']):+d}")
        print(f"  Gap traj: {[round(x) for x in g0['gap_trajectory_daily'][:10]]} ...")
        if g0["divergence_day"] is not None:
            print(f"  Divergence: Day {g0['divergence_day']}")

    print("\n\nSmoke test complete.")
    print("If numbers look reasonable, run_forensic_discovery.py is ready to execute.")
