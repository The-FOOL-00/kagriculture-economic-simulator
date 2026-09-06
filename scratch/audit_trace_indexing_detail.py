import sys
import os
sys.path.insert(0, ".")
import json
import candidates.slot2_aethel_refined_v2 as v2
import opponents.replay_crop_dusta as cd_opp

print("=== V2 _TRACE Check ===")
print("len(_V2_TRACE):", len(v2._TRACE))
print("V2 Turn 0 action:", v2._TRACE[0])
print("V2 Turn 1 action:", v2._TRACE[1])

print("\n=== Opponents Replay Crop Dusta _TRACE Check ===")
print("len(cd_opp._TRACE):", len(cd_opp._TRACE))
print("cd_opp Turn 0 action:", cd_opp._TRACE[0])
print("cd_opp Turn 1 action:", cd_opp._TRACE[1])

print("\n=== Replay Whyme_Labs_104824599.json Steps Check ===")
with open("scratch/replays/Whyme_Labs_104824599.json", "r", encoding="utf-8") as f:
    rep = json.load(f)

print("rep['steps'] length:", len(rep['steps']))
print("rep['steps'][0][1]['action'] (What arch_base took as Turn 0):", rep['steps'][0][1].get('action'))
print("rep['steps'][1][1]['action'] (What Crop Dusta actually submitted at Turn 0):", rep['steps'][1][1].get('action'))
print("rep['steps'][2][1]['action'] (What Crop Dusta actually submitted at Turn 1):", rep['steps'][2][1].get('action'))
