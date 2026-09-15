import json

with open('extracted_agents/dmitrii_lb2800/actions.json') as f:
    tapes = json.load(f)

for t_idx, name in [(7, "Tape 7 (Pizza+Yarn)"), (5, "Tape 5 (PetCafe+Yarn)"), (0, "Tape 0 (Generic)")]:
    tape = tapes[t_idx]
    tomatoes_bought = sum(o[2] for s in tape for o in s.get('market', []) if o and o[0] == 'BUY_SEED' and o[1] == 'TOMATO')
    carrots_bought = sum(o[2] for s in tape for o in s.get('market', []) if o and o[0] == 'BUY_SEED' and o[1] == 'CARROT')
    straws_bought = sum(o[2] for s in tape for o in s.get('market', []) if o and o[0] == 'BUY_SEED' and o[1] == 'STRAWBERRY')
    melons_bought = sum(o[2] for s in tape for o in s.get('market', []) if o and o[0] == 'BUY_SEED' and o[1] == 'MELON')
    cows_bought = sum(o[2] for s in tape for o in s.get('market', []) if o and o[0] == 'BUY_ANIMAL' and o[1] == 'COW')
    sheep_bought = sum(o[2] for s in tape for o in s.get('market', []) if o and o[0] == 'BUY_ANIMAL' and o[1] == 'SHEEP')
    
    print(f"\n=== {name} ===")
    print(f"Seeds bought: Tomato={tomatoes_bought}, Carrot={carrots_bought}, Straw={straws_bought}, Melon={melons_bought}")
    print(f"Animals bought: Cow={cows_bought}, Sheep={sheep_bought}")
