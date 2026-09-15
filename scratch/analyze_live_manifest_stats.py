import json
import os
from collections import defaultdict, Counter

def analyze_live_manifest():
    manifest = json.load(open("scratch/live_episodes_manifest.json", encoding="utf-8"))
    
    print("=" * 80)
    print("STEP 7–11: COMPREHENSIVE LIVE TOURNAMENT REPLAY AUDIT (162 MATCHES)")
    print("=" * 80)
    
    total_matches = 0
    total_wins = 0
    total_losses = 0
    total_ties = 0
    
    sub_stats = {}
    opponent_stats = defaultdict(lambda: {"matches": 0, "wins": 0, "losses": 0, "ties": 0, "our_cash": [], "opp_cash": [], "margins": [], "opp_ratings": []})
    
    margin_distribution = []
    
    for sid, eps in manifest.items():
        s_wins = 0
        s_losses = 0
        s_ties = 0
        s_our_cash = []
        s_opp_cash = []
        s_margins = []
        
        for ep in eps:
            ep_id = ep["id"]
            agents = ep["agents"]
            us = next((a for a in agents if a.get("submissionId") == int(sid)), None)
            them = next((a for a in agents if a.get("submissionId") != int(sid)), None)
            if not us or not them:
                continue
                
            rew_us = us.get("reward") or 0
            rew_them = them.get("reward") or 0
            margin = rew_us - rew_them
            
            total_matches += 1
            s_our_cash.append(rew_us)
            s_opp_cash.append(rew_them)
            s_margins.append(margin)
            margin_distribution.append(margin)
            
            opp_sub = them.get("submissionId")
            opp_score = them.get("initialScore", 0)
            
            opp_entry = opponent_stats[opp_sub]
            opp_entry["matches"] += 1
            opp_entry["our_cash"].append(rew_us)
            opp_entry["opp_cash"].append(rew_them)
            opp_entry["margins"].append(margin)
            opp_entry["opp_ratings"].append(opp_score)
            
            if margin > 0:
                total_wins += 1
                s_wins += 1
                opp_entry["wins"] += 1
            elif margin < 0:
                total_losses += 1
                s_losses += 1
                opp_entry["losses"] += 1
            else:
                total_ties += 1
                s_ties += 1
                opp_entry["ties"] += 1
                
        sub_stats[sid] = {
            "matches": len(s_our_cash),
            "wins": s_wins,
            "losses": s_losses,
            "ties": s_ties,
            "mean_our_cash": sum(s_our_cash) / len(s_our_cash),
            "mean_opp_cash": sum(s_opp_cash) / len(s_opp_cash),
            "mean_margin": sum(s_margins) / len(s_margins),
            "win_rate": (s_wins / len(s_our_cash)) * 100
        }
        
    print(f"\n1. AGGREGATE LIVE TOURNAMENT RECORD:")
    print(f"   Total Matches:  {total_matches}")
    print(f"   Total Record:   {total_wins} Wins / {total_losses} Losses / {total_ties} Ties")
    print(f"   Overall Win Rate: {(total_wins / total_matches) * 100:.2f}%")
    print(f"   Overall Mean Margin: ${sum(margin_distribution) / len(margin_distribution):+,.2f}")
    
    print("\n2. BREAKDOWN BY ACTIVE SUBMISSION:")
    for sid, st in sub_stats.items():
        role = "V54++ Residual (Challenger)" if sid == "56146971" else "V54++ Control (Baseline)"
        print(f"   Submission {sid} [{role}]:")
        print(f"     Matches:      {st['matches']}")
        print(f"     Record:       {st['wins']}W / {st['losses']}L / {st['ties']}T ({st['win_rate']:.1f}% WR)")
        print(f"     Our Mean:     ${st['mean_our_cash']:,.2f}")
        print(f"     Opp Mean:     ${st['mean_opp_cash']:,.2f}")
        print(f"     Mean Margin:  ${st['mean_margin']:+,.2f}")
        
    print("\n3. TAIL RISK & MARGIN DISTRIBUTION:")
    n = len(margin_distribution)
    p_loss_10k = sum(1 for m in margin_distribution if m < -10000) / n * 100
    p_loss_20k = sum(1 for m in margin_distribution if m < -20000) / n * 100
    p_win_10k  = sum(1 for m in margin_distribution if m > 10000) / n * 100
    p_win_20k  = sum(1 for m in margin_distribution if m > 20000) / n * 100
    print(f"   P(Loss > $10,000): {p_loss_10k:5.1f}% ({sum(1 for m in margin_distribution if m < -10000)} matches)")
    print(f"   P(Loss > $20,000): {p_loss_20k:5.1f}% ({sum(1 for m in margin_distribution if m < -20000)} matches)")
    print(f"   P(Win  > $10,000): {p_win_10k:5.1f}% ({sum(1 for m in margin_distribution if m > 10000)} matches)")
    print(f"   P(Win  > $20,000): {p_win_20k:5.1f}% ({sum(1 for m in margin_distribution if m > 20000)} matches)")
    print(f"   Worst Loss:       ${min(margin_distribution):+,.2f}")
    print(f"   Best Win:         ${max(margin_distribution):+,.2f}")
    
    print("\n4. WORST OPPONENT SUBMISSIONS (Most Severe Net Deficits):")
    opp_ranked = []
    for opp_sub, ost in opponent_stats.items():
        m_tot = sum(ost["margins"])
        avg_rating = sum(ost["opp_ratings"]) / len(ost["opp_ratings"])
        opp_ranked.append((m_tot, opp_sub, ost, avg_rating))
        
    opp_ranked.sort()
    for m_tot, opp_sub, ost, avg_rating in opp_ranked[:10]:
        mean_m = m_tot / ost["matches"]
        print(f"   OppSub {opp_sub} (Rating ~{avg_rating:.1f}): {ost['matches']} matches | {ost['wins']}W / {ost['losses']}L | Total Margin: ${m_tot:+8,.0f} (Avg: ${mean_m:+7,.0f}) | Our Cash: ${sum(ost['our_cash'])/len(ost['our_cash']):6,.0f} vs Opp: ${sum(ost['opp_cash'])/len(ost['opp_cash']):6,.0f}")

    print("\n5. BEST OPPONENT SUBMISSIONS (Most Dominant Wins):")
    for m_tot, opp_sub, ost, avg_rating in reversed(opp_ranked[-8:]):
        mean_m = m_tot / ost["matches"]
        print(f"   OppSub {opp_sub} (Rating ~{avg_rating:.1f}): {ost['matches']} matches | {ost['wins']}W / {ost['losses']}L | Total Margin: ${m_tot:+8,.0f} (Avg: ${mean_m:+7,.0f}) | Our Cash: ${sum(ost['our_cash'])/len(ost['our_cash']):6,.0f} vs Opp: ${sum(ost['opp_cash'])/len(ost['opp_cash']):6,.0f}")

if __name__ == "__main__":
    analyze_live_manifest()
