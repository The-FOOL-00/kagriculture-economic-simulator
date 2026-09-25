# SPDX-License-Identifier: MIT
"""R1 inference: checkpoint -> deterministic argmax expert selection."""

import json

import numpy as np
import torch

from v32.router.features import Normalizer, build_a_id, build_b
from v32.router.models import build


class RouterPredictor:
    def __init__(self, ckpt_path):
        d = np.load(ckpt_path, allow_pickle=True)
        self.meta = json.loads(str(d["meta"]))
        state = {k: torch.tensor(v) for k, v in d.items() if k != "meta"}
        self.model = build(self.meta["model"], self.meta["dim"])
        self.model.load_state_dict(state)
        self.model.eval()
        self.norm = Normalizer.from_json(self.meta["normalizer"])
        self.regime = self.meta["regime"]
        self.stack = self.meta.get("stack", "longer")

    def _feat(self, rows):
        if self.regime == "a_id":
            X = [build_a_id(r) for r in rows]
        else:
            X = [build_b(r, self.stack) for r in rows]
        return self.norm.transform(X)

    def predict_proba(self, rows):
        import numpy as _np
        X = torch.tensor(_np.asarray(self._feat(rows), dtype=_np.float32))
        with torch.no_grad():
            out = self.model(X)
            logits = out[0] if isinstance(out, tuple) else out
            return torch.softmax(logits, dim=1).numpy().tolist()

    def predict(self, rows):
        import numpy as _np
        P = _np.asarray(self.predict_proba(rows))
        # fixed tie-break: lowest index (documented, deterministic)
        return [int(_np.argmax(p - 1e-12 * _np.arange(len(p)))) for p in P]
