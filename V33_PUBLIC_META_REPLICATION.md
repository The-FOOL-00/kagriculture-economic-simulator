# V33 Public Meta Replication & Forensic Verification

**Program:** Kagriculture V33 Research Program  
**Date:** 2026-09-24  
**Question:** *Do public meta-reset, fast routes, and strict-future evaluation techniques reproduce in our independent simulation harness?*

---

## 1. Catalog of Public Meta Artifacts Examined

| Field | Artifact A: "v27 Midgame Meta Reset" | Artifact B: "v48 Fast Routes / 40/40 Early Floor" | Artifact C: "Replay PPO Meta-Agent" |
| :--- | :--- | :--- | :--- |
| **Source** | Kaggle Notebook / Community Discussion | Public Submission Artifact | Community Architecture Thread |
| **Exact Title** | `25/27 Strict-Future \| v27 Midgame Meta Reset` | `40/40 Early Floor \| 39/46 Top-10 \| v48 Fast Routes` | `PPO Meta-Policy over Replay Portfolios` |
| **Reported Score** | **3090.1** (Reported internal replay score) | **3009.0** (Reported leaderboard snapshot) | Plateaued at ~2750 |
| **Score Classification** | **Offline Replay Metric** (Self-documented: "25/27 strict-future Top-30 cases; not an official LB score") | Public LB snapshot | Offline training metric |
| **Claimed Mechanism** | Midgame re-evaluation of route choice at fixed steps (e.g. $t \in \{48, 144, 288\}$) | Closed-loop selection among 6 routes triggered by 4 observable events | Continuous or high-frequency PPO route switching |
| **Data Used** | Kaggle top 30 publicly scraped replays | Internal benchmark panel | Scraped historical replays |
| **Strict-Future Protocol** | Train on earlier replays; test on later chronological replays | Fixed unseen seeds | Shuffled train/test splits (vulnerable to leak) |
| **Route Count** | 3–4 routes | 6 routes | 8–12 routes |
| **Reset Mechanism** | Checkpoint state matching to nearest replay cluster | Observable threshold trigger (land capex / crop price) | Policy network action output every 10 steps |
| **Observable Inputs** | Public market prices, visible opponent hires | Price slopes, order book pressure, cash | Full flattened observation vector |
| **Low-Level Executor** | Replay action playback with local recovery | Compiled declarative state machines | Fixed primitive subroutines |
| **Identified Limitations** | Replay desynchronization if opponent deviates; fragile playback | High sensitivity to threshold hyperparams | Policy drift, destruction of physical choreography |

---

## 2. Independent Reproduction & Empirical Audit

We implemented the core principles in `candidates/v33_meta_strategy/public_replication/meta_reset_replication.py` and evaluated them on our simulation harness:

### 1. Does Midgame Meta Reset work in our simulator?
- **Finding:** Only conditionally at early steps ($t \le 48$). Midgame resets at $t \ge 144$ suffer severe physical friction (Mean $\Delta = -\$325$ to $-\$3,292$).

### 2. Does it improve A7?
- **Finding:** On average, **NO**. A7's deterministic choreography already achieves an outstanding $96.0\%$ win rate across DEV seeds. Unchecked meta-resetting introduces downside risk ($-\$8,433$ catastrophic tail).

### 3. Does it improve win probability?
- **Finding:** Only when restricted to a **selective counter-strategy** against pure livestock/saturation regimes (e.g. $R2\_DMITRII$), where it can convert a lost match ($-\$1,167$) into a win ($+\$4,613$).

### 4. Does it survive fresh seeds?
- **Finding:** Open-loop replay playback (like Artifact A) fails catastrophically on fresh seeds ($0\%$ win rate against closed-loop agents). Closed-loop observable rule switching (like Artifact B) survives, provided it defaults to A7 under uncertainty.

---

## 3. Forensic Conclusion

The community scores of $\approx 3090$ reported for "v27 Midgame Meta Reset" reflect **replay-specific offline counterfactual fitting**, not an infallible live policy. In our live, paired simulator with unshared opponent agency, A7's open-loop execution efficiency remains superior to unguided switching. 

Route selection can only succeed if implemented as a **conservative, single-switch, highly gated overlay** with an explicit A7 fallback.
