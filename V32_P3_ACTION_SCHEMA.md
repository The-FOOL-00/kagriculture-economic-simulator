# V32 P3 NATIVE ACTION SCHEMA (grounded in kaggriculture 1.32.7 source)

Source of truth: `.venv/.../kaggle_environments/envs/kaggriculture/kaggriculture.py`
(1086 lines, `kaggle-environments 1.32.7`) + `kaggriculture.json` §action.
Every row below cites the enforcing code. No legal-action enumeration API
exists; invalid actions are silent no-ops (function docstring,
`_apply_unit_action`). Line numbers refer to the installed simulator file.

## 6.1 Native action object

```python
action = {"farmer": [OP, ...args],
          "hands":  [[OP, ...args], ...],
          "market": [[OP, ...args], ...]}
```

Dispatch (`interpreter`, ~L918-940; `_process_market`, ~L544-560):

- Non-dict `s.action` is replaced by `{}` → all-default action.
- `farmer`: `action.get("farmer", ["PASS"])`. Missing → `["PASS"]`.
  Explicit `None`/non-list/empty → `_apply_unit_action` early-returns → no-op.
- `hands`: `action.get("hands", [])`; non-list → `[]`. Element `h` is applied
  to hand index `h` (`_farmer_position` idx `h+1`); elements beyond the live
  hand count hit `pos is None` → ignored. A live hand with NO provided element
  receives no call at all ≡ stands still ≡ `PASS` semantically.
- `market`: `action.get("market", [])`; non-list → `[]`; truncated to
  `maxMarketOrdersPerTurn` (config default 10, minimum 1) — extras silently
  dropped (`q[:max_orders]`).
- Intra-turn order: all unit actions (both players) → market → town consume →
  decay → possible end-of-day. Market: per index `i` across players, atomic
  HIRE/BUY_LAND first (player order), then per-unit lockstep for SELL/BUY_*,
  then `_refresh_prices` before index `i+1`.

## 6.2 Slot decomposition (the P3 factorization)

| Slot | Count | Identity rule |
| :--- | :--- | :--- |
| U0 farmer | 1 | fixed |
| U1..Uh hands | h = live hand count (0–14 observed, no sim cap) | positional: element h ↔ `farm["hands"][h]` |
| M0..M9 market | 10 = `maxMarketOrdersPerTurn` | positional: index = race-alignment slot |

Heads per unit slot: `U_OP` (18) × `U_ARG` (12) × `U_QTY` (|Q_unit|+implicit).
Heads per market slot: `M_OP` (7) × `M_ITEM` (12) × `M_QTY` (|Q_mkt|).
All slots predicted independently in parallel given the state (no chaining).

## 6.3 Per-slot domains

### 6.3.1 Unit opcodes — `U_OP`, 18 classes (`_apply_unit_action`, ~L312-505)

No-parameter ops (15) — extra trailing args are never read (inert):

| Op | Effect | No-op/silent conditions |
| :--- | :--- | :--- |
| NORTH/SOUTH/EAST/WEST | step 1 tile (`FARMER_MOVES`) | off-board target; LOCKED tiles ALLOWED |
| PASS | explicit no-op | — |
| DROP | move ALL unit inv → shed (capacity-clamped; OVERFLOW DESTROYED) | not shed-adjacent |
| WATER | water PLANT on tile (+yield bonus in window) | tile not PLANT; `watered_today` |
| HARVEST | PLANT (if age ok) or animal product → unit inv | `yield_units` ≤ 0; immature PLANT |
| FERTILIZE | consume 1 FERTILIZER from unit inv, 3-day buff | tile not PLANT; no FERTILIZER in inv |
| DIG | clear tile to None (plants/weeds/empty structures) | tile None; tile holds animal |
| BUILD_COOP / BUILD_PASTURE | place empty structure | tile not None |
| FEED | consume 1 WHEAT from unit inv, fed flag | tile not animal; `fed_today`; no WHEAT |
| COLLECT_FERTILIZER | +1 FERTILIZER to unit inv | tile not animal; none available |
| CARE | cared flag (future yield bonus path) | tile not animal; `cared_today` |

