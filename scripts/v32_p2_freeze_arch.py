# SPDX-License-Identifier: MIT
"""V32 P2 architecture freeze: assemble + hash V32_P2_ARCHITECTURE.json."""

import hashlib
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.p2 import actions as A  # noqa: E402
from v32.p2.features import SCHEMA_VERSION, WINDOWS, schema_names  # noqa: E402


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def main():
    vocab = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_vocab.json")))
    norm = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json")))
    man = {
        "architecture_version": "v32p2-a1",
        "state_feature_schema": SCHEMA_VERSION,
        "state_feature_names": schema_names(),
        "state_dim": len(schema_names()),
        "temporal_windows": list(WINDOWS),
        "normalization": {"source": "results/v32_p2_norm.json",
                          "sha256": norm["sha256"], "clip": 8.0,
                          "fit": "BC-train legs only (P2-TRAIN excl 249647-249649)"},
        "state_trunk": {"layers": [256, 256, 256], "activation": "Tanh",
                        "shared_actor_critic": True},
        "unit_ctx_dim": 12,
        "action_schema": "per-slot independent pointer heads (farmer+hands "
                         "share unit head; 10 market slots each own query). "
                         "All slots sample in parallel; NOT autoregressive.",
        "unit_vocab_size": len(vocab["unit_vocab"]),
        "market_vocab_size": len(vocab["market_vocab"]),
        "market_slots": A.M_MARKET_SLOTS,
        "max_hands_assert_cap": A.MAX_HANDS_CAP,
        "vocab_file": "results/v32_p2_vocab.json",
        "vocab_sha256": sha_file(os.path.join(REPO_ROOT, "results",
                                              "v32_p2_vocab.json")),
        "categorical_embeddings": {"op": [26, 16], "item": [25, 8]},
        "scalar_candidate_features": ["qty_scaled", "has_qty", "has_item"],
        "candidate_encoder": {"input_dim": 27, "hidden": 128,
                              "activation": "Tanh", "output_dim": 256,
                              "per_candidate_independent": True,
                              "state_dependent_features": "none"},
        "slot_embedding_dim": 16,
        "state_query_dim": 256,
        "candidate_key_dim": 256,
        "logit_formula": "q . k_i / sqrt(256)",
        "masking_rule": "PLANT_crop masked iff seeds[crop]==0 "
                        "(provably-noop, order-independent). All market "
                        "candidates always executable (simulator clamps). "
                        "Masked logit = -1e9. No other masks.",
        "padding_rule": "market slots beyond expert/list length emit [] "
                        "(NO-OP); trailing [] stripped. Unit batch padded to "
                        "batch-max hands with unit_valid mask (no logprob).",
        "order_invariance": "candidate semantics from literal features only; "
                            "permutation-tested (T3). Market SLOT order is "
                            "semantic (race alignment) and preserved.",
        "candidate_identity_hash": "sha256(canonical JSON literal); debug "
                                   "only, never a model input",
        "ppo_distribution": "independent categoricals per slot; joint "
                            "logprob = sum; entropy = sum (valid slots only)",
        "entropy_definition": "sum of per-slot categorical entropies over "
                              "legal (unmasked) candidates; N=1 -> 0",
        "critic": {"input": "shared h_s", "layers": [256, 1],
                   "activation": "Tanh", "output": "V(s)"},
        "params_total": 545705,
        "engine": "kaggriculture 1.32.7",
    }
    blob = json.dumps(man, sort_keys=True)
    man["config_hash"] = hashlib.sha256(blob.encode()).hexdigest()
    with open(os.path.join(REPO_ROOT, "V32_P2_ARCHITECTURE.json"), "w") as f:
        json.dump(man, f, indent=1, sort_keys=True)
    print("froze V32_P2_ARCHITECTURE.json hash=%s" % man["config_hash"])


if __name__ == "__main__":
    main()
