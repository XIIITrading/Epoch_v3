================================================================================
EPOCH ML - TRADE LIFECYCLE PATTERN ANALYSIS
Generated: 2026-02-01 13:54
Source: trade_lifecycle_signals table
Baseline: 5922 trades, 54.0% WR
================================================================================

--------------------------------------------------------------------------------
PHASE: RAMP-UP TRENDS (30 M1 bars before entry)
--------------------------------------------------------------------------------

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         464    281   60.6%    +6.5pp ***
  INC_THEN_DEC                 971    571   58.8%    +4.8pp
  DECREASING                  1868    921   49.3%    -4.7pp
  VOLATILE                     641    373   58.2%    +4.2pp
  INCREASING                  1005    530   52.7%    -1.3pp
  DEC_THEN_INC                 973    523   53.8%    -0.3pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                      64     31   48.4%    -5.6pp ***
  INC_THEN_DEC                 392    232   59.2%    +5.2pp ***
  DEC_THEN_INC                 407    217   53.3%    -0.7pp
  FLAT                          75     40   53.3%    -0.7pp
  DECREASING                  2511   1348   53.7%    -0.3pp
  INCREASING                  2463   1327   53.9%    -0.1pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                    45     17   37.8%   -16.2pp !!!
  DEC_THEN_INC                 435    248   57.0%    +3.0pp
  INCREASING                    82     46   56.1%    +2.1pp
  VOLATILE                     300    166   55.3%    +1.3pp
  INC_THEN_DEC                 441    240   54.4%    +0.4pp
  FLAT                        4619   2482   53.7%    -0.3pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    67     33   49.3%    -4.8pp
  DECREASING                   125     63   50.4%    -3.6pp
  VOLATILE                     409    215   52.6%    -1.5pp
  DEC_THEN_INC                 617    327   53.0%    -1.0pp
  FLAT                        3855   2099   54.4%    +0.4pp
  INC_THEN_DEC                 849    462   54.4%    +0.4pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    67     42   62.7%    +8.7pp ***
  DEC_THEN_INC                 706    345   48.9%    -5.2pp ***
  VOLATILE                     388    190   49.0%    -5.0pp ***
  DECREASING                   110     54   49.1%    -4.9pp
  FLAT                        3770   2082   55.2%    +1.2pp
  INC_THEN_DEC                 881    486   55.2%    +1.1pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                      23     15   65.2%   +11.2pp
  FLAT                         111     52   46.8%    -7.2pp ***
  DECREASING                  2356   1312   55.7%    +1.7pp
  DEC_THEN_INC                 476    265   55.7%    +1.7pp
  INCREASING                  2471   1297   52.5%    -1.5pp
  INC_THEN_DEC                 455    247   54.3%    +0.3pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          65     47   72.3%   +18.3pp !!!
  VOLATILE                      31     18   58.1%    +4.0pp
  DEC_THEN_INC                 312    159   51.0%    -3.1pp
  INCREASING                  2598   1370   52.7%    -1.3pp
  DECREASING                  2569   1419   55.2%    +1.2pp
  INC_THEN_DEC                 334    182   54.5%    +0.5pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         412    198   48.1%    -6.0pp ***
  INC_THEN_DEC                 797    465   58.3%    +4.3pp
  DECREASING                  1739    873   50.2%    -3.8pp
  DEC_THEN_INC                 727    419   57.6%    +3.6pp
  VOLATILE                     435    225   51.7%    -2.3pp
  INCREASING                  1812   1019   56.2%    +2.2pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 862    504   58.5%    +4.4pp
  DECREASING                  2040   1035   50.7%    -3.3pp
  INCREASING                  1045    598   57.2%    +3.2pp
  VOLATILE                     566    315   55.7%    +1.6pp
  FLAT                         464    245   52.8%    -1.2pp
  DEC_THEN_INC                 932    498   53.4%    -0.6pp

