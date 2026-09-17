# SPDX-License-Identifier: MIT
"""Test H — Opponent Pressure Interface and Market Modulation."""

from aec.counterfactual.opponent_pressure import OpponentPressureModel
from aec.ir.opponent_state import OpponentState


def test_opponent_pressure_generates_market_supply():
    # Synthetic opponent with heavy wool pressure
    opp_state = OpponentState(
        supply_forecast={"WOOL": 6.0, "STRAWBERRY": 0.0},
        sale_pressure={"WOOL": 0.8, "STRAWBERRY": 0.0},
        observed_animals={"SHEEP": 6}
    )
    
    model = OpponentPressureModel(opp_state)
    
    # Check simulated market orders at step divisible by 3
    orders = model.generate_simulated_opponent_market(step=12, offset=0)
    
    # Must generate rival wool sell
    wool_sells = [o for o in orders if o[0] == "SELL" and o[1] == "WOOL"]
    assert len(wool_sells) > 0
    assert wool_sells[0][2] >= 1
    
    # Must not generate strawberry sell (zero pressure)
    straw_sells = [o for o in orders if o[0] == "SELL" and o[1] == "STRAWBERRY"]
    assert len(straw_sells) == 0
