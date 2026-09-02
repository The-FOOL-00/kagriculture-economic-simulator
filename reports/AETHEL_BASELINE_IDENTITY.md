# AETHEL BASELINE IDENTITY REPORT

**Generated Date:** 2026-09-02
**Target Engine:** `kaggle-environments == 1.32.7`
**Audit Standard:** Zero-Trust Forensic Verification

---

## 1. Executive Summary & Identity Mapping

The baseline agent **`Aethel-Prime V1`** (historically deployed as Anchor in Slot 1, ~929 Elo) is functionally derived from the Tier-9 grandmaster reference agent **`Closer Cleo`** (`replays/raw/reference_agents/closer_cleo.py`, SHA-256: `8addafc2de814b4ea76c63a30b166420a0ff8e8a86d40c6ae2651ef5c043d1f9`).

In the corrected factorial framework, `Aethel-Prime V1` is parameterized as **Candidate A** (`agents/candidate_a_aethel_v1.py`, SHA-256: `c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f`), which is identical to `agents/aethel_factorial_base.py`.

The difference between raw `closer_cleo.py` and `aethel_factorial_base.py` / `candidate_a_aethel_v1.py` is strictly:
1. `_FRONT_RUN_HORIZON = 0` (Closer Cleo had 1; inert overlay disabled).
2. `_MARKET_CONTROLLER_ENABLED = False` (Closer Cleo had inline market controller enabled).
3. Parameterized terminal trigger `_TERMINAL_START_STEP = 717`.

---

## 2. Component Verification Table

| Component | Exact Implementation Details | Verified? | Verification Evidence |
| :--- | :--- | :---: | :--- |
| **Livestock Portfolio** | Exactly 8 Cows and 6 Sheep. Purchased at steps: Step 0 (3 Cows, 1 Sheep), Step 121 (1 Cow, 1 Sheep), Step 168 (1 Cow), Step 192 (1 Sheep), Step 198 (2 Sheep), Step 199 (1 Sheep), Step 216 (1 Cow), Step 264 (2 Cows). | **YES** | Verified by decompressing and auditing `_TRACE` across all 720 turns. |
| **Land Expansion** | 2 Land expansions (`BUY_LAND` executed at steps 120 and 216). Expands farm layout to 3 active quadrants. | **YES** | Verified from embedded `_TRACE`. |
| **Crop Schedule** | High-value rotation: Strawberries (41 seed buys), Melons (26 seed buys), Wheat (343 buys for seed + feed buffer), Fertilizer (15 buys). Total harvests yield 270 Strawberries, 132 Melons, 230 Milk, 164 Wool. | **YES** | Extracted from `_TRACE` buy/sell cumulative records. |
| **Labor Allocation** | 1 Master Farmer + 8 Hired Hands (total 9 workers). Fixed spatial trajectory for turns 0..711 (or 716 in A/B). Roles strictly partitioned into harvest, seeding, livestock tending, manure collection, shed delivery. | **YES** | Verified from `_TRACE['farmer']` and `_TRACE['hands']`. |
| **Market Queue Architecture** | Maximum 10 market order slots per turn. Interleaved resolution between P0 and P1. Sells and Buys co-exist in turn queue. In Candidate A/C, uses fixed tape queue. In Candidate B/D, dynamic impact sorting replaces only SELL slots in-place. | **YES** | Verified in `_base_agent` and `agent(obs, config)`. |
| **Feed Protection** | Critical `BUY_PRODUCT WHEAT` orders are locked in their tape positions. In Market Controller (B/D), sell slots never displace wheat purchase slots. Opponent money check `_PROMOTE_IF_OPP_MONEY` guards against subsidizing opponent wheat purchases. | **YES** | Verified in `_cash_needed` and queue allocation logic. |
| **Front-Running Overlay** | `_front_run(action, obs, step)` with `_FRONT_RUN_HORIZON = 0` (permanently disabled in A/B/C/D). Requires clone confidence $\ge 2$. Inert under current market limits. | **YES** | Code inspection and trigger tracing show 0 modifications when disabled. |
| **Terminal Controller** | Observation-driven dynamic harvester. Scans 2D grid for `yield_units > 0`, assigns nearest workers, routes to shed `(half-1..half, half-1..half)`, liquidates inventory in descending gross value order. Activated at Step 717 (A, B) vs Step 712 (C, D). | **YES** | Verified in `_terminal_action(obs)`. |
| **Turn Horizon** | Exactly 720 turns (steps 0..719). Terminal sweep runs 712..719 (8 turns in C/D) vs 717..719 (3 turns in A/B). | **YES** | Verified against engine step count. |
| **Observation Access** | Accesses `obs['step']`, `obs['players'][seat]['cash']`, `obs['players'][seat]['inventory']`, `obs['grid']` (for terminal sweep only). Accesses only current-step online data; no future or leaked test data. | **YES** | Code audit of all `obs` references. |

---

## 3. SHA-256 Identity Manifest

| File | SHA-256 Checksum | Status |
| :--- | :--- | :---: |
| `replays/raw/reference_agents/closer_cleo.py` | `8addafc2de814b4ea76c63a30b166420a0ff8e8a86d40c6ae2651ef5c043d1f9` | Verified Reference Anchor |
| `agents/aethel_factorial_base.py` | `c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f` | Verified Immutable Base |
| `agents/candidate_a_aethel_v1.py` | `c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f` | Byte-Identical to Base |
| `agents/candidate_b_aethel_mc.py` | `4ce1034a7e23aadd30dac1cd1c7e2ec9b2565ac2410ce4169bc0cc348cf4c1a7` | Verified MC Only |
| `agents/candidate_c_aethel_t712.py` | `61467e87ffb0b957283222e60e68fa597b5f9912400828c287c759ad71e7dda5` | Verified T712 Only |
| `agents/candidate_d_aethel_refined.py` | `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` | Verified Combined |
| `candidates/slot2_aethel_refined_v2.py` | `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` | Byte-Identical to Cand D |
| `submission_slot2_aethel_refined_v2.tar.gz` | `ac16af822ea972852ba923dbec45503597b8518ecbe62a8744040d352f0c7c92` | Packaged Tarball |
| `main.py` (extracted from tarball) | `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` | Byte-Identical to Cand D |
