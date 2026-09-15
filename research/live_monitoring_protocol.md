# Championship Live Monitoring Protocol & Telemetry Standard

**Document ID**: `research/live_monitoring_protocol.md`  
**Purpose**: Prescribe exact quantitative procedures for live match monitoring, leaderboard tracking, pairwise head-to-head comparison, and empirical decision rules once agents are deployed.  

---

## 1. Primary and Secondary Evaluation Hierarchy

When evaluating live performance on Kaggle's public matchmaking ladder, metrics must be evaluated in strict priority order:

```
[Level 1: Primary]    MATCH OUTCOME (Binary Win / Loss / Tie Record)
                           │
[Level 2: Secondary]  RATING TRAJECTORY & OPPONENT STRENGTH ADJUSTED WIN RATE
                           │
[Level 3: Diagnostic] COIN MARGIN (Net $ difference — DIAGNOSTIC ONLY)
```

### Level 1: Match Outcome (Primary Metric)
- **Wins / Losses / Ties**: Win rate is the definitive arbiter of competitive fitness.
- A bot that wins by $5.00$ earns the same competitive standing as a bot that wins by $50,000.00$.
- **Close-Game Conversion Rate**: The proportion of matches where final coin delta $|\Delta| \le \$500$ converted to wins.

### Level 2: Rating Trajectory (Secondary Metric)
- **Elo / Glicko Rating Convergence**: Track rating over cumulative match count $N \in [10, 50, 100, 250, 500]$.
- **Opponent Quality**: Weight wins against top-quartile leaderboard agents higher than wins against passive or random baselines.
- **Rating Stability**: Standard error of rating estimates $\sigma / \sqrt{N}$.

### Level 3: Coin Margin (Diagnostic Only)
- **Warning**: Do NOT infer agent superiority from raw coin margins alone.
- Offline advantage was measured at $+\$111.27$ mean paired delta. In live multiplayer dynamics, high coin margins against weak baselines can mask critical game-losing vulnerabilities against elite opponents.

---

## 2. Head-to-Head Pairwise Comparison Protocol

For every episode where **Agent A (V54++)** and **Agent B (V54++ Residual)** encounter identical opponents or face each other:

### 1. Opponent Class Archetype Matrix
Track outcomes across 4 distinct opponent archetypes:
1. **Early Rush / Wheat Hoarders**: Rapid early market exhaustion and aggressive wheat sales.
2. **Livestock Specialists (Apex / Quad-Livestock)**: Cow/Sheep scaling with high mid-to-late game milk/wool volume.
3. **Strawberry / Crop Monoculture**: High land-allocation crop strategies with heavy fertilizer investment.
4. **Passive / Baseline Bots**: Low-action or uncoordinated agents.

### 2. Live Matchup Logging Schema
For each recorded match, capture:
- Match ID & Timestamp
- Candidate Identity (`V54++` vs `V54++ Residual`)
- Opponent Team Name & Opponent ID
- Opponent Pre-Match Rating
- Match Result (`WIN` / `LOSS` / `TIE`)
- Candidate Final Cash ($)
- Opponent Final Cash ($)
- Cash Margin ($)
- Town Shop Sequence (Step 72 unlock, Step 144 unlock)
- Step 0–72 Market Liquidity Realization

---

## 3. Critical Interpretation Rules

### Rule 1: The +$111 Offline Advantage Reality Check
- Offline validation proved a mean advantage of $+\$111.27$ ($95\%\text{ CI } [+\$98.12, +\$124.78]$).
- This is a precision **residual margin optimization**, NOT a macro-strategic paradigm shift.
- Expect modest, incremental rating separation, NOT an immediate jump of several hundred Elo points.

### Rule 2: Close-Game Conversions are the Key Validator
- The theoretical hypothesis behind residual preemption (`preempt_money_deficit = 2000.0`, `preempt_minimum_delta = 4.0`, `preempt_maximum_batch = 12`) is that it recaptures liquidity in contested market turns.
- If Agent B exhibits higher conversion rates in games decided by $<\$500$, the offline causal mechanism is confirmed in live play.

### Rule 3: Zero Rationalization of Contradictory Evidence
- If live ladder results show Agent B underperforming Agent A across $>100$ games, do NOT rationalize the discrepancy.
- Treat live empirical evidence as authoritative over synthetic local simulations.

---

## 4. Operational Invariants (Anti-Chasing Rules)

1. **No Chasing Initial Leaderboard Noise**:
   - Initial 10–20 games have massive sampling variance. Do NOT submit replacements, rerolls, or adjustments based on early fluctuations.
2. **No Rerolls**:
   - Resubmission to seek favorable matchmaking draws is strictly prohibited.
3. **No Third Submission**:
   - Maximum active submissions on Kaggle is 2. Submitting a third agent forces retirement of an active candidate.
   - Retain exactly the two approved agents until formal review threshold ($N \ge 200$ games) is reached.