--------------------------------------------------------------------------------
PHASE: AT ENTRY (snapshot)
--------------------------------------------------------------------------------

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NORMAL                      1555    772   49.6%    -4.4pp
  EXPLOSIVE                   1818   1040   57.2%    +3.2pp
  COMPRESSED                  1302    737   56.6%    +2.6pp
  EXPANDING                   1247    650   52.1%    -1.9pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_FALLING                1791   1015   56.7%    +2.7pp
  STRONG_RISING               1109    574   51.8%    -2.3pp
  STRONG_FALLING              1061    565   53.3%    -0.8pp
  MILD_RISING                 1961   1045   53.3%    -0.7pp

  h1_structure:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                        2668   1465   54.9%    +0.9pp
  BEAR                        3254   1734   53.3%    -0.7pp

  h4_structure:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BEAR                        2545   1412   55.5%    +1.5pp
  BULL                        3377   1787   52.9%    -1.1pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  CRITICAL                     298    138   46.3%    -7.7pp ***
  MODERATE                    1808    941   52.0%    -2.0pp
  STRONG                      2072   1154   55.7%    +1.7pp
  WEAK                        1744    966   55.4%    +1.4pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     366    225   61.5%    +7.5pp ***
  LOW                         3052   1630   53.4%    -0.6pp
  MINIMAL                     2504   1344   53.7%    -0.3pp

  m15_structure:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                        2887   1689   58.5%    +4.5pp
  BEAR                        3035   1510   49.8%    -4.3pp

  m1_structure:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NEUTRAL                      531    321   60.5%    +6.4pp ***
  BEAR                        2645   1338   50.6%    -3.4pp
  BULL                        2746   1540   56.1%    +2.1pp

  structure:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NEUTRAL                      160     68   42.5%   -11.5pp !!!
  BULL                        3032   1668   55.0%    +1.0pp
  BEAR                        2730   1463   53.6%    -0.4pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     350    194   55.4%    +1.4pp
  MINIMAL                     1838   1005   54.7%    +0.7pp
  LOW                         3734   2000   53.6%    -0.5pp

  sma_momentum_label:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STABLE                       322    181   56.2%    +2.2pp
  WIDENING                    2948   1572   53.3%    -0.7pp
  NARROWING                   2635   1438   54.6%    +0.6pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDENING                    2185   1158   53.0%    -1.0pp
  STRONG_WIDENING              936    515   55.0%    +1.0pp
  FLAT                        2784   1518   54.5%    +0.5pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDE_BEAR                   2077   1173   56.5%    +2.5pp
  NARROW_BEAR                 1060    554   52.3%    -1.8pp
  WIDE_BULL                   1816    960   52.9%    -1.2pp
  NARROW_BULL                  959    508   53.0%    -1.0pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_BUY                    1286    673   52.3%    -1.7pp
  MILD_SELL                   1168    645   55.2%    +1.2pp
  STRONG_BUY                  1641    900   54.8%    +0.8pp
  STRONG_SELL                 1827    981   53.7%    -0.3pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXTREME                      939    534   56.9%    +2.9pp
  LOW                         3381   1804   53.4%    -0.7pp
  ELEVATED                     518    278   53.7%    -0.4pp
  MODERATE                    1074    579   53.9%    -0.1pp

