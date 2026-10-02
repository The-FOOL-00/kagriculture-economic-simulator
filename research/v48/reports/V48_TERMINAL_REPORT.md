# V48 Terminal Liquidation Report

## 1. Executive Summary

In accordance with Priority #2 (Part 11 of the V48 mandate), we tested whether V44's staggered terminal liquidation mechanics can improve 2945's terminal economy.

We evaluated four explicit terminal variants across **256 paired legs** (64 clean development seeds $\times$ 2 seats $\times$ 2 benchmark opponents: V44 and Dmitrii_lb2800):
- **T0**: Raw 2945 baseline (Native step 648 Route 2 + step 718 sweep)
- **T1**: 2945 + V44 50/50 Stagger (Step 693-694 50%, Step 704-705 50%, Step 716+ flush)
- **T2**: 2945 + V44 40/60 Stagger (Step 693 40%, Step 704 60%, Step 716+ flush)
- **T4**: 2945 + Hybrid Depth-Aware Stagger (Stagger only high-volume shed inventory)

### Empirical Results across 256 Paired Legs:

| Policy | Description | Mean $\Delta$ vs 2945 | Median $\Delta$ | 95% Bootstrap CI | Positive Legs | Zero Legs | Negative Legs | Status |
|---|---|---|---|---|---|---|---|---|
| **T0** | Raw 2945 Native | $0.00 | $0.00 | [$0.00, $0.00] | 0 | 256 | 0 | **BASELINE** |
| **T1** | V44 50/50 Stagger | **+$0.00** | **+$0.00** | [+$0.00, +$0.00] | 0 | 256 (100%) | 0 | **KILLED** |
| **T2** | V44 40/60 Stagger | **+$0.00** | **+$0.00** | [+$0.00, +$0.00] | 0 | 256 (100%) | 0 | **KILLED** |
| **T4** | Hybrid Depth Stagger | **+$0.00** | **+$0.00** | [+$0.00, +$0.00] | 0 | 256 (100%) | 0 | **KILLED** |

---

## 2. Root Cause Forensic: Why Did V44 Terminal Produce Exactly $0.00?

Dissection of `thomastschinkel_2945/main.py` revealed that at step 648, `_router` executes:
```python
if step >= 648 and not state.get('day27'):
    state['route'] = 2
    state['day27'] = True
```
Route 2 (`_ROUTES[2]`) is an engineered terminal tape whose market schedule already implements multi-stage staggered liquidation:
1. **Day 29 Staggered Pre-Flush (Steps 690–695)**:
   - Step 690: `[['SELL', 'WHEAT', 1000], ['SELL', 'CARROT', 1000]]`
   - Step 691: `[['SELL', 'WHEAT', 1000], ['SELL', 'CARROT', 1000]]`
   - Step 692: `[['SELL', 'FERTILIZER', 2], ['SELL', 'WHEAT', 1000], ['SELL', 'CARROT', 1000]]`
   - Step 693: `[['SELL', 'WHEAT', 1000], ['SELL', 'CARROT', 1000], ['SELL', 'EGG', 4]]`
   - Step 694–695: `[['SELL', 'FERTILIZER', 1000], ['SELL', 'WHEAT', 1000], ['SELL', 'EGG', 1000]]`
2. **Day 30 Final Liquidation Flush (Steps 712–718)**:
   - Steps 712–717: Sweeps all 9 products (`WHEAT`, `CARROT`, `TOMATO`, `STRAWBERRY`, `MELON`, `EGG`, `MILK`, `WOOL`, `FERTILIZER`) with quantity 1000 across every market turn.
   - Step 718: `_terminal_liquidation` layer flushes 100% of remaining shed stock.

Because Route 2 is already actively placing `SELL` orders for every marketable product at steps 693, 704, and 716+, V44's staggered overlay checks:
```python
if qty >= 2 and item not in already_selling:
```
and detects that every product is already being sold. Consequently, the overlay executes zero additional actions, resulting in bit-for-bit identity ($0.00 difference) across all 256 legs.

---

## 3. Governance Decision

Per the explicit instructions of Part 11:
> *"If terminal alpha disappears because 2945 already handles it optimally, kill this branch."*

**Decision**: **BRANCH TERMINATED**.
V48 will NOT include any external terminal liquidation overlay, preserving the validated native Route 2 terminal mechanics of 2945.
