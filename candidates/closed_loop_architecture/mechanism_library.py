"""
MECHANISM LIBRARY: Formal specifications of 15 economic sub-systems in Kaggriculture.
Each mechanism defines inputs, outputs, timing, labor, cash, fertilizer, shop dependence,
liquidity risk, upside, and failure modes.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class MechanismSpec:
    name: str
    category: str  # 'PRODUCTION', 'LIVESTOCK', 'MARKET', 'PROTECTION', 'LOGISTICS'
    inputs: Dict[str, float]
    outputs: Dict[str, float]
    cycle_time_days: int
    labor_hours_per_cycle: int
    cash_capex: float
    cash_opex_per_cycle: float
    fertilizer_required: int
    shop_dependence: str  # 'NONE', 'YARN', 'DAIRY', 'PET_CAFE', 'BAKERY', 'UNIVERSAL'
    liquidity_risk: str  # 'LOW', 'MEDIUM', 'HIGH', 'EXTREME'
    upside_cash_potential: float
    known_failure_modes: List[str]

MECHANISMS: Dict[str, MechanismSpec] = {
    # 1. Dmitrii Fertilization Engine
    "DMITRII_FERTILIZATION": MechanismSpec(
        name="Dmitrii Fertilization Engine",
        category="PRODUCTION",
        inputs={"MANURE": 1.0, "LABOR": 1.0},
        outputs={"CROP_YIELD_MULTIPLIER": 1.5, "FERTILIZED_TILES": 1.0},
        cycle_time_days=1,
        labor_hours_per_cycle=1,
        cash_capex=0.0,
        cash_opex_per_cycle=0.0,
        fertilizer_required=1,
        shop_dependence="NONE",
        liquidity_risk="LOW",
        upside_cash_potential=45000.0,
        known_failure_modes=[
            "Animal starvation halts manure supply",
            "Worker path blocked by unweeded tile",
            "Premature fertilization before plot tilled"
        ]
    ),

    # 2. Strawberry Production Loop
    "STRAWBERRY_LOOP": MechanismSpec(
        name="Strawberry Compounding Loop",
        category="PRODUCTION",
        inputs={"SEED_STRAWBERRY": 1.0, "WATER": 10.0, "FERTILIZER": 1.0},
        outputs={"STRAWBERRY": 3.0},  # 3 berries per harvest on fertilized tile
        cycle_time_days=10,
        labor_hours_per_cycle=12,
        cash_capex=100.0,  # seed cost
        cash_opex_per_cycle=0.0,
        fertilizer_required=1,
        shop_dependence="NONE",  # Market price is strong (~$450/berry)
        liquidity_risk="HIGH",  # 10 days cash lockup
        upside_cash_potential=95000.0,
        known_failure_modes=[
            "Day 10-12 cash cliff prevents dawn hiring, leaving crops unwatered",
            "Missed watering delays harvest past terminal liquidation",
            "Shed saturation (100 capacity) causes harvest discard"
        ]
    ),

    # 3. Sheep / Manure Loop
    "SHEEP_MANURE_LOOP": MechanismSpec(
        name="Sheep / Manure Sustaining Loop",
        category="LIVESTOCK",
        inputs={"WHEAT_FEED": 1.0, "LABOR_FEED": 1.0},
        outputs={"MANURE": 1.0, "WOOL": 1.0},
        cycle_time_days=3,
        labor_hours_per_cycle=2,
        cash_capex=1200.0,  # sheep purchase cost
        cash_opex_per_cycle=0.0,  # if autarkic wheat feed
        fertilizer_required=0,
        shop_dependence="YARN",  # wool is shop-dependent, manure is universal
        liquidity_risk="MEDIUM",
        upside_cash_potential=35000.0,
        known_failure_modes=[
            "consecutive_unfed >= 2 causes animal death/paralysis",
            "Holding wool in non-yarn worlds clogs shed inventory",
            "High early purchase cost depletes day-0 cash buffer"
        ]
    ),

    # 4. Goose Liquidity & Manure Contribution
    "GOOSE_LOOP": MechanismSpec(
        name="Goose Rapid Egg & Manure Loop",
        category="LIVESTOCK",
        inputs={"WHEAT_FEED": 0.5, "LABOR_FEED": 1.0},
        outputs={"EGG": 1.0, "MANURE": 0.5},
        cycle_time_days=2,
        labor_hours_per_cycle=1,
        cash_capex=500.0,
        cash_opex_per_cycle=0.0,
        fertilizer_required=0,
        shop_dependence="BAKERY",  # Bakery / Brunch demand eggs
        liquidity_risk="LOW",
        upside_cash_potential=15000.0,
        known_failure_modes=[
            "Low unit revenue ($180/egg) cannot justify high late-game worker travel"
        ]
    ),

    # 5. Wool Liquidity (Market Arbitrage)
    "WOOL_LIQUIDITY": MechanismSpec(
        name="Early Wool Market Liquidation",
        category="MARKET",
        inputs={"WOOL": 1.0},
        outputs={"CASH": 350.0},
        cycle_time_days=1,
        labor_hours_per_cycle=0,
        cash_capex=0.0,
        cash_opex_per_cycle=0.0,
        fertilizer_required=0,
        shop_dependence="NONE",
        liquidity_risk="LOW",
        upside_cash_potential=4000.0,
        known_failure_modes=[
            "Premature market dumping in a Yarn shop world loses 2.0x town bonus",
            "Deleting wool sales creates Day 10 cash collapse"
        ]
    ),

    # 6. Cow / Milk Production
    "COW_MILK_LOOP": MechanismSpec(
        name="Cow Dairy Industrial Loop",
        category="LIVESTOCK",
        inputs={"WHEAT_FEED": 1.5, "LABOR_FEED": 1.0, "LABOR_MILK": 1.0},
        outputs={"MILK": 2.0, "MANURE": 1.0},
        cycle_time_days=2,
        labor_hours_per_cycle=3,
        cash_capex=2000.0,  # cow purchase cost
        cash_opex_per_cycle=0.0,
        fertilizer_required=0,
        shop_dependence="DAIRY",  # Smoothie, Ice Cream, Pizza
        liquidity_risk="HIGH",
        upside_cash_potential=50000.0,
        known_failure_modes=[
            "2-day feeding desynchronization causes starvation",
            "Milk delivery worker pathing blocks strawberry watering",
            "High cow capex delays land expansion"
        ]
    ),

    # 7. Wheat Feed Production (Autarky)
    "WHEAT_FEED_AUTARKY": MechanismSpec(
        name="Wheat Autarkic Feed Supply",
        category="PRODUCTION",
        inputs={"SEED_WHEAT": 1.0, "WATER": 4.0},
        outputs={"WHEAT": 6.0},
        cycle_time_days=4,
        labor_hours_per_cycle=5,
        cash_capex=10.0,
        cash_opex_per_cycle=0.0,
        fertilizer_required=0,
        shop_dependence="NONE",
        liquidity_risk="LOW",
        upside_cash_potential=12000.0,
        known_failure_modes=[
            "Over-allocating land to wheat crowds out strawberry plot space",
            "Running out of wheat forces emergency market feed purchases at $250/unit"
        ]
    ),

    # 8. Carrot Rapid Cash Production
    "CARROT_CASH_LOOP": MechanismSpec(
        name="Carrot Fast Turnover Loop",
        category="PRODUCTION",
        inputs={"SEED_CARROT": 1.0, "WATER": 3.0},
        outputs={"CARROT": 4.0},
        cycle_time_days=3,
        labor_hours_per_cycle=4,
        cash_capex=20.0,
        cash_opex_per_cycle=0.0,
        fertilizer_required=0,
        shop_dependence="PET_CAFE",
        liquidity_risk="LOW",
        upside_cash_potential=35000.0,
        known_failure_modes=[
            "Rapid 3-day replant cycles consume excessive dawn labor",
            "Low individual unit price ($150) loses to fertilized strawberries post-Day 15"
        ]
    ),

    # 9. Melon Production
    "MELON_LOOP": MechanismSpec(
        name="Melon High-Yield Single Harvest",
        category="PRODUCTION",
        inputs={"SEED_MELON": 1.0, "WATER": 12.0},
        outputs={"MELON": 6.0},
        cycle_time_days=12,
        labor_hours_per_cycle=14,
        cash_capex=80.0,
        cash_opex_per_cycle=0.0,
        fertilizer_required=0,
        shop_dependence="NONE",
        liquidity_risk="MEDIUM",
        upside_cash_potential=28000.0,
        known_failure_modes=[
            "Long 12-day lockup; planting after Day 17 yields zero return",
            "Bulky harvest (6 units/tile) instantly clogs shed capacity"
        ]
    ),

    # 10. Market Selling Execution
    "MARKET_SELLING": MechanismSpec(
        name="Market Bulk Order Execution",
        category="MARKET",
        inputs={"COMMODITY": 1.0},
        outputs={"CASH": 1.0},  # variable market price
        cycle_time_days=0,
        labor_hours_per_cycle=0,
        cash_capex=0.0,
        cash_opex_per_cycle=0.0,
        fertilizer_required=0,
        shop_dependence="NONE",
        liquidity_risk="LOW",
        upside_cash_potential=150000.0,
        known_failure_modes=[
            "Submitting SELL orders on dawn steps displaces HIRE orders (max_orders=10)"
        ]
    ),

    # 11. Town Shop Dispatch
    "TOWN_DISPATCH": MechanismSpec(
        name="Town Targeted Shop Delivery",
        category="MARKET",
        inputs={"MATCHED_COMMODITY": 1.0, "LABOR_CART": 1.0},
        outputs={"CASH_BONUS": 2.0},  # up to 2.0x base market price
        cycle_time_days=1,
        labor_hours_per_cycle=3,
        cash_capex=0.0,
        cash_opex_per_cycle=0.0,
        fertilizer_required=0,
        shop_dependence="UNIVERSAL",
        liquidity_risk="MEDIUM",
        upside_cash_potential=60000.0,
        known_failure_modes=[
            "Opponent front-running exhausts town shop demand",
            "Worker cart travel distance distracts from core field watering"
        ]
    ),

    # 12. Terminal Liquidation Planner
    "TERMINAL_LIQUIDATION": MechanismSpec(
        name="Day 28-29 Terminal Asset Purge",
        category="MARKET",
        inputs={"ALL_REMAINING_INVENTORY": 1.0},
        outputs={"FINAL_CASH": 1.0},
        cycle_time_days=2,
        labor_hours_per_cycle=0,
        cash_capex=0.0,
        cash_opex_per_cycle=0.0,
        fertilizer_required=0,
        shop_dependence="NONE",
        liquidity_risk="LOW",
        upside_cash_potential=40000.0,
        known_failure_modes=[
            "Late harvest produces commodities on Turn 718 that cannot be sold",
            "Market queue saturation prevents full clearance"
        ]
    ),

    # 13. Liquidity Reserve Protection
    "LIQUIDITY_RESERVE": MechanismSpec(
        name="Safe Cash Runway Invariant",
        category="PROTECTION",
        inputs={"CASH": 1.0},
        outputs={"INSOLVENCY_IMMUNITY": 1.0},
        cycle_time_days=0,
        labor_hours_per_cycle=0,
        cash_capex=0.0,
        cash_opex_per_cycle=0.0,
        fertilizer_required=0,
        shop_dependence="NONE",
        liquidity_risk="LOW",
        upside_cash_potential=55000.0,  # prevented losses
        known_failure_modes=[
            "Excessive cash holding starves productive land expansion"
        ]
    ),

    # 14. Worker Hiring Order Arbiter
    "WORKER_HIRING_PROTECTION": MechanismSpec(
        name="Dawn Hire Slot Reservation",
        category="PROTECTION",
        inputs={"ORDER_SLOTS": 10.0},
        outputs={"HIRE_EXECUTION_GUARANTEE": 1.0},
        cycle_time_days=1,
        labor_hours_per_cycle=0,
        cash_capex=0.0,
        cash_opex_per_cycle=0.0,
        fertilizer_required=0,
        shop_dependence="NONE",
        liquidity_risk="LOW",
        upside_cash_potential=60000.0,
        known_failure_modes=[
            "None; strict priority allocation of order slots 0-9 for HIRE"
        ]
    ),

    # 15. Shed-Headroom Controller
    "SHED_HEADROOM_PROTECTION": MechanismSpec(
        name="Shed 75-Unit Headroom Guard",
        category="PROTECTION",
        inputs={"SHED_OCCUPANCY": 1.0},
        outputs={"ZERO_DISCARD_GUARANTEE": 1.0},
        cycle_time_days=0,
        labor_hours_per_cycle=0,
        cash_capex=0.0,
        cash_opex_per_cycle=0.0,
        fertilizer_required=0,
        shop_dependence="NONE",
        liquidity_risk="LOW",
        upside_cash_potential=30000.0,
        known_failure_modes=[
            "Premature dumping of slightly profitable inventory before price peak"
        ]
    )
}