--------------------------------------------------------------------------------
PHASE: POST-ENTRY TRENDS (30 M1 bars after entry)
--------------------------------------------------------------------------------

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     632    311   49.2%    -4.8pp
  DECREASING                  1280    728   56.9%    +2.9pp
  INC_THEN_DEC                 862    450   52.2%    -1.8pp
  FLAT                         488    256   52.5%    -1.6pp
  INCREASING                  1282    709   55.3%    +1.3pp
  DEC_THEN_INC                1378    745   54.1%    +0.0pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 357    158   44.3%    -9.8pp ***
  FLAT                          84     52   61.9%    +7.9pp ***
  VOLATILE                      54     28   51.9%    -2.2pp
  INC_THEN_DEC                 355    199   56.1%    +2.0pp
  DECREASING                  2531   1396   55.2%    +1.1pp
  INCREASING                  2541   1366   53.8%    -0.3pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    52     35   67.3%   +13.3pp !!!
  VOLATILE                     259    162   62.5%    +8.5pp ***
  DECREASING                    24     15   62.5%    +8.5pp
  INC_THEN_DEC                 380    203   53.4%    -0.6pp
  DEC_THEN_INC                 363    194   53.4%    -0.6pp
  FLAT                        4844   2590   53.5%    -0.6pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                    83     32   38.6%   -15.5pp !!!
  VOLATILE                     524    311   59.4%    +5.3pp ***
  INC_THEN_DEC                 690    380   55.1%    +1.1pp
  DEC_THEN_INC                 806    427   53.0%    -1.0pp
  INCREASING                   100     55   55.0%    +1.0pp
  FLAT                        3719   1994   53.6%    -0.4pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     597    287   48.1%    -5.9pp ***
  INC_THEN_DEC                 671    329   49.0%    -5.0pp
  DEC_THEN_INC                 802    457   57.0%    +3.0pp
  INCREASING                   104     54   51.9%    -2.1pp
  FLAT                        3686   2038   55.3%    +1.3pp
  DECREASING                    62     34   54.8%    +0.8pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                      46     18   39.1%   -14.9pp !!!
  FLAT                         111     75   67.6%   +13.5pp !!!
  INC_THEN_DEC                 477    244   51.2%    -2.9pp
  DEC_THEN_INC                 471    263   55.8%    +1.8pp
  DECREASING                  2227   1175   52.8%    -1.3pp
  INCREASING                  2590   1424   55.0%    +1.0pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 303    137   45.2%    -8.8pp ***
  FLAT                          68     31   45.6%    -8.4pp ***
  VOLATILE                      35     17   48.6%    -5.4pp ***
  INC_THEN_DEC                 328    189   57.6%    +3.6pp
  INCREASING                  2589   1428   55.2%    +1.1pp
  DECREASING                  2599   1397   53.8%    -0.3pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     358    172   48.0%    -6.0pp ***
  FLAT                         384    196   51.0%    -3.0pp
  DECREASING                  1827   1023   56.0%    +2.0pp
  DEC_THEN_INC                 779    432   55.5%    +1.4pp
  INC_THEN_DEC                 728    383   52.6%    -1.4pp
  INCREASING                  1846    993   53.8%    -0.2pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     568    270   47.5%    -6.5pp ***
  DEC_THEN_INC                1259    755   60.0%    +5.9pp ***
  FLAT                         516    303   58.7%    +4.7pp
  DECREASING                  1201    625   52.0%    -2.0pp
  INCREASING                  1516    792   52.2%    -1.8pp
  INC_THEN_DEC                 862    454   52.7%    -1.4pp

--------------------------------------------------------------------------------
PHASE: FLIP DETECTION (sign changes in ramp-up)
--------------------------------------------------------------------------------

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLIP_TO_NEGATIVE             753    361   47.9%    -6.1pp ***
  FLIP_TO_POSITIVE             795    452   56.9%    +2.8pp
  NO_FLIP                      573    320   55.8%    +1.8pp
  MULTIPLE_FLIPS              3801   2066   54.4%    +0.3pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NO_FLIP                      724    418   57.7%    +3.7pp
  FLIP_TO_NEGATIVE            1243    642   51.6%    -2.4pp
  FLIP_TO_POSITIVE            1067    592   55.5%    +1.5pp
  MULTIPLE_FLIPS              2875   1543   53.7%    -0.3pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLIP_TO_NEGATIVE              32     19   59.4%    +5.4pp ***
  FLIP_TO_POSITIVE              33     18   54.5%    +0.5pp
  MULTIPLE_FLIPS              5846   3155   54.0%    -0.1pp

--------------------------------------------------------------------------------
PHASE: M5 TRADE PROGRESSION
--------------------------------------------------------------------------------

  health_trend:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                    76     13   17.1%   -36.9pp !!!
  INCREASING                   223    110   49.3%    -4.7pp
  VOLATILE                     666    386   58.0%    +3.9pp
  DEC_THEN_INC                 878    501   57.1%    +3.0pp
  INC_THEN_DEC                 722    387   53.6%    -0.4pp
  FLAT                        3357   1802   53.7%    -0.3pp

