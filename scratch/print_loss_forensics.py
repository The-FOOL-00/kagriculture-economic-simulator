import json

def print_loss_forensics():
    losses = json.load(open("scratch/reconstructed_live_losses_forensics.json"))
    
    print("=" * 100)
    print("PHASE 1: LIVE LOSS RECONSTRUCTION & FORENSICS")
    print("=" * 100)
    
    for idx, l in enumerate(losses):
        ep_id = l["episode_id"]
        seat = l["our_seat"]
        opp_id = l["opp_sub_id"]
        seed = l["seed"]
        shops = l["shops"]
        rewards = l["final_rewards"]
        our_r = rewards[seat]
        opp_r = rewards[1 - seat]
        margin = our_r - opp_r
        
        print(f"\n----------------------------------------------------------------------------------------------------")
        print(f"LOSS #{idx+1}: Episode {ep_id} | Seat: P{seat} | Opponent: {opp_id} | Seed: {seed}")
        print(f"Shops: {shops}")
        print(f"Final Outcome: Us: ${our_r:,.0f} | Opp: ${opp_r:,.0f} | Margin: ${margin:+,.0f}")
        print(f"----------------------------------------------------------------------------------------------------")
        
        # Checkpoints table
        print(f"{'Day':<5} | {'Our Cash':<9} | {'Opp Cash':<9} | {'Margin':<9} | {'Our H':<5} | {'Opp H':<5} | {'Our Crops':<20} | {'Opp Crops':<20} | {'Our Ani':<12} | {'Opp Ani':<12}")
        print("-" * 115)
        
        cps = l["checkpoints"]
        first_div_step = None
        for day_str in ["3", "6", "9", "10", "11", "12", "13", "14", "15", "18", "21", "24", "27", "30"]:
            if day_str not in cps: continue
            cp = cps[day_str]
            our_c = cp["our"].get("money", 0)
            opp_c = cp["opp"].get("money", 0)
            m = our_c - opp_c
            our_h = cp["our"].get("hands", 0)
            opp_h = cp["opp"].get("hands", 0)
            our_crops = str(cp["our"].get("crops", {}))
            opp_crops = str(cp["opp"].get("crops", {}))
            our_ani = str(cp["our"].get("animals", {}))
            opp_ani = str(cp["opp"].get("animals", {}))
            
            print(f"D{day_str:<3} | ${our_c:7,.0f} | ${opp_c:7,.0f} | ${m:+7,.0f} | {our_h:3d}   | {opp_h:3d}   | {our_crops[:20]:<20} | {opp_crops[:20]:<20} | {our_ani[:12]:<12} | {opp_ani[:12]:<12}")
            
        # First irreversible divergence: look at turn-by-turn cash
        our_trace = l["cash_trace_our"]
        opp_trace = l["cash_trace_opp"]
        # Find when opp took lead and never gave it back
        last_our_lead = -1
        for s in range(len(our_trace)):
            if our_trace[s] >= opp_trace[s]:
                last_our_lead = s
                
        # Find lowest cash point for us between Day 8 and Day 15
        min_cash_d8_15 = min(our_trace[8*24:15*24])
        step_min_cash = 8*24 + our_trace[8*24:15*24].index(min_cash_d8_15)
        
        print(f"\n  * Irreversible Opponent Lead established: Step {last_our_lead + 1} (Day {(last_our_lead+1)//24}, Hour {(last_our_lead+1)%24})")
        print(f"  * Our minimum cash in Day 8-15 window: ${min_cash_d8_15:,.0f} at Step {step_min_cash} (Day {step_min_cash//24}, Hour {step_min_cash%24})")
        print(f"  * Our Key Market Orders: {list(l['our_market_counts'].items())[:8]}")
        print(f"  * Opp Key Market Orders: {list(l['opp_market_counts'].items())[:8]}")

if __name__ == "__main__":
    print_loss_forensics()
