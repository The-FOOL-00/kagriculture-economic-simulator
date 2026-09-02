# Kernel: boatlee__v21-r1-public-state-route-portfolio

## Notebook: v21-r1-public-state-route-portfolio.ipynb (2 cells)

### [Markdown Cell 0]
# V21-R1 | Public-State Route Portfolio

V21-R1 is a multi-route Kaggriculture agent. It keeps several complete production schedules available and uses only the current observation窶廃ublic farm state, public money, the shared market, and the unlocked Shop sequence窶杯o select a route and apply a small market-timing overlay.

The route hypotheses were developed from public Competition replays and public Notebooks. The submitted agent does not use usernames, episode IDs, seeds, replay files, network access, or future observations.

## Local closed-loop screens

| Panel | Games | W/T/L | Paired +/0/- |
|---|---:|---:|---:|
| Score-stratified executable proxies | 192 | 164/0/28 | 84/0/12 |
| Top-front executable proxies | 48 | 45/0/3 | 23/0/1 |
| Frozen regression routes | 32 | 26/0/6 | 13/0/3 |

Every recorded game completed 720 frames with both agents in `DONE` status. The code cell reconstructs the frozen single-file agent, verifies its digest, and creates the Competition archive.


