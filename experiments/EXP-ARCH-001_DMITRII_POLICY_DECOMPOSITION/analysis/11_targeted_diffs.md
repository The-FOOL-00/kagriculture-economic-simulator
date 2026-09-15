# Targeted tape diffs

## tape0 vs tape2 over 144..647 (110 diffs): step list
[313, 318, 320, 321, 333, 336, 337, 340, 354, 356, 359, 360, 361, 362, 371, 373, 375, 385, 397, 409, 433, 434, 439, 443, 445, 447, 449, 451, 452, 453, 454, 455, 457, 505, 516, 517, 521, 525, 526, 527, 529, 530, 532, 536, 538, 542, 543, 549, 550, 552, 553, 554, 555, 558, 561, 562, 563, 564, 569, 570, 573, 577, 578, 579, 582, 584, 586, 589, 591, 592, 595, 596, 597, 598, 599, 600, 601, 603, 605, 606, 607, 609, 611, 612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 631, 632, 634, 635, 636, 639, 640, 641, 647]

## tape1 vs tape0 over 0..143 (dead-code diffs, never executed): step list
[70, 90, 96, 98, 120, 122, 128, 131, 134, 141]
 step70: tape0={"farmer": ["CARE"], "hands": [["PASS"], ["PASS"], ["PASS"], ["WATER"]], "market": []}
 step70: tape1={"farmer": ["PASS"], "hands": [["PASS"], ["PASS"], ["PASS"], ["WATER"]], "market": []}
 step90: tape0={"farmer": ["PLACE", "FERTILIZER"], "hands": [["PASS"], ["EAST"], ["CARE"], ["WATER"], ["PASS"]], "market": [["SELL", "FERTILIZER", 1]]}
 step90: tape1={"farmer": ["PLACE", "FERTILIZER"], "hands": [["PASS"], ["EAST"], ["PASS"], ["WATER"], ["PASS"]], "market": [["SELL", "FERTILIZER", 1]]}
 step96: tape0={"farmer": ["PICKUP", "WHEAT", 5], "hands": [], "market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["SELL", "FERTILIZER", 1]]}
 step96: tape1={"farmer": ["PICKUP", "WHEAT", 5], "hands": [], "market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]]}
 step98: tape0={"farmer": ["CARE"], "hands": [["WEST"], ["NORTH"], ["NORTH"], ["NORTH"]], "market": []}
 step98: tape1={"farmer": ["CARE"], "hands": [["WEST"], ["NORTH"], ["NORTH"], ["NORTH"]], "market": [["SELL", "FERTILIZER", 1]]}
 step120: tape0={"farmer": ["WEST"], "hands": [], "market": [["HIRE"], ["HIRE"], ["HIRE"], ["SELL", "FERTILIZER", 1]]}
 step120: tape1={"farmer": ["WEST"], "hands": [], "market": [["HIRE"], ["HIRE"], ["HIRE"]]}
 step122: tape0={"farmer": ["PICKUP", "WHEAT", 2], "hands": [["FEED"], ["WEST"], ["CARE"], ["NORTH"]], "market": [["SELL", "WHEAT", 2]]}
 step122: tape1={"farmer": ["PICKUP", "WHEAT", 2], "hands": [["FEED"], ["WEST"], ["PASS"], ["NORTH"]], "market": [["SELL", "WHEAT", 2]]}
 step128: tape0={"farmer": ["COLLECT_FERTILIZER"], "hands": [["EAST"], ["FEED"], ["WEST"], ["WATER"]], "market": []}
 step128: tape1={"farmer": ["COLLECT_FERTILIZER"], "hands": [["EAST"], ["FEED"], ["WEST"], ["PASS"]], "market": []}
 step131: tape0={"farmer": ["NORTH"], "hands": [["COLLECT_FERTILIZER"], ["NORTH"], ["WATER"], ["PASS"]], "market": []}
 step131: tape1={"farmer": ["NORTH"], "hands": [["COLLECT_FERTILIZER"], ["NORTH"], ["WATER"], ["PASS"]], "market": [["SELL", "FERTILIZER", 1]]}
 step134: tape0={"farmer": ["WATER"], "hands": [["DROP"], ["WEST"], ["WATER"], ["WATER"]], "market": [["SELL", "FERTILIZER", 1]]}
 step134: tape1={"farmer": ["WATER"], "hands": [["DROP"], ["WEST"], ["WATER"], ["WATER"]], "market": []}
 step141: tape0={"farmer": ["DROP"], "hands": [["PASS"], ["WATER"], ["HARVEST"], ["WATER"]], "market": [["SELL", "FERTILIZER", 3]]}
 step141: tape1={"farmer": ["DROP"], "hands": [["PASS"], ["WATER"], ["HARVEST"], ["WATER"]], "market": [["SELL", "FERTILIZER", 4]]}

## cluster micro-diffs over 144..647 (sample pairs)
t1 vs t5: 17 diffs: [177, 312, 401, 429, 446, 473, 493, 526, 569, 581, 597, 598, 606, 614, 618, 622, 641]
t1 vs t4: 24 diffs: [216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239]
t7 vs t8: 16 diffs: [216, 217, 219, 220, 221, 222, 223, 224, 225, 226, 227, 233, 235, 236, 237, 238]
t3 vs t6: 23 diffs: [196, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 263]
t1 vs t3: 43 diffs: [196, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 236, 238, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259]
t4 vs t7: 24 diffs: [216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239]
t10 vs t1: 72 diffs: [192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231]
t11 vs t6: 24 diffs: [192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215]

## outlier diffs: t9 vs t1, t12 vs t1 over 144..647 (first 30 steps)
t9 vs t1: 481 diffs, first30: [144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173]
t12 vs t1: 494 diffs, first30: [144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 174, 175]
t9 vs t12: 412 diffs, first30: [144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173]
