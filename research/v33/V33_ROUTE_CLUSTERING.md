# V33 Route Clustering & Behavioral Taxonomy

**Program:** Kagriculture V33 Research Program  
**Date:** 2026-09-24  
**Source Dataset:** 72 normalized player trajectories from 36 full-length (720-step) replays  
**Artifacts Generated:** `route_fingerprints.json`, `route_clusters.json`

---

## 1. Feature Vector Representation

Each normalized trajectory was mapped to a 54-dimensional standardized behavioral and economic feature vector:
1. **Worker Trajectory (10 dims):** Worker counts sampled at steps $[12, 24, 48, 72, 120, 240, 360, 480, 600, 719]$.
2. **Land Trajectory (6 dims):** Quadrant count sampled at steps $[72, 144, 288, 432, 576, 719]$.
3. **Crop Allocation Profile (5 dims):** Fraction of planting tiles dedicated to `WHEAT`, `CARROT`, `TOMATO`, `STRAWBERRY`, and `MELON`.
4. **Livestock Allocation Profile (3 dims):** Peak animal stocking for `COW`, `SHEEP`, and `GOOSE`.
5. **Cash Trajectory (30 dims):** Daily closing cash balance at steps $[24, 48, \dots, 720]$, normalized by $\$100,000$.

---

## 2. Clustering Sweep & Evaluation Metrics

We performed $K$-means clustering across $k \in \{2, 3, 4, 5, 6, 8, 10, 12\}$ with $N=10$ random initializations:

| $k$ | Silhouette Score | Inertia (Within-Cluster Sum of Squares) | Separation Quality |
| :---: | :---: | :---: | :--- |
| **$k=2$** | 0.4694 | 697.2 | Coarse (High-capital vs Stalled) |
| **$k=3$** | 0.5070 | 447.7 | Captures low, medium, high activity |
| **$k=4$** | 0.5632 | 324.0 | Separates livestock from monoculture |
| **$k=5$** | 0.5816 | 249.9 | Strong boundary definitions |
| **$k=6$** | **0.6001** | **206.8** | **Optimal Parsimonious Taxonomy** |
| **$k=8$** | 0.5929 | 152.0 | Slight over-fragmentation |
| **$k=10$** | 0.6128 | 114.2 | Fine-grained sub-clusters |
| **$k=12$** | **0.6353** | **83.4** | Highest Silhouette score |

For strategic macro-routing, $k=6$ provides the cleanest balance between statistical separation (Silhouette $>0.60$) and behavioral interpretability.

---

## 3. Structural Taxonomy of the 6 Route Families

### Family 0: Elite Multi-Worker Capital Expanders (`EXP_ELITE`)
- **Cluster Size:** 7 trajectories
- **Mean Terminal Cash:** **$69,321.10**
- **Mean Final Workers:** **11.3 workers**
- **Mean Final Land:** **2.7 quadrants**
- **Strategic Profile:** Aggressive early hiring (`HIRE4` followed by 4–8 additional hands). Heavy investment in both multi-quadrant land expansion and continuous production. High revenue velocity, highly resilient to single market saturations.

### Family 1: Low-Labor Capital Accumulators (`CAP_LEAN`)
- **Cluster Size:** 5 trajectories
- **Mean Terminal Cash:** **$27,300.60**
- **Mean Final Workers:** **1.2 workers**
- **Mean Final Land:** **1.8 quadrants**
- **Strategic Profile:** Minimalist labor overhead (only 1–2 workers). Relies heavily on high-margin cash crops or livestock without scaling wage liability. Never risks insolvency from wage drain.

### Family 2: Standard Agro-Industrial Balance (`AGRO_BALANCED`)
- **Cluster Size:** 35 trajectories (Largest population class)
- **Mean Terminal Cash:** **$21,478.90**
- **Mean Final Workers:** **5.6 workers**
- **Mean Final Land:** **2.9 quadrants**
- **Strategic Profile:** The typical competitive archetype. 5–6 workers managing 2–3 quadrants with mixed wheat, carrots, and cattle. Moderate capital growth, susceptible to market dumps when competitors flood the same town shops.

### Family 3: Compact Livestock Monoculture (`LIVESTOCK_FOCUSED`)
- **Cluster Size:** 7 trajectories
- **Mean Terminal Cash:** **$34,084.00**
- **Mean Final Workers:** **5.9 workers**
- **Mean Final Land:** **1.3 quadrants**
- **Strategic Profile:** Concentrated pasture development on quadrant 1. Heavy cow/sheep milk and wool production with minimal crop farming. Immune to bakery crashes, but highly dependent on the town textile and dairy demands.

### Family 4: Large-Scale Commercial Farmers (`LAND_MAX`)
- **Cluster Size:** 8 trajectories
- **Mean Terminal Cash:** **$41,809.50**
- **Mean Final Workers:** **8.0 workers**
- **Mean Final Land:** **3.2 quadrants**
- **Strategic Profile:** Unlocks 3–4 quadrants early. Uses 8 workers to rotate large crop cycles. Requires substantial working capital buffer to avoid midgame cash squeeze.

### Family 5: Sub-Optimal / Passive Stallers (`STALL_PASSIVE`)
- **Cluster Size:** 10 trajectories
- **Mean Terminal Cash:** **$4,591.10**
- **Mean Final Workers:** **1.0 workers**
- **Mean Final Land:** **1.0 quadrant**
- **Strategic Profile:** Failed starts, stalled workers, or passive benchmark agents. Useful primarily as an adversarial stress-test baseline.
