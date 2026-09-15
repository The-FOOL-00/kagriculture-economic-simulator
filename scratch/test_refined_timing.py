import os
import sys

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, ".")
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2

class RefinedTimingAgent(ClosedLoopAgentV2):
    """
    Refined Market Timing:
    1. STRICT INVARIANT: Steps 0 to 143 (Days 0-6) are 100% untouched.
    2. After Step 144: if cash > $2,000, align non-essential commodity sales
       (Strawberry, Milk, Wool) to step % 4 == 1 (immediately after shop pull).
    3. Micro-batch sales: cap single-step sell orders to max 8 units to prevent slippage.
    4. Enforce JIT headroom: if projected_shed > 96, sell immediately.
    """
    def __init__(self):
        super().__init__(jit_headroom_threshold=96)
        self.pending_sales = {}

    def act(self, obs):
        step = int(obs["step"])
        player = int(obs["player"])
        
        # Steps 0 to 143: execute base V2 logic strictly untouched
        if step < 144:
            return super().act(obs)
            
        # Get base V2 action
        action = super().act(obs)
        if step >= mod_r.LAST_STEP:
            return action

        cash = float(obs["farms"][player]["money"])
        view = mod_r.FarmView(obs)
        stock = mod_r.projected_shed(action, view)
        feed_res = self._compute_feed_reserve(obs, player)
        
        # If cash is low (< $2,000) or shed is near capacity (> 94), execute immediately
        if cash < 2000 or sum(stock.values()) > 94:
            # Flush pending sales if any
            if self.pending_sales:
                for it, q in list(self.pending_sales.items()):
                    if q > 0 and len(action["market"]) < mod_r.MAX_ORDERS:
                        action["market"].append(["SELL", it, q])
                self.pending_sales.clear()
            action["market"] = action["market"][:mod_r.MAX_ORDERS]
            return action

        # After step 144 with safe cash and safe shed:
        # Separate market orders
        non_sells = []
        sells = {}
        for m in action.get("market", []):
            if not m: continue
            if m[0] == "SELL" and len(m) >= 3:
                it, q = m[1], max(0, int(m[2]))
                sells[it] = sells.get(it, 0) + q
            else:
                non_sells.append(m)

        # Merge in pending sales
        for it, q in list(self.pending_sales.items()):
            if q > 0:
                sells[it] = sells.get(it, 0) + q
        self.pending_sales.clear()

        # Check if this is post-pull step (step % 4 == 1)
        is_post_pull = (step % 4 == 1)
        
        new_sells = []
        for it, q in sells.items():
            if q <= 0: continue
            
            # Wheat and fertilizer are never deferred
            if it in ["WHEAT", "FERTILIZER"]:
                new_sells.append(["SELL", it, q])
                continue

            # On post-pull steps (step % 4 == 1), sell up to 8 units
            if is_post_pull:
                batch = min(q, 8)
                new_sells.append(["SELL", it, batch])
                rem = q - batch
                if rem > 0:
                    self.pending_sales[it] = rem
            else:
                # On non post-pull steps, defer up to 6 units to the next post-pull step
                if q > 4:
                    sell_now = 4
                    defer = q - 4
                    new_sells.append(["SELL", it, sell_now])
                    self.pending_sales[it] = defer
                else:
                    new_sells.append(["SELL", it, q])

        combined = non_sells + new_sells
        action["market"] = combined[:mod_r.MAX_ORDERS]
        return action

def test():
    test_seeds = [50001, 50004, 50006, 50007, 50011, 50013, 50016, 50028, 50037, 50042]
    print("="*80)
    print("TESTING REFINED TIMING AGENT vs DMITRII BASE & CLOSED-LOOP V2")
    print("="*80)

    wins = 0
    losses = 0
    margins = []

    for s in test_seeds:
        # Match Seat 0: Refined vs Dmitrii
        p_ref_0 = RefinedTimingAgent()
        p_dmi_1 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        g0 = kagsim.Game(s)
        while not g0.done:
            g0.step(p_ref_0.act(g0.observe(0)), p_dmi_1.act(g0.observe(1)))
        ref_s0 = g0.reward(0)
        dmi_s1 = g0.reward(1)
        m0 = ref_s0 - dmi_s1
        margins.append(m0)
        if m0 > 0: wins += 1
        elif m0 < 0: losses += 1

        # Match Seat 1: Dmitrii vs Refined
        p_dmi_0 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        p_ref_1 = RefinedTimingAgent()
        g1 = kagsim.Game(s)
        while not g1.done:
            g1.step(p_dmi_0.act(g1.observe(0)), p_ref_1.act(g1.observe(1)))
        dmi_s0 = g1.reward(0)
        ref_s1 = g1.reward(1)
        m1 = ref_s1 - dmi_s0
        margins.append(m1)
        if m1 > 0: wins += 1
        elif m1 < 0: losses += 1

        # V2 baseline
        p_v2_0 = ClosedLoopAgentV2()
        p_dmi_1_v2 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        gv2 = kagsim.Game(s)
        while not gv2.done:
            gv2.step(p_v2_0.act(gv2.observe(0)), p_dmi_1_v2.act(gv2.observe(1)))
        v2_s0 = gv2.reward(0)

        print(f"Seed {s:5d}: Ref S0 ${ref_s0:,.0f} vs Dmi S1 ${dmi_s1:,.0f} (M0: {m0:+,.0f}) | Ref S1 ${ref_s1:,.0f} vs Dmi S0 ${dmi_s0:,.0f} (M1: {m1:+,.0f}) | V2 S0: ${v2_s0:,.0f} (Ref-V2: {ref_s0-v2_s0:+,.0f})")

    mean_m = sum(margins) / len(margins)
    print("-" * 80)
    print(f"Total: {len(margins)} | Wins: {wins} | Losses: {losses} | Win Rate: {wins/len(margins)*100:.1f}% | Mean Margin: ${mean_m:+,.2f}")

if __name__ == "__main__":
    test()
