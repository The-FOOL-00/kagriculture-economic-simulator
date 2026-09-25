# V32 P3 BC LEARNING CURVE (mixture)

Source: `results/v32_p3_bc_report.json` :: curve (val, 30 epochs, no early stop).

```text
ep  full   sem   uop   uarg  uqty  mop   mitem mqty  mopnn
 0  .005  .005  .240  .751  .531  .896  .493  .455  .116
 5  .011  .011  .316  .872  .766  .919  .648  .608  .404
10  .015  .015  .371  .895  .788  .934  .714  .706  .544
15  .025  .025  .411  .909  .797  .947  .735  .737  .633
20  .035  .035  .441  .918  .797  .957  .741  .751  .704
25  .042  .042  .462  .920  .805  .965  .744  .756  .766
29  .046  .046  .470  .925  .804  .969  .744  .759  .801
```

Monotone-ish rise on every head through ep29 (no plateau, no early stop).
Market-op-nonnoop slope is steepest early (0.12→0.40 by ep5) and still climbing
(0.77→0.80 over eps 25–29). Unit-op rises near-linearly (0.24→0.47). Train≈val
throughout (no overfit) — the run is optimization-limited, not capacity- or
data-limited. PPO slope: NO DATA (P3 runs no PPO; gate CLOSED).
