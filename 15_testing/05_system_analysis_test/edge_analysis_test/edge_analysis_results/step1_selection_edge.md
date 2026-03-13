# Step 1: Selection Edge Analysis
> Generated: 2026-03-11 08:44:46

Do your manually selected tickers show edge? Does down-selecting to 4 improve it?

## 1. Data Shape

- **Date Range**: 2026-02-09 to 2026-03-10
- **Trading Days**: 10
- **Total Trades**: 3999
- **Unique Tickers**: 38

- **Ticker Analysis Rows**: 16
- **Ticker Analysis Days**: 4
- **Ticker Analysis Tickers**: 11
- **Ticker Analysis Range**: 2026-02-26 to 2026-03-11

- **Overlapping Days (trades + selections)**: 2

## 2. Tier A: Full Universe Baseline

- **Total Trades**: 3999
- **Wins / Losses**: 1903 / 2096
- **Win Rate**: 47.59%
- **Avg Max R**: 0.82

### By Model

| Model | Trades | Win Rate % | Avg R |
| ----- | -----: | ---------: | ----: |
| EPCH1 | 120    | 49.17      | 0.84  |
| EPCH2 | 1503   | 45.64      | 0.68  |
| EPCH3 | 186    | 47.31      | 0.89  |
| EPCH4 | 2190   | 48.86      | 0.90  |

### By Direction

| Direction | Trades | Win Rate % | Avg R |
| --------- | -----: | ---------: | ----: |
| LONG      | 2226   | 47.57      | 0.85  |
| SHORT     | 1773   | 47.60      | 0.77  |

### By Zone Type

| Zone Type | Trades | Win Rate % | Avg R |
| --------- | -----: | ---------: | ----: |
| PRIMARY   | 1623   | 45.90      | 0.69  |
| SECONDARY | 2376   | 48.74      | 0.90  |

### By Entry Hour

| Hour  | Trades | Win Rate % | Avg R |
| ----- | -----: | ---------: | ----: |
| 09:00 | 1044   | 54.50      | 1.11  |
| 10:00 | 928    | 46.34      | 0.70  |
| 11:00 | 575    | 51.13      | 1.10  |
| 12:00 | 441    | 46.71      | 0.85  |
| 13:00 | 354    | 44.92      | 0.50  |
| 14:00 | 428    | 48.36      | 0.76  |
| 15:00 | 229    | 16.59      | -0.29 |

### Index vs Custom

| Group  | Trades | Win Rate % | Avg R | Tickers |
| ------ | -----: | ---------: | ----: | ------: |
| CUSTOM | 3012   | 44.75      | 0.66  | 35      |
| INDEX  | 987    | 56.23      | 1.29  | 3       |

## 3. All Tickers Ranked by Trade Count

| Ticker | Type   | Trades | Win Rate % | Avg R |
| ------ | ------ | -----: | ---------: | ----: |
| QQQ    | INDEX  | 431    | 59.63      | 1.55  |
| DIA    | INDEX  | 370    | 47.57      | 1.01  |
| MU     | CUSTOM | 345    | 44.93      | 0.67  |
| TSLA   | CUSTOM | 305    | 46.89      | 0.41  |
| HOOD   | CUSTOM | 215    | 34.42      | 0.11  |
| AMD    | CUSTOM | 212    | 59.43      | 1.61  |
| COIN   | CUSTOM | 210    | 20.00      | -0.37 |
| GOOGL  | CUSTOM | 206    | 60.68      | 1.29  |
| PLTR   | CUSTOM | 200    | 47.50      | 0.82  |
| SPY    | INDEX  | 186    | 65.59      | 1.25  |
| AVGO   | CUSTOM | 166    | 37.35      | 0.28  |
| HIMS   | CUSTOM | 138    | 34.06      | 0.09  |
| MSTR   | CUSTOM | 120    | 55.00      | 1.63  |
| MSFT   | CUSTOM | 116    | 44.83      | 0.09  |
| AAPL   | CUSTOM | 103    | 33.98      | 0.39  |
| RTX    | CUSTOM | 90     | 4.44       | -0.91 |
| UNH    | CUSTOM | 84     | 38.10      | 0.32  |
| ORCL   | CUSTOM | 63     | 57.14      | 1.54  |
| JPM    | CUSTOM | 50     | 62.00      | 1.64  |
| EXPE   | CUSTOM | 46     | 43.48      | 0.33  |
| CSCO   | CUSTOM | 43     | 48.84      | 0.86  |
| ANET   | CUSTOM | 36     | 77.78      | 1.86  |
| META   | CUSTOM | 31     | 54.84      | 1.16  |
| PWR    | CUSTOM | 30     | 46.67      | 0.67  |
| DPZ    | CUSTOM | 29     | 72.41      | 2.14  |
| NVDA   | CUSTOM | 26     | 34.62      | 0.08  |
| ROKU   | CUSTOM | 23     | 60.87      | 1.78  |
| AAP    | CUSTOM | 22     | 90.91      | 2.55  |
| TMUS   | CUSTOM | 19     | 57.89      | 2.00  |
| GOOG   | CUSTOM | 18     | 55.56      | 0.78  |
| NFLX   | CUSTOM | 17     | 64.71      | 1.59  |
| AMZN   | CUSTOM | 14     | 85.71      | 3.07  |
| BIO    | CUSTOM | 11     | 72.73      | 1.18  |
| WYNN   | CUSTOM | 10     | 60.00      | 2.40  |
| SOFI   | CUSTOM | 8      | 0.00       | -1.00 |
| DIS    | CUSTOM | 4      | 0.00       | -1.00 |
| DHR    | CUSTOM | 1      | 100.00     | 5.00  |
| ABT    | CUSTOM | 1      | 0.00       | -1.00 |

