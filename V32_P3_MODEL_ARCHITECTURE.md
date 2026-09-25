# V32 P3 MODEL ARCHITECTURE (v32p3-a1)

Code: `v32/p3/models.py` (`P3Policy`, `LinearControl`). Schema:
`V32_P3_ACTION_SCHEMA.md`. State encoder: P2 Groups A–D, 157 dims,
`v32p2feat-v1`, normalizer `d2a41ab7…` — unchanged.

## 1. Structure (Repair A: native independent slot heads)

```text
157-dim normalized structured-temporal features
            ↓
   3 × 256 MLP, Tanh (shared trunk, P2 shape)
            ↓
      shared latent h
       ↓          ↓
 per-unit query  per-market-slot query
 [h; uctx_j]     [h; slot_emb_s]
 (268-dim)       (272-dim)
       ↓          ↓
 U_OP 18      M_OP 7
 U_ARG 12     M_ITEM 12
 U_QTY 17     M_QTY 77
 (linear)     (linear)
       ↓          ↓
 v32.p3.codec decode → exact native action dict
```

- `uctx_j`: P2 12-dim per-unit context (pos + tile one-hot + inv size).
- `slot_emb`: learned 10×16 market-slot embedding (slot identity = order).
- All slots/heads predicted independently in parallel. No chaining, no
  autoregression, no pointer, no Transformer/GRU/LSTM/attention/MoE/router.
- Critic head (256→Tanh→1) retained for PPO-driver interface parity; unused
  in BC (P3 runs no PPO).

## 2. Parameter count

Trunk ≈ 172k; unit heads ≈ 12.6k; market heads ≈ 26.2k; slot emb 160;
critic ≈ 66k. Total ≈ 277k (vs P2 a1 545,705). No candidate encoder, no
1466-way candidate matmuls — forward cost is dominated by the trunk.

## 3. Loss (BC)

Sum of 6 masked-CE head means. Arg/qty/item masking from TARGET ops
(never predicted): `U_ARG` iff target op ∈ {PLANT,PICKUP,PLACE}; `U_QTY`
iff ∈ {PICKUP,PLACE}; `M_ITEM`/`M_QTY` iff target `M_OP` is a qty-op.
No output masking in a1 (deliberate — codec doc §6): silent no-ops are
learned; decode is pure reconstruction.

## 4. Metrics (the honest ones)

- Per-head accuracy (6) + `m_op_nonnoop` (market-op accuracy on non-NOOP slots).
- `full_exact`: all 6 heads correct on all slots (masked heads excluded).
- `full_semantic`: decoded predicted literals == decoded target literals
  (don't-care heads can't hurt; this is the executable-fidelity metric).
- Closed-loop economics (the real gate) — see closed-loop report.

## 5. Control

`LinearControl`: single linear maps from the same head inputs (features+uctx /
features+fixed-slot-onehot) to the same 6 heads. No trunk, no learned
embeddings. Isolates "subset learnable from these features?" (P2 precedent:
linear hit 100% by ep75 on identical features with pointer targets).

## 6. Deliberate non-goals (Repair B–D not implemented)

No per-candidate embeddings (no candidates in this design), no normalization/
init changes (standard Adam 3e-4; revisit only on demonstrated pathology),
no pretraining. Fallback if G2 fails on PLANT slots specifically: per-crop
PLANT split (new schema version + new authorization, never silent).

## 7. Config hash

`v32p3-a1`: trunk 157→256³ Tanh; heads as above; no masking; Adam 3e-4,
batch 1024 (BC) / 64 (memorization); grad-clip 1.0; ≤30 epochs BC,
patience 5 on val full-exact (P2 rule). Architecture hash recorded in
training reports from `scripts/v32_p3_freeze.py`.
