#!/usr/bin/env python3
"""Comprehensive Unit Tests for WeedRepairEngine (V51 Phase 2)."""

import unittest
from typing import Any, Dict, List
from research.v51.mechanisms.weed_repair_engine import WeedRepairEngine, get_tile


class TestWeedRepairEngine(unittest.TestCase):

    def setUp(self):
        self.engine = WeedRepairEngine(replay_steps=8, stop_on_match=True)

    def _make_obs(self, step: int, seat: int = 0, farmer_pos=[1, 1], hands_pos=None, tiles=None):
        if hands_pos is None:
            hands_pos = [[2, 2]]
        if tiles is None:
            # 5x5 grid of empty dirt
            tiles = [[{"kind": "DIRT"} for _ in range(5)] for _ in range(5)]
        
        farm = {
            "farmer": farmer_pos,
            "hands": hands_pos,
            "tiles": tiles,
        }
        farms = [farm, farm] if seat == 0 else [farm, farm]
        return {
            "step": step,
            "player": seat,
            "farms": farms,
        }

    def test_pass_through_on_clean_tiles(self):
        """In states without weeds, action must be 100% identical."""
        obs = self._make_obs(step=10)
        raw = {
            "farmer": ["PLANT", "WHEAT"],
            "hands": [["WATER"]],
            "market": [["BUY_SEED", "WHEAT", 2]],
        }
        res = self.engine.process_turn(obs, raw)
        self.assertEqual(res, raw)
        self.assertEqual(self.engine.telemetry["collisions"], 0)

    def test_farmer_weed_collision_and_recovery(self):
        """Farmer attempts PLANT on WEED: Turn 0 DIG, Turn 1 PLANT, Turn 2+ Replay."""
        # 1. Collision Turn: tile (1,1) is WEED
        tiles = [[{"kind": "DIRT"} for _ in range(5)] for _ in range(5)]
        tiles[1][1] = {"kind": "WEED"}
        obs_0 = self._make_obs(step=20, farmer_pos=[1, 1], tiles=tiles)
        
        # Tape definition
        mock_tape = {
            19: ["MOVE", "NORTH"],
            20: ["PLANT", "WHEAT"],
            21: ["WATER"],
            22: ["MOVE", "EAST"],
            23: ["HARVEST"],
        }
        tape_lookup = lambda s, a: mock_tape.get(s, ["PASS"])

        raw_0 = {"farmer": ["PLANT", "WHEAT"], "hands": [["PASS"]], "market": []}
        res_0 = self.engine.process_turn(obs_0, raw_0, tape_lookup)
        
        # Turn 20: Must issue DIG
        self.assertEqual(res_0["farmer"], ["DIG"])
        self.assertEqual(self.engine.telemetry["collisions"], 1)
        self.assertEqual(self.engine.telemetry["dig_actions"], 1)

        # 2. Retry Turn: Turn 21, tile is now cleared (DIRT)
        tiles[1][1] = {"kind": "DIRT"}
        obs_1 = self._make_obs(step=21, farmer_pos=[1, 1], tiles=tiles)
        raw_1 = {"farmer": ["WATER"], "hands": [["PASS"]], "market": []}
        res_1 = self.engine.process_turn(obs_1, raw_1, tape_lookup)

        # Turn 21: Must replay original intended PLANT WHEAT
        self.assertEqual(res_1["farmer"], ["PLANT", "WHEAT"])
        self.assertEqual(self.engine.telemetry["retry_actions"], 1)

        # 3. Replay Phase: Turn 22 (age 2), tape scheduled MOVE EAST, but offset is step 21 (WATER)
        obs_2 = self._make_obs(step=22, farmer_pos=[1, 1], tiles=tiles)
        raw_2 = {"farmer": ["MOVE", "EAST"], "hands": [["PASS"]], "market": []}
        res_2 = self.engine.process_turn(obs_2, raw_2, tape_lookup)

        # Turn 22: Must replay step 21's WATER
        self.assertEqual(res_2["farmer"], ["WATER"])
        self.assertEqual(self.engine.telemetry["replay_actions"], 1)

    def test_farm_hand_collision_and_recovery(self):
        """Farm hand 0 encounters WEED on BUILD_PASTURE."""
        tiles = [[{"kind": "DIRT"} for _ in range(5)] for _ in range(5)]
        tiles[2][2] = {"kind": "WEED"}
        obs = self._make_obs(step=30, farmer_pos=[0, 0], hands_pos=[[2, 2]], tiles=tiles)

        raw = {
            "farmer": ["MOVE", "NORTH"],
            "hands": [["BUILD_PASTURE"]],
            "market": [["SELL", "MILK", 5]],
        }
        res = self.engine.process_turn(obs, raw)

        # Farmer and market must be untouched
        self.assertEqual(res["farmer"], ["MOVE", "NORTH"])
        self.assertEqual(res["market"], [["SELL", "MILK", 5]])
        # Hand 0 must DIG
        self.assertEqual(res["hands"][0], ["DIG"])
        self.assertEqual(self.engine.telemetry["collisions"], 1)

    def test_simultaneous_multi_actor_collisions(self):
        """Both farmer and hand 0 hit WEED on the same turn."""
        tiles = [[{"kind": "DIRT"} for _ in range(5)] for _ in range(5)]
        tiles[1][1] = {"kind": "WEED"}
        tiles[2][2] = {"kind": "WEED"}
        obs = self._make_obs(step=40, farmer_pos=[1, 1], hands_pos=[[2, 2]], tiles=tiles)

        raw = {
            "farmer": ["PLANT", "CARROT"],
            "hands": [["BUILD_PASTURE"]],
            "market": [],
        }
        res = self.engine.process_turn(obs, raw)

        self.assertEqual(res["farmer"], ["DIG"])
        self.assertEqual(res["hands"][0], ["DIG"])
        self.assertEqual(self.engine.telemetry["collisions"], 2)

    def test_seat_independence(self):
        """Collision on Seat 0 must not affect Seat 1."""
        tiles = [[{"kind": "DIRT"} for _ in range(5)] for _ in range(5)]
        tiles[1][1] = {"kind": "WEED"}
        
        obs_seat0 = self._make_obs(step=15, seat=0, farmer_pos=[1, 1], tiles=tiles)
        obs_seat1 = self._make_obs(step=15, seat=1, farmer_pos=[1, 1], tiles=[[{"kind": "DIRT"} for _ in range(5)] for _ in range(5)])

        raw = {"farmer": ["PLANT", "WHEAT"], "hands": [["PASS"]]}
        
        res_0 = self.engine.process_turn(obs_seat0, raw)
        res_1 = self.engine.process_turn(obs_seat1, raw)

        self.assertEqual(res_0["farmer"], ["DIG"])
        self.assertEqual(res_1["farmer"], ["PLANT", "WHEAT"])

    def test_episode_reset(self):
        """Step 0 must clear any pending active transactions."""
        # Create an active transaction at step 50
        tiles = [[{"kind": "DIRT"} for _ in range(5)] for _ in range(5)]
        tiles[1][1] = {"kind": "WEED"}
        obs_50 = self._make_obs(step=50, farmer_pos=[1, 1], tiles=tiles)
        self.engine.process_turn(obs_50, {"farmer": ["PLANT", "WHEAT"], "hands": []})
        self.assertIn("farmer", self.engine.states[0]["active"])

        # New episode at step 0
        obs_0 = self._make_obs(step=0, farmer_pos=[0, 0])
        self.engine.process_turn(obs_0, {"farmer": ["MOVE", "NORTH"], "hands": []})
        self.assertNotIn("farmer", self.engine.states[0]["active"])


if __name__ == "__main__":
    unittest.main()
