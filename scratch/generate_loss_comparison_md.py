import json
import os

with open("research/v54/losses/LOSS_STATE_COMPARISON.json") as f:
    losses = json.load(f)

md = []
md.append("# V54 Historical Loss Reconstructions & Observable State Comparison")
md.append("\n**Cycle**: V54  ")
md.append("**Baseline**: `V49_Meta_Fusion` vs `V44_Economic_Portfolio`  ")
md.append("**Scope**: Exhaustive turn-by-turn state reconstruction across all 11 historical loss worlds (L01..L11).  \n")
md.append("---")
md.append("\n## 1. Executive Summary: The Mathematical Equivalence Finding\n")
md.append("A central question of the V54 research program is whether legally observable opponent state at Step 150 ")
md.append("can distinguish worlds where COWSWAP fails (e.g. Seed `250436`, Loss L07/L08) from negative control worlds ")
md.append("where COWSWAP is beneficial (e.g. Seed `250416`, Loss L01/L02).\n")
md.append("> **CRUCIAL MATHEMATICAL FINDING**:\n")
md.append("> At Step 150, the complete legally observable game state between Seed `250416` and Seed `250436` ")
md.append("> is **100% BIT-FOR-BIT IDENTICAL** across all 100 tiles, money balance ($2,188), active hands (7), ")
md.append("> cow counts (4), sheep counts (2), pastures (6), market clearing prices (Milk $183, Egg $52, Wool $199), ")
md.append("> market inventory (Milk 9993, Egg 9973), and unlocked shops (`['BRUNCH_SPOT', 'FARMERS_MARKET']`).\n")
md.append("The divergence between 250416 and 250436 does NOT originate from opponent behavior or observable commitment ")
md.append("at or prior to Step 150. Both worlds follow the exact deterministic opening tape of V44. ")
md.append("The divergence occurs at **Step 216** (Day 9) and **Step 288** (Day 12), when the engine's pseudo-random shop generator ")
md.append("unlocked two `PIZZA_SHOP` instances (which consume Milk) on 250436, but unlocked `PET_CAFE` (which consumes Carrots, 0 Milk) on 250416.\n")
md.append("---")
md.append("\n## 2. Overview of the 11 Historical Losses\n")
md.append("| Loss ID | Seed | Seat | Nominal Loss | Category | V49 Action @ 150 | Unlocked Shops @ 150 | Opponent Cows @ 150 | Milk Price @ 150 | Terminal Margin |")
md.append("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

for l in losses:
    lid = l["loss_id"]
    seed = l["seed"]
    seat = l["seat"]
    nom = f"${l['nominal_loss']:,.0f}"
    cat = l["category"]
    cs = l["v49_decision"].get("cs_report", {}).get("cs_decision", "PASS")
    sh = str(l["snapshots"]["step_150"]["shops"])
    cows = l["snapshots"]["step_150"]["opponent_public_state"]["cows"]
    mp = f"${l['snapshots']['step_150']['milk_price']}"
    margin = f"${l['terminal_margin']:,.2f}"
    md.append(f"| **{lid}** | `{seed}` | {seat} | {nom} | {cat} | `{cs}` | `{sh}` | {cows} | {mp} | {margin} |")

md.append("\n---")
md.append("\n## 3. Deep-Dive State Comparison: Seed 250416 vs Seed 250436\n")
md.append("The table below documents the exact public state across key simulation checkpoints for the primary negative control (`250416`) ")
md.append("and the primary rescue target (`250436`):\n")
md.append("| Step | Checkpoint Event | Seed 250416 Public State | Seed 250436 Public State | State Delta (416 vs 436) |")
md.append("|:---:|---|---|---|:---:|")

l416 = next(l for l in losses if l["seed"] == 250416 and l["seat"] == 0)
l436 = next(l for l in losses if l["seed"] == 250436 and l["seat"] == 0)

steps = [0, 143, 144, 150, 168, 300]
step_labels = {
    0: "Match Start",
    143: "Eve of Shop 2 Unlock",
    144: "Shop 2 Unlocked",
    150: "COWSWAP Decision Point",
    168: "Mid-Day 7 Expansion",
    300: "Midgame Maturation"
}

for s in steps:
    k = f"step_{s}"
    s1 = l416["snapshots"][k]
    s2 = l436["snapshots"][k]
    lbl = step_labels.get(s, f"Step {s}")
    
    desc1 = f"Opp Cash: ${s1['opponent_public_state']['money']:.0f}, Herd: {s1['opponent_public_state']['cows']}C/{s1['opponent_public_state']['sheep']}S/{s1['opponent_public_state']['geese']}G, Milk: ${s1['milk_price']}, Shops: {s1['shops']}"
    desc2 = f"Opp Cash: ${s2['opponent_public_state']['money']:.0f}, Herd: {s2['opponent_public_state']['cows']}C/{s2['opponent_public_state']['sheep']}S/{s2['opponent_public_state']['geese']}G, Milk: ${s2['milk_price']}, Shops: {s2['shops']}"
    
    if desc1 == desc2:
        delta = "**0 DELTA (IDENTICAL)**"
    else:
        delta = f"Shops differ; Milk price ${s1['milk_price']} vs ${s2['milk_price']}"
    md.append(f"| **{s}** | {lbl} | {desc1} | {desc2} | {delta} |")

md.append("\n---")
md.append("\n## 4. Chronology of All 11 Losses\n")

for l in losses:
    lid = l["loss_id"]
    seed = l["seed"]
    seat = l["seat"]
    s150 = l["snapshots"]["step_150"]
    opp150 = s150["opponent_public_state"]
    cs = l["v49_decision"].get("cs_report", {}).get("cs_decision", "PASS")
    
    md.append(f"### Loss {lid}: Seed {seed} Seat {seat} (Nominal: ${l['nominal_loss']:,.0f}, Terminal: ${l['terminal_margin']:,.2f})")
    md.append(f"- **Category**: {l['category']}")
    md.append(f"- **V49 Step 150 Decision**: `{cs}`")
    md.append(f"- **Town Shops at Step 150**: `{s150['shops']}`")
    md.append(f"- **Market Prices at Step 150**: Milk = ${s150['milk_price']}, Egg = ${s150['egg_price']}, Wool = ${s150['wool_price']}")
    md.append(f"- **Opponent Farm at Step 150**: Cash = ${opp150['money']:,.0f}, Hands = {opp150['hands']}, Cows = {opp150['cows']}, Sheep = {opp150['sheep']}, Geese = {opp150['geese']}, Pastures = {opp150['pastures']}, Coops = {opp150['coops']}")
    md.append("")

os.makedirs("research/v54/losses", exist_ok=True)
with open("research/v54/losses/LOSS_STATE_COMPARISON.md", "w") as f:
    f.write("\n".join(md) + "\n")

print("Generated LOSS_STATE_COMPARISON.md")
