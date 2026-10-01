# V24 — Competitive Bottleneck Matrix

Prioritization of empirical bottlenecks ranked across 6 rigorous criteria:
1. Frequency among Top-10 agents
2. Size of V22R1 divergence
3. Reproducibility
4. Closed-loop plausibility
5. Implementation feasibility
6. Interaction risk with V3

## Ranked Bottleneck Prioritization

| Rank | Bottleneck Identification | Frequency | Divergence Size | Reproducibility | Closed-Loop Plausibility | Feasibility | V3 Risk | Overall Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Labor Dispatch & Idle-Zeroing** | 100% (10/10) | Severe (~25% early idle) | High | Very High | High | Low | **PRIORITY 1** |
| **2** | **Livestock Capital Allocation (10+ Cows)** | 90% (9/10) | High (+4–6 Cows) | High | High | High | Low | **PRIORITY 2** |
| **3** | **Secondary Crop Fast-Compound (Carrot vs Strawberry)** | 70% (7/10) | Moderate (+35–65 Carrots) | High | High | Medium | Medium | **PRIORITY 3** |
| **4** | **Turn 1 Early Labor Mobilization** | 50% (5/10) | Minor (1-turn shift) | High | Medium | High | Low | Secondary |
| **5** | **Continuous Market Liquidation Tranches** | 80% (8/10) | Moderate (Smooth vs Dump) | High | High | Medium | High | Secondary |

## Top 3 Candidate Action Hypotheses for Backbone Challengers

### Challenger 1 Hypothesis: 'Labor Dispatch & Idle Elimination'
> *Top agents consistently achieve 0.8%–5.1% worker idle rates by instantly assigning secondary tasks (watering/harvesting/patrolling) when primary tasks complete. Modifying V3's farmhand task dispatch to eliminate idle PASS actions will recover ~20% productive labor.* 

### Challenger 2 Hypothesis: 'Livestock Expansion & Clustered Pastures'
> *Top agents (Cluster A) scale to 10–13 Cows and 8–11 Sheep on Days 0–3 with tightly clustered pastures adjacent to the farmhouse. Modifying V3's animal purchase target and pasture placement policy will unlock Cluster A level milk/wool compounding.* 

### Challenger 3 Hypothesis: 'Carrot-Pipelined Fast Compounding'
> *Top agents heavily substitute Carrot for Strawberry during Days 2–15, exploiting Carrot's faster harvest cycle and lower water penalty to build a $25k+ Day 10 cash engine.* 

