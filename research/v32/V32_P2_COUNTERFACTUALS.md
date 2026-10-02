# V32 P2 COUNTERFACTUALS — NOT APPLICABLE (no PPO policy exists)

First-divergence analysis (§50) requires a learned policy whose gains can
be attributed. P2 produced no gains (BC replays at $0; PPO never ran).
The only divergence analyzed is BC's step-0 wash miss ([SELL,WHEAT,0]
instead of the teacher wash → no economy → drift), documented in
`V32_P2_BC_BASELINE.md` §3–§4 with an instrumented leg.
