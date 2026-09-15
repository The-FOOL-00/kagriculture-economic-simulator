import json

with open("external_repos/lixingtao123-Kaggriculture/opponents/top1_tetsuya/replays/episode-104058487-replay.json", "r") as f:
    d2 = json.load(f)
with open("external_repos/lixingtao123-Kaggriculture/opponents/top1_tetsuya/replays/episode-104060611-replay.json", "r") as f:
    d3 = json.load(f)

# Both are seat 0
farmer_match = 0
hands_match = 0
total_hands_comp = 0
for s in range(720):
    a2 = d2["steps"][s][0].get("action") or {}
    a3 = d3["steps"][s][0].get("action") or {}
    
    if a2.get("farmer") == a3.get("farmer"):
        farmer_match += 1
        
    h2 = a2.get("hands", [])
    h3 = a3.get("hands", [])
    min_len = min(len(h2), len(h3))
    for i in range(min_len):
        total_hands_comp += 1
        if h2[i] == h3[i]:
            hands_match += 1

print(f"Farmer exact match rate: {farmer_match}/720 ({farmer_match/720*100:.1f}%)")
if total_hands_comp > 0:
    print(f"Hands exact match rate : {hands_match}/{total_hands_comp} ({hands_match/total_hands_comp*100:.1f}%)")
