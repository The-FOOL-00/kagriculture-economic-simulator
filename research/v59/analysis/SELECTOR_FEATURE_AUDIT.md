# V59 — Selector Feature Audit
Generated: 2026-09-28

## Status: NOT CONSTRUCTIBLE

Building a legal opponent classifier requires:
1. September opponent action streams (for fingerprinting)
2. Sep rating labels (for strategy family assignment)
3. Tested counter-plans (for selector output)

NONE of these are available.

## Feature Design (Pre-registered for future use)

If Sep data becomes available, the recommended features at turn 24 are:
- opponent_cows_t24
- opponent_sheep_t24
- opponent_crops_planted_t24
- opponent_land_tiles_t24
- opponent_hands_t24
- opponent_cash_t24
- opponent_first_buy_product (day-0 first action)
- opponent_animal_to_crop_ratio_t24

## Classifier Type

Hand-derived rule classifier preferred (interpretable, deterministic).
Decision tree fallback if rule fails.
Neural classifier: explicitly NOT recommended (requires training data).

## Conclusion

SELECTOR_FEATURE_AUDIT: not executable, not applicable.
