# V32 P3 ACTION CODEC (v32p3-a1)

Code: `v32/p3/codec.py`. Schema: `V32_P3_ACTION_SCHEMA.md` (+`.json`).
Tests: `tests/test_v32_p3_codec.py` (edge cases, G1 full round-trip,
execution identity, determinism).

## 1. Interface

```python
encode_unit(lit) -> (op, arg, qty, flags)       # U_OP(18) U_ARG(12) U_QTY(17)
decode_unit(op, arg, qty) -> literal
encode_market(lit) -> (op, item, qty, flags)    # M_OP(7) M_ITEM(12) M_QTY(77)
decode_market(op, item, qty) -> literal
encode_action(native, n_hands) -> {"u","m","flags"}
decode_action(u_targ, m_targ) -> native_action_dict
```

Pure functions, no state, deterministic. `load_schema()` reads the frozen JSON.

## 2. Encode rules (recorded literal → targets)

- Unit missing/None/non-list/empty → PASS (simulator-identical no-op).
- Market missing/empty/None → NOOP → `[]` (parses to None, skipped).
- Malformed parameterized literals (bad crop/item, short market order,
  non-integer qty) → PASS / `[]` — exactly the simulator's silent no-op.
- Non-integer PICKUP/PLACE qty (simulator would RAISE ValueError — unexecutable
  literal) → PASS + N3 flag. Decoder only emits ints, so closed-loop can never
  produce this.
- OOV qty int → nearest observed value + N2 flag (bisect).
- Unknown unit opcode (incl. WEED — no simulator branch) → PASS + N1.
  Unknown market opcode → `[]` + N1.
- Trailing args beyond schema → dropped + N3 (never read by the sim).
- Hands beyond `n_hands`, market beyond slot 10 → dropped + U:TRUNC/M:TRUNC
  (simulator ignores/truncates identically). `n_hands > 16` raises
  AssertionError (stop-and-investigate tripwire, never silent truncation).

## 3. Decode rules (targets → native literal)

Exact literal reconstruction, no canonicalization, no masking, no reordering:

- Noparam unit op → `[OP]`; PLANT → `[PLANT, crop]`; PICKUP/PLACE →
  `[OP, item]` (IMPLICIT) or `[OP, item, qty]`.
- NOOP → `[]`; HIRE/BUY_LAND → `[OP]`; qty-op → `[OP, item, qty]`.
- Joint: `{"farmer": u0, "hands": u1.., "market": m0..}` with trailing `[]`
  stripped (interior `[]` preserved — race alignment, schema §6.4-C2).

## 4. Round-trip result (G1, 172,560 steps)

**Literal identity on 100% of recorded steps: N1=0, N2=0, N3=0, truncations 0.**
Target-level fixpoint holds (`encode(decode(encode(x))) == encode(x)`).
0 unexplained semantic mismatches — G1 PASSES (see test output).

## 5. Execution identity

Native vs codec-round-tripped seat-0 actions for consumed seed 249635 replayed
through two live envs (PASS opponent): per-step money and full tile grids
identical across all 719 steps; terminal rewards equal. Test:
`test_execution_identity_native_vs_decoded`.

## 6. No masking in P3 a1 (deliberate)

P3 a1 applies no loss/output masking: silent no-ops (invalid PLANT, empty
market slots, qty-0, C1 over-demand) are learned targets, and decode is pure
reconstruction. The seeds==0 PLANT rule stays exactly maskable (helper
`plant_crop_masked`; 84/57,629 expert PLANTs hit it) as a documented fallback
if G2 fails on PLANT slots specifically — not silently enabled.
