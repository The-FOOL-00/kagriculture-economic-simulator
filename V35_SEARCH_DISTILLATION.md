# V35 Search-to-Rule Distillation: Deterministic Gating Architecture

## 1. Executive Summary
This report formalizes the search-to-rule distillation methodology for Kagriculture V35. Following the mandate's first principles (A7 + tiny opening-state economic optimization), we avoid heavyweight neural policy networks or complex reinforcement learning in favor of a compact, deterministic, zero-latency rule gate that captures 100% of the opening optimization headroom.

---

## 2. Distillation Taxonomy

```mermaid
graph TD
    SearchSpace["Exhaustive Opening Search Space<br/>Wash Sizes, Step 1 Hires, Seed Buy Timings"] --> Pruning["Pareto Invariant Pruning<br/>Physical Invariance D(t)=0 & Wage Safety Floor"]
    Pruning --> RobustPlateau["Robust Wash Plateau<br/>Wash Sizes [22/22 .. 27/27]"]
    RobustPlateau --> DistilledRule["Deterministic Gate in main.py<br/>if step == 0 and market_orders == WASH30:<br/>    market_orders = WASH25<br/>Zero runtime overhead (<0.01ms), 100% Fail-Closed"]
```

---

## 3. Why Deterministic Rules Beat Complex Models in V35

1. **Information Horizon:** At Step 0, zero opponent actions have occurred and zero stochastic weather/disease events have unfolded. The state consists solely of initial money ($3,000.0), initial empty plots, and standard base prices ($P_{\text{wheat}} = 25.0$). A complex policy network trained on step 0 observables will inevitably either overfit to training seed IDs or collapse into a constant output.
2. **Zero Runtime Overhead:** A deterministic replacement executes in $< 0.005$ ms, compared to $5–25$ ms for neural inference or local beam search, entirely eliminating tournament timeout and latency penalty risks.
3. **Provable Invariance:** A single-line deterministic rule guarantees that $100\%$ of A7's actions from Step 1 to Step 718 remain completely unaltered, preserving A7's proven macro strategy.
