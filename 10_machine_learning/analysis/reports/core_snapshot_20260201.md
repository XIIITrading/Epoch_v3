================================================================================
EPOCH ML - CORE SNAPSHOT REPORT
Generated: 2026-02-01 14:36
Source: entry_indicators + trades_m5_r_win
Win Condition: trades_m5_r_win.is_winner (M5 ATR(14) x 1.1, close-based)
================================================================================

--------------------------------------------------------------------------------
SECTION 1: BASELINE
--------------------------------------------------------------------------------
  Total Trades: 5922
  Total Wins:   3199
  Baseline WR:  54.0%

--------------------------------------------------------------------------------
SECTION 2: ENTRY INDICATOR VALUES (snapshot at entry)
--------------------------------------------------------------------------------

  H4 Structure (h4_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NEUTRAL                     5886   3184   54.1%    +0.1pp

  H1 Structure (h1_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BEAR                         856    514   60.0%    +6.0pp ***
  BULL                         884    471   53.3%    -0.7pp
  NEUTRAL                     4146   2199   53.0%    -1.0pp

  M15 Structure (m15_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                        1958   1161   59.3%    +5.3pp ***
  NEUTRAL                     2168   1200   55.4%    +1.3pp
  BEAR                        1760    823   46.8%    -7.3pp ***

  M5 Structure (m5_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                        1948   1089   55.9%    +1.9pp
  NEUTRAL                     1519    838   55.2%    +1.1pp
  BEAR                        2419   1257   52.0%    -2.1pp

  SMA Alignment (sma_alignment):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BEAR                        3076   1795   58.4%    +4.3pp
  BULL                        2810   1389   49.4%    -4.6pp

  SMA Momentum (sma_momentum_label):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDENING                    3009   1713   56.9%    +2.9pp
  STABLE                       336    176   52.4%    -1.6pp
  NARROWING                   2495   1281   51.3%    -2.7pp

  VWAP Position (vwap_position):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BELOW                       3280   1799   54.8%    +0.8pp
  ABOVE                       2586   1375   53.2%    -0.8pp
  AT                            20     10   50.0%    -4.0pp

  Continuation Score Tier:
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STRONG (8-10)                 70     46   65.7%   +11.7pp !!!
  MODERATE (6-7)              1209    754   62.4%    +8.3pp ***
  CRITICAL (0-3)              2662   1401   52.6%    -1.4pp
  WEAK (4-5)                  1981    998   50.4%    -3.6pp

  Stop Distance:
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  TIGHT (<0.12%%)              317    196   61.8%    +7.8pp ***
  VERY WIDE (>=0.50%%)        2156   1208   56.0%    +2.0pp
  WIDE (0.25-0.50%%)          2077   1082   52.1%    -1.9pp
  NORMAL (0.12-0.25%%)        1372    713   52.0%    -2.1pp

  Direction (direction):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  SHORT                       3095   1719   55.5%    +1.5pp
  LONG                        2827   1480   52.4%    -1.7pp

  Entry Model (model):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  EPCH2                       2875   1580   55.0%    +0.9pp
  EPCH4                       2543   1357   53.4%    -0.7pp
  EPCH3                        232    123   53.0%    -1.0pp
  EPCH1                        272    139   51.1%    -2.9pp

  Zone Type (zone_type):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  PRIMARY                     3147   1719   54.6%    +0.6pp
  SECONDARY                   2775   1480   53.3%    -0.7pp

--------------------------------------------------------------------------------
SECTION 3: DIRECTION BREAKDOWN
--------------------------------------------------------------------------------

  === LONG TRADES ===

  H4 Structure (h4_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NEUTRAL                     2809   1478   52.6%    -1.4pp

  H1 Structure (h1_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BEAR                         372    203   54.6%    +0.6pp
  BULL                         537    291   54.2%    +0.2pp
  NEUTRAL                     1900    984   51.8%    -2.2pp

  M15 Structure (m15_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                         958    551   57.5%    +3.5pp
  NEUTRAL                     1035    547   52.9%    -1.2pp
  BEAR                         816    380   46.6%    -7.5pp ***

  M5 Structure (m5_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                         948    539   56.9%    +2.8pp
  NEUTRAL                      795    427   53.7%    -0.3pp
  BEAR                        1066    512   48.0%    -6.0pp ***

  SMA Alignment (sma_alignment):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BEAR                        1361    744   54.7%    +0.6pp
  BULL                        1448    734   50.7%    -3.3pp

  SMA Momentum (sma_momentum_label):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDENING                    1414    778   55.0%    +1.0pp
  NARROWING                   1200    613   51.1%    -2.9pp
  STABLE                       162     79   48.8%    -5.3pp ***

  VWAP Position (vwap_position):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BELOW                       1358    765   56.3%    +2.3pp
  AT                             8      4   50.0%    -4.0pp
  ABOVE                       1443    709   49.1%    -4.9pp

  === SHORT TRADES ===

  H4 Structure (h4_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NEUTRAL                     3077   1706   55.4%    +1.4pp

  H1 Structure (h1_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BEAR                         484    311   64.3%   +10.2pp !!!
  NEUTRAL                     2246   1215   54.1%    +0.1pp
  BULL                         347    180   51.9%    -2.1pp

  M15 Structure (m15_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                        1000    610   61.0%    +7.0pp ***
  NEUTRAL                     1133    653   57.6%    +3.6pp
  BEAR                         944    443   46.9%    -7.1pp ***

  M5 Structure (m5_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NEUTRAL                      724    411   56.8%    +2.7pp
  BEAR                        1353    745   55.1%    +1.0pp
  BULL                        1000    550   55.0%    +1.0pp

  SMA Alignment (sma_alignment):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BEAR                        1715   1051   61.3%    +7.3pp ***
  BULL                        1362    655   48.1%    -5.9pp ***

  SMA Momentum (sma_momentum_label):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDENING                    1595    935   58.6%    +4.6pp
  STABLE                       174     97   55.7%    +1.7pp
  NARROWING                   1295    668   51.6%    -2.4pp

  VWAP Position (vwap_position):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  ABOVE                       1143    666   58.3%    +4.2pp
  BELOW                       1922   1034   53.8%    -0.2pp
  AT                            12      6   50.0%    -4.0pp

--------------------------------------------------------------------------------
SECTION 4: MODEL BREAKDOWN (EPCH1-4)
--------------------------------------------------------------------------------

  === EPCH1 ===

  H4 Structure (h4_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NEUTRAL                      265    135   50.9%    -3.1pp

  H1 Structure (h1_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BEAR                          17     13   76.5%   +22.5pp
  NEUTRAL                      225    112   49.8%    -4.2pp
  BULL                          23     10   43.5%   -10.5pp

  M15 Structure (m15_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                          70     37   52.9%    -1.2pp
  NEUTRAL                      139     71   51.1%    -2.9pp
  BEAR                          56     27   48.2%    -5.8pp ***

  M5 Structure (m5_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NEUTRAL                       88     49   55.7%    +1.7pp
  BEAR                          81     42   51.9%    -2.2pp
  BULL                          96     44   45.8%    -8.2pp ***

  SMA Alignment (sma_alignment):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                         122     63   51.6%    -2.4pp
  BEAR                         143     72   50.3%    -3.7pp

  SMA Momentum (sma_momentum_label):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDENING                     138     72   52.2%    -1.8pp
  NARROWING                    104     53   51.0%    -3.1pp
  STABLE                        18      9   50.0%    -4.0pp

  VWAP Position (vwap_position):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BELOW                        135     72   53.3%    -0.7pp
  ABOVE                        129     63   48.8%    -5.2pp ***
  AT                             1      0    0.0%   -54.0pp

  === EPCH2 ===

  H4 Structure (h4_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NEUTRAL                     2855   1572   55.1%    +1.0pp

  H1 Structure (h1_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BEAR                         502    332   66.1%   +12.1pp !!!
  NEUTRAL                     1977   1049   53.1%    -1.0pp
  BULL                         376    191   50.8%    -3.2pp

  M15 Structure (m15_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                        1064    634   59.6%    +5.6pp ***
  NEUTRAL                      916    515   56.2%    +2.2pp
  BEAR                         875    423   48.3%    -5.7pp ***

  M5 Structure (m5_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NEUTRAL                      676    380   56.2%    +2.2pp
  BEAR                        1227    677   55.2%    +1.2pp
  BULL                         952    515   54.1%    +0.1pp

  SMA Alignment (sma_alignment):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BEAR                        1536    908   59.1%    +5.1pp ***
  BULL                        1319    664   50.3%    -3.7pp

  SMA Momentum (sma_momentum_label):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDENING                    1416    836   59.0%    +5.0pp ***
  STABLE                       161     86   53.4%    -0.6pp
  NARROWING                   1259    645   51.2%    -2.8pp

  VWAP Position (vwap_position):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BELOW                       1539    873   56.7%    +2.7pp
  AT                            11      6   54.5%    +0.5pp
  ABOVE                       1305    693   53.1%    -0.9pp

  === EPCH3 ===

  H4 Structure (h4_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NEUTRAL                      231    123   53.2%    -0.8pp

  H1 Structure (h1_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                          26     17   65.4%   +11.4pp
  NEUTRAL                      195    103   52.8%    -1.2pp
  BEAR                          10      3   30.0%   -24.0pp

  M15 Structure (m15_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                          52     32   61.5%    +7.5pp ***
  NEUTRAL                      138     76   55.1%    +1.1pp
  BEAR                          41     15   36.6%   -17.4pp !!!

  M5 Structure (m5_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                          64     38   59.4%    +5.4pp ***
  NEUTRAL                       99     53   53.5%    -0.5pp
  BEAR                          68     32   47.1%    -7.0pp ***

  SMA Alignment (sma_alignment):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                         117     63   53.8%    -0.2pp
  BEAR                         114     60   52.6%    -1.4pp

  SMA Momentum (sma_momentum_label):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  STABLE                        14      8   57.1%    +3.1pp
  WIDENING                     123     68   55.3%    +1.3pp
  NARROWING                     92     46   50.0%    -4.0pp

  VWAP Position (vwap_position):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BELOW                        124     70   56.5%    +2.4pp
  ABOVE                        107     53   49.5%    -4.5pp

  === EPCH4 ===

  H4 Structure (h4_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  NEUTRAL                     2535   1354   53.4%    -0.6pp

  H1 Structure (h1_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                         459    253   55.1%    +1.1pp
  NEUTRAL                     1749    935   53.5%    -0.6pp
  BEAR                         327    166   50.8%    -3.3pp

  M15 Structure (m15_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                         772    458   59.3%    +5.3pp ***
  NEUTRAL                      975    538   55.2%    +1.2pp
  BEAR                         788    358   45.4%    -8.6pp ***

  M5 Structure (m5_structure):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BULL                         836    492   58.9%    +4.8pp
  NEUTRAL                      656    356   54.3%    +0.2pp
  BEAR                        1043    506   48.5%    -5.5pp ***

  SMA Alignment (sma_alignment):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  BEAR                        1283    755   58.8%    +4.8pp
  BULL                        1252    599   47.8%    -6.2pp ***

  SMA Momentum (sma_momentum_label):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  WIDENING                    1332    737   55.3%    +1.3pp
  NARROWING                   1040    537   51.6%    -2.4pp
  STABLE                       143     73   51.0%    -3.0pp

  VWAP Position (vwap_position):
  Value                          N   Wins      WR     Edge
  ------------------------- ------ ------ ------- --------
  ABOVE                       1045    566   54.2%    +0.1pp
  BELOW                       1482    784   52.9%    -1.1pp
  AT                             8      4   50.0%    -4.0pp

--------------------------------------------------------------------------------
SECTION 5: TOP COMPOSITE PROFILES (M15 + SMA Alignment + Health Tier)
--------------------------------------------------------------------------------

  M15        SMA Align    Health          N   Wins      WR     Edge
  ---------- ------------ ---------- ------ ------ ------- --------
  BEAR       BEAR         STRONG         30     27   90.0%   +36.0pp !!!
  NEUTRAL    BEAR         MODERATE      214    155   72.4%   +18.4pp !!!
  BULL       BEAR         MODERATE      172    119   69.2%   +15.2pp !!!
  BULL       BULL         CRITICAL      427    283   66.3%   +12.3pp !!!
  NEUTRAL    BULL         MODERATE      178    111   62.4%    +8.3pp ***
  BEAR       BEAR         CRITICAL      417    257   61.6%    +7.6pp ***
  NEUTRAL    BEAR         WEAK          361    222   61.5%    +7.5pp ***
  BULL       BEAR         WEAK          401    245   61.1%    +7.1pp ***
  BEAR       BEAR         MODERATE      300    179   59.7%    +5.6pp ***
  BULL       BULL         WEAK          214    126   58.9%    +4.9pp
  BULL       BULL         MODERATE      275    158   57.5%    +3.4pp
  NEUTRAL    BEAR         CRITICAL      554    296   53.4%    -0.6pp
  BULL       BEAR         CRITICAL      429    211   49.2%    -4.8pp
  NEUTRAL    BULL         CRITICAL      458    223   48.7%    -5.3pp ***
  NEUTRAL    BULL         WEAK          403    193   47.9%    -6.1pp ***
  BULL       BULL         STRONG         37     17   45.9%    -8.1pp ***
  BEAR       BULL         MODERATE       70     32   45.7%    -8.3pp ***
  BEAR       BEAR         WEAK          195     82   42.1%   -12.0pp !!!
  BEAR       BULL         CRITICAL      341    116   34.0%   -20.0pp !!!
  BEAR       BULL         WEAK          407    130   31.9%   -22.1pp !!!

================================================================================
END OF CORE SNAPSHOT REPORT
================================================================================

*** = edge >= 5pp with N >= 30
!!! = edge >= 10pp with N >= 30
Baseline WR: 54.0%
Win Condition: trades_m5_r_win.is_winner