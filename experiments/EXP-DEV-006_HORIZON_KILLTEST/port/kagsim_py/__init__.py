# SPDX-License-Identifier: MIT
"""kagsim_py: bit-exact pure-Python port of the kagsim 1.32.7 engine."""
from .api import Game, Stream, run_episode, run_many  # noqa: F401
from .api import __version__, ENGINE_VERSION  # noqa: F401
