# SPDX-License-Identifier: MIT
"""V32 P3 native factorized action package (v32p3-a1).

Simulator-native slot factorization (see V32_P3_ACTION_SCHEMA.md):
per unit slot U_OP(18) x U_ARG(12) x U_QTY(17); per market slot
M_OP(7) x M_ITEM(12) x M_QTY(77). No pointer, no autoregression.
"""

from v32.p3.codec import (M_ITEM, M_OP, M_QTY, U_ARG, U_OP, U_QTY,
                          decode_market, decode_unit, encode_market,
                          encode_unit, load_schema)

__all__ = ["U_OP", "U_ARG", "U_QTY", "M_OP", "M_ITEM", "M_QTY",
           "encode_unit", "decode_unit", "encode_market",
           "decode_market", "load_schema"]