Parameterized ops (3):

| Op | Literal | Arg domain | Qty | Notes |
| :--- | :--- | :--- | :--- | :--- |
| PLANT | `[PLANT, crop]` | crop ∈ 5 CROPS | none (always exactly 1 seed) | tile must be None; `seeds[crop]` > 0; ALSO §6.4-C1 atomic rule; `len<2`/bad crop → no-op |
| PICKUP | `[PICKUP, item, n?]` | item effective = 12 shed keys | n default 1 | shed-adjacent only; `len<2` → no-op; `int(n)` with NO try/except (non-integer RAISES — decoder must only emit ints); n≤0 → no-op; clamped to shed availability; seeds NOT pickable (separate store) |
| PLACE | `[PLACE, item, n?]` | 12 shed keys | n default 1 | animal branch (matching empty structure + item in inv → place, takes exactly 1, n ignored) else shed-adjacent shed-drop (clamped to inv + shed room); same `int()` exception hazard as PICKUP |

Non-op: `WEED` (and any other unknown opcode, empty/non-list action) has NO
simulator branch → always silent no-op. P3 excludes WEED from `U_OP`
(normalize → PASS; semantically identical; 0 occurrences in P2 data per T11).

### 6.3.2 Unit arg — `U_ARG`, 12 classes (shed keys = 9 PRODUCTS + 3 ANIMALS)

WHEAT CARROT TOMATO STRAWBERRY MELON EGG MILK WOOL FERTILIZER GOOSE COW SHEEP.
Used by PLANT (crop ⊂ first 5; other 7 values → no-op), PICKUP, PLACE.
Don't-care for the 15 no-parameter ops (loss-masked). OOV items (e.g. "COOP")
resolve to availability 0 → no-op; 0 occurrences in P2 data (T11: 0 misses).

### 6.3.3 Unit qty — `U_QTY` (|Q_unit| observed ints + IMPLICIT class)

Positive ints for PICKUP/PLACE; absent ≡ explicit 1 (both default `n=1`).
Loss-masked unless op ∈ {PICKUP, PLACE}. Observed set enumerated in
`V32_P3_DATASET_AUDIT.md` (P2 T11: all recorded values in-vocab).

### 6.3.4 Market opcodes — `M_OP`, 7 classes (`_parse_order`, ~L631-649)

| Op | Literal | Parse rule | Execution |
| :--- | :--- | :--- | :--- |
| NOOP | `[]` | non-list/empty/None → None (skipped; race index preserved) | nothing |
| HIRE | `[HIRE]` (extras ignored) | always parses | atomic, player order; cost fib(hires_today)×mult; unaffordable → silent no-op; spawns hand + inventory |
| BUY_LAND | `[BUY_LAND]` | always parses | next quadrant in LAND_ORDER at LAND_PRICES; maxed/unaffordable → no-op |
| BUY_SEED | `[BUY_SEED, crop, n]` | len<3 → None; `int(n)` try/except (malformed → silent no-op); n≤0 → None | item must ∈ CROPS (quote stage, else abort); per-unit money check; seeds uncapped |
| BUY_PRODUCT | `[BUY_PRODUCT, item, n]` | same shape rules | item ∈ {WHEAT, FERTILIZER}; quoted at POST-buy inventory (buy/sell round-trip nets zero); per-unit money + shed-capacity stops |
| BUY_ANIMAL | `[BUY_ANIMAL, animal, n]` | same shape rules | item ∈ {GOOSE, COW, SHEEP}; per-unit money + shed-capacity stops; lands in shed unplaced |
| SELL | `[SELL, item, n]` | same shape rules | item ∈ 9 PRODUCTS; per-unit shed-availability stop; money += price; price $1 → pays but does NOT add market inventory |

Unknown market op → None → silent no-op. Qty = MAXIMUM (partial fills stop at
first failed unit). Qty 0 occurs in expert data (silent no-op class — must be
encodable; P2 vocab confirms).

