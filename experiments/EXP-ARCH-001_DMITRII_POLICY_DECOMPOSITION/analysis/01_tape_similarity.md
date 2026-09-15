# Tape structural similarity

## steps 0..143 vs tape 0 (branch point check)
tape0: 0 diffs IDENTICAL
tape1: 10 diffs first@[70, 90, 96, 98, 120]
tape2: 0 diffs IDENTICAL
tape3: 0 diffs IDENTICAL
tape4: 0 diffs IDENTICAL
tape5: 0 diffs IDENTICAL
tape6: 0 diffs IDENTICAL
tape7: 0 diffs IDENTICAL
tape8: 0 diffs IDENTICAL
tape9: 0 diffs IDENTICAL
tape10: 0 diffs IDENTICAL
tape11: 0 diffs IDENTICAL
tape12: 0 diffs IDENTICAL

## steps 144..647 vs tape 0 (count diffs)
tape0: 0 diffs of 504
tape1: 430 diffs of 504
tape2: 110 diffs of 504
tape3: 417 diffs of 504
tape4: 430 diffs of 504
tape5: 431 diffs of 504
tape6: 430 diffs of 504
tape7: 412 diffs of 504
tape8: 421 diffs of 504
tape9: 504 diffs of 504
tape10: 431 diffs of 504
tape11: 430 diffs of 504
tape12: 504 diffs of 504

## steps 648..718 vs tape 2 (forced plan-2 regime)
tape0: 11 diffs first@[649, 669, 673, 692, 693]
tape1: 68 diffs first@[648, 649, 650, 651, 652]
tape2: 0 diffs IDENTICAL
tape3: 0 diffs IDENTICAL
tape4: 0 diffs IDENTICAL
tape5: 0 diffs IDENTICAL
tape6: 0 diffs IDENTICAL
tape7: 0 diffs IDENTICAL
tape8: 0 diffs IDENTICAL
tape9: 0 diffs IDENTICAL
tape10: 0 diffs IDENTICAL
tape11: 0 diffs IDENTICAL
tape12: 0 diffs IDENTICAL

## pairwise diff counts over steps 144..647
          0     1     2     3     4     5     6     7     8     9    10    11    12
t  0      0   430   110   417   430   431   430   412   421   504   431   430   504
t  1    430     0   429    43    24    17    20    24    24   481    72    44   494
t  2    110   429     0   416   429   431   429   411   420   504   430   429   504
t  3    417    43   416     0    47    60    23    47    47   481    72    46   494
t  4    430    24   429    47     0    41    24    24    24   478    65    48   485
t  5    431    17   431    60    41     0    37    41    41   481    89    61   495
t  6    430    20   429    23    24    37     0    24    24   481    72    24   494
t  7    412    24   411    47    24    41    24     0    16   481    72    48   494
t  8    421    24   420    47    24    41    24    16     0   481    72    48   494
t  9    504   481   504   481   478   481   481   481   481     0   473   476   412
t 10    431    72   430    72    65    89    72    72    72   473     0    72   457
t 11    430    44   429    46    48    61    24    48    48   476    72     0   494
t 12    504   494   504   494   485   495   494   494   494   412   457   494     0

## distinct-action counts per 24-step day across 13 tapes (divergence map)
day 0 steps  0.. 23:   24 distinct of 312
day 1 steps 24.. 47:   21 distinct of 312
day 2 steps 48.. 71:   25 distinct of 312
day 3 steps 72.. 95:   25 distinct of 312
day 4 steps 96..119:   26 distinct of 312
day 5 steps120..143:   30 distinct of 312
day 6 steps144..167:   84 distinct of 312
day 7 steps168..191:   95 distinct of 312
day 8 steps192..215:  140 distinct of 312
day 9 steps216..239:  149 distinct of 312
day10 steps240..263:  104 distinct of 312
day11 steps264..287:   96 distinct of 312
day12 steps288..311:   69 distinct of 312
day13 steps312..335:   93 distinct of 312
day14 steps336..359:   95 distinct of 312
day15 steps360..383:   99 distinct of 312
day16 steps384..407:   93 distinct of 312
day17 steps408..431:   73 distinct of 312
day18 steps432..455:   98 distinct of 312
day19 steps456..479:   94 distinct of 312
day20 steps480..503:   90 distinct of 312
day21 steps504..527:   77 distinct of 312
day22 steps528..551:   99 distinct of 312
day23 steps552..575:   98 distinct of 312
day24 steps576..599:  107 distinct of 312
day25 steps600..623:  114 distinct of 312
day26 steps624..647:  100 distinct of 312
day27 steps648..671:   50 distinct of 312
day28 steps672..695:   52 distinct of 312
day29 steps696..718:   48 distinct of 312
