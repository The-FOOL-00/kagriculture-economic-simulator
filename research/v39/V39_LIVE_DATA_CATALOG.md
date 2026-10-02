# V39 Live Data Catalog — Ground-Truth Verified V35 Production Episodes

## 1. Data Collection & Identity Provenance
- **Target Submission**: `56540535` (`V35_FINAL_SUBMISSION.tar.gz`)
- **Submission Time**: `2026-09-25 05:03:39 UTC`
- **Current Live Elo**: `1642.5`
- **Total Cataloged Episodes**: 29
- **Validation Matches**: 1 (`113153701`)
- **Public Ladder Matches**: 28 (`113155209` – `113186749`)
- **Seat & Identity Resolution**: V35 is unambiguously identified in all 29 matches by its unique, deterministic opening action:
  `['BUY_PRODUCT', 'WHEAT', 25], ['SELL', 'WHEAT', 25]` executed at Step 1.
- **Team Names on Ladder**: `Sanjay` (episodes 1–8) / `Eldritch` (episodes 9–29).
- **Holdout Integrity**: 100% verified. Zero seeds in quarantined ranges (`214200–214249`, `340090–340199`, `249695–249734`).

---

## 2. Complete Ground-Truth Episode Catalog (N = 29)
| Episode ID | Date / Time (UTC) | V35 Seat | Board Seed | V35 Cash ($) | Opponent Cash ($) | Margin ($) | Result | Opponent Name | Replay & Logs |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **`113153701`** | 2026-09-25 05:03:39 | 0 | 0 | $67,695 | $68,335 | -$640 | `LOSS` | Self-Play Validation | Local Replay + Log |
| **`113155209`** | 2026-09-25 05:10:07 | 0 | 1528624348 | $163,016 | $57,299 | +$105,717 | `WIN` | Saptanshu Samal | Local Replay + Log |
| **`113156362`** | 2026-09-25 05:14:08 | 0 | 138732798 | $97,653 | $47,587 | +$50,066 | `WIN` | Tahsan Ferdous | Local Replay + Log |
| **`113157531`** | 2026-09-25 05:18:16 | 1 | 1400747604 | $153,727 | $101,827 | +$51,900 | `WIN` | Abhi Kumar Agrawal | Local Replay + Log |
| **`113158665`** | 2026-09-25 05:22:00 | 0 | 1600792203 | $127,151 | $58,680 | +$68,471 | `WIN` | mg | Local Replay + Log |
| **`113159827`** | 2026-09-25 05:26:05 | 1 | 239978678 | $61,351 | $30,628 | +$30,723 | `WIN` | yuhan wu | Local Replay + Log |
| **`113160962`** | 2026-09-25 05:30:00 | 0 | 1519661647 | $119,368 | $82,854 | +$36,514 | `WIN` | 綿鍋だよん | Local Replay + Log |
| **`113162119`** | 2026-09-25 05:34:01 | 0 | 1090980640 | $78,932 | $53,856 | +$25,076 | `WIN` | Moro | Local Replay + Log |
| **`113163245`** | 2026-09-25 05:38:08 | 0 | 1262830238 | $137,586 | $93,161 | +$44,425 | `WIN` | 古德拜吃 | Local Replay + Log |
| **`113164394`** | 2026-09-25 05:42:04 | 1 | 1722133329 | $77,965 | $79,953 | -$1,988 | `LOSS` | junxing peng | Local Replay + Log |
| **`113165586`** | 2026-09-25 05:46:03 | 1 | 1478624174 | $108,955 | $95,578 | +$13,377 | `WIN` | yukichi0403 | Local Replay + Log |
| **`113166778`** | 2026-09-25 05:50:03 | 1 | 2020456157 | $132,705 | $134,952 | -$2,247 | `LOSS` | NonCaffeine | Local Replay + Log |
| **`113167894`** | 2026-09-25 05:54:06 | 1 | 696018730 | $118,594 | $115,324 | +$3,270 | `WIN` | savoelh | Local Replay + Log |
| **`113169085`** | 2026-09-25 05:58:09 | 1 | 1810897973 | $89,632 | $79,341 | +$10,291 | `WIN` | mr_children_0617 | Local Replay + Log |
| **`113170295`** | 2026-09-25 06:02:07 | 0 | 405432148 | $103,450 | $97,646 | +$5,804 | `WIN` | Juniperss | Local Replay + Log |
| **`113171441`** | 2026-09-25 06:06:04 | 1 | 194590906 | $74,297 | $75,293 | -$996 | `LOSS` | Lisan al-Gaib | Local Replay + Log |
| **`113172595`** | 2026-09-25 06:10:04 | 0 | 1426837210 | $100,201 | $91,124 | +$9,077 | `WIN` | atsushi11o7 | Local Replay + Log |
| **`113173773`** | 2026-09-25 06:14:10 | 0 | 200975867 | $89,484 | $86,849 | +$2,635 | `WIN` | Zhen Li | Local Replay + Log |
| **`113174935`** | 2026-09-25 06:18:14 | 0 | 622826506 | $109,274 | $102,709 | +$6,565 | `WIN` | Kenan Zhang9 | Local Replay + Log |
| **`113176099`** | 2026-09-25 06:22:05 | 1 | 1345834087 | $125,796 | $124,216 | +$1,580 | `WIN` | kowalskii | Local Replay + Log |
| **`113177277`** | 2026-09-25 06:26:05 | 0 | 203942858 | $126,502 | $138,132 | -$11,630 | `LOSS` | Adhiraj Jagtap | Local Replay + Log |
| **`113178448`** | 2026-09-25 06:30:05 | 0 | 260527959 | $157,385 | $55,770 | +$101,615 | `WIN` | SOLUCIENCE | Local Replay + Log |
| **`113179717`** | 2026-09-25 06:34:05 | 1 | 425062345 | $115,229 | $109,881 | +$5,348 | `WIN` | Michael Mueller | Local Replay + Log |
| **`113180924`** | 2026-09-25 06:38:06 | 1 | 1721156009 | $126,822 | $117,916 | +$8,906 | `WIN` | Aastik Rajan15 | Local Replay + Log |
| **`113182085`** | 2026-09-25 06:42:05 | 1 | 1689121130 | $158,445 | $116,951 | +$41,494 | `WIN` | 🚜 Sub-Par Seedlings | Local Replay + Log |
| **`113183263`** | 2026-09-25 06:46:04 | 1 | 124304182 | $93,619 | $94,410 | -$791 | `LOSS` | Yassine Chritt | Local Replay + Log |
| **`113184429`** | 2026-09-25 06:50:04 | 1 | 1965223883 | $135,642 | $134,473 | +$1,169 | `WIN` | zeel vavliya | Local Replay + Log |
| **`113185602`** | 2026-09-25 06:54:04 | 0 | 1488666746 | $90,968 | $84,059 | +$6,909 | `WIN` | morality0707 | Local Replay + Log |
| **`113186749`** | 2026-09-25 06:58:09 | 1 | 1623486727 | $132,717 | $131,427 | +$1,290 | `WIN` | lllleeeo | Local Replay + Log |

---

## 3. High-Level Summary Statistics
- **Overall Record**: **23 Wins, 6 Losses, 0 Ties** (Win Rate: **79.31%**)
- **Mean Score**: V35 **$112,902** vs Field **$91,732** (Surplus Margin: **+$21,170.0**)
- **Seat Balance**:
  - Seat 0: 13 games, 11 Wins, 2 Losses (84.6% Win Rate, Mean Margin +$33,636)
  - Seat 1: 16 games, 12 Wins, 4 Losses (75.0% Win Rate, Mean Margin +$11,041)
