import os, sys, time, json, hashlib
import numpy as np

# We define the strategy grid for 1.32.7
STRATEGY_GRID = [
    {"name": "Apex_8C_4S_15M_B24", "cows": 8, "sheep": 4, "geese": 0, "melons": 15, "c2_melons": 8, "batch": 24, "feed_buf": 2, "day0_land": True},
    {"name": "Apex_10C_2S_15M_B24", "cows": 10, "sheep": 2, "geese": 0, "melons": 15, "c2_melons": 8, "batch": 24, "feed_buf": 2, "day0_land": True},
    {"name": "Apex_12C_0S_15M_B24", "cows": 12, "sheep": 0, "geese": 0, "melons": 15, "c2_melons": 8, "batch": 24, "feed_buf": 2, "day0_land": True},
    {"name": "Apex_6C_6S_15M_B24", "cows": 6, "sheep": 6, "geese": 0, "melons": 15, "c2_melons": 8, "batch": 24, "feed_buf": 2, "day0_land": True},
    {"name": "Apex_8C_4S_4G_15M_B24", "cows": 8, "sheep": 4, "geese": 4, "melons": 15, "c2_melons": 8, "batch": 24, "feed_buf": 2, "day0_land": True},
    {"name": "Apex_8C_4S_20M_B24", "cows": 8, "sheep": 4, "geese": 0, "melons": 20, "c2_melons": 10, "batch": 24, "feed_buf": 2, "day0_land": True},
    {"name": "Apex_8C_4S_10M_B24", "cows": 8, "sheep": 4, "geese": 0, "melons": 10, "c2_melons": 5, "batch": 24, "feed_buf": 2, "day0_land": True},
    {"name": "Apex_8C_4S_15M_B18", "cows": 8, "sheep": 4, "geese": 0, "melons": 15, "c2_melons": 8, "batch": 18, "feed_buf": 2, "day0_land": True},
]

print(f"Defined {len(STRATEGY_GRID)} strategic variants for 1.32.7 meta optimization.")
