import kagsim

pizza_seeds = []
pet_seeds = []

for s in range(50000, 50200):
    g = kagsim.Game(s)
    # Fast forward to step 144
    for _ in range(144):
        g.step({'farmer': ['PASS'], 'hands': [], 'market': []}, {'farmer': ['PASS'], 'hands': [], 'market': []})
    shops = g.observe(0)['town']['unlocked_shops']
    if 'PIZZA_SHOP' in shops:
        pizza_seeds.append((s, shops))
    if 'PET_CAFE' in shops:
        pet_seeds.append((s, shops))

print(f"Found {len(pizza_seeds)} Pizza seeds in 50000-50200:")
for s, sh in pizza_seeds[:10]:
    print(f"  Seed {s}: {sh}")

print(f"\nFound {len(pet_seeds)} Pet Cafe seeds in 50000-50200:")
for s, sh in pet_seeds[:10]:
    print(f"  Seed {s}: {sh}")
