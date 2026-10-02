# V49 — Live Top-Meta Snapshot (September 26, 2026)

## 1. Executive Context & Leaderboard State

As of September 26, 2026 (4 days prior to the September 30 final deadline), the active competition leaderboard has converged around a cluster of 3000+ rating agents. 

Official Top Leaderboard (Active):
1. **Boey** — Rating: **3097.2** (Submission: 2026-09-24)
2. **DSM** — Rating: **3062.4** (Submission: 2026-09-26)
3. **M & M & P & Q** — Rating: **2995.5** (Submission: 2026-09-25)
4. **Vadim Vasilenko** — Rating: **2993.9** (Submission: 2026-09-25)
5. **DECEM** — Rating: **2981.6** (Submission: 2026-09-25)
6. **Fourth Quadrant** — Rating: **2950.3** (Submission: 2026-09-25)
7. **Unknown Mother-Goose** — Rating: **2942.9** (Submission: 2026-09-26)
8. **吃白饭的大肥鱼** — Rating: **2900.8** (Submission: 2026-09-24)
9. **Majkel1337** — Rating: **2899.2** (Submission: 2026-09-25)
10. **THIRD FARM CLUB** — Rating: **2898.7** (Submission: 2026-09-25)

The official Kaggle daily episodes dataset (`kaggle/kaggriculture-episodes-index`) confirms that top-tier episodes on September 25 have a mean rating of **3070.0** and median rating of **2970.4**.

---

## 2. Key Public Elite Sources Analyzed

The newest top-performing and high-vote public notebooks (September 22–25, 2026) were downloaded, unpacked, and analyzed:

| Agent / Notebook | Author | Votes | Date | Architecture Family | Key Mechanism Introduced |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `abhinav0370/cha22-agent` | Abhinav0370 | 94 | 2026-09-24 | Chassis + Tactical Layers | `e402` late seed cap, `mg` same-item sell merge, `ig` queue hole closure, `v44y` herd wrapper |
| `arsgorynich/herd-safe-v3-experimental-risk-aware-feed` | Arsgorynich | 73 | 2026-09-23 | Chassis + Risk-Aware Feed | `counter T-B` tomato price gate, `counter D` best-response market ordering, `v44y` herd wrapper |
| `guruprasaathas111/kaggriculture-master-engine-v3` | Guru Prasaath S | 122 | 2026-09-25 | Master Chassis Engine | Tactical stack over V39/V44 chassis, order book response |
| `statma/kaggriculture-herd-safe-sale-window-race-ca25` | statma | 11 | 2026-09-23 | Herd-Safe Sale Window | Reservation step 192, horizon 40 / margin 12, sale window race |
| `wzhengbiao/kaggriculture-v15stack-submit` | WUZB | 61 | 2026-09-22 | Stack Ensemble | Pasture/coop multi-agent stack |
| `flexonafft/kaggriculture-multi-route-farming-agent` | Igor Zharov | 112 | 2026-09-25 | Multi-Route Dynamic | Shop-dependent dynamic branching |

---

## 3. Discovered Tactical Mechanisms (Separation of Known vs New)

### A. KNOWN (Already in 2945 / V48)
- `ORDERPRI2` (Rival-harvest tracking and turn-by-turn sell priority)
- `room_guard` (Maintaining shed $\le 99$ before hour 23)
- `clamp_sells` (Trimming SELL orders to projected shed inventory)
- `dead_stock` (Selling commodities the route will not use)
- `Step-144 Shop Routing` (2945 backbone + V48 Route 105 cow preservation)
- `Route 2 Terminal Liquidation` (Multi-stage sweeps at steps 690–695 and 712–718)

### B. NEW (Absent from 2945 / V48 Backbone)
1. **`E402` Late Seed Cap**:
   - At step $\ge 624$ (the final 4 days), calculates exact remaining `PLANT` operations needed in the route tape.
   - Clamps `BUY_SEED` orders for wheat and carrot to prevent purchasing seeds that can never be planted or harvested before step 719.
   - Direct cash savings: 10–20 coins per seed, avoiding dead inventory at game end.
2. **`MG` Same-Item SELL Compaction**:
   - Merges multiple SELL orders of the same commodity into a single order in the turn market list (`[SELL, item, total_qty]`).
   - Prevents running out of the 10 available market order slots per turn.
3. **`IG` Queue Hole-Closure**:
   - Scans market order queue; removes zero-quantity orders and pulls subsequent valid SELL orders forward to ensure all 10 slots execute properly.
4. **`V44Y` Shop-Aware Herd Swapping**:
   - At days 8–11 (steps 192–264), inspects revealed town shops:
     - If `YARN_STORE` is present $\to$ swap cow/goose purchases to `SHEEP`.
     - If no `YARN_STORE` and high milk demand $\to$ swap sheep purchases to `COW`.
5. **`Counter T-B` Tomato Price Gating**:
   - Tomatoes have narrow market anchor $T=200$. Saturated inventory ($\ge 10,200$) collapses price from 300 to 24 or 1. Gating tomato investment by projected market clearing price prevents catastrophic crop losses.
6. **`Counter D` Best-Response Market Ordering**:
   - Permuting SELL orders ahead of fixed-price orders (`HIRE`, `BUY_SEED`, `BUY_ANIMAL`) to generate cash before expenditures execute, preventing emergency loan/cash penalties.