## 4. Tier B: Your 10 Custom Picks (Non-Index)

- **Trades**: 3012
- **Wins**: 1348
- **Win Rate**: 44.75%
- **Avg Max R**: 0.66
- **Unique Tickers**: 35
- **Trading Days**: 10

### Tier B by Model

| Model | Trades | Win Rate % | Avg R |
| ----- | -----: | ---------: | ----: |
| EPCH1 | 104    | 48.08      | 0.76  |
| EPCH2 | 1229   | 42.72      | 0.45  |
| EPCH3 | 146    | 44.52      | 0.67  |
| EPCH4 | 1533   | 46.18      | 0.82  |

### Tier B by Zone Type

| Zone Type | Trades | Win Rate % | Avg R |
| --------- | -----: | ---------: | ----: |
| PRIMARY   | 1333   | 43.14      | 0.48  |
| SECONDARY | 1679   | 46.04      | 0.81  |

### Daily Breakdown: Index vs Custom

| Date       | Group  | Trades | Win Rate % | Avg R |
| ---------- | ------ | -----: | ---------: | ----: |
| 2026-02-09 | CUSTOM | 230    | 56.52      | 0.93  |
| 2026-02-09 | INDEX  | 84     | 59.52      | 1.85  |
| 2026-02-12 | CUSTOM | 249    | 64.66      | 2.07  |
| 2026-02-12 | INDEX  | 85     | 76.47      | 1.75  |
| 2026-02-13 | CUSTOM | 394    | 41.88      | 0.60  |
| 2026-02-13 | INDEX  | 85     | 54.12      | 1.34  |
| 2026-02-17 | CUSTOM | 336    | 37.80      | 0.20  |
| 2026-02-17 | INDEX  | 166    | 49.40      | 0.48  |
| 2026-02-18 | CUSTOM | 320    | 27.50      | 0.08  |
| 2026-02-18 | INDEX  | 71     | 64.79      | 2.38  |
| 2026-02-19 | CUSTOM | 295    | 35.93      | 0.20  |
| 2026-02-19 | INDEX  | 114    | 59.65      | 0.75  |
| 2026-02-23 | CUSTOM | 252    | 47.62      | 0.51  |
| 2026-02-23 | INDEX  | 56     | 41.07      | 0.77  |
| 2026-02-26 | CUSTOM | 249    | 56.22      | 0.81  |
| 2026-02-26 | INDEX  | 66     | 42.42      | 0.68  |
| 2026-03-09 | CUSTOM | 327    | 51.07      | 1.50  |
| 2026-03-09 | INDEX  | 157    | 71.34      | 2.38  |
| 2026-03-10 | CUSTOM | 360    | 40.00      | 0.14  |
| 2026-03-10 | INDEX  | 103    | 33.98      | 0.60  |

## 5. Tier C: Your Final 4 Down-Selections

### All Selections with Trade Matches