--------------------------------------------------------------------------------
LONG TRADE RAMP-UP PATTERNS
--------------------------------------------------------------------------------

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         206    126   61.2%    +7.1pp ***
  DECREASING                   870    430   49.4%    -4.6pp
  VOLATILE                     292    149   51.0%    -3.0pp
  INCREASING                   502    257   51.2%    -2.8pp
  INC_THEN_DEC                 488    269   55.1%    +1.1pp
  DEC_THEN_INC                 469    249   53.1%    -0.9pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          28     21   75.0%   +21.0pp
  INCREASING                  1170    596   50.9%    -3.1pp
  INC_THEN_DEC                 164     85   51.8%    -2.2pp
  DEC_THEN_INC                 212    113   53.3%    -0.7pp
  DECREASING                  1228    655   53.3%    -0.7pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    26     16   61.5%    +7.5pp
  INC_THEN_DEC                 187     89   47.6%    -6.4pp ***
  VOLATILE                     161     82   50.9%    -3.1pp
  FLAT                        2236   1179   52.7%    -1.3pp
  DEC_THEN_INC                 202    107   53.0%    -1.0pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    31     14   45.2%    -8.9pp ***
  INC_THEN_DEC                 404    185   45.8%    -8.2pp ***
  VOLATILE                     182     90   49.5%    -4.6pp
  DEC_THEN_INC                 253    129   51.0%    -3.0pp
  DECREASING                    65     36   55.4%    +1.4pp
  FLAT                        1892   1026   54.2%    +0.2pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     175     78   44.6%    -9.4pp ***
  DEC_THEN_INC                 346    158   45.7%    -8.4pp ***
  DECREASING                    37     17   45.9%    -8.1pp ***
  INC_THEN_DEC                 446    232   52.0%    -2.0pp
  INCREASING                    43     24   55.8%    +1.8pp
  FLAT                        1780    971   54.6%    +0.5pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          69     28   40.6%   -13.4pp !!!
  DEC_THEN_INC                 234    140   59.8%    +5.8pp ***
  INCREASING                  1161    592   51.0%    -3.0pp
  INC_THEN_DEC                 228    130   57.0%    +3.0pp
  DECREASING                  1105    580   52.5%    -1.5pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          34     23   67.6%   +13.6pp !!!
  DEC_THEN_INC                 151     76   50.3%    -3.7pp
  DECREASING                  1230    640   52.0%    -2.0pp
  INCREASING                  1244    648   52.1%    -1.9pp
  INC_THEN_DEC                 142     77   54.2%    +0.2pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         197     91   46.2%    -7.8pp ***
  VOLATILE                     194     97   50.0%    -4.0pp
  DECREASING                   790    413   52.3%    -1.7pp
  INCREASING                   891    472   53.0%    -1.0pp
  INC_THEN_DEC                 410    220   53.7%    -0.4pp
  DEC_THEN_INC                 345    187   54.2%    +0.2pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   904    426   47.1%    -6.9pp ***
  INCREASING                   545    315   57.8%    +3.8pp
  INC_THEN_DEC                 420    220   52.4%    -1.6pp
  VOLATILE                     267    146   54.7%    +0.7pp
  DEC_THEN_INC                 443    242   54.6%    +0.6pp
  FLAT                         241    129   53.5%    -0.5pp

