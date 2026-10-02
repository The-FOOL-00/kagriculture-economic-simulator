import json

with open("research/v54/losses/LOSS_STATE_COMPARISON.json") as f:
    losses = json.load(f)

print(f"{'Loss ID':<8} {'Seed':<8} {'Seat':<5} {'Margin':<10} {'CS Dec':<12} {'Shops @ 150':<30}")
for l in losses:
    cs = l['v49_decision'].get('cs_report', {}).get('cs_decision', '')
    shops = str(l['snapshots']['step_150']['shops'])
    print(f"{l['loss_id']:<8} {l['seed']:<8} {l['seat']:<5} ${l['terminal_margin']:<9.0f} {cs:<12} {shops:<30}")

print("\n" + "="*80)
print("DEEP DIVE: 250416 (Negative Control) vs 250436 (COWSWAP Loss)")
print("="*80)

l_416 = next(l for l in losses if l["seed"] == 250416 and l["seat"] == 0)
l_436 = next(l for l in losses if l["seed"] == 250436 and l["seat"] == 0)
l_439 = next(l for l in losses if l["seed"] == 250439 and l["seat"] == 0)

for step_key in ["step_0", "step_143", "step_144", "step_150", "step_168", "step_300", "step_719"]:
    print(f"\n--- {step_key.upper()} ---")
    s416 = l_416["snapshots"][step_key]
    s436 = l_436["snapshots"][step_key]
    s439 = l_439["snapshots"][step_key]
    
    print(f"250416 Opponent: Money={s416['opponent_public_state']['money']:.0f}, Hands={s416['opponent_public_state']['hands']}, Cows={s416['opponent_public_state']['cows']}, Sheep={s416['opponent_public_state']['sheep']}, Geese={s416['opponent_public_state']['geese']}, Pastures={s416['opponent_public_state']['pastures']}")
    print(f"250436 Opponent: Money={s436['opponent_public_state']['money']:.0f}, Hands={s436['opponent_public_state']['hands']}, Cows={s436['opponent_public_state']['cows']}, Sheep={s436['opponent_public_state']['sheep']}, Geese={s436['opponent_public_state']['geese']}, Pastures={s436['opponent_public_state']['pastures']}")
    print(f"250439 Opponent: Money={s439['opponent_public_state']['money']:.0f}, Hands={s439['opponent_public_state']['hands']}, Cows={s439['opponent_public_state']['cows']}, Sheep={s439['opponent_public_state']['sheep']}, Geese={s439['opponent_public_state']['geese']}, Pastures={s439['opponent_public_state']['pastures']}")
    print(f"Prices 250416: Milk={s416['milk_price']}, Egg={s416['egg_price']}, Wool={s416['wool_price']}")
    print(f"Prices 250436: Milk={s436['milk_price']}, Egg={s436['egg_price']}, Wool={s436['wool_price']}")
    print(f"Prices 250439: Milk={s439['milk_price']}, Egg={s439['egg_price']}, Wool={s439['wool_price']}")
