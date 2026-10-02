import json

with open("research/v50/loss_regimes/v49_loss_corpus.json") as f:
    corpus = json.load(f)

for i, l in enumerate(corpus):
    print(f"=== Loss {i+1:02d} (Seed {l['seed']}, Seat {l['seat']}, Margin: {l['final_margin']}) ===")
    print("  Final Inventory:", {k: v for k, v in l["final_inventory"].items() if v > 0})
    print("  Final Seeds:", {k: v for k, v in l["final_seeds"].items() if v > 0})
    print("  Shop Profile:", l["shops"][:4])
