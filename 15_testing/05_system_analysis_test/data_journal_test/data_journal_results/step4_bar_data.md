# Step 4: Bar Data Characteristics vs Outcomes
> Generated: 2026-03-11 10:06:50

Which observable market characteristics at screening time predict wins?

## 1. Data Shape

- **Bar Data Rows**: 500
- **Bar Data Days**: 43
- **Bar Data Tickers**: 13

- **Trades with Bar Data Match**: 3999

## 2. D1 ATR Ranges vs Outcomes

Do higher-ATR (more volatile) tickers produce better or worse results?

| ATR Range | Trades | Win Rate % | Avg R | Tickers |
| --------- | -----: | ---------: | ----: | ------: |
| $10+ ATR  | 1395   | 48.96      | 0.83  | 13      |
| $5-10 ATR | 2185   | 48.79      | 0.90  | 21      |
| $3-5 ATR  | 186    | 29.57      | 0.05  | 4       |
| $1-3 ATR  | 233    | 42.49      | 0.51  | 7       |

## 3. ATR as % of Price (Normalized Volatility)

Normalizes ATR by price so $5 stocks and $500 stocks are comparable.

| Volatility          | Trades | Win Rate % | Avg R |
| ------------------- | -----: | ---------: | ----: |
| 5%+ (Very High Vol) | 1530   | 42.22      | 0.64  |
| 3-5% (High Vol)     | 993    | 52.17      | 0.87  |
| 2-3% (Medium Vol)   | 539    | 40.45      | 0.47  |
| 1-2% (Normal Vol)   | 937    | 55.60      | 1.25  |

## 4. Overnight Range vs Outcomes

Does a wide overnight range (gap) predict better or worse intraday entries?

| Overnight Range     | Trades | Win Rate % | Avg R |
| ------------------- | -----: | ---------: | ----: |
| 1.5+ ATR (Wide Gap) | 404    | 39.36      | 0.43  |
| 1.0-1.5 ATR         | 100    | 63.00      | 1.93  |
| 0.5-1.0 ATR         | 976    | 47.75      | 1.05  |
| < 0.5 ATR (Tight)   | 2519   | 48.23      | 0.74  |

## 5. Price Level vs Outcomes

Do higher-priced or lower-priced stocks perform differently?

| Price Range | Trades | Win Rate % | Avg R | Tickers |
| ----------- | -----: | ---------: | ----: | ------: |
| $500+       | 739    | 61.16      | 1.41  | 5       |
| $200-500    | 2047   | 45.58      | 0.66  | 17      |
| $100-200    | 770    | 44.81      | 0.92  | 12      |
| $50-100     | 297    | 42.42      | 0.48  | 4       |
| $20-50      | 138    | 34.06      | 0.09  | 1       |
| < $20       | 8      | 0.00       | -1.00 | 1       |

## 6. Proximity to Prior Day Close

How far from prior day close was entry? (as % of ATR)

| Proximity to PDC   | Trades | Win Rate % | Avg R |
| ------------------ | -----: | ---------: | ----: |
| 2+ ATR from PDC    | 30     | 73.33      | 2.23  |
| 1-2 ATR from PDC   | 52     | 65.38      | 1.46  |
| 0.5-1 ATR from PDC | 516    | 54.84      | 1.24  |
| < 0.5 ATR from PDC | 3401   | 45.99      | 0.73  |

## 7. Your Final 4: Bar Data Profile vs Skipped

Did your selected tickers have different ATR/price/gap profiles?

| Selection  | Avg ATR | Avg Price | ATR % | O/N Range (ATR) | Trades | WR %  | Avg R |
| ---------- | ------: | --------: | ----: | --------------: | -----: | ----: | ----: |
| YOUR PICKS | 8.71    | 192.62    | 5.54  | 1.19            | 315    | 54.92 | 1.54  |
| SKIPPED    | 9.41    | 249.42    | 4.50  | 0.43            | 261    | 51.34 | 0.79  |

## 8. Key Findings

**Review the tables above to answer:**
1. Is there an ATR sweet spot? (too low = no movement, too high = noise)
2. Does overnight gap size help or hurt?
3. Do certain price ranges consistently outperform?
4. Does proximity to prior day close matter?
5. What bar data characteristics should become screener filters?

**Metrics Worth Persisting (if they show edge):**
- D1 ATR % of price (normalized volatility)
- Overnight range as ATR multiple
- Distance from prior day close as ATR multiple
- Price level bucket

---
