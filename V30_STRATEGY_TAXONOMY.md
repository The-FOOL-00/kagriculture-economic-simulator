# V30 STRATEGY TAXONOMY (from replay + code evidence)

Date: 2026-09-21. Five runnable families + one live-only reference.

## FAM-HIRE4-TAPE (META-A): dominant public high-rating macro

Members: P3090, P3000, P2900 (P3000==P2900 tape bytes; P3090 same skeleton,
different unit micro).
Signature: fixed 719/720-step tape; HIRE4-5 + livestock at step 0; wheat/
strawberry/melon only; fertilizer COLLECT 296 but FERTILIZE only 72 while
SELLING 235-300; 2x land; SELL-slot reordering by price impact; WEED repair.
Result vs V3: 0-16 each, self-play 73-80k vs V3 101k.
Interpretation: earlier-generation open-loop peak. Loses on crop diversity
(no carrot/tomato/egg), fertilizer application intensity, and shop
adaptivity (tape cannot react to shop draws; V3 parent routes by shops).

## FAM-WHEAT-CYCLE-TAPE (META-B): heavy market-cycling variant

Members: NIGHT.
Signature: same skeleton as META-A but BUY_PRODUCT WHEAT 980 / SELL 828
(4x the cycling), fewer wheat plants (92), more melon/strawberry.
Result vs V3: 0-16, -47k, self-play 62k (weakest tape).
Interpretation: wheat cycling is a NEGATIVE signal — cost without benefit.
Do not imitate.

## FAM-OZER-REACTIVE (META-C): near-peer reactive lineage

Members: DMITRII (LB2800 submission).
Signature: router + terminal planner; macro twin of V3 (same hires, plants,
animals, land, movement skeleton, daily money within ~5%). Differs: V3
fertilizes 2x (118-126 vs 61), buys more fertilizer input, sells more
wheat, wraps markets (frontload + 2-turn advance + horizon 24).
Result vs V3: 0-16 but smallest margin (-6.8k); self-play 95.5k (nearest
to V3's 101.6k). A7 beats it 16-0 by +12.2k (opening wash path matters
vs reactive peers).
Interpretation: the only frontier-adjacent family. V3's edge = fertilizer
application + microstructure wrappers, not macro shape.

## FAM-CLOSED-LOOP-RULES (META-D): reactive expert systems

Members: OKAMI (stateless expert rules), V66 (multi-route conditional with
stage gates at t=72/144 + terminal phase + sanitizer).
Result vs V3: OKAMI 0-16 (-91k, self-play 54k); V66 0-16 (-17.6k,
self-play 77k).
Interpretation: closed-loop reactivity alone does not reach the frontier;
V66's route conditioning helps (77k) but its route library is weaker than
the Ozer tape core. Adaptive route SELECTION is the interesting idea, but
this instance loses.

## FAM-LIX-CLUSTER (META-E): independent author best-cluster

Members: L2530, ANDREY11, MELON2736, SOIL2843 (+h3q4/h4/h5 not runnable).
Result vs V3: all 0-16 (-18k to -55k); self-play 76-88k.
Interpretation: an independent hill-climbing lineage that plateaued below
V3. Author's own logs show intra-cluster margins (+25k over older
variants) of the same ORDER as V3's margin over them — consistent with
V3 sitting ~1 generation above this cluster.

## LIVE-ONLY (META-F, not runnable): late live opponents

Members: xxxxyt (145k), ORiginators (126k), Les 2 oies (115k), Captainuknow
(124k), tetsuya top1 (98/114/138k), Eldritch (team agent, Sep-11 era).
Same-seed control: V3-vs-weak matches or exceeds every live-best absolute
(152 vs 152 exact; 193 vs 145; 178 vs 127; 150 vs 126; 159 vs 180; 165 vs
175). No live absolute exceeds V3's same-seed capability.
Interpretation: no evidence of a live-only absolute frontier above V3.

## Coverage gaps (honest)

- Current (late-Sept) live top is unobservable (no API). All directional
  evidence is early/mid-Sept.
- v66 older candidates (v60/v62/v65) not run: same author as V66, older
  versions; V66 itself lost by 17k. Documented skip, not oversight.
- lix h4/h5 not runnable (missing offline base file).