--------------------------------------------------------------------------------
SHORT TRADE RAMP-UP PATTERNS
--------------------------------------------------------------------------------

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     349    224   64.2%   +10.2pp !!!
  INC_THEN_DEC                 483    302   62.5%    +8.5pp ***
  FLAT                         258    155   60.1%    +6.1pp ***
  DECREASING                   998    491   49.2%    -4.8pp
  DEC_THEN_INC                 504    274   54.4%    +0.3pp
  INCREASING                   503    273   54.3%    +0.3pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          47     19   40.4%   -13.6pp !!!
  INC_THEN_DEC                 228    147   64.5%   +10.5pp !!!
  VOLATILE                      45     23   51.1%    -2.9pp
  INCREASING                  1293    731   56.5%    +2.5pp
  DEC_THEN_INC                 195    104   53.3%    -0.7pp
  DECREASING                  1283    693   54.0%    -0.0pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                    30     10   33.3%   -20.7pp !!!
  DEC_THEN_INC                 233    141   60.5%    +6.5pp ***
  VOLATILE                     139     84   60.4%    +6.4pp ***
  INC_THEN_DEC                 254    151   59.4%    +5.4pp ***
  FLAT                        2383   1303   54.7%    +0.7pp
  INCREASING                    56     30   53.6%    -0.4pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                    60     27   45.0%    -9.0pp ***
  INC_THEN_DEC                 445    277   62.2%    +8.2pp ***
  INCREASING                    36     19   52.8%    -1.2pp
  VOLATILE                     227    125   55.1%    +1.0pp
  FLAT                        1963   1073   54.7%    +0.6pp
  DEC_THEN_INC                 364    198   54.4%    +0.4pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    24     18   75.0%   +21.0pp
  INC_THEN_DEC                 435    254   58.4%    +4.4pp
  DECREASING                    73     37   50.7%    -3.3pp
  DEC_THEN_INC                 360    187   51.9%    -2.1pp
  FLAT                        1990   1111   55.8%    +1.8pp
  VOLATILE                     213    112   52.6%    -1.4pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                  1251    732   58.5%    +4.5pp
  FLAT                          42     24   57.1%    +3.1pp
  INC_THEN_DEC                 227    117   51.5%    -2.5pp
  DEC_THEN_INC                 242    125   51.7%    -2.4pp
  INCREASING                  1310    705   53.8%    -0.2pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          31     24   77.4%   +23.4pp !!!
  DECREASING                  1339    779   58.2%    +4.2pp
  DEC_THEN_INC                 161     83   51.6%    -2.5pp
  INCREASING                  1354    722   53.3%    -0.7pp
  INC_THEN_DEC                 192    105   54.7%    +0.7pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 387    245   63.3%    +9.3pp ***
  DEC_THEN_INC                 382    232   60.7%    +6.7pp ***
  DECREASING                   949    460   48.5%    -5.5pp ***
  INCREASING                   921    547   59.4%    +5.4pp ***
  FLAT                         215    107   49.8%    -4.3pp
  VOLATILE                     241    128   53.1%    -0.9pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 442    284   64.3%   +10.2pp !!!
  INCREASING                   500    283   56.6%    +2.6pp
  VOLATILE                     299    169   56.5%    +2.5pp
  FLAT                         223    116   52.0%    -2.0pp
  DEC_THEN_INC                 489    256   52.4%    -1.7pp
  DECREASING                  1136    609   53.6%    -0.4pp

