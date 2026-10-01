# V24 — Controlled Challenger Validation Report

Preregistered CRN pilot tournament evaluation against V3 standalone baseline.

- **Cohort**: Fresh Pilot Seeds `249400..249409` (N=10 seeds, 20 mirrored matches per candidate)
- **Seating**: Mirrored CRN (Seat 0 and Seat 1 per seed)
- **Parallel Execution**: `MAX_WORKERS = 9`
- **Engine Version**: `1.32.7`

## Headline Candidate Qualification Summary

| Candidate ID | Bottleneck Targeted | Mean Paired Delta | 95% Conf Interval | Win / Loss / Tie | Win Rate | Qualification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **C1_IDLE_ZEROING** | C1 IDLE ZEROING | **$-45,282.0** | [$-58,000.5, $-32,563.5] | 0W / 10L / 0T | **0.0%** | `FALSIFIED` |
| **C2_LIVESTOCK_SCALE** | C2 LIVESTOCK SCALE | **$-146,760.5** | [$-165,854.6, $-127,666.3] | 0W / 10L / 0T | **0.0%** | `FALSIFIED` |
| **C3_CARROT_COMPOUND** | C3 CARROT COMPOUND | **$-45,330.9** | [$-50,524.7, $-40,137.2] | 0W / 10L / 0T | **0.0%** | `FALSIFIED` |

---

## Per-Seed Mirrored Match Breakdown

### C1_IDLE_ZEROING

| Seed | Seat 0 Cand Reward | Seat 0 V3 Reward | Seat 1 Cand Reward | Seat 1 V3 Reward | Paired Seed Delta |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 249400 | $77,877 | $109,059 | $77,877 | $109,059 | **$-31,182.0** |
| 249401 | $82,990 | $142,362 | $84,603 | $142,337 | **$-58,553.0** |
| 249402 | $119,295 | $143,899 | $114,856 | $139,595 | **$-24,671.5** |
| 249403 | $89,231 | $158,945 | $83,569 | $147,428 | **$-66,786.5** |
| 249404 | $60,807 | $78,186 | $60,807 | $78,186 | **$-17,379.0** |
| 249405 | $92,816 | $147,903 | $92,816 | $147,903 | **$-55,087.0** |
| 249406 | $75,417 | $98,968 | $75,417 | $98,968 | **$-23,551.0** |
| 249407 | $93,599 | $165,037 | $93,599 | $165,037 | **$-71,438.0** |
| 249408 | $80,749 | $118,625 | $80,749 | $118,625 | **$-37,876.0** |
| 249409 | $106,020 | $172,434 | $106,141 | $172,319 | **$-66,296.0** |

### C2_LIVESTOCK_SCALE

| Seed | Seat 0 Cand Reward | Seat 0 V3 Reward | Seat 1 Cand Reward | Seat 1 V3 Reward | Paired Seed Delta |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 249400 | $13,743 | $183,562 | $13,743 | $183,562 | **$-169,819.0** |
| 249401 | $19,365 | $114,880 | $19,365 | $114,880 | **$-95,515.0** |
| 249402 | $18,405 | $173,772 | $18,405 | $173,772 | **$-155,367.0** |
| 249403 | $18,363 | $193,519 | $17,990 | $186,666 | **$-171,916.0** |
| 249404 | $14,448 | $199,074 | $15,586 | $201,659 | **$-185,349.5** |
| 249405 | $15,517 | $174,064 | $15,517 | $174,064 | **$-158,547.0** |
| 249406 | $19,378 | $171,865 | $19,378 | $171,865 | **$-152,487.0** |
| 249407 | $17,885 | $175,139 | $17,885 | $175,139 | **$-157,254.0** |
| 249408 | $14,541 | $112,938 | $14,541 | $112,938 | **$-98,397.0** |
| 249409 | $29,587 | $150,901 | $30,002 | $154,594 | **$-122,953.0** |

### C3_CARROT_COMPOUND

| Seed | Seat 0 Cand Reward | Seat 0 V3 Reward | Seat 1 Cand Reward | Seat 1 V3 Reward | Paired Seed Delta |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 249400 | $66,233 | $110,819 | $66,233 | $110,819 | **$-44,586.0** |
| 249401 | $99,770 | $150,192 | $99,770 | $150,192 | **$-50,422.0** |
| 249402 | $93,738 | $141,564 | $91,140 | $139,410 | **$-48,048.0** |
| 249403 | $77,183 | $134,414 | $77,103 | $134,494 | **$-57,311.0** |
| 249404 | $76,866 | $114,041 | $76,866 | $114,041 | **$-37,175.0** |
| 249405 | $63,101 | $111,373 | $63,101 | $111,373 | **$-48,272.0** |
| 249406 | $99,246 | $125,380 | $99,246 | $125,380 | **$-26,134.0** |
| 249407 | $87,595 | $135,007 | $87,595 | $135,007 | **$-47,412.0** |
| 249408 | $97,149 | $144,883 | $97,149 | $144,883 | **$-47,734.0** |
| 249409 | $73,995 | $122,460 | $71,704 | $115,670 | **$-46,215.5** |

## Scientific Findings & Epistemic Decision

1. **Heuristic Interception Incompatibility**: All 3 challenger variants suffered severe negative paired deltas when evaluated standalone against V3.
2. **Underlying Cause**: V3's internal state machine maintains non-local path and transaction commitments (`_proposals`, `_R37_HORIZONS`). Intercepting worker movements or market orders post-hoc breaks V3's internal synchronization, leading to resource misallocation.
3. **Stop Condition Invocation (Section 23)**: None of the 3 challenger backbones achieved positive standalone alpha against V3. Per Section 14, challengers that fail standalone evaluation do NOT proceed to AEC integration. Per Section 23, V22R1 is preserved as the frozen active submission.
