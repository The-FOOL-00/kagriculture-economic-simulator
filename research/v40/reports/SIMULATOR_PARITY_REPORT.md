# V40 Simulator Parity Verification Report

**Document ID:** `research/v40/reports/SIMULATOR_PARITY_REPORT.md`  
**Date:** 2026-09-25 14:36:57  
**Component:** `research/v40/env/fast_sim.py` vs `kaggle_environments 1.32.7`  
**Total Steps Verified:** 4314 steps across 6 complete 720-step episodes  
**Overall Parity Status:** PASSED (100% BIT-FOR-BIT EQUIVALENCE)  

---

## 1. Executive Summary

This report documents the parity verification between the official `kaggle_environments` competition engine and the high-throughput `FastKagricultureSim` engine constructed for the V40 research program.

The goal was to eliminate all framework-level serialization, stdout redirection, and JSON schema validation overhead without altering a single line of game mechanics.

### Results Matrix

| Seed | Matchup | Steps | Official (r0 / r1) | Fast Sim (r0 / r1) | Off SPS | Fast SPS | Speedup | Parity Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249635 | `E2_A7 vs E8_DMITRII` | 719 | $75,124 / $61,846 | $75,124 / $61,846 | 51.3 | 198.4 | **3.9x** | **PASS** |
| 249636 | `E2_A7 vs E0_V3` | 719 | $119,978 / $118,692 | $119,978 / $118,692 | 46.8 | 150.2 | **3.2x** | **PASS** |
| 249637 | `E2_A7 vs SYN_AGG` | 719 | $193,825 / $3,000 | $193,825 / $3,000 | 64.6 | 255.5 | **4.0x** | **PASS** |
| 249638 | `E8_DMITRII vs E2_A7` | 719 | $106,588 / $114,128 | $106,588 / $114,128 | 51.1 | 196.0 | **3.8x** | **PASS** |
| 249639 | `V35 vs E8_DMITRII` | 719 | $128,907 / $92,513 | $128,907 / $92,513 | 49.3 | 191.0 | **3.9x** | **PASS** |
| 249640 | `E2_A7 vs PASSIVE` | 719 | $115,463 / $3,000 | $115,463 / $3,000 | 73.7 | 265.3 | **3.6x** | **PASS** |

---

## 2. Throughput Metrics

- **Official Baseline Throughput:** 56.1 SPS (~12.8 seconds per game)
- **FastKagricultureSim Throughput:** 209.4 SPS (~3.4 seconds per game)
- **Single-Core Speedup Factor:** **3.7×**
- **Turn-by-Turn Discrepancies:** Exactly **0** discrepancies across 4314 turns. Every single tile, money value, shed item, and market spot price matched identically.

---

## 3. Discrepancy Gate Verdict

**Status: ZERO DISCREPANCIES DETECTED.**  
The high-throughput simulation engine is formally approved for use in V40 rollout collection, counterfactual dataset generation, and population-based training.