--------------------------------------------------------------------------------
COMBINATION PATTERNS (indicator pairs, edge >= 5pp)
--------------------------------------------------------------------------------

  Pattern                                                               N      WR     Edge
  ----------------------------------------------------------------- ----- ------- --------
  rampup_vol_delta=DECREASING+rampup_cvd_slope=FLAT                    21   19.0%   -35.0pp !!!
  rampup_candle_range_pct=DEC_THEN_INC+rampup_vol_delta=FLAT           93   23.7%   -30.4pp !!!
  rampup_vol_delta=INCREASING+rampup_cvd_slope=INC_THEN_DEC            60   83.3%   +29.3pp !!!
  rampup_candle_range_pct=INC_THEN_DEC+rampup_vol_delta=VOLATILE       83   26.5%   -27.5pp !!!
  entry_health_score=CRITICAL+entry_candle_range_pct=EXPLOSIVE         32   31.2%   -22.8pp !!!
  rampup_candle_range_pct=VOLATILE+rampup_vol_delta=VOLATILE           25   32.0%   -22.0pp !!!
  rampup_sma_spread=INC_THEN_DEC+rampup_vol_delta=INCREASING           65   75.4%   +21.4pp !!!
  rampup_candle_range_pct=INC_THEN_DEC+rampup_vol_delta=INC_THEN_DEC   128   75.0%   +21.0pp !!!
  rampup_candle_range_pct=FLAT+rampup_vol_roc=VOLATILE                 24   75.0%   +21.0pp !!!
  rampup_sma_spread=DEC_THEN_INC+rampup_vol_delta=DECREASING           70   34.3%   -19.7pp !!!
  rampup_candle_range_pct=VOLATILE+rampup_vol_delta=FLAT               64   73.4%   +19.4pp !!!
  rampup_sma_spread=INCREASING+rampup_vol_delta=VOLATILE              162   35.2%   -18.8pp !!!
  rampup_candle_range_pct=DEC_THEN_INC+rampup_vol_roc=FLAT             66   72.7%   +18.7pp !!!
  flip_cvd_slope=FLIP_TO_POSITIVE+rampup_vol_delta=INC_THEN_DEC       124   72.6%   +18.6pp !!!
  rampup_candle_range_pct=FLAT+rampup_vol_delta=DEC_THEN_INC           42   71.4%   +17.4pp !!!
  rampup_candle_range_pct=INCREASING+rampup_vol_delta=FLAT             56   71.4%   +17.4pp !!!
  entry_health_score=CRITICAL+entry_candle_range_pct=EXPANDING         56   37.5%   -16.5pp !!!
  rampup_candle_range_pct=VOLATILE+rampup_vol_delta=INC_THEN_DEC       91   70.3%   +16.3pp !!!
  rampup_vol_delta=FLAT+rampup_cvd_slope=DECREASING                   168   38.1%   -15.9pp !!!
  rampup_candle_range_pct=INCREASING+rampup_vol_delta=DECREASING      308   38.3%   -15.7pp !!!
  rampup_candle_range_pct=VOLATILE+rampup_vol_roc=VOLATILE             92   69.6%   +15.5pp !!!
  rampup_vol_delta=FLAT+rampup_vol_roc=FLAT                            50   40.0%   -14.0pp !!!
  rampup_vol_delta=FLAT+rampup_vol_roc=INC_THEN_DEC                    45   40.0%   -14.0pp !!!
  rampup_candle_range_pct=DEC_THEN_INC+rampup_vol_delta=DEC_THEN_INC   125   68.0%   +14.0pp !!!
  rampup_candle_range_pct=INC_THEN_DEC+rampup_vol_delta=INCREASING    336   67.6%   +13.5pp !!!
  flip_cvd_slope=FLIP_TO_POSITIVE+rampup_vol_delta=VOLATILE            79   40.5%   -13.5pp !!!
  rampup_vol_delta=DEC_THEN_INC+rampup_vol_roc=INC_THEN_DEC           126   67.5%   +13.4pp !!!
  rampup_candle_range_pct=FLAT+rampup_vol_roc=DEC_THEN_INC             78   66.7%   +12.6pp !!!
  entry_candle_range_pct=EXPLOSIVE+entry_vol_delta=MILD_SELL          202   66.3%   +12.3pp !!!
  rampup_candle_range_pct=DECREASING+rampup_vol_delta=FLAT            125   42.4%   -11.6pp !!!
  rampup_candle_range_pct=INC_THEN_DEC+rampup_vol_roc=INCREASING      174   65.5%   +11.5pp !!!
  entry_health_score=CRITICAL+entry_candle_range_pct=NORMAL            89   42.7%   -11.3pp !!!
  rampup_vol_delta=DECREASING+rampup_cvd_slope=DEC_THEN_INC            49   42.9%   -11.2pp !!!
  rampup_vol_delta=VOLATILE+rampup_vol_roc=DEC_THEN_INC                56   42.9%   -11.2pp !!!
  rampup_sma_spread=INC_THEN_DEC+rampup_vol_delta=FLAT                 28   42.9%   -11.2pp !!!
  rampup_sma_spread=DEC_THEN_INC+rampup_vol_delta=VOLATILE             21   42.9%   -11.2pp !!!
  rampup_candle_range_pct=INCREASING+rampup_vol_delta=VOLATILE         83   65.1%   +11.0pp !!!
  rampup_sma_spread=FLAT+rampup_vol_delta=INCREASING                   20   65.0%   +11.0pp !!!
  rampup_candle_range_pct=INC_THEN_DEC+rampup_vol_roc=VOLATILE         81   43.2%   -10.8pp !!!
  rampup_candle_range_pct=FLAT+rampup_vol_roc=INC_THEN_DEC             53   43.4%   -10.6pp !!!
  rampup_vol_delta=DECREASING+rampup_vol_roc=FLAT                     131   43.5%   -10.5pp !!!
  flip_cvd_slope=NO_FLIP+rampup_vol_delta=FLAT                         31   64.5%   +10.5pp !!!
  rampup_candle_range_pct=FLAT+rampup_vol_roc=INCREASING              104   64.4%   +10.4pp !!!
  flip_cvd_slope=FLIP_TO_POSITIVE+rampup_vol_delta=INCREASING         212   64.2%   +10.1pp !!!
  rampup_sma_spread=DECREASING+rampup_vol_delta=FLAT                  200   44.0%   -10.0pp !!!
  rampup_sma_spread=DEC_THEN_INC+rampup_vol_delta=DEC_THEN_INC         61   63.9%    +9.9pp ***
  rampup_candle_range_pct=DECREASING+rampup_vol_roc=FLAT              131   44.3%    -9.7pp ***
  rampup_vol_delta=INCREASING+rampup_vol_roc=INC_THEN_DEC             240   63.7%    +9.7pp ***
  rampup_vol_delta=FLAT+rampup_vol_roc=DECREASING                     142   44.4%    -9.7pp ***
  rampup_vol_delta=VOLATILE+rampup_vol_roc=INCREASING                  66   63.6%    +9.6pp ***

