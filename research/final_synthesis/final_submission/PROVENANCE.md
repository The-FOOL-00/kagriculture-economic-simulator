# PROVENANCE & ATTRIBUTION RECORD

## 1. Primary Upstream Sources

### Teammate Submission 1: Vj_kc_v24
- **Original Archive**: `team_submissions/submission_Vj_kc_v24.tar.gz`
- **Archive SHA256**: `4C9EF1DC189DE6185AFADE682CB8A758139390E4BAA8B6A010500443C75BD5CE`
- **Credited Lineage in Source**:
  - `guruprasaathas111`
  - `thomastschinkel` (The 2945 Farm)
  - `yhay81` (shop router, action tapes)
  - `destbreso`
  - `aurax7`
  - `tetsutani` (room guard, dead stock)
  - `prvsiyan`
  - `Dmitrii Gluzdov` (HybridOpening, temporary wheat maturation, terminal rescue)
  - `Ahmed Berat Ozer` (crop_public_order, market sequencing)
- **License**: Apache-2.0 (retained verbatim in header).

### Teammate Submission 2: Vj_kc_v27
- **Original Archive**: `team_submissions/submission_Vj_kc_v27.tar.gz`
- **Archive SHA256**: `EEE5AD4D7C67B27D7713E70B4B9E56220E92A8E8B90E6C59656A93ECE74B9A6C`
- **Modifications vs v24**:
  - Disabled `room_guard` and `dead_stock` (harmful; lost 55.2 cash per game).
  - Omitted `pet_any_demand_agent` wrapper (harmful on PET_CAFE seeds).
  - Regressed `_v234_rescue` to allow zero-quantity WHEAT pickup to abort rescue (stall risk).
  - Removed mirror farm shape check in `step738_sale_advance_agent`.

### Incumbent Control Baseline: V49_Meta_Fusion
- **Original Implementation**: `candidates/v49_meta_fusion/main.py`
- **Protected Frozen Copy**: `research/final_synthesis/baselines/V49_FROZEN/main.py`
- **SHA256**: `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11`
- **Key Contributions**:
  - V44 CapEx safeguard (step >= 520).
  - V48 selective shop-route overrides (route 105 for 3 shop pairs).
  - V49 E402 late seed-cap overlay (step >= 624).
  - Authoritative 92.19% panel win rate across broad public competitive field.

---

## 2. Synthesized Candidate Manifest: Final_Meta_Synthesis

- **Source Path**: `research/final_synthesis/final_candidate/main.py`
- **SHA256**: `076AB4447A198C972C6F5415A48FB6DDF7B1E3E1B8AA306783D3F2B8BD29177D`
- **Modifications Applied**:
  1. Base Architecture: Inherited V24's superior configuration (`room_guard=True`, `dead_stock=True`, stranded wheat fix `len(command)>2 and command[2]>0`, PET_CAFE margin tilt `_CA_MARGIN=-30.0`, and mirror lookahead).
  2. Production De-Instrumentation: Removed prohibited debug hook `print('HP_TELEMETRY',_HP_STATS)` at step 718.
  3. Production Safety Wrap: Enclosed in deep-copying, exception-catching safety agent guaranteeing action dictionary shape and capping market orders to 10.
  4. Retained Upstream Licenses: Preserved all Apache-2.0 notices, contributor attributions, and history verbatim.

---

## 3. Governance Audit & Final Determination
The synthesized candidate was rigorously evaluated across 640 legs in tournament play. Although it showed promising micro-economic acceleration in narrow head-to-head scenarios, it suffered severe negative generalization against the broader competitive meta (48.91% panel WR vs V49's 92.19%).
In accordance with zero-fake-results governance and competition victory criteria, `V49_Meta_Fusion` is retained as the authoritative submission.
