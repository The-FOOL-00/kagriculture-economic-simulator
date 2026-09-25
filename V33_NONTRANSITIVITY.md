# V33 Non-Transitivity & Graph Structure Analysis

**Program:** Kagriculture V33 Research Program  
**Date:** 2026-09-24  
**Question:** *Is the matchup structure between candidate expert routes transitive or non-transitive?*  
**Dataset:** 150 pairwise match legs over DEV seeds (`249675..249679`)

---

## 1. Directed Dominance Graph Formulation

We define a directed edge $A \longrightarrow B$ if route $A$ achieves a statistically meaningful competitive advantage over route $B$ ($\text{WinRate}(A \text{ vs } B) \ge 60\%$ over 10 paired legs):

### Observed Dominance Edges:
1. `R0_A7` $\longrightarrow$ `R1_V22R1` (10-0, 100% Win Rate, $\Delta = +\$1,280$)
2. `R0_A7` $\longrightarrow$ `R2_DMITRII` (8-2, 80% Win Rate, $\Delta = +\$4,012$)
3. `R0_A7` $\longrightarrow$ `R3_P3090` (10-0, 100% Win Rate, $\Delta = +\$30,272$)
4. `R0_A7` $\longrightarrow$ `R4_V54` (10-0, 100% Win Rate, $\Delta = +\$15,518$)
5. `R0_A7` $\longrightarrow$ `R5_V25P3` (10-0, 100% Win Rate, $\Delta = +\$1,746$)
6. `R1_V22R1` $\longrightarrow$ `R2_DMITRII` (8-2, 80% Win Rate, $\Delta = +\$4,624$)
7. `R1_V22R1` $\longrightarrow$ `R3_P3090` (10-0, 100% Win Rate, $\Delta = +\$30,239$)
8. `R1_V22R1` $\longrightarrow$ `R4_V54` (10-0, 100% Win Rate, $\Delta = +\$15,450$)
9. `R1_V22R1` $\longrightarrow$ `R5_V25P3` (6-4, 60% Win Rate, $\Delta = +\$496$)
10. `R5_V25P3` $\longrightarrow$ `R2_DMITRII` (8-2, 80% Win Rate, $\Delta = +\$3,804$)
11. `R5_V25P3` $\longrightarrow$ `R3_P3090` (10-0, 100% Win Rate, $\Delta = +\$29,842$)
12. `R5_V25P3` $\longrightarrow$ `R4_V54` (10-0, 100% Win Rate, $\Delta = +\$15,478$)
13. `R2_DMITRII` $\longrightarrow$ `R3_P3090` (10-0, 100% Win Rate, $\Delta = +\$47,205$)
14. `R2_DMITRII` $\longrightarrow$ `R4_V54` (10-0, 100% Win Rate, $\Delta = +\$12,148$)
15. `R4_V54` $\longrightarrow$ `R3_P3090` (10-0, 100% Win Rate, $\Delta = +\$15,679$)

---

## 2. Graph Cycle Search Results

We executed a comprehensive cycle-detection search for cycles of length $k \in \{3, 4, 5, 6\}$.

- **Cycles Found:** **ZERO (0)**
- **Graph Topology:** Strictly a **Directed Acyclic Graph (DAG)**.
- **Topological Ordering:**
  $$\mathbf{R0\_A7} \succ \mathbf{R1\_V22R1} \succ \mathbf{R5\_V25P3} \succ \mathbf{R2\_DMITRII} \succ \mathbf{R4\_V54} \succ \mathbf{R3\_P3090}$$

---

## 3. Scientific Implications for V33

Per Section 14 of the research specification:
> *"If the route graph is approximately transitive: a simple strong route may dominate. If the graph is meaningfully non-transitive: route-selection meta becomes much more valuable. Do not assume non-transitivity just because it sounds theoretically interesting. Measure it."*

The empirical measurement is unequivocal:
1. **No Non-Transitivity Exists:** There is no "Rock-Paper-Scissors" cycle in the candidate route bank. `R0_A7` strictly dominates every other route in head-to-head play (48-2, 96.0% overall win rate).
2. **Dominance Hierarchy:**
   - Level 1: `R0_A7` (Universal Master, 96% win rate, +$10.5k mean delta).
   - Level 2: `R1_V22R1` (68% win rate, beats all routes except A7).
   - Level 3: `R5_V25P3` (64% win rate, close to V22R1, beats Dmitrii and below).
   - Level 4: `R2_DMITRII` (52% win rate, livestock specialist).
   - Level 5: `R4_V54` (20% win rate, beats only P3090).
   - Level 6: `R3_P3090` (0% win rate, beaten by every route).
3. **Strategic Conclusion:** A meta-controller that switches *away* from A7 to any other static expert route against these opponents would strictly reduce expected win probability.