| Date       | Ticker | Direction | Trades | Win Rate % | Avg R | Verdict   |
| ---------- | ------ | --------- | -----: | ---------: | ----: | --------- |
| 2026-02-26 | AMD    | BEAR      | 5      | 100.00     | 3.40  | STRONG    |
| 2026-02-26 | AMZN   | BULL      | 14     | 85.71      | 3.07  | STRONG    |
| 2026-02-26 | NVDA   | BULL      | 0      | N/A        | N/A   | NO TRADES |
| 2026-02-26 | TSLA   | BEAR      | 48     | 52.08      | 0.15  | OK        |
| 2026-02-27 | COIN   | BULL      | 0      | N/A        | N/A   | NO TRADES |
| 2026-02-27 | MARA   | BULL      | 0      | N/A        | N/A   | NO TRADES |
| 2026-02-27 | MU     | BULL      | 0      | N/A        | N/A   | NO TRADES |
| 2026-02-27 | NVDA   | BEAR      | 0      | N/A        | N/A   | NO TRADES |
| 2026-03-09 | AMD    | BEAR      | 76     | 63.16      | 2.58  | STRONG    |
| 2026-03-09 | GOOGL  | BEAR      | 28     | 85.71      | 4.11  | STRONG    |
| 2026-03-09 | HIMS   | BEAR      | 112    | 31.25      | 0.06  | WEAK      |
| 2026-03-09 | MU     | BEAR      | 32     | 75.00      | 3.09  | STRONG    |
| 2026-03-11 | AMD    | BULL      | 0      | N/A        | N/A   | NO TRADES |
| 2026-03-11 | MU     | BEAR      | 0      | N/A        | N/A   | NO TRADES |
| 2026-03-11 | ORCL   | BULL      | 0      | N/A        | N/A   | NO TRADES |
| 2026-03-11 | PLTR   | BEAR      | 0      | N/A        | N/A   | NO TRADES |

### Tier C Aggregate

- **Trades**: 315
- **Wins**: 173
- **Win Rate**: 54.92%
- **Avg Max R**: 1.54
- **Unique Tickers**: 6
- **Days with Data**: 2

### Tier C by Model

| Model | Trades | Win Rate % | Avg R |
| ----- | -----: | ---------: | ----: |
| EPCH1 | 9      | 66.67      | 1.78  |
| EPCH2 | 88     | 57.95      | 1.26  |
| EPCH3 | 26     | 34.62      | 0.35  |
| EPCH4 | 192    | 55.73      | 1.81  |

### Tier C by Zone Type

| Zone Type | Trades | Win Rate % | Avg R |
| --------- | -----: | ---------: | ----: |
| PRIMARY   | 97     | 58.76      | 1.31  |
| SECONDARY | 218    | 53.21      | 1.64  |

## 6. Same-Day Tier Comparison

Comparing tiers ONLY on days where Tier C selections exist (apples to apples).

| Tier              | Trades | Win Rate % | Avg R | Edge vs A |
| ----------------- | -----: | ---------: | ----: | --------: |
| A: Full Universe  | 799    | 55.94      | 1.39  | --        |
| B: Your 10 Custom | 576    | 53.30      | 1.20  | -2.64pp   |
| C: Your Final 4   | 315    | 54.92      | 1.54  | -1.02pp   |
| IDX: SPY/QQQ/DIA  | 223    | 62.78      | 1.87  | +6.84pp   |

## 7. Your Picks vs What You Skipped (Custom Only, Same Days)

| Selection  | Trades | Win Rate % | Avg R | Tickers |
| ---------- | -----: | ---------: | ----: | ------: |
| YOUR PICKS | 315    | 54.92      | 1.54  | 6       |
| SKIPPED    | 261    | 51.34      | 0.79  | 9       |

### Tickers You Left on the Table (Detail)

| Date       | Ticker | Trades | Win Rate % | Avg R | Verdict |
| ---------- | ------ | -----: | ---------: | ----: | ------- |
| 2026-02-26 | PLTR   | 57     | 71.93      | 1.16  | STRONG  |
| 2026-02-26 | MSFT   | 27     | 70.37      | 0.67  | STRONG  |
| 2026-02-26 | NFLX   | 17     | 64.71      | 1.59  | STRONG  |
| 2026-02-26 | META   | 31     | 54.84      | 1.16  | OK      |
| 2026-02-26 | MSTR   | 50     | 20.00      | -0.26 | WEAK    |
| 2026-03-09 | TSLA   | 4      | 100.00     | 3.00  | STRONG  |
| 2026-03-09 | JPM    | 50     | 62.00      | 1.64  | STRONG  |
| 2026-03-09 | PLTR   | 13     | 7.69       | -0.69 | WEAK    |
| 2026-03-09 | SOFI   | 8      | 0.00       | -1.00 | WEAK    |
| 2026-03-09 | DIS    | 4      | 0.00       | -1.00 | WEAK    |

## 8. Key Findings

1. **Full Universe Baseline**: 47.59% WR, 0.82 avg R across 3999 trades
2. **Your 10 Custom Picks (Tier B)**: 44.75% WR (-2.84pp vs baseline), 0.66 avg R
3. **Your Final 4 (Tier C)**: 54.92% WR (+7.33pp vs baseline), 1.54 avg R
4. **Down-Selection Edge (C vs B)**: +10.17pp win rate, +0.88 avg R

**CONCLUSION**: Your down-selection from 10 to 4 ADDS edge. Your judgment is filtering signal from noise.

**CAVEAT**: Only 2 overlapping day(s) with both selections and backtest data. These findings need more data to confirm. Keep saving daily selections to build the dataset.

---

*Analysis covers 10 trading days from 2026-02-09 to 2026-03-10*