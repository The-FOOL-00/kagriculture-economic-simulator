# SPDX-License-Identifier: MIT
"""Kagriculture Competition Entrypoint — AEC Robust Qualified Foundation (V22R1).

Loader-safe entrypoint. The competition loader executes this source in a bare
namespace WITHOUT __file__ (kaggle_environments/agent.py:get_last_callable
uses exec(source) with only an exec_dir sys.path entry during exec). Nothing
here assumes __file__ exists:

- sys.path fallback is append-only (never shadows an already-configured path)
  and engages only for directories validated by submission markers.
- The V3 tarball is located by ordered, existence-validated candidates; when
  none resolve, the config default is kept and BackboneAdapter resolves the
  tarball relative to its own (real, imported) module file — the same file.
- No cwd, repo-layout, or absolute-path assumptions anywhere.
"""

import os
import sys
from typing import Any, Dict, Optional

_V3_ARCHIVE_NAME = "submission_Vj_kc_v3.tar.gz"


def _submission_root_candidates():
    """Ordered candidate submission roots. Never raises for missing __file__."""
    roots = []
    f = globals().get("__file__")
    if isinstance(f, str) and f:
        roots.append(os.path.dirname(os.path.abspath(f)))
    try:
        code_file = _submission_root_candidates.__code__.co_filename
    except Exception:
        code_file = None
    if isinstance(code_file, str) and code_file not in ("", "<string>"):
        roots.append(os.path.dirname(os.path.abspath(code_file)))
    return roots


def _looks_like_submission_root(d):
    """True only if d contains the submission markers (validated, not assumed)."""
    try:
        return (
            isinstance(d, str)
            and bool(d)
            and os.path.isfile(os.path.join(d, "aec", "__init__.py"))
            and os.path.isfile(os.path.join(d, _V3_ARCHIVE_NAME))
        )
    except Exception:
        return False


for _root in _submission_root_candidates():
    if _looks_like_submission_root(_root) and _root not in sys.path:
        sys.path.append(_root)

from aec.config import build_robust_qualified_config
from aec.integration.executor import AECExecutor

_EXECUTOR: Optional[AECExecutor] = None


def _find_v3_tarball(configuration=None):
    """Locate the bundled V3 tarball without assuming __file__.

    Ordered candidates (first existing file wins):
    1. __file__-derived / code-filename-derived submission roots.
    2. The imported aec package location (same derivation BackboneAdapter uses).
    3. The KE-injected configuration['__raw_path__'] agent path directory.
    Returns None when nothing resolves; the caller then keeps the config
    default, which BackboneAdapter resolves relative to its own module file.
    """
    cands = []
    for _r in _submission_root_candidates():
        cands.append(os.path.join(_r, _V3_ARCHIVE_NAME))
    try:
        import aec.integration.backbone_adapter as _ba
        _bf = getattr(_ba, "__file__", None)
        if isinstance(_bf, str) and _bf:
            _bd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(_bf))))
            cands.append(os.path.join(_bd, _V3_ARCHIVE_NAME))
    except Exception:
        pass
    try:
        _raw = configuration.get("__raw_path__") if configuration is not None else None
    except Exception:
        _raw = None
    if isinstance(_raw, str) and _raw and os.path.isfile(_raw):
        cands.append(os.path.join(os.path.dirname(os.path.abspath(_raw)), _V3_ARCHIVE_NAME))
    for c in cands:
        try:
            if c and os.path.isfile(c):
                return c
        except Exception:
            pass
    return None


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Kaggle competition agent entrypoint (V22R1, loader-safe)."""
    global _EXECUTOR
    step = int(observation.get("step", 0) or 0)

    if _EXECUTOR is None or step == 0:
        cfg = build_robust_qualified_config()
        local_v3 = _find_v3_tarball(configuration)
        if local_v3:
            cfg.v3_tarball_path = local_v3
        _EXECUTOR = AECExecutor(config=cfg)

    return _EXECUTOR.act(observation, configuration)
