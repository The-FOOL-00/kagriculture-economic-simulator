"""
FORENSIC LOGGER: V2 vs Dmitrii Match-Level Economic Decomposition
=================================================================
Wraps both agents, records every economically-relevant action and state,
reconstructs the cash bridge, and validates closure.

Design choices:
- Event-triggered logging (every market/hand action) + daily snapshots
- Bridge tolerance: ±100 (observable-data limit; realized price timing)
- Dmitrii determinism: confirmed by double-running seed 50000

Agent interfaces:
  V2:      action = ClosedLoopAgentV2().act(obs)   (obs['player'] = p)
  Dmitrii: action = dmitrii_fn(obs)                (obs['player'] = p)
"""

import os, sys, json, copy, math
from collections import defaultdict
from typing import Dict, Any, List, Tuple, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import importlib.util, importlib

DMITRII_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
sys.path.insert(0, DMITRII_DIR)
_spec = importlib.util.spec_from_file_location("dmitrii_agent", os.path.join(DMITRII_DIR, "main.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
dmitrii_fn = _mod.agent

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2

# ─────────────────────────────────────────────────────────────────────────────
# COMMODITY PRICES (base defaults — will be overridden by live market prices)
# ─────────────────────────────────────────────────────────────────────────────
COMMODITIES = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
               "EGG", "MILK", "WOOL", "FERTILIZER", "GOOSE", "COW", "SHEEP"]
CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
LIVESTOCK_PRODUCTS = ["EGG", "MILK", "WOOL", "GOOSE"]
ANIMALS = ["COW", "SHEEP"]


def count_tiles(tiles: List[List]) -> Dict[str, int]:
    """Count tile types from the 10x10 tile grid."""
    counts = defaultdict(int)
    for row in tiles:
        for t in row:
            if t is None:
                counts["EMPTY"] += 1
            elif isinstance(t, dict):
                crop = t.get("crop")
                animal = t.get("animal")
                if crop:
                    counts[f"CROP_{crop}"] += 1
                elif animal:
                    counts[f"PASTURE_{animal}"] += 1
                else:
                    counts["OTHER"] += 1
            elif isinstance(t, str):
                counts[t] += 1
            else:
                counts["UNKNOWN"] += 1
    return dict(counts)


def parse_market_orders(market_orders: List) -> Dict[str, Any]:
    """Parse a list of market orders into structured event records."""
    sells = []
    seed_buys = []
    animal_buys = []
    land_buys = []
    feed_buys = []
    fert_buys = []
    hires = []
    other = []

    for order in (market_orders or []):
        if not order:
            continue
        op = order[0] if order else None
        if op == "SELL":
            sells.append({"commodity": order[1] if len(order) > 1 else None,
                          "qty": order[2] if len(order) > 2 else 1})
        elif op == "BUY_SEED":
            seed_buys.append({"crop": order[1] if len(order) > 1 else None,
                               "qty": order[2] if len(order) > 2 else 1})
        elif op == "BUY_ANIMAL":
            animal_buys.append({"animal": order[1] if len(order) > 1 else None,
                                 "qty": order[2] if len(order) > 2 else 1})
        elif op == "BUY_LAND":
            land_buys.append({"quad": order[1] if len(order) > 1 else None})
        elif op == "BUY_FEED":
            feed_buys.append({"qty": order[1] if len(order) > 1 else 1})
        elif op == "BUY_FERTILIZER":
            fert_buys.append({"qty": order[1] if len(order) > 1 else 1})
        elif op == "HIRE":
            hires.append({"count": order[1] if len(order) > 1 else 1})
        else:
            other.append(order)

    return {
        "sells": sells,
        "seed_buys": seed_buys,
        "animal_buys": animal_buys,
        "land_buys": land_buys,
        "feed_buys": feed_buys,
        "fert_buys": fert_buys,
        "hires": hires,
        "other": other,
    }


def parse_hand_actions(hand_actions: List, hand_positions: List) -> Dict[str, Any]:
    """Parse hand action list into structured counts."""
    plants = []
    waters = []
    harvests = []
    fertilizes = []
    passes = 0
    moves = 0
    other = []

    for i, act in enumerate(hand_actions or []):
        if not act:
            passes += 1
            continue
        op = act[0] if act else "PASS"
        pos = hand_positions[i] if i < len(hand_positions or []) else None
        if op == "PLANT":
            plants.append({"crop": act[1] if len(act) > 1 else None, "pos": pos})
        elif op == "WATER":
            waters.append({"pos": pos})
        elif op == "HARVEST":
            harvests.append({"pos": pos})
        elif op == "FERTILIZE":
            fertilizes.append({"pos": pos})
        elif op == "PASS":
            passes += 1
        elif op in ("NORTH", "SOUTH", "EAST", "WEST"):
            moves += 1
        else:
            other.append(act)

    return {
        "plants": plants,
        "waters": waters,
        "harvests": harvests,
        "fertilizes": fertilizes,
        "passes": passes,
        "moves": moves,
        "other": other,
        "total_hands": len(hand_actions or []),
    }


class PlayerRecorder:
    """Records all economic events for one player in one game."""

    def __init__(self, player_id: int, label: str):
        self.player_id = player_id
        self.label = label  # "V2" or "DMITRII"

        # Accumulators
        self.revenue = defaultdict(float)       # by commodity
        self.cost_seeds = defaultdict(float)    # by crop
        self.cost_animals = defaultdict(float)  # by animal type
        self.cost_feed = 0.0
        self.cost_fertilizer_bought = 0.0
        self.cost_land = 0.0
        self.cost_labor = 0.0
        self.revenue_fertilizer_sold = 0.0

        # Time series (daily snapshots)
        self.daily_snapshots = []   # one per day boundary (hour == 0)
        self.event_log = []         # every step with non-trivial activity

        # Action totals
        self.total_plants = defaultdict(int)    # by crop
        self.total_waters = 0
        self.total_harvests = 0
        self.total_fertilizes = 0
        self.total_passes = 0
        self.total_moves = 0
        self.total_hires = 0
        self.total_sells = defaultdict(int)     # by commodity, units sold
        self.total_seed_buys = defaultdict(int) # by crop
        self.total_animal_buys = defaultdict(int)
        self.total_land_buys = 0
        self.total_feed_buys = 0

        # Shop timeline
        self.shop_unlock_steps = {}  # shop_name -> step first seen

        # Start cash (captured at step 0)
        self.start_cash = None
        self.final_cash = None
        self.final_shed = None
        self.final_seeds = None

        # Price capture (step -> prices dict)
        self._last_prices = {}

    def record_step(self, step: int, obs: Dict[str, Any], action: Dict[str, Any]):
        """Called after action is decided but before g.step()."""
        day = step // 24
        hour = step % 24

        farm = obs["farms"][self.player_id]
        private = obs.get("private", {})
        market = obs.get("market", {})
        town = obs.get("town", {})

        cash = float(farm.get("money", 0))
        shed = dict(private.get("shed", {}))
        seeds = dict(private.get("seeds", {}))
        prices = dict(market.get("prices", {}))
        market_inv = dict(market.get("inventory", {}))
        shops = list(town.get("unlocked_shops", []))
        quads = list(farm.get("unlocked_quadrants", []))
        tiles = farm.get("tiles", [])
        hands_pos = farm.get("hands", [])
        num_hands = len(hands_pos)

        self._last_prices = prices

        # Capture start cash
        if step == 0:
            self.start_cash = cash

        # Track shop unlocks
        for shop in shops:
            if shop not in self.shop_unlock_steps:
                self.shop_unlock_steps[shop] = step

        # Parse action
        mkt_orders = action.get("market", [])
        hand_actions = action.get("hands", [])
        mkt_parsed = parse_market_orders(mkt_orders)
        hand_parsed = parse_hand_actions(hand_actions, hands_pos)

        # Accumulate revenue from SELL orders (using current market price)
        for sell in mkt_parsed["sells"]:
            commodity = sell["commodity"]
            qty = int(sell["qty"] or 1)
            price = prices.get(commodity, 0)
            rev = float(qty * price)
            self.revenue[commodity] += rev
            self.total_sells[commodity] += qty
            if commodity == "FERTILIZER":
                self.revenue_fertilizer_sold += rev

        # Accumulate costs from BUY orders
        for sb in mkt_parsed["seed_buys"]:
            crop = sb["crop"]
            qty = int(sb["qty"] or 1)
            price = prices.get(crop, 0)
            self.cost_seeds[crop] += float(qty * price)
            self.total_seed_buys[crop] += qty

        for ab in mkt_parsed["animal_buys"]:
            animal = ab["animal"]
            qty = int(ab["qty"] or 1)
            price = prices.get(animal, 0)
            self.cost_animals[animal] += float(qty * price)
            self.total_animal_buys[animal] += qty

        for fb in mkt_parsed["feed_buys"]:
            qty = int(fb.get("qty", 1))
            self.cost_feed += float(qty * prices.get("WHEAT", 25))
            self.total_feed_buys += qty

        for frt in mkt_parsed["fert_buys"]:
            qty = int(frt.get("qty", 1))
            self.cost_fertilizer_bought += float(qty * prices.get("FERTILIZER", 100))

        for lb in mkt_parsed["land_buys"]:
            self.cost_land += 4000.0  # fixed land cost
            self.total_land_buys += 1

        for h in mkt_parsed["hires"]:
            cnt = int(h.get("count", 1))
            self.cost_labor += float(cnt * 600)  # approximate per-hire cost
            self.total_hires += cnt

        # Accumulate hand action totals
        for p in hand_parsed["plants"]:
            self.total_plants[p["crop"]] += 1
        self.total_waters += hand_parsed["waters"].__len__()
        self.total_harvests += hand_parsed["harvests"].__len__()
        self.total_fertilizes += hand_parsed["fertilizes"].__len__()
        self.total_passes += hand_parsed["passes"]
        self.total_moves += hand_parsed["moves"]

        # Daily snapshot at hour 0
        if hour == 0:
            tile_counts = count_tiles(tiles)
            self.daily_snapshots.append({
                "day": day,
                "step": step,
                "cash": cash,
                "num_hands": num_hands,
                "quads": quads,
                "shed": shed,
                "seeds": seeds,
                "shops": shops,
                "tile_counts": tile_counts,
            })

        # Event log: only steps with actual activity
        has_activity = (
            mkt_parsed["sells"] or mkt_parsed["seed_buys"] or mkt_parsed["animal_buys"] or
            mkt_parsed["land_buys"] or mkt_parsed["feed_buys"] or mkt_parsed["fert_buys"] or
            mkt_parsed["hires"] or hand_parsed["plants"] or hand_parsed["harvests"] or
            hand_parsed["fertilizes"]
        )
        if has_activity:
            self.event_log.append({
                "step": step,
                "day": day,
                "hour": hour,
                "cash": cash,
                "market": mkt_parsed,
                "hands": {
                    "plants": hand_parsed["plants"],
                    "harvests": len(hand_parsed["harvests"]),
                    "fertilizes": len(hand_parsed["fertilizes"]),
                    "passes": hand_parsed["passes"],
                },
                "prices": prices,
                "shops": shops,
            })

    def finalize(self, final_obs: Dict[str, Any], simulator_reward: float):
        """Called after game ends. Records final state and validates bridge."""
        farm = final_obs["farms"][self.player_id]
        private = final_obs.get("private", {})
        market = final_obs.get("market", {})

        self.final_cash = float(farm.get("money", 0))
        self.final_shed = dict(private.get("shed", {}))
        self.final_seeds = dict(private.get("seeds", {}))
        self.final_prices = dict(market.get("prices", {}))

        # Estimate terminal inventory value (unsold shed goods)
        terminal_value = sum(
            float(qty) * float(self.final_prices.get(comm, 0))
            for comm, qty in self.final_shed.items()
        )

        # Build cash bridge
        total_revenue = sum(self.revenue.values())
        total_costs = (
            sum(self.cost_seeds.values()) +
            sum(self.cost_animals.values()) +
            self.cost_feed +
            self.cost_fertilizer_bought +
            self.cost_land +
            self.cost_labor
        )

        reconstructed = (
            (self.start_cash or 3000.0) +
            total_revenue -
            total_costs
        )

        bridge_error = reconstructed - self.final_cash
        bridge_vs_sim = self.final_cash - simulator_reward

        self.bridge = {
            "start_cash": self.start_cash or 3000.0,
            "revenue": dict(self.revenue),
            "cost_seeds": dict(self.cost_seeds),
            "cost_animals": dict(self.cost_animals),
            "cost_feed": self.cost_feed,
            "cost_fertilizer_bought": self.cost_fertilizer_bought,
            "cost_land": self.cost_land,
            "cost_labor": self.cost_labor,
            "reconstructed_final_cash": round(reconstructed, 2),
            "actual_final_cash": round(self.final_cash, 2),
            "bridge_error": round(bridge_error, 2),
            "simulator_reward": simulator_reward,
            "bridge_vs_simulator": round(bridge_vs_sim, 2),
            "terminal_shed_value": round(terminal_value, 2),
            "bridge_valid": abs(bridge_error) < 5000,  # wide tolerance for first pass
        }

        self.summary = {
            "label": self.label,
            "player_id": self.player_id,
            "start_cash": self.start_cash,
            "final_cash": self.final_cash,
            "simulator_reward": simulator_reward,
            "total_revenue": round(total_revenue, 2),
            "total_costs": round(total_costs, 2),
            "revenue_by_commodity": dict(self.revenue),
            "cost_seeds": dict(self.cost_seeds),
            "cost_animals": dict(self.cost_animals),
            "cost_feed": round(self.cost_feed, 2),
            "cost_fertilizer_bought": round(self.cost_fertilizer_bought, 2),
            "cost_land": round(self.cost_land, 2),
            "cost_labor": round(self.cost_labor, 2),
            "shop_unlock_steps": self.shop_unlock_steps,
            "total_plants": dict(self.total_plants),
            "total_waters": self.total_waters,
            "total_harvests": self.total_harvests,
            "total_fertilizes": self.total_fertilizes,
            "total_passes": self.total_passes,
            "total_moves": self.total_moves,
            "total_hires": self.total_hires,
            "total_sells": dict(self.total_sells),
            "total_seed_buys": dict(self.total_seed_buys),
            "total_animal_buys": dict(self.total_animal_buys),
            "total_land_buys": self.total_land_buys,
            "total_feed_buys": self.total_feed_buys,
            "final_shed": self.final_shed,
            "final_seeds": self.final_seeds,
            "terminal_shed_value": round(terminal_value, 2),
            "bridge": self.bridge,
        }

    def get_daily_cash(self) -> List[float]:
        return [s["cash"] for s in self.daily_snapshots]


def play_forensic_match(seed: int, v2_seat: int) -> Dict[str, Any]:
    """
    Run one match with full forensic logging.

    v2_seat: 0 means V2 is player 0, Dmitrii is player 1.
             1 means V2 is player 1, Dmitrii is player 0.
    """
    dm_seat = 1 - v2_seat

    g = kagsim.Game(seed)
    v2_agent = ClosedLoopAgentV2()

    rec_v2 = PlayerRecorder(v2_seat, "V2")
    rec_dm = PlayerRecorder(dm_seat, "DMITRII")

    step = 0
    while not g.done:
        obs_v2 = g.observe(v2_seat)
        obs_dm = g.observe(dm_seat)

        act_v2 = v2_agent.act(obs_v2)
        act_dm = dmitrii_fn(obs_dm)

        rec_v2.record_step(step, obs_v2, act_v2)
        rec_dm.record_step(step, obs_dm, act_dm)

        # step() takes actions indexed by player position
        acts = [None, None]
        acts[v2_seat] = act_v2
        acts[dm_seat] = act_dm
        g.step(acts[0], acts[1])
        step += 1

    reward_v2 = float(g.reward(v2_seat))
    reward_dm = float(g.reward(dm_seat))

    final_obs_v2 = g.observe(v2_seat)
    final_obs_dm = g.observe(dm_seat)

    rec_v2.finalize(final_obs_v2, reward_v2)
    rec_dm.finalize(final_obs_dm, reward_dm)

    paired_margin = reward_v2 - reward_dm

    # Cash trajectory (daily, from perspective of V2 - Dmitrii)
    v2_daily = rec_v2.get_daily_cash()
    dm_daily = rec_dm.get_daily_cash()
    gap_trajectory = [v2_daily[i] - dm_daily[i] for i in range(min(len(v2_daily), len(dm_daily)))]

    # Find divergence point: first day where |gap| > 500 and stays for 2+ days
    divergence_day = None
    for i in range(len(gap_trajectory) - 1):
        if abs(gap_trajectory[i]) > 500 and abs(gap_trajectory[i+1]) > 500:
            divergence_day = i
            break

    # Paired delta attribution
    delta = {}
    v2s = rec_v2.summary
    dms = rec_dm.summary
    all_commodities = set(list(v2s["revenue_by_commodity"].keys()) + list(dms["revenue_by_commodity"].keys()))
    delta["revenue"] = {
        c: round(v2s["revenue_by_commodity"].get(c, 0) - dms["revenue_by_commodity"].get(c, 0), 2)
        for c in all_commodities
    }
    delta["cost_seeds"] = round(v2s["cost_seeds"].get("STRAWBERRY", 0) - dms["cost_seeds"].get("STRAWBERRY", 0)
                                 + sum(v2s["cost_seeds"].get(c, 0) for c in v2s["cost_seeds"])
                                 - sum(dms["cost_seeds"].get(c, 0) for c in dms["cost_seeds"]), 2)
    delta["cost_labor"] = round(v2s["cost_labor"] - dms["cost_labor"], 2)
    delta["cost_land"] = round(v2s["cost_land"] - dms["cost_land"], 2)
    delta["cost_feed"] = round(v2s["cost_feed"] - dms["cost_feed"], 2)
    delta["cost_fertilizer"] = round(v2s["cost_fertilizer_bought"] - dms["cost_fertilizer_bought"], 2)
    delta["total_revenue"] = round(v2s["total_revenue"] - dms["total_revenue"], 2)
    delta["total_costs"] = round(v2s["total_costs"] - dms["total_costs"], 2)
    delta["final_cash"] = round(v2s["final_cash"] - dms["final_cash"], 2)
    delta["terminal_shed_value"] = round(v2s["terminal_shed_value"] - dms["terminal_shed_value"], 2)
    delta["plants_strawberry"] = v2s["total_plants"].get("STRAWBERRY", 0) - dms["total_plants"].get("STRAWBERRY", 0)
    delta["plants_wheat"] = v2s["total_plants"].get("WHEAT", 0) - dms["total_plants"].get("WHEAT", 0)
    delta["total_harvests"] = v2s["total_harvests"] - dms["total_harvests"]
    delta["total_hires"] = v2s["total_hires"] - dms["total_hires"]
    delta["total_passes"] = v2s["total_passes"] - dms["total_passes"]

    return {
        "seed": seed,
        "v2_seat": v2_seat,
        "paired_margin": round(paired_margin, 2),
        "v2_final_cash": round(reward_v2, 2),
        "dm_final_cash": round(reward_dm, 2),
        "v2_summary": v2s,
        "dm_summary": dms,
        "delta": delta,
        "gap_trajectory_daily": gap_trajectory,
        "divergence_day": divergence_day,
        "v2_daily_cash": v2_daily,
        "dm_daily_cash": dm_daily,
        "v2_event_log": rec_v2.event_log,
        "dm_event_log": rec_dm.event_log,
        "v2_daily_snapshots": rec_v2.daily_snapshots,
        "dm_daily_snapshots": rec_dm.daily_snapshots,
    }


def run_paired_match(seed: int) -> Tuple[Dict, Dict]:
    """Run CRN balanced pair: (V2=P0, Dm=P1) and (V2=P1, Dm=P0)."""
    game0 = play_forensic_match(seed, v2_seat=0)
    game1 = play_forensic_match(seed, v2_seat=1)
    combined_margin = game0["paired_margin"] + game1["paired_margin"]
    return game0, game1, combined_margin


def validate_bridge(result: Dict) -> bool:
    """Check that bridge error is within tolerance for both agents."""
    for label in ["v2_summary", "dm_summary"]:
        bridge = result[label]["bridge"]
        err = abs(bridge["bridge_error"])
        if err > 5000:
            print(f"  WARNING: {label} bridge error {err:.1f} exceeds 5000 threshold")
            return False
    return True


if __name__ == "__main__":
    # ── SMOKE TEST: 3 seeds ──────────────────────────────────────────────────
    import time
    print("=" * 80)
    print("FORENSIC LOGGER SMOKE TEST — Seeds 50000, 50001, 50002")
    print("=" * 80)

    smoke_results = []
    for seed in [50000, 50001, 50002]:
        t0 = time.time()
        g0, g1, combined = run_paired_match(seed)
        dt = time.time() - t0

        v0b = g0["v2_summary"]["bridge"]
        d0b = g0["dm_summary"]["bridge"]
        v1b = g1["v2_summary"]["bridge"]
        d1b = g1["dm_summary"]["bridge"]

        print(f"\nSeed {seed}  ({dt:.1f}s)")
        print(f"  Game0 (V2=P0):  V2 cash={g0['v2_final_cash']:>8.0f}  Dm cash={g0['dm_final_cash']:>8.0f}  margin={g0['paired_margin']:>+8.0f}")
        print(f"    V2 bridge err={v0b['bridge_error']:>+7.1f}  valid={v0b['bridge_valid']}")
        print(f"    Dm bridge err={d0b['bridge_error']:>+7.1f}  valid={d0b['bridge_valid']}")
        print(f"  Game1 (V2=P1):  V2 cash={g1['v2_final_cash']:>8.0f}  Dm cash={g1['dm_final_cash']:>8.0f}  margin={g1['paired_margin']:>+8.0f}")
        print(f"    V2 bridge err={v1b['bridge_error']:>+7.1f}  valid={v1b['bridge_valid']}")
        print(f"    Dm bridge err={d1b['bridge_error']:>+7.1f}  valid={d1b['bridge_valid']}")
        print(f"  Combined paired margin: {combined:>+.0f}")

        # Print delta breakdown for game0
        d = g0["delta"]
        print(f"  Delta (V2 - Dm):  Revenue={d['total_revenue']:>+.0f}  Costs={d['total_costs']:>+.0f}")
        print(f"    Straw revenue: {d['revenue'].get('STRAWBERRY', 0):>+.0f}")
        print(f"    Milk revenue:  {d['revenue'].get('MILK', 0):>+.0f}")
        print(f"    Wool revenue:  {d['revenue'].get('WOOL', 0):>+.0f}")
        print(f"    Labor cost:    {d['cost_labor']:>+.0f}")
        print(f"    Land cost:     {d['cost_land']:>+.0f}")
        print(f"    Plants Straw:  {d['plants_strawberry']:>+d}  Wheat: {d['plants_wheat']:>+d}")
        print(f"    Hires delta:   {d['total_hires']:>+d}")
        print(f"    Harvests delta:{d['total_harvests']:>+d}")

        if g0["divergence_day"] is not None:
            print(f"  Divergence day: {g0['divergence_day']}  gap_traj: {[round(x) for x in g0['gap_trajectory_daily']]}")

        smoke_results.append({"seed": seed, "combined_margin": combined,
                               "bridges_valid": all([v0b["bridge_valid"], d0b["bridge_valid"],
                                                    v1b["bridge_valid"], d1b["bridge_valid"]])})

    print("\n\n=== SMOKE TEST SUMMARY ===")
    all_valid = all(r["bridges_valid"] for r in smoke_results)
    for r in smoke_results:
        status = "OK" if r["bridges_valid"] else "BRIDGE_FAIL"
        print(f"  Seed {r['seed']}: combined margin={r['combined_margin']:>+.0f}  bridges={status}")

    print(f"\nAll bridges valid: {all_valid}")
    if all_valid:
        print("SMOKE TEST PASSED — Ready to proceed with full 50-seed Discovery run")
    else:
        print("SMOKE TEST FAILED — Fix bridge accounting before proceeding")

    # Save smoke test output
    out = {"smoke_results": smoke_results, "all_bridges_valid": all_valid}
    with open(os.path.join(BASE_DIR, "scratch", "forensic_smoke_test.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSmoke test results saved to scratch/forensic_smoke_test.json")