### 6.3.5 Market item — `M_ITEM`, 12 classes (same shed-key vocabulary as U_ARG)

Validity is op-dependent (table above); invalid (op,item) pairs parse but abort
at quote → silent no-op (learned, NOT masked). Don't-care for NOOP/HIRE/BUY_LAND
(loss-masked).

### 6.3.6 Market qty — `M_QTY`, |Q_mkt| = 77 observed values (`results/v32_p2_vocab.json`)

Categorical over recorded ints (incl. 0). Loss-masked unless op is a qty-op.
Decode always emits an in-set int (OOV impossible at decode). Encode of an
out-of-set int → nearest set element (documented §6.6-N2; 0 occurrences on BC
data by construction).

## 6.4 Couplings

- C1 (cross-unit, the ONLY one): PLANT atomic validation (`interpreter`,
  ~L925-936). Per-crop total demand across farmer+hands > `seeds[crop]` →
  ALL PLANTs for that crop become PASS. Representation unaffected (literal
  round-trip); execution semantic applied identically to expert and decoded
  actions. Mask consequence: `PLANT_c masked iff seeds[c]==0` stays EXACT
  (demand ≥ 1 > 0 → dropped); finer demand-vs-seeds gating is NOT per-slot
  maskable → must be learned.
- C2 (market order): race alignment (index `i` processed jointly across
  players) + sequential `_refresh_prices` between indices. Slot identity IS
  order; independent heads preserve it. Interior `[]` preserved (P2
  `emit_market_list` rule retained); trailing `[]` stripped (provably harmless:
  `i < len(q)` guard).
- C3 (temporal): units act before market each turn; a HIRE affects unit actions
  only from the next turn; hands/inventories/`hires_today` reset at end of day.
- C4 (hand indexing): positional; spawn order deterministic (shed-access tiles,
  min occupancy, NWSE preference — `_spawn_hand`).
- C5 (market micro-semantics): SELL-at-$1 inventory exception; BUY_PRODUCT
  post-buy quote; partial fills. All preserved by literal round-trip.
- Mutually exclusive pairs: NONE at the literal level (every slot accepts every
  op; validity resolves silently). Jointly required pairs: NONE (all slots
  optional). Conditional dependence: qty meaningful only with valid (op,item);
  PICKUP/PLACE qty meaningful only with valid item + position.

## 6.5 Maximum dimensions (confirmed by source)

| Dimension | Value | Source |
| :--- | :--- | :--- |
| M market slots | 10 | config `maxMarketOrdersPerTurn` default 10 (`kaggriculture.json`); `q[:max_orders]`; P2 observed len-10 704×, never >10 (T9) |
| hands | 0–14 observed, NO simulator cap | `_do_hire` unbounded; P2 legs max 14; assert-cap 16 retained as stop-and-investigate tripwire, never truncation |
| unit slots | 1 + h | construction |
| shed capacity | 100 | config `shedCapacity` default 100 |
| qty ints | unbounded in principle; 77 market values + unit set observed | `int()` parse; audit enumerates |
| episode | 720 steps | config `episodeSteps` 720 |

## 6.6 Mapping theorem

> A simulator-native joint action literal is represented by the P3 factorized
> heads (U_OP×U_ARG×U_QTY per unit slot, M_OP×M_ITEM×M_QTY per market slot)
> without loss of executable information, modulo three normalizations:

- N1: unknown unit opcode (incl. WEED) → PASS. Semantically identical (no
  simulator branch). Expected occurrences on BC data: 0 (T11).
- N2: out-of-vocabulary qty int → nearest observed value. Expected: 0 on BC
  data (vocab built from the same data).
- N3: trailing args beyond the schema (e.g. `[PASS, X]`) → dropped.
  Semantically inert (never read). Occurrences counted in the dataset audit.

`V32_P3_ACTION_CODEC.md` + the round-trip test over all 172,560 recorded steps
must show 0 unexplained semantic mismatches (G1); any occurrence of N1–N3 is
classified per §7 (encoder/decoder bug, simulator ambiguity, schema ambiguity,
or irreducible loss) before training.
