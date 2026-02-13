================================================================================
EPOCH ML - LIFECYCLE RAMP-UP REPORT
Generated: 2026-02-01 14:36
Source: trade_lifecycle_signals + m1_indicator_bars
Win Condition: trades_m5_r_win.is_winner (M5 ATR(14) x 1.1, close-based)
Baseline: 5922 trades, 54.0% WR
================================================================================

================================================================================
SECTION 1: PRE-ENTRY - LONG TRADES
  Trades: 2827, Wins: 1480, WR: 52.4% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  DECREASING         VOLATILE           DECREASING           38   81.6%   +27.6pp !!!
  INC_THEN_DEC       INC_THEN_DEC       DECREASING           23   78.3%   +24.2pp
  VOLATILE           INC_THEN_DEC       DECREASING           32   78.1%   +24.1pp !!!
  DEC_THEN_INC       DEC_THEN_INC       DECREASING           27   77.8%   +23.8pp
  INCREASING         DEC_THEN_INC       INCREASING           30   76.7%   +22.6pp !!!
  INCREASING         DEC_THEN_INC       DECREASING           49   73.5%   +19.5pp !!!
  INC_THEN_DEC       INC_THEN_DEC       INCREASING           30   73.3%   +19.3pp !!!
  FLAT               INCREASING         DECREASING           25   72.0%   +18.0pp
  INC_THEN_DEC       INCREASING         DECREASING           63   71.4%   +17.4pp !!!
  INC_THEN_DEC       DECREASING         DECREASING           64   65.6%   +11.6pp !!!
  DEC_THEN_INC       DECREASING         INCREASING           60   65.0%   +11.0pp !!!
  INC_THEN_DEC       INCREASING         DEC_THEN_INC         20   65.0%   +11.0pp
  DEC_THEN_INC       INC_THEN_DEC       DECREASING           34   64.7%   +10.7pp !!!
  FLAT               DECREASING         INCREASING           42   61.9%    +7.9pp ***
  INCREASING         INC_THEN_DEC       INCREASING           33   60.6%    +6.6pp ***

  --- RAMP-UP TREND SIGNALS (30 M1 bars before entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         206    126   61.2%    +7.1pp ***
  INC_THEN_DEC                 488    269   55.1%    +1.1pp
  DEC_THEN_INC                 469    249   53.1%    -0.9pp
  INCREASING                   502    257   51.2%    -2.8pp
  VOLATILE                     292    149   51.0%    -3.0pp
  DECREASING                   870    430   49.4%    -4.6pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 345    187   54.2%    +0.2pp
  INC_THEN_DEC                 410    220   53.7%    -0.4pp
  INCREASING                   891    472   53.0%    -1.0pp
  DECREASING                   790    413   52.3%    -1.7pp
  VOLATILE                     194     97   50.0%    -4.0pp
  FLAT                         197     91   46.2%    -7.8pp ***

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                   545    315   57.8%    +3.8pp
  VOLATILE                     267    146   54.7%    +0.7pp
  DEC_THEN_INC                 443    242   54.6%    +0.6pp
  FLAT                         241    129   53.5%    -0.5pp
  INC_THEN_DEC                 420    220   52.4%    -1.6pp
  DECREASING                   904    426   47.1%    -6.9pp ***

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          28     21   75.0%   +21.0pp
  DECREASING                  1228    655   53.3%    -0.7pp
  DEC_THEN_INC                 212    113   53.3%    -0.7pp
  INC_THEN_DEC                 164     85   51.8%    -2.2pp
  INCREASING                  1170    596   50.9%    -3.1pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          34     23   67.6%   +13.6pp !!!
  INC_THEN_DEC                 142     77   54.2%    +0.2pp
  INCREASING                  1244    648   52.1%    -1.9pp
  DECREASING                  1230    640   52.0%    -2.0pp
  DEC_THEN_INC                 151     76   50.3%    -3.7pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 234    140   59.8%    +5.8pp ***
  INC_THEN_DEC                 228    130   57.0%    +3.0pp
  DECREASING                  1105    580   52.5%    -1.5pp
  INCREASING                  1161    592   51.0%    -3.0pp
  FLAT                          69     28   40.6%   -13.4pp !!!

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    26     16   61.5%    +7.5pp
  DEC_THEN_INC                 202    107   53.0%    -1.0pp
  FLAT                        2236   1179   52.7%    -1.3pp
  VOLATILE                     161     82   50.9%    -3.1pp
  INC_THEN_DEC                 187     89   47.6%    -6.4pp ***

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                    65     36   55.4%    +1.4pp
  FLAT                        1892   1026   54.2%    +0.2pp
  DEC_THEN_INC                 253    129   51.0%    -3.0pp
  VOLATILE                     182     90   49.5%    -4.6pp
  INC_THEN_DEC                 404    185   45.8%    -8.2pp ***
  INCREASING                    31     14   45.2%    -8.9pp ***

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    43     24   55.8%    +1.8pp
  FLAT                        1780    971   54.6%    +0.5pp
  INC_THEN_DEC                 446    232   52.0%    -2.0pp
  DECREASING                    37     17   45.9%    -8.1pp ***
  DEC_THEN_INC                 346    158   45.7%    -8.4pp ***
  VOLATILE                     175     78   44.6%    -9.4pp ***

  --- ENTRY LEVEL SIGNALS (snapshot at entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPANDING                    539    295   54.7%    +0.7pp
  EXPLOSIVE                    821    432   52.6%    -1.4pp
  COMPRESSED                   712    373   52.4%    -1.6pp
  NORMAL                       755    380   50.3%    -3.7pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_BUY                   902    501   55.5%    +1.5pp
  STRONG_SELL                  727    389   53.5%    -0.5pp
  MILD_SELL                    563    299   53.1%    -0.9pp
  MILD_BUY                     635    291   45.8%    -8.2pp ***

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     476    267   56.1%    +2.1pp
  EXTREME                      447    243   54.4%    +0.3pp
  ELEVATED                     253    134   53.0%    -1.1pp
  LOW                         1645    834   50.7%    -3.3pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_FALLING                 814    448   55.0%    +1.0pp
  STRONG_RISING                605    315   52.1%    -2.0pp
  STRONG_FALLING               474    246   51.9%    -2.1pp
  MILD_RISING                  934    471   50.4%    -3.6pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NARROW_BULL                  529    281   53.1%    -0.9pp
  NARROW_BEAR                  559    295   52.8%    -1.2pp
  WIDE_BULL                    865    452   52.3%    -1.8pp
  WIDE_BEAR                    868    450   51.8%    -2.2pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                        1383    741   53.6%    -0.4pp
  STRONG_WIDENING              430    228   53.0%    -1.0pp
  WIDENING                    1007    509   50.5%    -3.5pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WEAK                         883    482   54.6%    +0.6pp
  STRONG                       912    491   53.8%    -0.2pp
  MODERATE                     903    446   49.4%    -4.6pp
  CRITICAL                     129     61   47.3%    -6.7pp ***

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     181     96   53.0%    -1.0pp
  MINIMAL                     1311    686   52.3%    -1.7pp
  LOW                         1335    698   52.3%    -1.7pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MINIMAL                      928    504   54.3%    +0.3pp
  MODERATE                     200    106   53.0%    -1.0pp
  LOW                         1699    870   51.2%    -2.8pp

  --- FLIP SIGNALS (sign changes in ramp-up) ---

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS              2781   1455   52.3%    -1.7pp
  FLIP_TO_POSITIVE              23     12   52.2%    -1.8pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NO_FLIP                      258    147   57.0%    +3.0pp
  MULTIPLE_FLIPS              1887    999   52.9%    -1.1pp
  FLIP_TO_POSITIVE             340    172   50.6%    -3.4pp
  FLIP_TO_NEGATIVE             342    162   47.4%    -6.7pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLIP_TO_POSITIVE             478    279   58.4%    +4.3pp
  FLIP_TO_NEGATIVE             550    293   53.3%    -0.7pp
  MULTIPLE_FLIPS              1444    744   51.5%    -2.5pp
  NO_FLIP                      348    162   46.6%    -7.5pp ***

================================================================================
SECTION 1: PRE-ENTRY - SHORT TRADES
  Trades: 3095, Wins: 1719, WR: 55.5% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  VOLATILE           FLAT               DECREASING           21   90.5%   +36.5pp
  VOLATILE           INCREASING         DECREASING           39   84.6%   +30.6pp !!!
  INCREASING         VOLATILE           DECREASING           31   83.9%   +29.9pp !!!
  INC_THEN_DEC       INC_THEN_DEC       INCREASING           36   80.6%   +26.5pp !!!
  INC_THEN_DEC       INC_THEN_DEC       DECREASING           20   80.0%   +26.0pp
  DEC_THEN_INC       DEC_THEN_INC       INCREASING           30   76.7%   +22.6pp !!!
  INC_THEN_DEC       INCREASING         INCREASING           80   76.2%   +22.2pp !!!
  DECREASING         INCREASING         INC_THEN_DEC         21   76.2%   +22.2pp
  INC_THEN_DEC       INCREASING         DECREASING           62   74.2%   +20.2pp !!!
  DEC_THEN_INC       INCREASING         DECREASING           45   73.3%   +19.3pp !!!
  FLAT               INC_THEN_DEC       DECREASING           29   72.4%   +18.4pp
  VOLATILE           INCREASING         INCREASING           52   71.2%   +17.1pp !!!
  DEC_THEN_INC       DEC_THEN_INC       DECREASING           41   70.7%   +16.7pp !!!
  INC_THEN_DEC       DECREASING         DECREASING           67   68.7%   +14.6pp !!!
  DEC_THEN_INC       INC_THEN_DEC       INCREASING           22   68.2%   +14.2pp

  --- RAMP-UP TREND SIGNALS (30 M1 bars before entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     349    224   64.2%   +10.2pp !!!
  INC_THEN_DEC                 483    302   62.5%    +8.5pp ***
  FLAT                         258    155   60.1%    +6.1pp ***
  DEC_THEN_INC                 504    274   54.4%    +0.3pp
  INCREASING                   503    273   54.3%    +0.3pp
  DECREASING                   998    491   49.2%    -4.8pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 387    245   63.3%    +9.3pp ***
  DEC_THEN_INC                 382    232   60.7%    +6.7pp ***
  INCREASING                   921    547   59.4%    +5.4pp ***
  VOLATILE                     241    128   53.1%    -0.9pp
  FLAT                         215    107   49.8%    -4.3pp
  DECREASING                   949    460   48.5%    -5.5pp ***

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 442    284   64.3%   +10.2pp !!!
  INCREASING                   500    283   56.6%    +2.6pp
  VOLATILE                     299    169   56.5%    +2.5pp
  DECREASING                  1136    609   53.6%    -0.4pp
  DEC_THEN_INC                 489    256   52.4%    -1.7pp
  FLAT                         223    116   52.0%    -2.0pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 228    147   64.5%   +10.5pp !!!
  INCREASING                  1293    731   56.5%    +2.5pp
  DECREASING                  1283    693   54.0%    -0.0pp
  DEC_THEN_INC                 195    104   53.3%    -0.7pp
  VOLATILE                      45     23   51.1%    -2.9pp
  FLAT                          47     19   40.4%   -13.6pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          31     24   77.4%   +23.4pp !!!
  DECREASING                  1339    779   58.2%    +4.2pp
  INC_THEN_DEC                 192    105   54.7%    +0.7pp
  INCREASING                  1354    722   53.3%    -0.7pp
  DEC_THEN_INC                 161     83   51.6%    -2.5pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                  1251    732   58.5%    +4.5pp
  FLAT                          42     24   57.1%    +3.1pp
  INCREASING                  1310    705   53.8%    -0.2pp
  DEC_THEN_INC                 242    125   51.7%    -2.4pp
  INC_THEN_DEC                 227    117   51.5%    -2.5pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 233    141   60.5%    +6.5pp ***
  VOLATILE                     139     84   60.4%    +6.4pp ***
  INC_THEN_DEC                 254    151   59.4%    +5.4pp ***
  FLAT                        2383   1303   54.7%    +0.7pp
  INCREASING                    56     30   53.6%    -0.4pp
  DECREASING                    30     10   33.3%   -20.7pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 445    277   62.2%    +8.2pp ***
  VOLATILE                     227    125   55.1%    +1.0pp
  FLAT                        1963   1073   54.7%    +0.6pp
  DEC_THEN_INC                 364    198   54.4%    +0.4pp
  INCREASING                    36     19   52.8%    -1.2pp
  DECREASING                    60     27   45.0%    -9.0pp ***

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    24     18   75.0%   +21.0pp
  INC_THEN_DEC                 435    254   58.4%    +4.4pp
  FLAT                        1990   1111   55.8%    +1.8pp
  VOLATILE                     213    112   52.6%    -1.4pp
  DEC_THEN_INC                 360    187   51.9%    -2.1pp
  DECREASING                    73     37   50.7%    -3.3pp

  --- ENTRY LEVEL SIGNALS (snapshot at entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  COMPRESSED                   590    364   61.7%    +7.7pp ***
  EXPLOSIVE                    997    608   61.0%    +7.0pp ***
  EXPANDING                    708    355   50.1%    -3.9pp
  NORMAL                       800    392   49.0%    -5.0pp ***

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_BUY                     651    382   58.7%    +4.7pp
  MILD_SELL                    605    346   57.2%    +3.2pp
  STRONG_BUY                   739    399   54.0%    -0.0pp
  STRONG_SELL                 1100    592   53.8%    -0.2pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXTREME                      492    291   59.1%    +5.1pp ***
  LOW                         1736    970   55.9%    +1.9pp
  ELEVATED                     265    144   54.3%    +0.3pp
  MODERATE                     598    312   52.2%    -1.8pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_FALLING                 977    567   58.0%    +4.0pp
  MILD_RISING                 1027    574   55.9%    +1.9pp
  STRONG_FALLING               587    319   54.3%    +0.3pp
  STRONG_RISING                504    259   51.4%    -2.6pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDE_BEAR                   1209    723   59.8%    +5.8pp ***
  WIDE_BULL                    951    508   53.4%    -0.6pp
  NARROW_BULL                  430    227   52.8%    -1.2pp
  NARROW_BEAR                  501    259   51.7%    -2.3pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_WIDENING              506    287   56.7%    +2.7pp
  FLAT                        1401    777   55.5%    +1.4pp
  WIDENING                    1178    649   55.1%    +1.1pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG                      1160    663   57.2%    +3.1pp
  WEAK                         861    484   56.2%    +2.2pp
  MODERATE                     905    495   54.7%    +0.7pp
  CRITICAL                     169     77   45.6%    -8.5pp ***

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     185    129   69.7%   +15.7pp !!!
  MINIMAL                     1193    658   55.2%    +1.1pp
  LOW                         1717    932   54.3%    +0.3pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     150     88   58.7%    +4.6pp
  LOW                         2035   1130   55.5%    +1.5pp
  MINIMAL                      910    501   55.1%    +1.0pp

  --- FLIP SIGNALS (sign changes in ramp-up) ---

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS              3065   1700   55.5%    +1.4pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLIP_TO_POSITIVE             455    280   61.5%    +7.5pp ***
  MULTIPLE_FLIPS              1914   1067   55.7%    +1.7pp
  NO_FLIP                      315    173   54.9%    +0.9pp
  FLIP_TO_NEGATIVE             411    199   48.4%    -5.6pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NO_FLIP                      376    256   68.1%   +14.1pp !!!
  MULTIPLE_FLIPS              1431    799   55.8%    +1.8pp
  FLIP_TO_POSITIVE             589    313   53.1%    -0.9pp
  FLIP_TO_NEGATIVE             693    349   50.4%    -3.7pp

================================================================================
SECTION 2A: PRE-ENTRY - CONTINUATION TRADES (M5 aligned with direction)
  Trades: 2915, Wins: 1491, WR: 51.1% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  INC_THEN_DEC       INC_THEN_DEC       INCREASING           38   81.6%   +27.6pp !!!
  VOLATILE           INC_THEN_DEC       DECREASING           21   81.0%   +26.9pp
  DEC_THEN_INC       DEC_THEN_INC       DECREASING           41   80.5%   +26.5pp !!!
  INC_THEN_DEC       INCREASING         DECREASING           43   76.7%   +22.7pp !!!
  INCREASING         INCREASING         INCREASING           43   72.1%   +18.1pp !!!
  VOLATILE           INCREASING         INCREASING           44   70.5%   +16.4pp !!!
  INCREASING         DEC_THEN_INC       INCREASING           26   69.2%   +15.2pp
  INCREASING         INCREASING         DECREASING           45   68.9%   +14.9pp !!!
  DECREASING         VOLATILE           DECREASING           38   68.4%   +14.4pp !!!
  INCREASING         FLAT               DECREASING           22   68.2%   +14.2pp
  FLAT               INCREASING         DECREASING           25   68.0%   +14.0pp
  INCREASING         DEC_THEN_INC       DECREASING           42   66.7%   +12.6pp !!!
  DEC_THEN_INC       DECREASING         DECREASING           41   65.9%   +11.8pp !!!
  INC_THEN_DEC       DEC_THEN_INC       INCREASING           31   64.5%   +10.5pp !!!
  DEC_THEN_INC       DECREASING         INCREASING           81   63.0%    +8.9pp ***

  --- RAMP-UP TREND SIGNALS (30 M1 bars before entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         257    143   55.6%    +1.6pp
  VOLATILE                     314    169   53.8%    -0.2pp
  INC_THEN_DEC                 435    231   53.1%    -0.9pp
  INCREASING                   477    250   52.4%    -1.6pp
  DEC_THEN_INC                 502    248   49.4%    -4.6pp
  DECREASING                   930    450   48.4%    -5.6pp ***

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 348    203   58.3%    +4.3pp
  INCREASING                   899    506   56.3%    +2.3pp
  INC_THEN_DEC                 416    206   49.5%    -4.5pp
  DECREASING                   830    396   47.7%    -6.3pp ***
  FLAT                         205     92   44.9%    -9.1pp ***
  VOLATILE                     217     88   40.6%   -13.5pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 418    239   57.2%    +3.2pp
  FLAT                         211    120   56.9%    +2.9pp
  INCREASING                   523    283   54.1%    +0.1pp
  VOLATILE                     282    140   49.6%    -4.4pp
  DEC_THEN_INC                 474    233   49.2%    -4.9pp
  DECREASING                   999    473   47.3%    -6.7pp ***

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          46     26   56.5%    +2.5pp
  DEC_THEN_INC                 209    115   55.0%    +1.0pp
  VOLATILE                      24     13   54.2%    +0.1pp
  DECREASING                  1190    631   53.0%    -1.0pp
  INC_THEN_DEC                 196    103   52.6%    -1.5pp
  INCREASING                  1243    600   48.3%    -5.7pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          33     23   69.7%   +15.7pp !!!
  DECREASING                  1205    658   54.6%    +0.6pp
  DEC_THEN_INC                 137     71   51.8%    -2.2pp
  INCREASING                  1351    658   48.7%    -5.3pp ***
  INC_THEN_DEC                 169     68   40.2%   -13.8pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                  1218    663   54.4%    +0.4pp
  INC_THEN_DEC                 216    116   53.7%    -0.3pp
  DEC_THEN_INC                 233    125   53.6%    -0.4pp
  FLAT                          67     32   47.8%    -6.3pp ***
  INCREASING                  1146    540   47.1%    -6.9pp ***

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 215    134   62.3%    +8.3pp ***
  INCREASING                    44     24   54.5%    +0.5pp
  FLAT                        2304   1182   51.3%    -2.7pp
  INC_THEN_DEC                 209     95   45.5%    -8.6pp ***
  VOLATILE                     119     50   42.0%   -12.0pp !!!
  DECREASING                    24      6   25.0%   -29.0pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 311    173   55.6%    +1.6pp
  DECREASING                    67     37   55.2%    +1.2pp
  INC_THEN_DEC                 407    222   54.5%    +0.5pp
  INCREASING                    37     19   51.4%    -2.7pp
  FLAT                        1912    957   50.1%    -4.0pp
  VOLATILE                     181     83   45.9%    -8.2pp ***

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    34     19   55.9%    +1.9pp
  INC_THEN_DEC                 406    218   53.7%    -0.3pp
  FLAT                        1849    963   52.1%    -1.9pp
  DEC_THEN_INC                 382    184   48.2%    -5.9pp ***
  VOLATILE                     188     85   45.2%    -8.8pp ***
  DECREASING                    56     22   39.3%   -14.7pp !!!

  --- ENTRY LEVEL SIGNALS (snapshot at entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  COMPRESSED                   641    351   54.8%    +0.7pp
  EXPLOSIVE                    861    447   51.9%    -2.1pp
  NORMAL                       807    402   49.8%    -4.2pp
  EXPANDING                    606    291   48.0%    -6.0pp ***

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_BUY                   801    416   51.9%    -2.1pp
  STRONG_SELL                  862    443   51.4%    -2.6pp
  MILD_SELL                    578    297   51.4%    -2.6pp
  MILD_BUY                     674    335   49.7%    -4.3pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     490    271   55.3%    +1.3pp
  ELEVATED                     234    127   54.3%    +0.3pp
  EXTREME                      447    233   52.1%    -1.9pp
  LOW                         1737    857   49.3%    -4.7pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_FALLING                 840    469   55.8%    +1.8pp
  STRONG_FALLING               509    271   53.2%    -0.8pp
  STRONG_RISING                576    293   50.9%    -3.2pp
  MILD_RISING                  990    458   46.3%    -7.8pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDE_BEAR                    980    537   54.8%    +0.8pp
  NARROW_BEAR                  561    307   54.7%    +0.7pp
  WIDE_BULL                    886    423   47.7%    -6.3pp ***
  NARROW_BULL                  481    221   45.9%    -8.1pp ***

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                        1439    742   51.6%    -2.5pp
  WIDENING                    1012    516   51.0%    -3.0pp
  STRONG_WIDENING              456    230   50.4%    -3.6pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG                       952    515   54.1%    +0.1pp
  WEAK                         922    492   53.4%    -0.7pp
  MODERATE                     909    444   48.8%    -5.2pp ***
  CRITICAL                     132     40   30.3%   -23.7pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     169    103   60.9%    +6.9pp ***
  MINIMAL                     1292    672   52.0%    -2.0pp
  LOW                         1454    716   49.2%    -4.8pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MINIMAL                      934    508   54.4%    +0.4pp
  MODERATE                     172     89   51.7%    -2.3pp
  LOW                         1809    894   49.4%    -4.6pp

  --- FLIP SIGNALS (sign changes in ramp-up) ---

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS              2885   1473   51.1%    -3.0pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NO_FLIP                      291    177   60.8%    +6.8pp ***
  FLIP_TO_POSITIVE             380    213   56.1%    +2.0pp
  MULTIPLE_FLIPS              1875    928   49.5%    -4.5pp
  FLIP_TO_NEGATIVE             369    173   46.9%    -7.1pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NO_FLIP                      393    233   59.3%    +5.3pp ***
  MULTIPLE_FLIPS              1362    703   51.6%    -2.4pp
  FLIP_TO_POSITIVE             557    276   49.6%    -4.5pp
  FLIP_TO_NEGATIVE             595    276   46.4%    -7.6pp ***

================================================================================
SECTION 2B: PRE-ENTRY - REJECTION TRADES (M5 opposing direction)
  Trades: 2847, Wins: 1640, WR: 57.6% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  INCREASING         VOLATILE           DECREASING           27   92.6%   +38.6pp
  VOLATILE           FLAT               DECREASING           20   90.0%   +36.0pp
  INC_THEN_DEC       DECREASING         DECREASING           63   84.1%   +30.1pp !!!
  INC_THEN_DEC       INC_THEN_DEC       DECREASING           29   82.8%   +28.7pp
  FLAT               DECREASING         INCREASING           45   77.8%   +23.8pp !!!
  INCREASING         DEC_THEN_INC       INCREASING           20   75.0%   +21.0pp
  VOLATILE           INC_THEN_DEC       DECREASING           28   75.0%   +21.0pp
  DECREASING         VOLATILE           DECREASING           47   74.5%   +20.4pp !!!
  VOLATILE           DECREASING         DECREASING           31   74.2%   +20.2pp !!!
  VOLATILE           INC_THEN_DEC       INCREASING           23   73.9%   +19.9pp
  INC_THEN_DEC       INCREASING         INCREASING           78   73.1%   +19.1pp !!!
  INCREASING         INC_THEN_DEC       INCREASING           25   72.0%   +18.0pp
  DEC_THEN_INC       DEC_THEN_INC       DECREASING           21   71.4%   +17.4pp
  DEC_THEN_INC       INCREASING         DECREASING           76   71.1%   +17.0pp !!!
  INC_THEN_DEC       INCREASING         DECREASING           81   70.4%   +16.4pp !!!

  --- RAMP-UP TREND SIGNALS (30 M1 bars before entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         194    133   68.6%   +14.5pp !!!
  INC_THEN_DEC                 519    332   64.0%   +10.0pp ***
  VOLATILE                     301    189   62.8%    +8.8pp ***
  DEC_THEN_INC                 448    265   59.2%    +5.1pp ***
  INCREASING                   488    267   54.7%    +0.7pp
  DECREASING                   897    454   50.6%    -3.4pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 361    243   67.3%   +13.3pp !!!
  VOLATILE                     212    136   64.2%   +10.1pp !!!
  DEC_THEN_INC                 356    208   58.4%    +4.4pp
  INCREASING                   855    486   56.8%    +2.8pp
  DECREASING                   862    464   53.8%    -0.2pp
  FLAT                         201    103   51.2%    -2.8pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     270    169   62.6%    +8.6pp ***
  INCREASING                   499    305   61.1%    +7.1pp ***
  INC_THEN_DEC                 414    249   60.1%    +6.1pp ***
  DEC_THEN_INC                 433    260   60.0%    +6.0pp ***
  DECREASING                   984    536   54.5%    +0.5pp
  FLAT                         242    120   49.6%    -4.4pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 187    125   66.8%   +12.8pp !!!
  INCREASING                  1146    693   60.5%    +6.5pp ***
  DECREASING                  1258    695   55.2%    +1.2pp
  DEC_THEN_INC                 184     94   51.1%    -2.9pp
  FLAT                          29     14   48.3%    -5.7pp
  VOLATILE                      40     18   45.0%    -9.0pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          28     20   71.4%   +17.4pp
  INC_THEN_DEC                 161    111   68.9%   +14.9pp !!!
  INCREASING                  1184    688   58.1%    +4.1pp
  DECREASING                  1304    733   56.2%    +2.2pp
  DEC_THEN_INC                 150     80   53.3%    -0.7pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 224    139   62.1%    +8.0pp ***
  INCREASING                  1256    728   58.0%    +3.9pp
  DECREASING                  1087    622   57.2%    +3.2pp
  INC_THEN_DEC                 218    120   55.0%    +1.0pp
  FLAT                          44     20   45.5%    -8.6pp ***

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     172    112   65.1%   +11.1pp !!!
  INC_THEN_DEC                 216    137   63.4%    +9.4pp ***
  INCREASING                    38     22   57.9%    +3.9pp
  FLAT                        2200   1250   56.8%    +2.8pp
  DEC_THEN_INC                 202    110   54.5%    +0.4pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                        1847   1101   59.6%    +5.6pp ***
  VOLATILE                     219    128   58.4%    +4.4pp
  INC_THEN_DEC                 418    232   55.5%    +1.5pp
  DEC_THEN_INC                 278    142   51.1%    -2.9pp
  DECREASING                    58     26   44.8%    -9.2pp ***
  INCREASING                    27     11   40.7%   -13.3pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    30     20   66.7%   +12.6pp !!!
  DECREASING                    49     29   59.2%    +5.2pp ***
  FLAT                        1835   1081   58.9%    +4.9pp
  INC_THEN_DEC                 446    258   57.8%    +3.8pp
  VOLATILE                     191    102   53.4%    -0.6pp
  DEC_THEN_INC                 296    150   50.7%    -3.3pp

  --- ENTRY LEVEL SIGNALS (snapshot at entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPLOSIVE                    895    555   62.0%    +8.0pp ***
  COMPRESSED                   639    379   59.3%    +5.3pp ***
  EXPANDING                    612    343   56.0%    +2.0pp
  NORMAL                       701    363   51.8%    -2.2pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_SELL                    547    339   62.0%    +8.0pp ***
  STRONG_BUY                   791    453   57.3%    +3.3pp
  STRONG_SELL                  922    519   56.3%    +2.3pp
  MILD_BUY                     587    329   56.0%    +2.0pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXTREME                      458    286   62.4%    +8.4pp ***
  LOW                         1572    907   57.7%    +3.7pp
  ELEVATED                     259    148   57.1%    +3.1pp
  MODERATE                     555    298   53.7%    -0.3pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_RISING                  911    565   62.0%    +8.0pp ***
  MILD_FALLING                 903    524   58.0%    +4.0pp
  STRONG_FALLING               516    279   54.1%    +0.1pp
  STRONG_RISING                517    272   52.6%    -1.4pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NARROW_BULL                  441    273   61.9%    +7.9pp ***
  WIDE_BEAR                   1052    618   58.7%    +4.7pp
  WIDE_BULL                    886    516   58.2%    +4.2pp
  NARROW_BEAR                  465    232   49.9%    -4.1pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_WIDENING              455    277   60.9%    +6.9pp ***
  FLAT                        1278    742   58.1%    +4.0pp
  WIDENING                    1105    616   55.7%    +1.7pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  CRITICAL                     165     97   58.8%    +4.8pp
  STRONG                      1052    617   58.7%    +4.6pp
  WEAK                         760    444   58.4%    +4.4pp
  MODERATE                     870    482   55.4%    +1.4pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     181    117   64.6%   +10.6pp !!!
  MINIMAL                     1146    658   57.4%    +3.4pp
  LOW                         1520    865   56.9%    +2.9pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     161    100   62.1%    +8.1pp ***
  LOW                         1833   1053   57.4%    +3.4pp
  MINIMAL                      853    487   57.1%    +3.1pp

  --- FLIP SIGNALS (sign changes in ramp-up) ---

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS              2806   1619   57.7%    +3.7pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS              1816   1085   59.7%    +5.7pp ***
  FLIP_TO_POSITIVE             398    229   57.5%    +3.5pp
  FLIP_TO_NEGATIVE             355    185   52.1%    -1.9pp
  NO_FLIP                      278    141   50.7%    -3.3pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLIP_TO_POSITIVE             485    307   63.3%    +9.3pp ***
  NO_FLIP                      306    183   59.8%    +5.8pp ***
  FLIP_TO_NEGATIVE             619    351   56.7%    +2.7pp
  MULTIPLE_FLIPS              1432    798   55.7%    +1.7pp

================================================================================
SECTION 2C: PRE-ENTRY - NEUTRAL TRADES (M5 structure = NEUTRAL)
  Trades: 160, Wins: 68, WR: 42.5% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES ---
  No composite profiles with N >= 20

  --- RAMP-UP TREND SIGNALS (30 M1 bars before entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                      26     15   57.7%    +3.7pp
  DEC_THEN_INC                  23     10   43.5%   -10.5pp
  DECREASING                    41     17   41.5%   -12.6pp !!!
  INCREASING                    40     13   32.5%   -21.5pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                  20     16   80.0%   +26.0pp
  INCREASING                    58     27   46.6%    -7.5pp ***
  DEC_THEN_INC                  23      8   34.8%   -19.2pp
  DECREASING                    47     13   27.7%   -26.4pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                  30     16   53.3%    -0.7pp
  DECREASING                    57     26   45.6%    -8.4pp ***
  INCREASING                    23     10   43.5%   -10.5pp
  DEC_THEN_INC                  25      5   20.0%   -34.0pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    74     34   45.9%    -8.1pp ***
  DECREASING                    63     22   34.9%   -19.1pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                    60     28   46.7%    -7.4pp ***
  INCREASING                    63     24   38.1%   -15.9pp !!!
  DEC_THEN_INC                  25      8   32.0%   -22.0pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                    51     27   52.9%    -1.1pp
  INC_THEN_DEC                  21     11   52.4%    -1.6pp
  INCREASING                    69     29   42.0%   -12.0pp !!!

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         115     50   43.5%   -10.5pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                  28     12   42.9%   -11.2pp
  FLAT                          96     41   42.7%   -11.3pp !!!
  INC_THEN_DEC                  24      8   33.3%   -20.7pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          86     38   44.2%    -9.8pp ***
  DEC_THEN_INC                  28     11   39.3%   -14.7pp
  INC_THEN_DEC                  29     10   34.5%   -19.5pp

  --- ENTRY LEVEL SIGNALS (snapshot at entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPLOSIVE                     62     38   61.3%    +7.3pp ***
  EXPANDING                     29     16   55.2%    +1.2pp
  COMPRESSED                    22      7   31.8%   -22.2pp
  NORMAL                        47      7   14.9%   -39.1pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_BUY                    49     31   63.3%    +9.2pp ***
  STRONG_SELL                   43     19   44.2%    -9.8pp ***
  MILD_BUY                      25      9   36.0%   -18.0pp
  MILD_SELL                     43      9   20.9%   -33.1pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  LOW                           72     40   55.6%    +1.5pp
  EXTREME                       34     15   44.1%    -9.9pp ***
  MODERATE                      29     10   34.5%   -19.5pp
  ELEVATED                      25      3   12.0%   -42.0pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_FALLING                  48     22   45.8%    -8.2pp ***
  STRONG_FALLING                36     15   41.7%   -12.4pp !!!
  MILD_RISING                   60     22   36.7%   -17.4pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDE_BULL                     44     21   47.7%    -6.3pp ***
  NARROW_BEAR                   34     15   44.1%    -9.9pp ***
  WIDE_BEAR                     45     18   40.0%   -14.0pp !!!
  NARROW_BULL                   37     14   37.8%   -16.2pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          67     34   50.7%    -3.3pp
  WIDENING                      68     26   38.2%   -15.8pp !!!
  STRONG_WIDENING               25      8   32.0%   -22.0pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                      29     15   51.7%    -2.3pp
  WEAK                          62     30   48.4%    -5.6pp ***
  STRONG                        68     22   32.4%   -21.7pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  LOW                           78     49   62.8%    +8.8pp ***
  MINIMAL                       66     14   21.2%   -32.8pp !!!

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  LOW                           92     53   57.6%    +3.6pp
  MINIMAL                       51     10   19.6%   -34.4pp !!!

  --- FLIP SIGNALS (sign changes in ramp-up) ---

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS               155     63   40.6%   -13.4pp !!!

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS               110     53   48.2%    -5.8pp ***
  FLIP_TO_NEGATIVE              29      3   10.3%   -43.7pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS                81     42   51.9%    -2.2pp
  FLIP_TO_NEGATIVE              29     15   51.7%    -2.3pp
  FLIP_TO_POSITIVE              25      9   36.0%   -18.0pp
  NO_FLIP                       25      2    8.0%   -46.0pp

================================================================================
SECTION 3: PRE-ENTRY - MODEL EPCH1
  Trades: 272, Wins: 139, WR: 51.1% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES ---
  No composite profiles with N >= 20

  --- RAMP-UP TREND SIGNALS (30 M1 bars before entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          23     14   60.9%    +6.9pp
  VOLATILE                      33     18   54.5%    +0.5pp
  DECREASING                    83     45   54.2%    +0.2pp
  INC_THEN_DEC                  42     21   50.0%    -4.0pp
  DEC_THEN_INC                  42     19   45.2%    -8.8pp ***
  INCREASING                    49     22   44.9%    -9.1pp ***

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                  30     16   53.3%    -0.7pp
  DECREASING                    94     47   50.0%    -4.0pp
  DEC_THEN_INC                  28     14   50.0%    -4.0pp
  INCREASING                    85     41   48.2%    -5.8pp ***

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                  47     30   63.8%    +9.8pp ***
  INCREASING                    45     24   53.3%    -0.7pp
  VOLATILE                      32     17   53.1%    -0.9pp
  DEC_THEN_INC                  35     18   51.4%    -2.6pp
  FLAT                          21     10   47.6%    -6.4pp
  DECREASING                    91     40   44.0%   -10.1pp !!!

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                  23     13   56.5%    +2.5pp
  INCREASING                   112     56   50.0%    -4.0pp
  DECREASING                   113     54   47.8%    -6.2pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                   125     61   48.8%    -5.2pp ***
  DECREASING                   110     52   47.3%    -6.7pp ***

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                   112     61   54.5%    +0.4pp
  DECREASING                   103     52   50.5%    -3.5pp
  INC_THEN_DEC                  29     13   44.8%    -9.2pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                  22     15   68.2%   +14.2pp
  FLAT                         204    105   51.5%    -2.5pp
  DEC_THEN_INC                  24      8   33.3%   -20.7pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                  36     22   61.1%    +7.1pp ***
  DEC_THEN_INC                  30     17   56.7%    +2.6pp
  VOLATILE                      26     13   50.0%    -4.0pp
  FLAT                         170     82   48.2%    -5.8pp ***

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                  43     31   72.1%   +18.1pp !!!
  FLAT                         164     81   49.4%    -4.6pp
  DEC_THEN_INC                  35     14   40.0%   -14.0pp !!!

  --- ENTRY LEVEL SIGNALS (snapshot at entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NORMAL                        51     28   54.9%    +0.9pp
  COMPRESSED                    31     17   54.8%    +0.8pp
  EXPLOSIVE                    129     65   50.4%    -3.6pp
  EXPANDING                     61     29   47.5%    -6.5pp ***

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_BUY                      34     20   58.8%    +4.8pp
  STRONG_SELL                  107     56   52.3%    -1.7pp
  STRONG_BUY                    97     49   50.5%    -3.5pp
  MILD_SELL                     34     14   41.2%   -12.8pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  ELEVATED                      33     19   57.6%    +3.6pp
  EXTREME                       71     38   53.5%    -0.5pp
  LOW                          115     57   49.6%    -4.5pp
  MODERATE                      52     25   48.1%    -5.9pp ***

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_FALLING                47     26   55.3%    +1.3pp
  MILD_FALLING                  88     45   51.1%    -2.9pp
  STRONG_RISING                 71     36   50.7%    -3.3pp
  MILD_RISING                   66     32   48.5%    -5.5pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NARROW_BEAR                   47     28   59.6%    +5.6pp ***
  WIDE_BULL                     94     51   54.3%    +0.2pp
  NARROW_BULL                   34     18   52.9%    -1.1pp
  WIDE_BEAR                     96     42   43.8%   -10.3pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_WIDENING               55     30   54.5%    +0.5pp
  WIDENING                      89     46   51.7%    -2.3pp
  FLAT                         126     62   49.2%    -4.8pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WEAK                          61     33   54.1%    +0.1pp
  STRONG                       127     67   52.8%    -1.3pp
  MODERATE                      67     31   46.3%    -7.8pp ***

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                      32     17   53.1%    -0.9pp
  MINIMAL                       54     28   51.9%    -2.2pp
  LOW                          186     94   50.5%    -3.5pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                      31     17   54.8%    +0.8pp
  MINIMAL                       42     23   54.8%    +0.7pp
  LOW                          199     99   49.7%    -4.3pp

  --- FLIP SIGNALS (sign changes in ramp-up) ---

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS               265    137   51.7%    -2.3pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLIP_TO_POSITIVE              34     19   55.9%    +1.9pp
  MULTIPLE_FLIPS               165     88   53.3%    -0.7pp
  FLIP_TO_NEGATIVE              38     17   44.7%    -9.3pp ***
  NO_FLIP                       35     15   42.9%   -11.2pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLIP_TO_POSITIVE              52     30   57.7%    +3.7pp
  MULTIPLE_FLIPS               120     67   55.8%    +1.8pp
  NO_FLIP                       35     18   51.4%    -2.6pp
  FLIP_TO_NEGATIVE              64     24   37.5%   -16.5pp !!!

================================================================================
SECTION 3: PRE-ENTRY - MODEL EPCH2
  Trades: 2875, Wins: 1580, WR: 55.0% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  INCREASING         DEC_THEN_INC       INCREASING           21   95.2%   +41.2pp
  INC_THEN_DEC       INC_THEN_DEC       INCREASING           38   89.5%   +35.5pp !!!
  INCREASING         VOLATILE           DECREASING           26   84.6%   +30.6pp
  INC_THEN_DEC       INC_THEN_DEC       DECREASING           30   80.0%   +26.0pp !!!
  INC_THEN_DEC       INCREASING         DECREASING           62   79.0%   +25.0pp !!!
  FLAT               DECREASING         INCREASING           47   78.7%   +24.7pp !!!
  DEC_THEN_INC       DEC_THEN_INC       DECREASING           35   77.1%   +23.1pp !!!
  INC_THEN_DEC       INCREASING         INCREASING           60   73.3%   +19.3pp !!!
  DEC_THEN_INC       INCREASING         DECREASING           63   68.3%   +14.2pp !!!
  FLAT               INCREASING         DECREASING           33   66.7%   +12.6pp !!!
  INCREASING         INCREASING         DECREASING           44   65.9%   +11.9pp !!!
  DECREASING         VOLATILE           DECREASING           35   65.7%   +11.7pp !!!
  VOLATILE           INC_THEN_DEC       DECREASING           29   65.5%   +11.5pp
  DECREASING         INC_THEN_DEC       INCREASING           49   65.3%   +11.3pp !!!
  INCREASING         INCREASING         INCREASING           43   65.1%   +11.1pp !!!

  --- RAMP-UP TREND SIGNALS (30 M1 bars before entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         230    150   65.2%   +11.2pp !!!
  INC_THEN_DEC                 472    295   62.5%    +8.5pp ***
  DEC_THEN_INC                 482    278   57.7%    +3.7pp
  INCREASING                   472    262   55.5%    +1.5pp
  VOLATILE                     327    164   50.2%    -3.9pp
  DECREASING                   892    431   48.3%    -5.7pp ***

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 376    231   61.4%    +7.4pp ***
  INC_THEN_DEC                 419    251   59.9%    +5.9pp ***
  INCREASING                   862    484   56.1%    +2.1pp
  DECREASING                   855    438   51.2%    -2.8pp
  VOLATILE                     201     99   49.3%    -4.8pp
  FLAT                         162     77   47.5%    -6.5pp ***

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                   495    297   60.0%    +6.0pp ***
  DEC_THEN_INC                 440    256   58.2%    +4.2pp
  FLAT                         232    133   57.3%    +3.3pp
  VOLATILE                     275    157   57.1%    +3.1pp
  INC_THEN_DEC                 423    239   56.5%    +2.5pp
  DECREASING                  1002    496   49.5%    -4.5pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 191    117   61.3%    +7.2pp ***
  INC_THEN_DEC                 164     98   59.8%    +5.7pp ***
  INCREASING                  1209    661   54.7%    +0.7pp
  DECREASING                  1226    667   54.4%    +0.4pp
  VOLATILE                      38     18   47.4%    -6.7pp ***
  FLAT                          41     17   41.5%   -12.6pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          30     20   66.7%   +12.6pp !!!
  DECREASING                  1280    734   57.3%    +3.3pp
  DEC_THEN_INC                 137     77   56.2%    +2.2pp
  INCREASING                  1237    650   52.5%    -1.5pp
  INC_THEN_DEC                 167     83   49.7%    -4.3pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          56     38   67.9%   +13.8pp !!!
  DEC_THEN_INC                 258    152   58.9%    +4.9pp
  INC_THEN_DEC                 207    115   55.6%    +1.5pp
  DECREASING                  1163    643   55.3%    +1.3pp
  INCREASING                  1159    618   53.3%    -0.7pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    37     22   59.5%    +5.4pp ***
  DEC_THEN_INC                 214    126   58.9%    +4.9pp
  VOLATILE                     140     80   57.1%    +3.1pp
  FLAT                        2235   1227   54.9%    +0.9pp
  INC_THEN_DEC                 221    119   53.8%    -0.2pp
  DECREASING                    28      6   21.4%   -32.6pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    30     18   60.0%    +6.0pp ***
  FLAT                        1854   1050   56.6%    +2.6pp
  INC_THEN_DEC                 430    241   56.0%    +2.0pp
  DEC_THEN_INC                 282    141   50.0%    -4.0pp
  VOLATILE                     208     99   47.6%    -6.4pp ***
  DECREASING                    71     31   43.7%   -10.4pp !!!

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    36     24   66.7%   +12.6pp !!!
  INC_THEN_DEC                 447    263   58.8%    +4.8pp
  FLAT                        1813   1013   55.9%    +1.9pp
  DEC_THEN_INC                 343    171   49.9%    -4.2pp
  DECREASING                    63     31   49.2%    -4.8pp
  VOLATILE                     173     78   45.1%    -8.9pp ***

  --- ENTRY LEVEL SIGNALS (snapshot at entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  COMPRESSED                   632    425   67.2%   +13.2pp !!!
  EXPLOSIVE                    847    453   53.5%    -0.5pp
  EXPANDING                    640    322   50.3%    -3.7pp
  NORMAL                       756    380   50.3%    -3.8pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_SELL                    561    330   58.8%    +4.8pp
  MILD_BUY                     629    351   55.8%    +1.8pp
  STRONG_BUY                   818    438   53.5%    -0.5pp
  STRONG_SELL                  867    461   53.2%    -0.8pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  ELEVATED                     225    129   57.3%    +3.3pp
  EXTREME                      350    198   56.6%    +2.6pp
  MODERATE                     575    314   54.6%    +0.6pp
  LOW                         1719    937   54.5%    +0.5pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_FALLING                 839    505   60.2%    +6.2pp ***
  MILD_RISING                  975    547   56.1%    +2.1pp
  STRONG_FALLING               513    257   50.1%    -3.9pp
  STRONG_RISING                548    271   49.5%    -4.6pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NARROW_BEAR                  519    308   59.3%    +5.3pp ***
  WIDE_BEAR                    986    554   56.2%    +2.2pp
  NARROW_BULL                  481    262   54.5%    +0.5pp
  WIDE_BULL                    883    454   51.4%    -2.6pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                        1413    806   57.0%    +3.0pp
  WIDENING                    1020    549   53.8%    -0.2pp
  STRONG_WIDENING              432    221   51.2%    -2.9pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WEAK                         911    534   58.6%    +4.6pp
  CRITICAL                     148     85   57.4%    +3.4pp
  STRONG                       953    513   53.8%    -0.2pp
  MODERATE                     863    448   51.9%    -2.1pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MINIMAL                     1240    732   59.0%    +5.0pp ***
  MODERATE                     144     82   56.9%    +2.9pp
  LOW                         1491    766   51.4%    -2.6pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MINIMAL                      900    553   61.4%    +7.4pp ***
  MODERATE                     144     76   52.8%    -1.2pp
  LOW                         1831    951   51.9%    -2.1pp

  --- FLIP SIGNALS (sign changes in ramp-up) ---

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLIP_TO_NEGATIVE              24     15   62.5%    +8.5pp
  MULTIPLE_FLIPS              2829   1554   54.9%    +0.9pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS              1804   1019   56.5%    +2.5pp
  FLIP_TO_POSITIVE             409    230   56.2%    +2.2pp
  NO_FLIP                      284    148   52.1%    -1.9pp
  FLIP_TO_NEGATIVE             378    183   48.4%    -5.6pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NO_FLIP                      347    207   59.7%    +5.6pp ***
  MULTIPLE_FLIPS              1367    748   54.7%    +0.7pp
  FLIP_TO_NEGATIVE             610    333   54.6%    +0.6pp
  FLIP_TO_POSITIVE             543    290   53.4%    -0.6pp

================================================================================
SECTION 3: PRE-ENTRY - MODEL EPCH3
  Trades: 232, Wins: 123, WR: 53.0% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES ---
  No composite profiles with N >= 20

  --- RAMP-UP TREND SIGNALS (30 M1 bars before entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                      25     20   80.0%   +26.0pp
  INCREASING                    35     21   60.0%    +6.0pp ***
  FLAT                          20     11   55.0%    +1.0pp
  INC_THEN_DEC                  37     19   51.4%    -2.7pp
  DECREASING                    73     35   47.9%    -6.1pp ***
  DEC_THEN_INC                  42     17   40.5%   -13.5pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                    69     38   55.1%    +1.1pp
  FLAT                          20     11   55.0%    +1.0pp
  DEC_THEN_INC                  24     13   54.2%    +0.1pp
  INCREASING                    75     40   53.3%    -0.7pp
  INC_THEN_DEC                  26     12   46.2%    -7.9pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                      25     18   72.0%   +18.0pp
  INC_THEN_DEC                  27     18   66.7%   +12.6pp
  INCREASING                    48     29   60.4%    +6.4pp ***
  FLAT                          22     10   45.5%    -8.6pp
  DECREASING                    80     36   45.0%    -9.0pp ***
  DEC_THEN_INC                  30     12   40.0%   -14.0pp !!!

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                    92     53   57.6%    +3.6pp
  INCREASING                   102     47   46.1%    -7.9pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                    94     54   57.4%    +3.4pp
  INCREASING                   106     54   50.9%    -3.1pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                  26     18   69.2%   +15.2pp
  DECREASING                    86     47   54.7%    +0.6pp
  INCREASING                    97     50   51.5%    -2.5pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                  22     12   54.5%    +0.5pp
  FLAT                         170     87   51.2%    -2.8pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                      21     15   71.4%   +17.4pp
  INC_THEN_DEC                  37     21   56.8%    +2.7pp
  FLAT                         146     74   50.7%    -3.3pp
  DEC_THEN_INC                  23     11   47.8%    -6.2pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                      20     15   75.0%   +21.0pp
  INC_THEN_DEC                  34     22   64.7%   +10.7pp !!!
  FLAT                         147     74   50.3%    -3.7pp
  DEC_THEN_INC                  28     10   35.7%   -18.3pp

  --- ENTRY LEVEL SIGNALS (snapshot at entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPLOSIVE                    102     62   60.8%    +6.8pp ***
  NORMAL                        50     25   50.0%    -4.0pp
  EXPANDING                     45     22   48.9%    -5.1pp ***
  COMPRESSED                    35     14   40.0%   -14.0pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_BUY                    75     45   60.0%    +6.0pp ***
  STRONG_SELL                   84     47   56.0%    +1.9pp
  MILD_SELL                     34     17   50.0%    -4.0pp
  MILD_BUY                      39     14   35.9%   -18.1pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                      39     24   61.5%    +7.5pp ***
  EXTREME                       80     43   53.8%    -0.3pp
  LOW                           88     47   53.4%    -0.6pp
  ELEVATED                      25      9   36.0%   -18.0pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_FALLING                  66     38   57.6%    +3.6pp
  STRONG_FALLING                49     28   57.1%    +3.1pp
  MILD_RISING                   74     37   50.0%    -4.0pp
  STRONG_RISING                 43     20   46.5%    -7.5pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDE_BEAR                     76     45   59.2%    +5.2pp ***
  WIDE_BULL                     84     47   56.0%    +1.9pp
  NARROW_BEAR                   39     18   46.2%    -7.9pp ***
  NARROW_BULL                   33     13   39.4%   -14.6pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDENING                     105     58   55.2%    +1.2pp
  STRONG_WIDENING               38     20   52.6%    -1.4pp
  FLAT                          89     45   50.6%    -3.5pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                      75     43   57.3%    +3.3pp
  STRONG                       105     55   52.4%    -1.6pp
  WEAK                          42     20   47.6%    -6.4pp ***

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                      25     15   60.0%    +6.0pp
  LOW                          141     76   53.9%    -0.1pp
  MINIMAL                       66     32   48.5%    -5.5pp ***

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  LOW                          153     85   55.6%    +1.5pp
  MODERATE                      30     16   53.3%    -0.7pp
  MINIMAL                       49     22   44.9%    -9.1pp ***

  --- FLIP SIGNALS (sign changes in ramp-up) ---

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS               230    122   53.0%    -1.0pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLIP_TO_POSITIVE              30     18   60.0%    +6.0pp ***
  MULTIPLE_FLIPS               158     84   53.2%    -0.9pp
  FLIP_TO_NEGATIVE              26     11   42.3%   -11.7pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS               111     67   60.4%    +6.3pp ***
  FLIP_TO_POSITIVE              47     27   57.4%    +3.4pp
  NO_FLIP                       33     16   48.5%    -5.5pp ***
  FLIP_TO_NEGATIVE              41     13   31.7%   -22.3pp !!!

================================================================================
SECTION 3: PRE-ENTRY - MODEL EPCH4
  Trades: 2543, Wins: 1357, WR: 53.4% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  VOLATILE           INCREASING         INCREASING           37   94.6%   +40.6pp !!!
  VOLATILE           FLAT               DECREASING           20   90.0%   +36.0pp
  DECREASING         VOLATILE           DECREASING           42   78.6%   +24.6pp !!!
  INC_THEN_DEC       DECREASING         DECREASING           48   72.9%   +18.9pp !!!
  INCREASING         VOLATILE           DECREASING           24   70.8%   +16.8pp
  INC_THEN_DEC       INCREASING         DECREASING           50   70.0%   +16.0pp !!!
  DEC_THEN_INC       DEC_THEN_INC       DECREASING           29   69.0%   +14.9pp
  INCREASING         DEC_THEN_INC       DECREASING           25   68.0%   +14.0pp
  INCREASING         INCREASING         INCREASING           65   66.2%   +12.1pp !!!
  VOLATILE           DECREASING         DECREASING           29   65.5%   +11.5pp
  INCREASING         FLAT               DECREASING           20   65.0%   +11.0pp
  DEC_THEN_INC       INCREASING         DECREASING           62   64.5%   +10.5pp !!!
  DECREASING         INCREASING         INCREASING          112   63.4%    +9.4pp ***
  INC_THEN_DEC       INCREASING         INCREASING           95   62.1%    +8.1pp ***
  DECREASING         INC_THEN_DEC       INCREASING           28   60.7%    +6.7pp

  --- RAMP-UP TREND SIGNALS (30 M1 bars before entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     256    171   66.8%   +12.8pp !!!
  INC_THEN_DEC                 420    236   56.2%    +2.2pp
  FLAT                         191    106   55.5%    +1.5pp
  DEC_THEN_INC                 407    209   51.4%    -2.7pp
  INCREASING                   449    225   50.1%    -3.9pp
  DECREASING                   820    410   50.0%    -4.0pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 322    186   57.8%    +3.7pp
  INCREASING                   790    454   57.5%    +3.4pp
  VOLATILE                     198    107   54.0%    +0.0pp
  DEC_THEN_INC                 299    161   53.8%    -0.2pp
  DECREASING                   721    350   48.5%    -5.5pp ***
  FLAT                         213     99   46.5%    -7.5pp ***

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 365    217   59.5%    +5.4pp ***
  INCREASING                   457    248   54.3%    +0.2pp
  DECREASING                   867    463   53.4%    -0.6pp
  VOLATILE                     234    123   52.6%    -1.5pp
  DEC_THEN_INC                 427    212   49.6%    -4.4pp
  FLAT                         189     92   48.7%    -5.3pp ***

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 186    111   59.7%    +5.7pp ***
  FLAT                          27     16   59.3%    +5.2pp
  INCREASING                  1040    563   54.1%    +0.1pp
  DECREASING                  1080    574   53.1%    -0.9pp
  DEC_THEN_INC                 188     83   44.1%    -9.9pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          28     22   78.6%   +24.6pp
  INC_THEN_DEC                 136     78   57.4%    +3.3pp
  INCREASING                  1130    605   53.5%    -0.5pp
  DECREASING                  1085    579   53.4%    -0.7pp
  DEC_THEN_INC                 149     68   45.6%    -8.4pp ***

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                  1004    570   56.8%    +2.8pp
  DEC_THEN_INC                 186    100   53.8%    -0.3pp
  INC_THEN_DEC                 193    101   52.3%    -1.7pp
  INCREASING                  1103    568   51.5%    -2.5pp
  FLAT                          45     11   24.4%   -29.6pp !!!

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 180    103   57.2%    +3.2pp
  INCREASING                    38     21   55.3%    +1.2pp
  VOLATILE                     126     68   54.0%    -0.1pp
  INC_THEN_DEC                 176     94   53.4%    -0.6pp
  FLAT                        2010   1063   52.9%    -1.1pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                    46     27   58.7%    +4.7pp
  VOLATILE                     154     88   57.1%    +3.1pp
  DEC_THEN_INC                 282    158   56.0%    +2.0pp
  FLAT                        1685    893   53.0%    -1.0pp
  INC_THEN_DEC                 346    178   51.4%    -2.6pp
  INCREASING                    30     13   43.3%   -10.7pp !!!

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    23     13   56.5%    +2.5pp
  FLAT                        1646    914   55.5%    +1.5pp
  VOLATILE                     176     90   51.1%    -2.9pp
  DEC_THEN_INC                 300    150   50.0%    -4.0pp
  DECREASING                    41     20   48.8%    -5.2pp ***
  INC_THEN_DEC                 357    170   47.6%    -6.4pp ***

  --- ENTRY LEVEL SIGNALS (snapshot at entry) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPLOSIVE                    740    460   62.2%    +8.1pp ***
  EXPANDING                    501    277   55.3%    +1.3pp
  NORMAL                       698    339   48.6%    -5.5pp ***
  COMPRESSED                   604    281   46.5%    -7.5pp ***

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_BUY                   651    368   56.5%    +2.5pp
  STRONG_SELL                  769    417   54.2%    +0.2pp
  MILD_SELL                    539    284   52.7%    -1.3pp
  MILD_BUY                     584    288   49.3%    -4.7pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXTREME                      438    255   58.2%    +4.2pp
  MODERATE                     408    216   52.9%    -1.1pp
  LOW                         1459    763   52.3%    -1.7pp
  ELEVATED                     235    121   51.5%    -2.5pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_FALLING               452    254   56.2%    +2.2pp
  STRONG_RISING                447    247   55.3%    +1.2pp
  MILD_FALLING                 798    427   53.5%    -0.5pp
  MILD_RISING                  846    429   50.7%    -3.3pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDE_BEAR                    919    532   57.9%    +3.9pp
  WIDE_BULL                    755    408   54.0%    +0.0pp
  NARROW_BULL                  411    215   52.3%    -1.7pp
  NARROW_BEAR                  455    200   44.0%   -10.1pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_WIDENING              411    244   59.4%    +5.3pp ***
  FLAT                        1156    605   52.3%    -1.7pp
  WIDENING                     971    505   52.0%    -2.0pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG                       887    519   58.5%    +4.5pp
  MODERATE                     803    419   52.2%    -1.8pp
  WEAK                         730    379   51.9%    -2.1pp
  CRITICAL                     123     40   32.5%   -21.5pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     165    111   67.3%   +13.3pp !!!
  LOW                         1234    694   56.2%    +2.2pp
  MINIMAL                     1144    552   48.3%    -5.8pp ***

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     145     85   58.6%    +4.6pp
  LOW                         1551    865   55.8%    +1.8pp
  MINIMAL                      847    407   48.1%    -6.0pp ***

  --- FLIP SIGNALS (sign changes in ramp-up) ---

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MULTIPLE_FLIPS              2522   1342   53.2%    -0.8pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NO_FLIP                      236    147   62.3%    +8.3pp ***
  FLIP_TO_POSITIVE             322    185   57.5%    +3.4pp
  MULTIPLE_FLIPS              1674    875   52.3%    -1.7pp
  FLIP_TO_NEGATIVE             311    150   48.2%    -5.8pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLIP_TO_POSITIVE             425    245   57.6%    +3.6pp
  NO_FLIP                      309    177   57.3%    +3.3pp
  MULTIPLE_FLIPS              1277    661   51.8%    -2.3pp
  FLIP_TO_NEGATIVE             528    272   51.5%    -2.5pp

================================================================================
SECTION 4: PATH TO MFE (15-bar M1 ramp-up + snapshot at MFE)
  Trades: 5377, Wins: 3134, WR: 58.3% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES (ramp-up to event) ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  VOLATILE           FLAT               INCREASING           61   98.4%   +44.3pp !!!
  VOLATILE           DEC_THEN_INC       DECREASING           32   93.8%   +39.7pp !!!
  DECREASING         DECREASING         DEC_THEN_INC         22   90.9%   +36.9pp
  FLAT               INCREASING         DECREASING           87   85.1%   +31.0pp !!!
  INCREASING         FLAT               DECREASING           26   84.6%   +30.6pp
  DEC_THEN_INC       DEC_THEN_INC       DECREASING           41   82.9%   +28.9pp !!!
  INC_THEN_DEC       DECREASING         INCREASING           95   81.1%   +27.0pp !!!
  DECREASING         DEC_THEN_INC       DECREASING          105   78.1%   +24.1pp !!!
  DEC_THEN_INC       DEC_THEN_INC       INCREASING           54   77.8%   +23.8pp !!!
  INC_THEN_DEC       VOLATILE           DECREASING          116   77.6%   +23.6pp !!!
  INCREASING         INCREASING         DECREASING           93   77.4%   +23.4pp !!!
  INC_THEN_DEC       DEC_THEN_INC       INCREASING           51   76.5%   +22.5pp !!!
  DEC_THEN_INC       DECREASING         DECREASING           89   76.4%   +22.4pp !!!
  DECREASING         VOLATILE           INCREASING           45   75.6%   +21.5pp !!!
  INCREASING         VOLATILE           DECREASING           28   75.0%   +21.0pp

  --- RAMP-UP TRENDS (15 M1 bars before event) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 984    633   64.3%   +10.3pp !!!
  INC_THEN_DEC                 955    606   63.5%    +9.4pp ***
  DECREASING                  1634    935   57.2%    +3.2pp
  FLAT                         462    254   55.0%    +1.0pp
  VOLATILE                     490    266   54.3%    +0.3pp
  INCREASING                   852    440   51.6%    -2.4pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     473    297   62.8%    +8.8pp ***
  FLAT                         420    248   59.0%    +5.0pp ***
  DEC_THEN_INC                 714    417   58.4%    +4.4pp
  INCREASING                  1568    911   58.1%    +4.1pp
  INC_THEN_DEC                 646    375   58.0%    +4.0pp
  DECREASING                  1556    886   56.9%    +2.9pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         321    211   65.7%   +11.7pp !!!
  VOLATILE                     603    372   61.7%    +7.7pp ***
  INC_THEN_DEC                 673    410   60.9%    +6.9pp ***
  INCREASING                  1324    778   58.8%    +4.7pp
  DECREASING                  1580    888   56.2%    +2.2pp
  DEC_THEN_INC                 876    475   54.2%    +0.2pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          83     63   75.9%   +21.9pp !!!
  DEC_THEN_INC                 367    256   69.8%   +15.7pp !!!
  VOLATILE                      45     27   60.0%    +6.0pp ***
  INCREASING                  2095   1236   59.0%    +5.0pp
  DECREASING                  2404   1391   57.9%    +3.8pp
  INC_THEN_DEC                 383    161   42.0%   -12.0pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 199    133   66.8%   +12.8pp !!!
  DECREASING                  2466   1566   63.5%    +9.5pp ***
  INCREASING                  2305   1281   55.6%    +1.6pp
  VOLATILE                      43     22   51.2%    -2.9pp
  INC_THEN_DEC                 264    100   37.9%   -16.1pp !!!
  FLAT                         100     32   32.0%   -22.0pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         123     90   73.2%   +19.2pp !!!
  DECREASING                  2178   1362   62.5%    +8.5pp ***
  INC_THEN_DEC                 322    193   59.9%    +5.9pp ***
  DEC_THEN_INC                 489    281   57.5%    +3.4pp
  INCREASING                  2247   1200   53.4%    -0.6pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 412    283   68.7%   +14.7pp !!!
  FLAT                        4207   2453   58.3%    +4.3pp
  INC_THEN_DEC                 469    273   58.2%    +4.2pp
  VOLATILE                     264    125   47.3%    -6.7pp ***

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 804    514   63.9%    +9.9pp ***
  FLAT                        3243   1922   59.3%    +5.2pp ***
  DEC_THEN_INC                 693    400   57.7%    +3.7pp
  INCREASING                    57     28   49.1%    -4.9pp
  VOLATILE                     520    253   48.7%    -5.4pp ***
  DECREASING                    60     17   28.3%   -25.7pp !!!

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     374    267   71.4%   +17.4pp !!!
  INCREASING                    72     51   70.8%   +16.8pp !!!
  INC_THEN_DEC                 852    560   65.7%   +11.7pp !!!
  DECREASING                    54     32   59.3%    +5.2pp ***
  DEC_THEN_INC                 710    394   55.5%    +1.5pp
  FLAT                        3315   1830   55.2%    +1.2pp

  --- SNAPSHOT AT EVENT ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPANDING                   1130    728   64.4%   +10.4pp !!!
  COMPRESSED                  1650    997   60.4%    +6.4pp ***
  NORMAL                      1502    815   54.3%    +0.2pp
  EXPLOSIVE                   1095    594   54.2%    +0.2pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_SELL                   1181    748   63.3%    +9.3pp ***
  STRONG_SELL                 1620    950   58.6%    +4.6pp
  MILD_BUY                    1000    560   56.0%    +2.0pp
  STRONG_BUY                  1576    876   55.6%    +1.6pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXTREME                      868    559   64.4%   +10.4pp !!!
  ELEVATED                     902    528   58.5%    +4.5pp
  MODERATE                    1287    748   58.1%    +4.1pp
  LOW                         2320   1299   56.0%    +2.0pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_RISING                 1620   1014   62.6%    +8.6pp ***
  STRONG_FALLING              1096    679   62.0%    +7.9pp ***
  MILD_FALLING                1677    928   55.3%    +1.3pp
  STRONG_RISING                984    513   52.1%    -1.9pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NARROW_BULL                  860    540   62.8%    +8.8pp ***
  WIDE_BEAR                   1817   1084   59.7%    +5.6pp ***
  WIDE_BULL                   1754   1004   57.2%    +3.2pp
  NARROW_BEAR                  946    506   53.5%    -0.5pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                        2403   1447   60.2%    +6.2pp ***
  STRONG_WIDENING              657    382   58.1%    +4.1pp
  WIDENING                    2317   1305   56.3%    +2.3pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WEAK                        1138    693   60.9%    +6.9pp ***
  MODERATE                    2144   1298   60.5%    +6.5pp ***
  STRONG                      1958   1098   56.1%    +2.1pp
  CRITICAL                     137     45   32.8%   -21.2pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     259    179   69.1%   +15.1pp !!!
  LOW                         2586   1502   58.1%    +4.1pp
  MINIMAL                     2532   1453   57.4%    +3.4pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  LOW                         3250   1952   60.1%    +6.0pp ***
  MINIMAL                     1749    980   56.0%    +2.0pp
  MODERATE                     378    202   53.4%    -0.6pp

================================================================================
SECTION 4L: PATH TO MFE - LONG TRADES
  Trades: 2535, Wins: 1448, WR: 57.1% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES (ramp-up to event) ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  VOLATILE           FLAT               INCREASING           24  100.0%   +46.0pp
  DECREASING         DECREASING         DEC_THEN_INC         22   90.9%   +36.9pp
  FLAT               INCREASING         DECREASING           52   88.5%   +34.4pp !!!
  INC_THEN_DEC       DECREASING         INCREASING           59   88.1%   +34.1pp !!!
  DEC_THEN_INC       DECREASING         DECREASING           31   87.1%   +33.1pp !!!
  INCREASING         FLAT               DECREASING           26   84.6%   +30.6pp
  DEC_THEN_INC       DEC_THEN_INC       DECREASING           26   76.9%   +22.9pp
  INCREASING         FLAT               INCREASING           25   76.0%   +22.0pp
  DEC_THEN_INC       DEC_THEN_INC       INCREASING           50   76.0%   +22.0pp !!!
  DECREASING         VOLATILE           INCREASING           41   75.6%   +21.6pp !!!
  INC_THEN_DEC       DECREASING         DECREASING           71   73.2%   +19.2pp !!!
  DECREASING         DECREASING         INCREASING          108   73.1%   +19.1pp !!!
  DEC_THEN_INC       INCREASING         DECREASING           58   72.4%   +18.4pp !!!
  DEC_THEN_INC       INCREASING         INCREASING           61   72.1%   +18.1pp !!!
  INCREASING         INC_THEN_DEC       INCREASING           25   72.0%   +18.0pp

  --- RAMP-UP TRENDS (15 M1 bars before event) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 367    244   66.5%   +12.5pp !!!
  INC_THEN_DEC                 510    317   62.2%    +8.1pp ***
  FLAT                         203    119   58.6%    +4.6pp
  DECREASING                   798    449   56.3%    +2.2pp
  INCREASING                   409    201   49.1%    -4.9pp
  VOLATILE                     248    118   47.6%    -6.4pp ***

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         151    103   68.2%   +14.2pp !!!
  DECREASING                   543    326   60.0%    +6.0pp ***
  INC_THEN_DEC                 218    129   59.2%    +5.2pp ***
  VOLATILE                     193    111   57.5%    +3.5pp
  INCREASING                  1055    590   55.9%    +1.9pp
  DEC_THEN_INC                 375    189   50.4%    -3.6pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         143    109   76.2%   +22.2pp !!!
  INC_THEN_DEC                 361    239   66.2%   +12.2pp !!!
  VOLATILE                     268    162   60.4%    +6.4pp ***
  INCREASING                   627    357   56.9%    +2.9pp
  DECREASING                   774    415   53.6%    -0.4pp
  DEC_THEN_INC                 362    166   45.9%    -8.2pp ***

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          53     43   81.1%   +27.1pp !!!
  DEC_THEN_INC                 230    160   69.6%   +15.5pp !!!
  DECREASING                   905    520   57.5%    +3.4pp
  INCREASING                  1163    660   56.7%    +2.7pp
  INC_THEN_DEC                 171     60   35.1%   -18.9pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 139    100   71.9%   +17.9pp !!!
  DECREASING                   960    616   64.2%   +10.1pp !!!
  INCREASING                  1298    698   53.8%    -0.2pp
  INC_THEN_DEC                  55     21   38.2%   -15.8pp !!!
  FLAT                          64      9   14.1%   -40.0pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 134     95   70.9%   +16.9pp !!!
  FLAT                          35     22   62.9%    +8.8pp ***
  DECREASING                  1174    734   62.5%    +8.5pp ***
  DEC_THEN_INC                 198    123   62.1%    +8.1pp ***
  INCREASING                   994    474   47.7%    -6.3pp ***

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 153    109   71.2%   +17.2pp !!!
  INC_THEN_DEC                 278    170   61.2%    +7.1pp ***
  FLAT                        1950   1122   57.5%    +3.5pp
  VOLATILE                     143     47   32.9%   -21.2pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 438    261   59.6%    +5.6pp ***
  FLAT                        1506    897   59.6%    +5.5pp ***
  DEC_THEN_INC                 303    166   54.8%    +0.8pp
  VOLATILE                     247    115   46.6%    -7.5pp ***
  INCREASING                    29      7   24.1%   -29.9pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    26     25   96.2%   +42.1pp
  VOLATILE                     155    116   74.8%   +20.8pp !!!
  INC_THEN_DEC                 413    248   60.0%    +6.0pp ***
  FLAT                        1525    844   55.3%    +1.3pp
  DEC_THEN_INC                 396    205   51.8%    -2.3pp
  DECREASING                    20     10   50.0%    -4.0pp

  --- SNAPSHOT AT EVENT ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPANDING                    393    245   62.3%    +8.3pp ***
  COMPRESSED                   905    545   60.2%    +6.2pp ***
  NORMAL                       810    486   60.0%    +6.0pp ***
  EXPLOSIVE                    427    172   40.3%   -13.7pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_SELL                    379    277   73.1%   +19.1pp !!!
  STRONG_BUY                  1227    701   57.1%    +3.1pp
  MILD_BUY                     741    397   53.6%    -0.4pp
  STRONG_SELL                  188     73   38.8%   -15.2pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXTREME                      253    164   64.8%   +10.8pp !!!
  LOW                         1200    701   58.4%    +4.4pp
  ELEVATED                     438    242   55.3%    +1.2pp
  MODERATE                     644    341   53.0%    -1.1pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_RISING                 1125    709   63.0%    +9.0pp ***
  STRONG_RISING                929    510   54.9%    +0.9pp
  MILD_FALLING                 367    189   51.5%    -2.5pp
  STRONG_FALLING               114     40   35.1%   -18.9pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NARROW_BULL                  640    388   60.6%    +6.6pp ***
  WIDE_BULL                   1590    955   60.1%    +6.0pp ***
  WIDE_BEAR                    142     50   35.2%   -18.8pp !!!
  NARROW_BEAR                  163     55   33.7%   -20.3pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                        1164    714   61.3%    +7.3pp ***
  STRONG_WIDENING              340    206   60.6%    +6.6pp ***
  WIDENING                    1031    528   51.2%    -2.8pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WEAK                         606    400   66.0%   +12.0pp !!!
  MODERATE                    1049    595   56.7%    +2.7pp
  STRONG                       787    422   53.6%    -0.4pp
  CRITICAL                      93     31   33.3%   -20.7pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MINIMAL                     1373    824   60.0%    +6.0pp ***
  MODERATE                     165     91   55.2%    +1.1pp
  LOW                          997    533   53.5%    -0.6pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MINIMAL                      432    261   60.4%    +6.4pp ***
  LOW                         1814   1041   57.4%    +3.4pp
  MODERATE                     289    146   50.5%    -3.5pp

================================================================================
SECTION 4S: PATH TO MFE - SHORT TRADES
  Trades: 2842, Wins: 1686, WR: 59.3% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES (ramp-up to event) ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  INCREASING         INCREASING         DECREASING           44   97.7%   +43.7pp !!!
  VOLATILE           FLAT               INCREASING           37   97.3%   +43.3pp !!!
  VOLATILE           DEC_THEN_INC       DECREASING           32   93.8%   +39.7pp !!!
  INC_THEN_DEC       VOLATILE           INCREASING           21   90.5%   +36.5pp
  INC_THEN_DEC       DEC_THEN_INC       INCREASING           36   86.1%   +32.1pp !!!
  DECREASING         DEC_THEN_INC       DECREASING           88   83.0%   +28.9pp !!!
  FLAT               INCREASING         DECREASING           35   80.0%   +26.0pp !!!
  DEC_THEN_INC       FLAT               INCREASING           43   79.1%   +25.1pp !!!
  INCREASING         INC_THEN_DEC       DECREASING           22   77.3%   +23.3pp
  DEC_THEN_INC       INCREASING         INCREASING           35   77.1%   +23.1pp !!!
  INC_THEN_DEC       VOLATILE           DECREASING          113   77.0%   +23.0pp !!!
  INCREASING         INCREASING         INCREASING           21   76.2%   +22.2pp
  DEC_THEN_INC       INC_THEN_DEC       DECREASING          100   74.0%   +20.0pp !!!
  DECREASING         VOLATILE           DECREASING           83   73.5%   +19.5pp !!!
  DECREASING         DECREASING         DECREASING          165   72.1%   +18.1pp !!!

  --- RAMP-UP TRENDS (15 M1 bars before event) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 445    289   64.9%   +10.9pp !!!
  DEC_THEN_INC                 617    389   63.0%    +9.0pp ***
  VOLATILE                     242    148   61.2%    +7.1pp ***
  DECREASING                   836    486   58.1%    +4.1pp
  INCREASING                   443    239   54.0%    -0.1pp
  FLAT                         259    135   52.1%    -1.9pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 339    228   67.3%   +13.2pp !!!
  VOLATILE                     280    186   66.4%   +12.4pp !!!
  INCREASING                   513    321   62.6%    +8.6pp ***
  INC_THEN_DEC                 428    246   57.5%    +3.5pp
  DECREASING                  1013    560   55.3%    +1.3pp
  FLAT                         269    145   53.9%    -0.1pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     335    210   62.7%    +8.7pp ***
  INCREASING                   697    421   60.4%    +6.4pp ***
  DEC_THEN_INC                 514    309   60.1%    +6.1pp ***
  DECREASING                   806    473   58.7%    +4.7pp
  FLAT                         178    102   57.3%    +3.3pp
  INC_THEN_DEC                 312    171   54.8%    +0.8pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 137     96   70.1%   +16.1pp !!!
  VOLATILE                      32     22   68.8%   +14.7pp !!!
  FLAT                          30     20   66.7%   +12.6pp !!!
  INCREASING                   932    576   61.8%    +7.8pp ***
  DECREASING                  1499    871   58.1%    +4.1pp
  INC_THEN_DEC                 212    101   47.6%    -6.4pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                      24     18   75.0%   +21.0pp
  FLAT                          36     23   63.9%    +9.9pp ***
  DECREASING                  1506    950   63.1%    +9.1pp ***
  INCREASING                  1007    583   57.9%    +3.9pp
  DEC_THEN_INC                  60     33   55.0%    +1.0pp
  INC_THEN_DEC                 209     79   37.8%   -16.2pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          88     68   77.3%   +23.3pp !!!
  DECREASING                  1004    628   62.5%    +8.5pp ***
  INCREASING                  1253    726   57.9%    +3.9pp
  DEC_THEN_INC                 291    158   54.3%    +0.3pp
  INC_THEN_DEC                 188     98   52.1%    -1.9pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 259    174   67.2%   +13.2pp !!!
  VOLATILE                     121     78   64.5%   +10.4pp !!!
  FLAT                        2257   1331   59.0%    +5.0pp
  INC_THEN_DEC                 191    103   53.9%    -0.1pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                    28     21   75.0%   +21.0pp
  INC_THEN_DEC                 366    253   69.1%   +15.1pp !!!
  DEC_THEN_INC                 390    234   60.0%    +6.0pp ***
  FLAT                        1737   1025   59.0%    +5.0pp
  VOLATILE                     273    138   50.5%    -3.5pp
  DECREASING                    48     15   31.2%   -22.8pp !!!

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INC_THEN_DEC                 439    312   71.1%   +17.1pp !!!
  VOLATILE                     219    151   68.9%   +14.9pp !!!
  DECREASING                    34     22   64.7%   +10.7pp !!!
  DEC_THEN_INC                 314    189   60.2%    +6.2pp ***
  INCREASING                    46     26   56.5%    +2.5pp
  FLAT                        1790    986   55.1%    +1.1pp

  --- SNAPSHOT AT EVENT ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPANDING                    737    483   65.5%   +11.5pp !!!
  EXPLOSIVE                    668    422   63.2%    +9.2pp ***
  COMPRESSED                   745    452   60.7%    +6.7pp ***
  NORMAL                       692    329   47.5%    -6.5pp ***

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_BUY                     259    163   62.9%    +8.9pp ***
  STRONG_SELL                 1432    877   61.2%    +7.2pp ***
  MILD_SELL                    802    471   58.7%    +4.7pp
  STRONG_BUY                   349    175   50.1%    -3.9pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXTREME                      615    395   64.2%   +10.2pp !!!
  MODERATE                     643    407   63.3%    +9.3pp ***
  ELEVATED                     464    286   61.6%    +7.6pp ***
  LOW                         1120    598   53.4%    -0.6pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_FALLING               982    639   65.1%   +11.1pp !!!
  MILD_RISING                  495    305   61.6%    +7.6pp ***
  MILD_FALLING                1310    739   56.4%    +2.4pp
  STRONG_RISING                 55      3    5.5%   -48.6pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NARROW_BULL                  220    152   69.1%   +15.1pp !!!
  WIDE_BEAR                   1675   1034   61.7%    +7.7pp ***
  NARROW_BEAR                  783    451   57.6%    +3.6pp
  WIDE_BULL                    164     49   29.9%   -24.1pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDENING                    1286    777   60.4%    +6.4pp ***
  FLAT                        1239    733   59.2%    +5.1pp ***
  STRONG_WIDENING              317    176   55.5%    +1.5pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                    1095    703   64.2%   +10.2pp !!!
  STRONG                      1171    676   57.7%    +3.7pp
  WEAK                         532    293   55.1%    +1.1pp
  CRITICAL                      44     14   31.8%   -22.2pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                      94     88   93.6%   +39.6pp !!!
  LOW                         1589    969   61.0%    +7.0pp ***
  MINIMAL                     1159    629   54.3%    +0.3pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  LOW                         1436    911   63.4%    +9.4pp ***
  MODERATE                      89     56   62.9%    +8.9pp ***
  MINIMAL                     1317    719   54.6%    +0.6pp

================================================================================
SECTION 5: PATH TO EXIT / MAX-R (15-bar M1 ramp-up + snapshot at max R time)
  Trades: 5922, Wins: 3199, WR: 54.0% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES (ramp-up to event) ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  FLAT               DECREASING         INC_THEN_DEC         24  100.0%   +46.0pp
  INC_THEN_DEC       DECREASING         VOLATILE             22  100.0%   +46.0pp
  INCREASING         INCREASING         DEC_THEN_INC         26   96.2%   +42.1pp
  DEC_THEN_INC       VOLATILE           DECREASING           20   95.0%   +41.0pp
  DECREASING         DEC_THEN_INC       INCREASING           65   80.0%   +26.0pp !!!
  FLAT               VOLATILE           DECREASING           28   78.6%   +24.6pp
  FLAT               VOLATILE           INCREASING           29   75.9%   +21.8pp
  FLAT               INCREASING         INCREASING           78   75.6%   +21.6pp !!!
  INCREASING         DEC_THEN_INC       INCREASING           78   74.4%   +20.3pp !!!
  INCREASING         DECREASING         INC_THEN_DEC         48   72.9%   +18.9pp !!!
  FLAT               DECREASING         INCREASING           50   72.0%   +18.0pp !!!
  DEC_THEN_INC       INCREASING         DEC_THEN_INC         28   71.4%   +17.4pp
  INC_THEN_DEC       DEC_THEN_INC       INCREASING           27   70.4%   +16.4pp
  VOLATILE           DECREASING         DECREASING           77   70.1%   +16.1pp !!!
  VOLATILE           DEC_THEN_INC       INCREASING           66   68.2%   +14.2pp !!!

  --- RAMP-UP TRENDS (15 M1 bars before event) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                  1294    764   59.0%    +5.0pp ***
  DECREASING                  1362    764   56.1%    +2.1pp
  VOLATILE                     567    318   56.1%    +2.1pp
  FLAT                         544    285   52.4%    -1.6pp
  DEC_THEN_INC                1137    592   52.1%    -2.0pp
  INC_THEN_DEC                1018    476   46.8%    -7.3pp ***

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     316    189   59.8%    +5.8pp ***
  DEC_THEN_INC                 698    393   56.3%    +2.3pp
  DECREASING                  1790    994   55.5%    +1.5pp
  INCREASING                  1738    929   53.5%    -0.6pp
  INC_THEN_DEC                 880    452   51.4%    -2.7pp
  FLAT                         500    242   48.4%    -5.6pp ***

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                1106    636   57.5%    +3.5pp
  VOLATILE                     445    255   57.3%    +3.3pp
  INCREASING                  1613    900   55.8%    +1.8pp
  FLAT                         454    245   54.0%    -0.1pp
  INC_THEN_DEC                 977    506   51.8%    -2.2pp
  DECREASING                  1324    654   49.4%    -4.6pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                 341    199   58.4%    +4.3pp
  VOLATILE                      81     47   58.0%    +4.0pp
  DECREASING                  2397   1333   55.6%    +1.6pp
  INCREASING                  2553   1373   53.8%    -0.2pp
  FLAT                         123     62   50.4%    -3.6pp
  INC_THEN_DEC                 425    183   43.1%   -11.0pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                      63     35   55.6%    +1.5pp
  DECREASING                  2466   1343   54.5%    +0.4pp
  INCREASING                  2674   1455   54.4%    +0.4pp
  INC_THEN_DEC                 294    158   53.7%    -0.3pp
  DEC_THEN_INC                 354    173   48.9%    -5.1pp ***
  FLAT                          68     32   47.1%    -7.0pp ***

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     102     70   68.6%   +14.6pp !!!
  INCREASING                  2590   1452   56.1%    +2.0pp
  DECREASING                  2069   1146   55.4%    +1.4pp
  FLAT                         116     64   55.2%    +1.2pp
  INC_THEN_DEC                 497    231   46.5%    -7.5pp ***
  DEC_THEN_INC                 538    233   43.3%   -10.7pp !!!

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     373    250   67.0%   +13.0pp !!!
  INC_THEN_DEC                 502    298   59.4%    +5.3pp ***
  DEC_THEN_INC                 428    250   58.4%    +4.4pp
  INCREASING                    94     51   54.3%    +0.2pp
  FLAT                        4496   2341   52.1%    -2.0pp
  DECREASING                    29      9   31.0%   -23.0pp

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                     598    386   64.5%   +10.5pp !!!
  FLAT                        3466   1846   53.3%    -0.8pp
  DEC_THEN_INC                 844    445   52.7%    -1.3pp
  INCREASING                   153     80   52.3%    -1.7pp
  INC_THEN_DEC                 780    403   51.7%    -2.4pp
  DECREASING                    81     39   48.1%    -5.9pp ***

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                   107     75   70.1%   +16.1pp !!!
  VOLATILE                     546    314   57.5%    +3.5pp
  DEC_THEN_INC                 805    454   56.4%    +2.4pp
  INC_THEN_DEC                 784    425   54.2%    +0.2pp
  FLAT                        3576   1893   52.9%    -1.1pp
  DECREASING                   104     38   36.5%   -17.5pp !!!

  --- SNAPSHOT AT EVENT ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPANDING                   1519    849   55.9%    +1.9pp
  COMPRESSED                  1069    591   55.3%    +1.3pp
  NORMAL                      1660    895   53.9%    -0.1pp
  EXPLOSIVE                   1674    864   51.6%    -2.4pp

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_BUY                     807    473   58.6%    +4.6pp
  STRONG_SELL                 1987   1111   55.9%    +1.9pp
  MILD_SELL                    983    545   55.4%    +1.4pp
  STRONG_BUY                  2145   1070   49.9%    -4.1pp

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXTREME                     1284    758   59.0%    +5.0pp ***
  ELEVATED                    1178    693   58.8%    +4.8pp
  MODERATE                    1591    902   56.7%    +2.7pp
  LOW                         1867    844   45.2%    -8.8pp ***

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_FALLING              1262    791   62.7%    +8.7pp ***
  STRONG_RISING               1358    779   57.4%    +3.3pp
  MILD_FALLING                1564    824   52.7%    -1.3pp
  MILD_RISING                 1738    805   46.3%    -7.7pp ***

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDE_BEAR                   2109   1299   61.6%    +7.6pp ***
  WIDE_BULL                   2045   1133   55.4%    +1.4pp
  NARROW_BULL                  894    411   46.0%    -8.0pp ***
  NARROW_BEAR                  872    354   40.6%   -13.4pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_WIDENING             1097    642   58.5%    +4.5pp
  WIDENING                    2603   1481   56.9%    +2.9pp
  FLAT                        2215   1073   48.4%    -5.6pp ***

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG                      2986   1812   60.7%    +6.7pp ***
  MODERATE                    1633    922   56.5%    +2.4pp
  WEAK                        1104    420   38.0%   -16.0pp !!!
  CRITICAL                     199     45   22.6%   -31.4pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     691    400   57.9%    +3.9pp
  LOW                         3269   1759   53.8%    -0.2pp
  MINIMAL                     1962   1040   53.0%    -1.0pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  LOW                         3593   1975   55.0%    +0.9pp
  MODERATE                     847    460   54.3%    +0.3pp
  MINIMAL                     1482    764   51.6%    -2.5pp

================================================================================
SECTION 5.1: PATH TO EXIT - TRADES REACHING EXACTLY R1
  Trades: 1332, Wins: 1332, WR: 100.0% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES (ramp-up to event) ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  DECREASING         DECREASING         DECREASING           93  100.0%   +46.0pp !!!
  DECREASING         INCREASING         DECREASING           27  100.0%   +46.0pp
  INCREASING         INCREASING         INCREASING           54  100.0%   +46.0pp !!!
  INCREASING         INC_THEN_DEC       INCREASING           24  100.0%   +46.0pp
  INCREASING         DECREASING         INC_THEN_DEC         23  100.0%   +46.0pp
  INC_THEN_DEC       INCREASING         INCREASING           30  100.0%   +46.0pp !!!
  INCREASING         INCREASING         DECREASING           36  100.0%   +46.0pp !!!
  INCREASING         DEC_THEN_INC       DECREASING           23  100.0%   +46.0pp
  INCREASING         DECREASING         DECREASING           25  100.0%   +46.0pp
  INCREASING         INC_THEN_DEC       DECREASING           25  100.0%   +46.0pp
  DEC_THEN_INC       INCREASING         DECREASING           38  100.0%   +46.0pp !!!
  DEC_THEN_INC       DECREASING         DECREASING           33  100.0%   +46.0pp !!!
  INC_THEN_DEC       INCREASING         DECREASING           28  100.0%   +46.0pp
  DECREASING         FLAT               INCREASING           20  100.0%   +46.0pp
  DEC_THEN_INC       DECREASING         INCREASING           35  100.0%   +46.0pp !!!

  --- RAMP-UP TRENDS (15 M1 bars before event) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   322    322  100.0%   +46.0pp !!!
  INC_THEN_DEC                 206    206  100.0%   +46.0pp !!!
  FLAT                          92     92  100.0%   +46.0pp !!!
  INCREASING                   340    340  100.0%   +46.0pp !!!
  DEC_THEN_INC                 248    248  100.0%   +46.0pp !!!
  VOLATILE                     124    124  100.0%   +46.0pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   437    437  100.0%   +46.0pp !!!
  VOLATILE                      85     85  100.0%   +46.0pp !!!
  INCREASING                   387    387  100.0%   +46.0pp !!!
  INC_THEN_DEC                 177    177  100.0%   +46.0pp !!!
  DEC_THEN_INC                 157    157  100.0%   +46.0pp !!!
  FLAT                          89     89  100.0%   +46.0pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                   419    419  100.0%   +46.0pp !!!
  VOLATILE                     130    130  100.0%   +46.0pp !!!
  INC_THEN_DEC                 179    179  100.0%   +46.0pp !!!
  FLAT                          97     97  100.0%   +46.0pp !!!
  DECREASING                   233    233  100.0%   +46.0pp !!!
  DEC_THEN_INC                 272    272  100.0%   +46.0pp !!!

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   564    564  100.0%   +46.0pp !!!
  DEC_THEN_INC                  80     80  100.0%   +46.0pp !!!
  INCREASING                   618    618  100.0%   +46.0pp !!!
  INC_THEN_DEC                  46     46  100.0%   +46.0pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   543    543  100.0%   +46.0pp !!!
  INCREASING                   599    599  100.0%   +46.0pp !!!
  INC_THEN_DEC                  85     85  100.0%   +46.0pp !!!
  DEC_THEN_INC                  68     68  100.0%   +46.0pp !!!
  VOLATILE                      22     22  100.0%   +46.0pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  INCREASING                   593    593  100.0%   +46.0pp !!!
  INC_THEN_DEC                  84     84  100.0%   +46.0pp !!!
  FLAT                          29     29  100.0%   +46.0pp
  DECREASING                   464    464  100.0%   +46.0pp !!!
  DEC_THEN_INC                 132    132  100.0%   +46.0pp !!!
  VOLATILE                      28     28  100.0%   +46.0pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  VOLATILE                      92     92  100.0%   +46.0pp !!!
  FLAT                        1001   1001  100.0%   +46.0pp !!!
  DEC_THEN_INC                 108    108  100.0%   +46.0pp !!!
  INC_THEN_DEC                 115    115  100.0%   +46.0pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         775    775  100.0%   +46.0pp !!!
  VOLATILE                     156    156  100.0%   +46.0pp !!!
  INC_THEN_DEC                 186    186  100.0%   +46.0pp !!!
  INCREASING                    36     36  100.0%   +46.0pp !!!
  DEC_THEN_INC                 172    172  100.0%   +46.0pp !!!

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         780    780  100.0%   +46.0pp !!!
  VOLATILE                     111    111  100.0%   +46.0pp !!!
  INC_THEN_DEC                 226    226  100.0%   +46.0pp !!!
  INCREASING                    36     36  100.0%   +46.0pp !!!
  DEC_THEN_INC                 164    164  100.0%   +46.0pp !!!

  --- SNAPSHOT AT EVENT ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPANDING                    385    385  100.0%   +46.0pp !!!
  COMPRESSED                   238    238  100.0%   +46.0pp !!!
  NORMAL                       345    345  100.0%   +46.0pp !!!
  EXPLOSIVE                    364    364  100.0%   +46.0pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MILD_SELL                    208    208  100.0%   +46.0pp !!!
  STRONG_BUY                   414    414  100.0%   +46.0pp !!!
  MILD_BUY                     257    257  100.0%   +46.0pp !!!
  STRONG_SELL                  453    453  100.0%   +46.0pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXTREME                      266    266  100.0%   +46.0pp !!!
  MODERATE                     417    417  100.0%   +46.0pp !!!
  ELEVATED                     243    243  100.0%   +46.0pp !!!
  LOW                          404    404  100.0%   +46.0pp !!!

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_FALLING               275    275  100.0%   +46.0pp !!!
  MILD_FALLING                 376    376  100.0%   +46.0pp !!!
  MILD_RISING                  364    364  100.0%   +46.0pp !!!
  STRONG_RISING                317    317  100.0%   +46.0pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NARROW_BEAR                  161    161  100.0%   +46.0pp !!!
  WIDE_BULL                    481    481  100.0%   +46.0pp !!!
  WIDE_BEAR                    494    494  100.0%   +46.0pp !!!
  NARROW_BULL                  194    194  100.0%   +46.0pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDENING                     615    615  100.0%   +46.0pp !!!
  STRONG_WIDENING              226    226  100.0%   +46.0pp !!!
  FLAT                         489    489  100.0%   +46.0pp !!!

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG                       662    662  100.0%   +46.0pp !!!
  MODERATE                     396    396  100.0%   +46.0pp !!!
  WEAK                         237    237  100.0%   +46.0pp !!!
  CRITICAL                      37     37  100.0%   +46.0pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  LOW                          736    736  100.0%   +46.0pp !!!
  MINIMAL                      466    466  100.0%   +46.0pp !!!
  MODERATE                     130    130  100.0%   +46.0pp !!!

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  LOW                          875    875  100.0%   +46.0pp !!!
  MINIMAL                      279    279  100.0%   +46.0pp !!!
  MODERATE                     178    178  100.0%   +46.0pp !!!

================================================================================
SECTION 5.2: PATH TO EXIT - TRADES REACHING EXACTLY R2
  Trades: 768, Wins: 768, WR: 100.0% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES (ramp-up to event) ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  VOLATILE           DECREASING         DECREASING           25  100.0%   +46.0pp
  INC_THEN_DEC       INCREASING         INCREASING           24  100.0%   +46.0pp
  INCREASING         DECREASING         DECREASING           40  100.0%   +46.0pp !!!
  INCREASING         INCREASING         INCREASING           42  100.0%   +46.0pp !!!
  INCREASING         INCREASING         DECREASING           31  100.0%   +46.0pp !!!
  DEC_THEN_INC       INC_THEN_DEC       DECREASING           23  100.0%   +46.0pp
  FLAT               INCREASING         INCREASING           27  100.0%   +46.0pp
  VOLATILE           DEC_THEN_INC       INCREASING           29  100.0%   +46.0pp
  DECREASING         INCREASING         DECREASING           20  100.0%   +46.0pp
  VOLATILE           FLAT               INCREASING           32  100.0%   +46.0pp !!!
  INC_THEN_DEC       DECREASING         INCREASING           24  100.0%   +46.0pp

  --- RAMP-UP TRENDS (15 M1 bars before event) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   122    122  100.0%   +46.0pp !!!
  VOLATILE                     113    113  100.0%   +46.0pp !!!
  INCREASING                   199    199  100.0%   +46.0pp !!!
  INC_THEN_DEC                 129    129  100.0%   +46.0pp !!!
  DEC_THEN_INC                 122    122  100.0%   +46.0pp !!!
  FLAT                          83     83  100.0%   +46.0pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          71     71  100.0%   +46.0pp !!!
  DECREASING                   247    247  100.0%   +46.0pp !!!
  DEC_THEN_INC                  90     90  100.0%   +46.0pp !!!
  VOLATILE                      39     39  100.0%   +46.0pp !!!
  INC_THEN_DEC                  99     99  100.0%   +46.0pp !!!
  INCREASING                   222    222  100.0%   +46.0pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   154    154  100.0%   +46.0pp !!!
  VOLATILE                      61     61  100.0%   +46.0pp !!!
  FLAT                          52     52  100.0%   +46.0pp !!!
  INCREASING                   201    201  100.0%   +46.0pp !!!
  DEC_THEN_INC                 178    178  100.0%   +46.0pp !!!
  INC_THEN_DEC                 122    122  100.0%   +46.0pp !!!

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                  39     39  100.0%   +46.0pp !!!
  DECREASING                   344    344  100.0%   +46.0pp !!!
  INC_THEN_DEC                  39     39  100.0%   +46.0pp !!!
  INCREASING                   303    303  100.0%   +46.0pp !!!
  FLAT                          33     33  100.0%   +46.0pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   306    306  100.0%   +46.0pp !!!
  INCREASING                   359    359  100.0%   +46.0pp !!!
  DEC_THEN_INC                  49     49  100.0%   +46.0pp !!!
  INC_THEN_DEC                  41     41  100.0%   +46.0pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   268    268  100.0%   +46.0pp !!!
  INCREASING                   341    341  100.0%   +46.0pp !!!
  INC_THEN_DEC                  65     65  100.0%   +46.0pp !!!
  FLAT                          29     29  100.0%   +46.0pp
  DEC_THEN_INC                  44     44  100.0%   +46.0pp !!!
  VOLATILE                      21     21  100.0%   +46.0pp

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         562    562  100.0%   +46.0pp !!!
  VOLATILE                      78     78  100.0%   +46.0pp !!!
  DEC_THEN_INC                  40     40  100.0%   +46.0pp !!!
  INC_THEN_DEC                  70     70  100.0%   +46.0pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         440    440  100.0%   +46.0pp !!!
  VOLATILE                     134    134  100.0%   +46.0pp !!!
  INC_THEN_DEC                  82     82  100.0%   +46.0pp !!!
  DEC_THEN_INC                  76     76  100.0%   +46.0pp !!!

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         470    470  100.0%   +46.0pp !!!
  VOLATILE                      87     87  100.0%   +46.0pp !!!
  DEC_THEN_INC                 114    114  100.0%   +46.0pp !!!
  INC_THEN_DEC                  65     65  100.0%   +46.0pp !!!

  --- SNAPSHOT AT EVENT ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPLOSIVE                    191    191  100.0%   +46.0pp !!!
  EXPANDING                    157    157  100.0%   +46.0pp !!!
  NORMAL                       243    243  100.0%   +46.0pp !!!
  COMPRESSED                   177    177  100.0%   +46.0pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_BUY                   271    271  100.0%   +46.0pp !!!
  STRONG_SELL                  217    217  100.0%   +46.0pp !!!
  MILD_BUY                     102    102  100.0%   +46.0pp !!!
  MILD_SELL                    178    178  100.0%   +46.0pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXTREME                      216    216  100.0%   +46.0pp !!!
  MODERATE                     174    174  100.0%   +46.0pp !!!
  ELEVATED                     183    183  100.0%   +46.0pp !!!
  LOW                          195    195  100.0%   +46.0pp !!!

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_RISING                199    199  100.0%   +46.0pp !!!
  STRONG_FALLING               180    180  100.0%   +46.0pp !!!
  MILD_FALLING                 166    166  100.0%   +46.0pp !!!
  MILD_RISING                  223    223  100.0%   +46.0pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NARROW_BULL                  112    112  100.0%   +46.0pp !!!
  WIDE_BEAR                    300    300  100.0%   +46.0pp !!!
  NARROW_BEAR                   89     89  100.0%   +46.0pp !!!
  WIDE_BULL                    267    267  100.0%   +46.0pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         245    245  100.0%   +46.0pp !!!
  WIDENING                     350    350  100.0%   +46.0pp !!!
  STRONG_WIDENING              173    173  100.0%   +46.0pp !!!

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     244    244  100.0%   +46.0pp !!!
  STRONG                       435    435  100.0%   +46.0pp !!!
  WEAK                          81     81  100.0%   +46.0pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  LOW                          360    360  100.0%   +46.0pp !!!
  MODERATE                     106    106  100.0%   +46.0pp !!!
  MINIMAL                      302    302  100.0%   +46.0pp !!!

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     111    111  100.0%   +46.0pp !!!
  LOW                          446    446  100.0%   +46.0pp !!!
  MINIMAL                      211    211  100.0%   +46.0pp !!!

================================================================================
SECTION 5.3: PATH TO EXIT - TRADES REACHING EXACTLY R3
  Trades: 446, Wins: 446, WR: 100.0% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES (ramp-up to event) ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  DECREASING         DECREASING         DECREASING           31  100.0%   +46.0pp !!!
  DECREASING         INCREASING         INCREASING           41  100.0%   +46.0pp !!!
  DEC_THEN_INC       DECREASING         DECREASING           29  100.0%   +46.0pp

  --- RAMP-UP TRENDS (15 M1 bars before event) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   142    142  100.0%   +46.0pp !!!
  INCREASING                    86     86  100.0%   +46.0pp !!!
  DEC_THEN_INC                  94     94  100.0%   +46.0pp !!!
  INC_THEN_DEC                  57     57  100.0%   +46.0pp !!!
  FLAT                          35     35  100.0%   +46.0pp !!!
  VOLATILE                      32     32  100.0%   +46.0pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          42     42  100.0%   +46.0pp !!!
  INCREASING                   134    134  100.0%   +46.0pp !!!
  DECREASING                   145    145  100.0%   +46.0pp !!!
  INC_THEN_DEC                  59     59  100.0%   +46.0pp !!!
  DEC_THEN_INC                  47     47  100.0%   +46.0pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   107    107  100.0%   +46.0pp !!!
  DEC_THEN_INC                  87     87  100.0%   +46.0pp !!!
  FLAT                          29     29  100.0%   +46.0pp
  INC_THEN_DEC                  72     72  100.0%   +46.0pp !!!
  INCREASING                   126    126  100.0%   +46.0pp !!!
  VOLATILE                      24     24  100.0%   +46.0pp

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                  28     28  100.0%   +46.0pp
  INCREASING                   166    166  100.0%   +46.0pp !!!
  DECREASING                   220    220  100.0%   +46.0pp !!!
  INC_THEN_DEC                  26     26  100.0%   +46.0pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   228    228  100.0%   +46.0pp !!!
  INCREASING                   170    170  100.0%   +46.0pp !!!
  DEC_THEN_INC                  28     28  100.0%   +46.0pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   163    163  100.0%   +46.0pp !!!
  INC_THEN_DEC                  36     36  100.0%   +46.0pp !!!
  INCREASING                   217    217  100.0%   +46.0pp !!!

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         336    336  100.0%   +46.0pp !!!
  INC_THEN_DEC                  44     44  100.0%   +46.0pp !!!
  VOLATILE                      21     21  100.0%   +46.0pp
  DEC_THEN_INC                  39     39  100.0%   +46.0pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         254    254  100.0%   +46.0pp !!!
  INC_THEN_DEC                  63     63  100.0%   +46.0pp !!!
  VOLATILE                      55     55  100.0%   +46.0pp !!!
  DEC_THEN_INC                  66     66  100.0%   +46.0pp !!!

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         263    263  100.0%   +46.0pp !!!
  DEC_THEN_INC                  65     65  100.0%   +46.0pp !!!
  INC_THEN_DEC                  63     63  100.0%   +46.0pp !!!
  VOLATILE                      43     43  100.0%   +46.0pp !!!

  --- SNAPSHOT AT EVENT ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPLOSIVE                     99     99  100.0%   +46.0pp !!!
  EXPANDING                    109    109  100.0%   +46.0pp !!!
  NORMAL                       151    151  100.0%   +46.0pp !!!
  COMPRESSED                    87     87  100.0%   +46.0pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_BUY                   116    116  100.0%   +46.0pp !!!
  STRONG_SELL                  190    190  100.0%   +46.0pp !!!
  MILD_SELL                     94     94  100.0%   +46.0pp !!!
  MILD_BUY                      46     46  100.0%   +46.0pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXTREME                      101    101  100.0%   +46.0pp !!!
  MODERATE                     121    121  100.0%   +46.0pp !!!
  LOW                           92     92  100.0%   +46.0pp !!!
  ELEVATED                     132    132  100.0%   +46.0pp !!!

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_RISING                 62     62  100.0%   +46.0pp !!!
  STRONG_FALLING               163    163  100.0%   +46.0pp !!!
  MILD_FALLING                 118    118  100.0%   +46.0pp !!!
  MILD_RISING                  103    103  100.0%   +46.0pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NARROW_BULL                   35     35  100.0%   +46.0pp !!!
  WIDE_BEAR                    219    219  100.0%   +46.0pp !!!
  WIDE_BULL                    150    150  100.0%   +46.0pp !!!
  NARROW_BEAR                   42     42  100.0%   +46.0pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         124    124  100.0%   +46.0pp !!!
  WIDENING                     219    219  100.0%   +46.0pp !!!
  STRONG_WIDENING              102    102  100.0%   +46.0pp !!!

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     137    137  100.0%   +46.0pp !!!
  STRONG                       278    278  100.0%   +46.0pp !!!
  WEAK                          31     31  100.0%   +46.0pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  LOW                          273    273  100.0%   +46.0pp !!!
  MINIMAL                      130    130  100.0%   +46.0pp !!!
  MODERATE                      43     43  100.0%   +46.0pp !!!

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                      30     30  100.0%   +46.0pp !!!
  LOW                          278    278  100.0%   +46.0pp !!!
  MINIMAL                      138    138  100.0%   +46.0pp !!!

================================================================================
SECTION 5.3+: PATH TO EXIT - TRADES REACHING R3 OR HIGHER
  Trades: 993, Wins: 993, WR: 100.0% (baseline: 54.0%)
================================================================================

  --- BEST COMPOSITE PROFILES (ramp-up to event) ---
  candle_range_pc    vol_delta          sma_spread            N      WR     Edge
  ------------------------------------------------------------------------------
  DECREASING         INCREASING         DECREASING           31  100.0%   +46.0pp !!!
  DEC_THEN_INC       INCREASING         DECREASING           42  100.0%   +46.0pp !!!
  INC_THEN_DEC       INCREASING         INCREASING           25  100.0%   +46.0pp
  DEC_THEN_INC       INC_THEN_DEC       DECREASING           24  100.0%   +46.0pp
  INCREASING         DECREASING         DECREASING           35  100.0%   +46.0pp !!!
  DECREASING         DECREASING         DECREASING           49  100.0%   +46.0pp !!!
  INCREASING         DEC_THEN_INC       INCREASING           33  100.0%   +46.0pp !!!
  DEC_THEN_INC       DECREASING         DECREASING           48  100.0%   +46.0pp !!!
  DECREASING         INCREASING         INCREASING           64  100.0%   +46.0pp !!!
  INCREASING         INC_THEN_DEC       INCREASING           21  100.0%   +46.0pp
  INCREASING         DECREASING         INCREASING           43  100.0%   +46.0pp !!!

  --- RAMP-UP TRENDS (15 M1 bars before event) ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   273    273  100.0%   +46.0pp !!!
  INCREASING                   218    218  100.0%   +46.0pp !!!
  DEC_THEN_INC                 211    211  100.0%   +46.0pp !!!
  INC_THEN_DEC                 126    126  100.0%   +46.0pp !!!
  FLAT                          90     90  100.0%   +46.0pp !!!
  VOLATILE                      75     75  100.0%   +46.0pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                          79     79  100.0%   +46.0pp !!!
  INCREASING                   292    292  100.0%   +46.0pp !!!
  DECREASING                   289    289  100.0%   +46.0pp !!!
  DEC_THEN_INC                 127    127  100.0%   +46.0pp !!!
  INC_THEN_DEC                 141    141  100.0%   +46.0pp !!!
  VOLATILE                      65     65  100.0%   +46.0pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   251    251  100.0%   +46.0pp !!!
  DEC_THEN_INC                 173    173  100.0%   +46.0pp !!!
  FLAT                          69     69  100.0%   +46.0pp !!!
  INC_THEN_DEC                 180    180  100.0%   +46.0pp !!!
  INCREASING                   267    267  100.0%   +46.0pp !!!
  VOLATILE                      52     52  100.0%   +46.0pp !!!

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DEC_THEN_INC                  76     76  100.0%   +46.0pp !!!
  INCREASING                   407    407  100.0%   +46.0pp !!!
  DECREASING                   405    405  100.0%   +46.0pp !!!
  INC_THEN_DEC                  68     68  100.0%   +46.0pp !!!
  VOLATILE                      23     23  100.0%   +46.0pp

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   447    447  100.0%   +46.0pp !!!
  INCREASING                   454    454  100.0%   +46.0pp !!!
  DEC_THEN_INC                  49     49  100.0%   +46.0pp !!!
  INC_THEN_DEC                  23     23  100.0%   +46.0pp

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  DECREASING                   386    386  100.0%   +46.0pp !!!
  INC_THEN_DEC                  74     74  100.0%   +46.0pp !!!
  INCREASING                   457    457  100.0%   +46.0pp !!!
  VOLATILE                      20     20  100.0%   +46.0pp
  DEC_THEN_INC                  49     49  100.0%   +46.0pp !!!

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         719    719  100.0%   +46.0pp !!!
  INCREASING                    25     25  100.0%   +46.0pp
  INC_THEN_DEC                  88     88  100.0%   +46.0pp !!!
  DEC_THEN_INC                  88     88  100.0%   +46.0pp !!!
  VOLATILE                      73     73  100.0%   +46.0pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         557    557  100.0%   +46.0pp !!!
  INC_THEN_DEC                 125    125  100.0%   +46.0pp !!!
  DEC_THEN_INC                 183    183  100.0%   +46.0pp !!!
  VOLATILE                      95     95  100.0%   +46.0pp !!!
  INCREASING                    21     21  100.0%   +46.0pp

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         552    552  100.0%   +46.0pp !!!
  DEC_THEN_INC                 172    172  100.0%   +46.0pp !!!
  INC_THEN_DEC                 125    125  100.0%   +46.0pp !!!
  VOLATILE                     114    114  100.0%   +46.0pp !!!
  INCREASING                    21     21  100.0%   +46.0pp

  --- SNAPSHOT AT EVENT ---

  candle_range_pct:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXPLOSIVE                    273    273  100.0%   +46.0pp !!!
  EXPANDING                    291    291  100.0%   +46.0pp !!!
  NORMAL                       280    280  100.0%   +46.0pp !!!
  COMPRESSED                   149    149  100.0%   +46.0pp !!!

  vol_delta:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_BUY                   353    353  100.0%   +46.0pp !!!
  STRONG_SELL                  389    389  100.0%   +46.0pp !!!
  MILD_SELL                    151    151  100.0%   +46.0pp !!!
  MILD_BUY                     100    100  100.0%   +46.0pp !!!

  vol_roc:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EXTREME                      246    246  100.0%   +46.0pp !!!
  MODERATE                     273    273  100.0%   +46.0pp !!!
  LOW                          213    213  100.0%   +46.0pp !!!
  ELEVATED                     261    261  100.0%   +46.0pp !!!

  cvd_slope:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG_RISING                251    251  100.0%   +46.0pp !!!
  STRONG_FALLING               328    328  100.0%   +46.0pp !!!
  MILD_FALLING                 237    237  100.0%   +46.0pp !!!
  MILD_RISING                  177    177  100.0%   +46.0pp !!!

  sma_spread:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NARROW_BULL                   88     88  100.0%   +46.0pp !!!
  WIDE_BEAR                    477    477  100.0%   +46.0pp !!!
  WIDE_BULL                    351    351  100.0%   +46.0pp !!!
  NARROW_BEAR                   77     77  100.0%   +46.0pp !!!

  sma_momentum_ratio:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  FLAT                         303    303  100.0%   +46.0pp !!!
  WIDENING                     470    470  100.0%   +46.0pp !!!
  STRONG_WIDENING              219    219  100.0%   +46.0pp !!!

  health_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     259    259  100.0%   +46.0pp !!!
  STRONG                       654    654  100.0%   +46.0pp !!!
  WEAK                          80     80  100.0%   +46.0pp !!!

  long_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  LOW                          598    598  100.0%   +46.0pp !!!
  MINIMAL                      231    231  100.0%   +46.0pp !!!
  MODERATE                     164    164  100.0%   +46.0pp !!!

  short_score:
  Signal                         N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  MODERATE                     169    169  100.0%   +46.0pp !!!
  LOW                          581    581  100.0%   +46.0pp !!!
  MINIMAL                      243    243  100.0%   +46.0pp !!!

================================================================================
END OF LIFECYCLE RAMP-UP REPORT
================================================================================

*** = edge >= 5pp with N >= 30
!!! = edge >= 10pp with N >= 30
Baseline WR: 54.0%
Win Condition: trades_m5_r_win.is_winner