import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
import copy
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2

# Load Yuyajk trace
with open("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json") as f:
    yuyajk_steps = json.load(f)["steps"]

yuyajk_trace = [s[1].get("action", {}) for s in yuyajk_steps]

class SafeJITAgent:
    def __init__(self, use_v2_controller=True):
        self.use_v2_controller = use_v2_controller
        self.last_step = -1

    def __call__(self, obs, config=None):
        step = int(obs.get("step", 0) or 0)
        player = int(obs.get("player", 0) or 0)
        farm = obs.get("farms", [{}])[player]
        private = obs.get("private", {}) or {}
        shed = private.get("shed", {}) or {}
        money = float(farm.get("money", 0) or 0)
        
        # 1. Base action from Yuyajk trace
        if step < len(yuyajk_trace):
            action = copy.deepcopy(yuyajk_trace[step])
        else:
            action = {"farmer": ["PASS"], "hands": [], "market": []}
            
        # 2. Terminal controller at step >= 712
        if step >= 712:
            return v2._terminal_action(obs)
            
        # 3. Market safety: If money is low, protect animal feed!
        # Deterministic JIT feed protection:
        # If shed has <= 2 wheat and step % 24 < 20 and money >= 50, ensure we buy feed
        shed_wheat = shed.get("WHEAT", 0)
        orders = action.get("market", [])
        
        # Check if buying wheat is already present
        buying_wheat = any(isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT" for o in orders)
        
        # If shed wheat is critical (<= 2) and not currently buying wheat
        if shed_wheat <= 2 and not buying_wheat and money >= 60 and len(orders) < 10:
            orders.append(["BUY_PRODUCT", "WHEAT", 2])
            
        # Check if we can afford all buy orders. If not, drop non-essential buys (e.g. seeds, hires) to preserve feed!
        # Compute cost of buy orders
        prices = (obs.get("market") or {}).get("prices") or {}
        total_buy_cost = 0
        filtered_orders = []
        # Sort sells first, then feed, then others
        sells = [o for o in orders if isinstance(o, list) and len(o) >= 1 and o[0] == "SELL"]
        feed_buys = [o for o in orders if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT"]
        other_buys = [o for o in orders if o not in sells and o not in feed_buys]
        
        # In kaggriculture, sells generate cash during the turn
        # But to be safe against cash starvation:
        action["market"] = (sells + feed_buys + other_buys)[:10]
        
        return action

# Test SafeJITAgent vs V2 across seeds 42, 100, 2026
safe_agent = SafeJITAgent()
for seed in [42, 100, 2026]:
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([v2.agent, safe_agent])
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    print(f"Seed {seed}: V2={r0:,.0f}, SafeJIT={r1:,.0f}, Margin={r1-r0:+,.0f}")
