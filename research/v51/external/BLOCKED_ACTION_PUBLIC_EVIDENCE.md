# External Evidence Audit: Blocked-Action Recovery & Community Meta Findings

**Topic:** Public Community Intelligence on Blocked Actions, Replay Brittleness, and Top-Tier Meta Transfer  
**Primary Sources:**
1. Rayk Kretzschmar: *Kaggriculture: Findings from Zero to Top Meta* (Kernel `raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta`)
2. Avineesh Arora: *What actually predicted the ladder, and 15 things that didn't* (Discussion `#742856`, September 2026)
3. Debmalya: *Byte-Identical Simulator & Tournament Toolkit* (Discussion `#742943`)
4. Kaito Fukami: *Strict-Future Replay & Action Recovery Series* (v27, v43, v48)

---

## 1. The Core Public Lead: Blocked-Action Recovery

In competitive Kaggriculture, the dominant paradigm among top bots (such as the 2945 farm and 3009) is **deterministic action tape replay**. While open-loop tapes provide near-optimal physical efficiency and worker synchronization, they suffer from a single catastrophic vulnerability:

> **A single unexpected physical blocker can desynchronize an entire 719-step worker schedule.**

When an actor attempts an action that is blocked by the environment (e.g., trying to `PLANT` or `BUILD_PASTURE` on a tile where a `WEED` has randomly spawned), the game engine silently rejects the action or executes a `PASS`. The worker then advances to its next scheduled action on the subsequent turn, while the prerequisite task remains unfulfilled. This causes cascading failures:
- Crops are not planted, so future harvest orders find empty plots.
- Pastures are not built, preventing subsequent animal acquisitions.
- Workers wander off-sequence, blocking adjacent paths.

### The Proposed Public Recovery Pattern:
```text
blocked action -> queue intended action -> clear blocker -> replay intended action -> resume tape
```

In Kaito Fukami's published notebooks, this pattern was codified into `scripts.v22_weed_repair`:
1. Detect collision: intended `PLANT` or `BUILD_PASTURE` on a tile with `kind == "WEED"`.
2. Intercept: execute `["DIG"]` on turn $t$.
3. Retry: execute the original intended action on turn $t+1$.
4. Replay buffer: shift the actor's subsequent scheduled actions by 1 turn for the next 8 steps, snapping back to the base route when actions realign.

---

## 2. Synthesis of Community Discussion: "What Actually Predicted the Ladder"

From discussion topic `#742856` (Avineesh Arora) and community post-mortems across 15 tested paradigms:

### What Actually Predicted Ladder Success:
1. **Local Engine Determinism:** `kaggle-environments==1.32.7` matches the live Kaggle sandbox to the exact cent for fixed seeds. Local evaluation on deterministic paired seeds is 100% predictive of live performance when sample sizes are sufficiently large ($N \ge 256$).
2. **Extreme Score Density at Top Elo:** At 2200+ Elo, 40% of matches are decided by $< \$100$, and 78% by $< \$1,000$. Minor tactical rescues (e.g. recovering 1 unplanted crop or 1 unfertilized plot) frequently flip losses into wins.
3. **Strict Win Rate Optimization:** Bradley-Terry rating penalizes losses symmetrically regardless of deficit magnitude. Eliminating rare tail-end losses (even at small margins) drives disproportionately large ladder jumps.
4. **Local Feedback over Global Rewriting:** Successful interventions preserve 99%+ of the underlying choreography and intervene only when an observable precondition fails.

### What Failed (The "15 Things That Didn't"):
1. **Micro Behavioral Cloning:** Training neural policies on scraped top replays yielded agents unable to bank even $\$1,000$ due to spatial and temporal compounding errors.
2. **PPO / RL Splicing:** Reinforcement learning agents failed to coordinate multi-unit 719-step economic cascades, suffering catastrophic policy drift.
3. **Unguided Midgame Route Switching ($t \ge 144$):** Evaluating market divergence at $t=144$ and switching routes destroyed farm capitalization, yielding a 33% win rate.
4. **Arbitrary Early Selling:** Splitting sales or liquidating inventories prematurely collapsed market prices and cost $-\$60,000$ to $-\$80,000$ per game.

---

## 3. Critical Scientific Assessment for V51

| Question | Assessment Based on Public Evidence | Local Verification Requirement |
| :--- | :--- | :--- |
| **Is weed repair a proven win?** | **Hypothesis.** It was part of Kaito's 3009 bot, but 3009 as a whole lost 100% of matches against V44 locally. | Must test weed repair in isolation on top of V49 to establish causal delta. |
| **Does weed repair alter unrelated actions?** | **No.** In `scripts.v22_weed_repair`, only the blocked actor's unit action is altered; market orders and other workers are untouched. | Must prove zero divergence when no weeds are present across all turns. |
| **Do weeds actually block V49?** | **Unknown.** In the 2945 farm (which V49 inherits), the opening sequence tills and manages plots early. Weeds only spawn on uncultivated or idle tiles. | Must instrument V49 across hundreds of seeds to measure exact weed collision frequency. |
| **Can we generalize past weeds?** | **Research only.** While unit occupancy collisions or cash starvation are theoretically possible, arbitrary repairs risk de-synchronizing the choreography. | Only B1 (Weed Blocker) is eligible for direct promotion; other blockers remain research-only. |