================================================================================
KEY FINDINGS SUMMARY
================================================================================

  TOP 15 POSITIVE EDGES (highest WR above 54.0% baseline):
  Pattern                                                          N      WR     Edge
  ------------------------------------------------------------ ----- ------- --------
  SHORT_rampup_sma_spread -> FLAT                                 31   77.4%   +23.4pp
  SHORT_rampup_short_score -> INCREASING                          24   75.0%   +21.0pp
  LONG_rampup_cvd_slope -> FLAT                                   28   75.0%   +21.0pp
  rampup_sma_spread -> FLAT                                       65   72.3%   +18.3pp
  LONG_rampup_sma_spread -> FLAT                                  34   67.6%   +13.6pp
  post_sma_momentum_ratio -> FLAT                                111   67.6%   +13.5pp
  post_health_score -> INCREASING                                 52   67.3%   +13.3pp
  rampup_sma_momentum_ratio -> VOLATILE                           23   65.2%   +11.2pp
  SHORT_rampup_cvd_slope -> INC_THEN_DEC                         228   64.5%   +10.5pp
  SHORT_rampup_vol_roc -> INC_THEN_DEC                           442   64.3%   +10.2pp
  SHORT_rampup_candle_range_pct -> VOLATILE                      349   64.2%   +10.2pp
  SHORT_rampup_vol_delta -> INC_THEN_DEC                         387   63.3%    +9.3pp
  rampup_short_score -> INCREASING                                67   62.7%    +8.7pp
  post_health_score -> VOLATILE                                  259   62.5%    +8.5pp
  SHORT_rampup_candle_range_pct -> INC_THEN_DEC                  483   62.5%    +8.5pp

  TOP 15 NEGATIVE EDGES (lowest WR below 54.0% baseline):
  Pattern                                                          N      WR     Edge
  ------------------------------------------------------------ ----- ------- --------
  LONG_rampup_short_score -> DEC_THEN_INC                        346   45.7%    -8.4pp
  post_sma_spread -> FLAT                                         68   45.6%    -8.4pp
  post_sma_spread -> DEC_THEN_INC                                303   45.2%    -8.8pp
  LONG_rampup_long_score -> INCREASING                            31   45.2%    -8.9pp
  SHORT_rampup_long_score -> DECREASING                           60   45.0%    -9.0pp
  LONG_rampup_short_score -> VOLATILE                            175   44.6%    -9.4pp
  post_cvd_slope -> DEC_THEN_INC                                 357   44.3%    -9.8pp
  entry_m5_structure -> NEUTRAL                                  160   42.5%   -11.5pp
  LONG_rampup_sma_momentum_ratio -> FLAT                          69   40.6%   -13.4pp
  SHORT_rampup_cvd_slope -> FLAT                                  47   40.4%   -13.6pp
  post_sma_momentum_ratio -> VOLATILE                             46   39.1%   -14.9pp
  post_long_score -> DECREASING                                   83   38.6%   -15.5pp
  rampup_health_score -> DECREASING                               45   37.8%   -16.2pp
  SHORT_rampup_health_score -> DECREASING                         30   33.3%   -20.7pp
  m5_health_trend -> DECREASING                                   76   17.1%   -36.9pp

*** = edge >= 5pp with N >= 30
!!! = edge >= 10pp with N >= 30
Baseline WR: 54.0%