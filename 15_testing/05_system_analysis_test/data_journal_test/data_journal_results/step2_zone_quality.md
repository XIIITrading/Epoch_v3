# Step 2: Zone Quality vs Outcomes
> Generated: 2026-03-11 10:06:42

Do higher-quality zones predict better trade outcomes?

## 1. Data Shape

- **Total Zones**: 468
- **Zone Days**: 47
- **Zone Tickers**: 96
- **Zone Date Range**: 2025-12-15 to 2026-03-11

- **Trades with Zone Match**: 905 / 3999

## 2. Win Rate by Zone Tier

Zones are classified T3 (institutional/L4-L5), T2 (medium/L3), T1 (lower/L1-L2).
Does T3 actually outperform T1?

| Tier               | Trades | Win Rate % | Avg R | Zones |
| ------------------ | -----: | ---------: | ----: | ----: |
| T3 (Institutional) | 226    | 52.65      | 0.97  | 6     |
| T2 (Medium)        | 376    | 45.48      | 0.73  | 9     |
| T1 (Lower)         | 303    | 25.08      | -0.10 | 5     |

## 3. Win Rate by Zone Rank

Ranks: L5 (>=12.0 score), L4 (>=9.0), L3 (>=6.0), L2 (>=3.0), L1 (<3.0)

| Rank | Trades | Win Rate % | Avg R |
| ---- | -----: | ---------: | ----: |
| L1   | 10     | 100.00     | 2.90  |
| L2   | 293    | 22.53      | -0.20 |
| L3   | 376    | 45.48      | 0.73  |
| L4   | 123    | 59.35      | 0.80  |
| L5   | 103    | 44.66      | 1.18  |

## 4. Win Rate by Overlap Count (Confluence Density)

Does more confluence (more technical levels inside the zone) predict wins?

| Overlaps | Trades | Win Rate % | Avg R |
| -------: | -----: | ---------: | ----: |
| 1        | 10     | 100.00     | 2.90  |
| 2        | 176    | 17.05      | -0.57 |
| 4        | 114    | 38.60      | 0.37  |
| 5        | 170    | 44.71      | 0.29  |
| 6        | 223    | 44.84      | 0.83  |
| 7        | 106    | 55.66      | 1.80  |
| 8        | 14     | 42.86      | 0.21  |
| 9        | 49     | 26.53      | 0.00  |
| 10       | 14     | 35.71      | -0.29 |
| 11       | 29     | 79.31      | 2.45  |

## 5. Win Rate by Zone Score Ranges

| Score Range | Trades | Win Rate % | Avg R | Avg Score |
| ----------- | -----: | ---------: | ----: | --------: |
| 12+ (L5)    | 103    | 44.66      | 1.18  | 12.78     |
| 9-12 (L4)   | 123    | 59.35      | 0.80  | 10.30     |
| 6-9 (L3)    | 376    | 45.48      | 0.73  | 7.59      |
| 3-6 (L2)    | 293    | 22.53      | -0.20 | 4.33      |
| 0-3 (L1)    | 10     | 100.00     | 2.90  | 2.40      |

## 6. Confluence Type Analysis

Which confluence types appear in winning vs losing trade zones?
(Parsing the confluences text field for pattern matching)

- **Zones with Confluences Data**: 429

### Zones with Options Confluence

| Options    | Trades | Win Rate % | Avg R |
| ---------- | -----: | ---------: | ----: |
| No Options | 905    | 40.44      | 0.51  |

### Zones with Camarilla Monthly Confluence

| Cam Monthly    | Trades | Win Rate % | Avg R |
| -------------- | -----: | ---------: | ----: |
| No Cam Monthly | 905    | 40.44      | 0.51  |

### Zones with Structure Level Confluence

| Structure     | Trades | Win Rate % | Avg R |
| ------------- | -----: | ---------: | ----: |
| Has Structure | 302    | 46.36      | 0.94  |
| No Structure  | 603    | 37.48      | 0.30  |

## 7. Zone Quality: Your Final 4 vs Skipped Tickers

Did your selected tickers have higher-quality zones than the ones you skipped?

| Selection | Avg Score | Avg Overlaps | Trades | Win Rate % | Avg R |
| --------- | --------: | -----------: | -----: | ---------: | ----: |
| SKIPPED   | 7.56      | 4.63         | 62     | 58.06      | 0.81  |

## 8. Key Findings

Summary of zone quality impact on trade outcomes:

**Review the tables above to answer:**
1. Do T3 zones win more than T1 zones? By how much?
2. Does overlap count (confluence density) linearly predict win rate?
3. Is there a score threshold below which zones should be filtered out?
4. Do options confluences add edge?
5. Did your picks have objectively better zone quality than skipped tickers?

---
