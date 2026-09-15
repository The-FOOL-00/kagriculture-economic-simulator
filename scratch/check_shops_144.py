import kagsim

for s in [50007, 50012, 50030, 50037, 50266]:
    g = kagsim.Game(s)
    for step in range(300):
        g.step({'farmer': ['PASS'], 'hands': [], 'market': []}, {'farmer': ['PASS'], 'hands': [], 'market': []})
        if step == 144:
            shops = g.observe(0)['town']['unlocked_shops']
            print(f"Seed {s}: shops at 144 = {shops}")
