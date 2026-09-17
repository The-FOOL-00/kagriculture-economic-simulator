# AEC Phase 0 Audit Amendments & Formal Corrections
**Project:** Kagriculture AEC Development  
**Date:** 2026-09-17  
**Status:** BINDING ARCHITECTURAL SPECIFICATION — INCORPORATED INTO AEC PHASE 1  

This document formally records the eight mandatory corrections to the Phase 0 repository audit, superseding any prior conflicting text in earlier discovery documents.

---

## 1. Correction 0.1 — Backbone Characterization
- **Prior Draft Phrasing:** "competitive supremacy", "proven supremacy".
- **Authoritative Standard:** **"Primary observed-strong backbone for AEC development"**.
- **Scientific Rationale:** V3 (`submission_Vj_kc_v3.tar.gz`) is the selected primary engineering baseline for AEC tactical compilation based on empirical observation in competitive play. It is not an unalterable or universally proven theoretical optimum.

---

## 2. Correction 0.2 — Terminal Weak Dominance Scope
- **Prior Draft Phrasing:** Requiring candidate cumulative deposits and shed inventories to weakly dominate baseline at all intermediate points.
- **Authoritative Standard:** **Decouple Safety Invariants from Economic Acceptance**.
  - **Safety Invariants (Hard Constraints):**
    1. Legality under engine rules (`env_1_32_7.py` / `sim.hpp`).
    2. Feasibility of worker movements and tool requirements.
    3. Zero shed overflow (no destructive item discard at hour 23 or step 718).
    4. Scheduled market obligation preservation (intermediate solvency on required commitments).
    5. Executable terminal state.
    6. Deterministic execution.
  - **Economic Acceptance (Strategic Objective):**
    1. Primary: Expected Probability of Win ($P(\text{WIN})$).
    2. Secondary: Expected Terminal Margin ($\Delta M_{\text{term}}$).
    3. Tertiary: Own Economic Gain ($\Delta C_{\text{own}}$).
  - **Temporary Sacrifice Principle:** AEC is explicitly permitted to accept a temporary intermediate economic sacrifice if:
    - The candidate remains strictly safe and solvent.
    - Path to recovery is verified in counterfactual simulation.
    - Terminal execution remains feasible.
    - Counterfactual evaluation demonstrates superior eventual outcome.
  - ARCH-003 terminal dominance predicates are reused for terminal transformations and specialized safety proofs, but are **NOT** a global requirement for every intermediate step of a tactical patch.

---

## 3. Correction 0.3 — Adaptive Horizon Policy
- **Prior Draft Phrasing:** Unconditional global horizon $H = 24$.
- **Authoritative Standard:** **Adaptive Dependency-Driven Horizon**:
  - **SHORT ($H \in [4, 8]$):** Local/cheap events (weed repair, local tile bypass, single-turn cargo drop).
  - **NORMAL ($H \in [12, 24]$):** Standard economic patches (market advance, worker re-routing, crop harvesting chains).
  - **EXTENDED ($H \in [24, 48]$):** Long dependency chains, market town-cycle multi-turn alignments, or terminal conversion consequences.
- Bounded search depth driven by economic coupling, never brute-force 500-turn search.

---

## 4. Correction 0.4 — Opponent State Modeling
- **Prior Draft Phrasing:** 4-class discrete opponent classifiers (`WOOL_SPECIALIST`, `CROP_ACCUMULATOR`, `TAPE_CLONE`, `PASSIVE_GENERALIST`).
- **Authoritative Standard:** **Continuous Economic Pressure Quantities**:
  - Discrete archetypes are demoted to diagnostic features only.
  - The runtime model exposes continuous, observable economic quantities:
    - `opponent_supply_forecast[item]`: Projected volume entering market.
    - `opponent_harvest_pressure[item]`: Likelihood of rival harvest within horizon.
    - `opponent_sale_pressure[item]`: Estimated price depression probability.
    - `opponent_buy_pressure[item]`: Estimated price inflation probability.
    - `opponent_market_collision_risk[item]`: Probability of same-turn order contention.
    - `opponent_tape_similarity`: Rolling coordinate identity metric.
  - Inferred strictly from observable public signals (farm tiles, mature crop counts, herd size, visible cash, historical drops). No hallucination of private hand inventories.
  - Opponent reasoning directly conditions counterfactual planning; it is not a standalone controller overriding AEC.

---

## 5. Correction 0.5 — Lead-Aware Endgame Extension Point
- **Authoritative Standard:** Reserved as a clean, explicit extension interface.
- **Specification:**
  - `LeadState`: `AHEAD`, `CLOSE`, `BEHIND`.
  - Not hard-coded with rigid arbitrary thresholds in V1.
  - Prepares the evaluation engine to adjust variance tolerance:
    - `AHEAD`: Protect margin lead, minimize high-variance deviations.
    - `CLOSE`: Maximize expected terminal margin.
    - `BEHIND`: Permit controlled variance when justified by $P(\text{WIN})$.

---

## 6. Correction 0.6 — Live Baseline Immutability & Single-Call Discipline
- **Authoritative Standard:** **Strict Baseline Immutability**:
  - Exactly **ONE** live backbone call per game step.
  - Zero redundant calls for purity checking, search, or evaluation.
  - Baseline action is captured into an immutable reference snapshot.
  - Candidate mutations operate solely on deep copies.
  - Live baseline state and action objects are never mutated.

---

## 7. Correction 0.7 — Backbone Isolation & Packaging
- **Authoritative Standard:** `scratch/teammate_v3/` must not be a permanent architectural dependency.
- **Implementation:** `aec/integration/backbone_adapter.py` loads the frozen V3 implementation directly from `submission_Vj_kc_v3.tar.gz` in memory, verifying its SHA-256 hash (`845e0d10...`), and wraps it in a clean, isolated interface.

---

## 8. Correction 0.8 — Module Tree Governance
- **Authoritative Standard:** The actual module dependency tree and functional cohesion govern file creation.
- Keep modules focused, cleanly structured, and avoid monolithic files or arbitrary file counts.
