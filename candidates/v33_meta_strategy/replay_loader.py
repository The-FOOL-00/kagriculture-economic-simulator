# SPDX-License-Identifier: MIT
"""V33 Replay Loader.

Loads full-game replays from root, replays/ directory, and JSONL telemetry.
"""

from __future__ import annotations
import glob
import json
import os
from typing import Any, Dict, List, Optional, Tuple


class ReplayLoader:
    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.abspath(root_dir)

    def list_all_replays(self) -> List[str]:
        """Finds all Kaggle JSON replay files in root and replays/."""
        replays = sorted(glob.glob(os.path.join(self.root_dir, "*replay*.json")))
        replays += sorted(glob.glob(os.path.join(self.root_dir, "replays", "*.json")))
        return [p for p in replays if os.path.getsize(p) > 1024]

    def load_replay(self, filepath: str) -> Dict[str, Any]:
        """Loads and parses a single Kaggle replay JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def iter_replays(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Iterates through all valid replays, yielding (filepath, data)."""
        results = []
        for path in self.list_all_replays():
            try:
                data = self.load_replay(path)
                if "steps" in data and len(data["steps"]) >= 700:
                    results.append((path, data))
            except Exception as e:
                print(f"Warning: Failed to load replay {path}: {e}")
        return results
