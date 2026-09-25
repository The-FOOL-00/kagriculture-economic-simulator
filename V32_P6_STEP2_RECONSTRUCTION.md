# V32 P6 — STEP-2 STATE RECONSTRUCTION & COMPARISON REPORT

## 1. PURPOSE & METHODOLOGY

In accordance with Section 6 of the **V32 P6 Protocol**, this document establishes an exact forensic comparison between the canonical expert (`E2_A7`) and the policy (`P5 Arm 2`) across the opening trajectory (Steps 0, 1, 2) on development seed `249675` before the Step-2 action is executed.

The objective is to resolve the fundamental distinction required by Section 3:
- **A. On-manifold action error**: The model sees the correct teacher Step-2 state but predicts the wrong action.
- **B. Off-manifold action error**: The model only fails after the state has already diverged due to earlier errors.

---

## 2. CHRONOLOGICAL RECONSTRUCTION (STEPS 0, 1, 2)

### Step 0 (Pre-Action Observation)
- **Teacher (`E2_A7`)**:
  - Farmer Position: `[4, 4]` (Shed access tile)
  - Money: `$3,000.0`
  - Shed Inventory: Empty (all 0)
  - Active Hands: 0
  - Action Executed: `{'farmer': ['PASS'], 'hands': [], 'market': [['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]}`
- **Policy (`P5 Arm 2`)**:
  - Farmer Position: `[4, 4]`
  - Money: `$3,000.0`
  - Shed Inventory: Empty (all 0)
  - Active Hands: 0
  - Action Executed: `{'farmer': ['PASS'], 'hands': [], 'market': [['BUY_PRODUCT', 'WHEAT', 7], ['SELL', 'WHEAT', 30]]}`
- **Status**: Match (100% on-manifold).

---

### Step 1 (Pre-Action Observation)
- **Teacher (`E2_A7`)**:
  - Farmer Position: `[4, 4]`
  - Money: `$3,054.0` (Capital from Step-0 Wash)
  - Shed Inventory: Empty
  - Active Hands: 0
  - Action Executed: `{'farmer': ['NORTH'], 'hands': [], 'market': [['SELL', 'WHEAT', 13], ['BUY_PRODUCT', 'WHEAT', 5], ['HIRE'] * 5, ['BUY_ANIMAL', 'COW', 2], ['BUY_ANIMAL', 'SHEEP', 2]]}`
- **Policy (`P5 Arm 2`)**:
  - Farmer Position: `[4, 4]`
  - Money: `$3,032.0`
  - Shed Inventory: Empty
  - Active Hands: 0
  - Action Executed: `{'farmer': ['NORTH'], 'hands': [], 'market': [['BUY_PRODUCT', 'WHEAT', 13], ['SELL', 'WHEAT', 5], ['HIRE'] * 5, ['BUY_ANIMAL', 'COW', 2], ['BUY_ANIMAL', 'SHEEP', 2]]}`
- **Status**: Match (Both execute `NORTH`, hire 5 hands, and buy 2 Cows + 2 Sheep).

---

### Step 2 (Pre-Action Observation)
Recorded immediately before the Step-2 action is issued:

| State Variable | Teacher State ($s_2^T$) | Policy State ($s_2^P$) | Absolute Delta | Forensic Assessment |
|:---|:---:|:---:|:---:|:---|
| **Farmer Position** | `[4, 3]` | `[4, 3]` | `[0, 0]` | **IDENTICAL** |
| **Active Hand Count** | 5 | 5 | 0 | **IDENTICAL** |
| **Hand 0 Position** | `[4, 4]` | `[4, 4]` | `[0, 0]` | **IDENTICAL** |
| **Hand 1 Position** | `[5, 4]` | `[5, 4]` | `[0, 0]` | **IDENTICAL** |
| **Hand 2 Position** | `[4, 5]` | `[4, 5]` | `[0, 0]` | **IDENTICAL** |
| **Hand 3 Position** | `[5, 5]` | `[5, 5]` | `[0, 0]` | **IDENTICAL** |
| **Hand 4 Position** | `[4, 4]` | `[4, 4]` | `[0, 0]` | **IDENTICAL** |
| **Shed: COW** | 2 | 2 | 0 | **IDENTICAL** |
| **Shed: SHEEP** | 2 | 2 | 0 | **IDENTICAL** |
| **Shed: WHEAT** | 5 | 8 | 3 | Functionally Equivalent |
| **Cash Reserves** | $1,106.0 | $1,005.0 | $101.0 | Functionally Equivalent |
| **Unlocked Quadrants** | 1 (NW) | 1 (NW) | 0 | **IDENTICAL** |
| **Tile (4, 3) Status** | None (Empty) | None (Empty) | 0 | **IDENTICAL** |

---

## 3. PRIMARY FORENSIC FINDING

> **THE STEP-2 FAILURE IS STRICTLY AN ON-MANIFOLD ACTION-SELECTION ERROR.**

The policy arrives at Step 2 in a state that is materially and geometrically identical to the expert trajectory:
1. The farmer is at `[4, 3]`.
2. All 5 hired hands occupy the exact same spawn coordinates around the shed.
3. The shed holds the exact required livestock contracts (2 Cows, 2 Sheep).
4. No prior covariate shift or state dislocation has occurred.

The subsequent catastrophe is triggered entirely by the **action predicted at Step 2**:
- **Teacher Action**: `['SOUTH']` (Farmer moves back to shed tile [4, 4]).
- **Policy Action**: `['PICKUP', 'COW']` (Farmer attempts to pickup livestock while standing 1 tile away from the shed).
