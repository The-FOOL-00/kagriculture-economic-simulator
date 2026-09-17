import sys, os
sys.path.insert(0, os.path.abspath("."))
import tarfile, kagsim

with tarfile.open("submission_Vj_kc_v3.tar.gz", "r:gz") as tar:
    code = tar.extractfile("main.py").read().decode("utf-8")

def run_until_575(frontload=False):
    ns0, ns1 = {}, {}
    exec(compile(code, "v3_0.py", "exec"), ns0)
    exec(compile(code, "v3_1.py", "exec"), ns1)
    agent0 = ns0["agent"]
    agent1 = ns1["agent"]
    
    seed = 340224
    g = kagsim.Game(seed)
    
    for s in range(575):
        obs0 = g.observe(0)
        obs1 = g.observe(1)
        a0 = agent0(obs0)
        a1 = agent1(obs1)
        g.step(a0, a1)
        
    obs0 = g.observe(0)
    obs1 = g.observe(1)
    base0 = agent0(obs0)
    base1 = agent1(obs1)
    
    c_before = g.reward(0)
    
    if frontload:
        act0 = dict(base0)
        act0["market"] = [["SELL", "WHEAT", 2], ["BUY_PRODUCT", "WHEAT", 16], ["BUY_PRODUCT", "FERTILIZER", 11]]
    else:
        act0 = base0
        
    g.step(act0, base1)
    c_after = g.reward(0)
    
    return c_before, c_after, c_after - c_before, g.observe(0)

b_bef, b_aft, b_delta, b_obs = run_until_575(frontload=False)
f_bef, f_aft, f_delta, f_obs = run_until_575(frontload=True)

print(f"Baseline:    Before={b_bef}, After={b_aft}, Delta={b_delta}")
print(f"Frontloaded: Before={f_bef}, After={f_aft}, Delta={f_delta}")
print(f"Difference (Frontloaded - Baseline): {f_delta - b_delta}")

# Compare inventory
print("Baseline inventory:", b_obs.get("private", {}).get("inventory"))
print("Frontloaded inventory:", f_obs.get("private", {}).get("inventory"))
