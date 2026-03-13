# Step 3: Market Structure vs Outcomes
> Generated: 2026-03-11 10:06:47

Does market structure alignment predict trade outcomes?

## 1. Data Shape

- **Setup Rows**: 1014
- **Setup Days**: 47
- **Setup Tickers**: 83

- **Trades with Setup Match**: 3999

## 2. Win Rate by Setup Direction

| Direction | Trades | Win Rate % | Avg R |
| --------- | -----: | ---------: | ----: |
| Bear      | 1929   | 46.03      | 0.73  |
| Bull      | 2070   | 49.03      | 0.89  |

## 3. Trade Direction vs Setup Direction (Alignment)

Does trading WITH the setup direction outperform counter-direction?

| Alignment | Trades | Win Rate % | Avg R |
| --------- | -----: | ---------: | ----: |
| COUNTER   | 3999   | 47.59      | 0.82  |

## 4. Primary (With-Trend) vs Secondary (Counter-Trend)

| Zone Type | Trades | Win Rate % | Avg R |
| --------- | -----: | ---------: | ----: |
| PRIMARY   | 1623   | 45.90      | 0.69  |
| SECONDARY | 2376   | 48.74      | 0.90  |

## 5. Direction x Model Performance Matrix

Which direction + entry model combinations work best?

| Direction | Model | Trades | Win Rate % | Avg R |
| --------- | ----- | -----: | ---------: | ----: |
| LONG      | EPCH1 | 61     | 45.90      | 0.89  |
| LONG      | EPCH2 | 817    | 44.68      | 0.78  |
| LONG      | EPCH3 | 97     | 50.52      | 0.95  |
| LONG      | EPCH4 | 1251   | 49.32      | 0.88  |
| SHORT     | EPCH1 | 59     | 52.54      | 0.80  |
| SHORT     | EPCH2 | 686    | 46.79      | 0.55  |
| SHORT     | EPCH3 | 89     | 43.82      | 0.82  |
| SHORT     | EPCH4 | 939    | 48.24      | 0.93  |

## 6. Zone Type x Model Performance Matrix

Primary vs Secondary across all 4 entry models.

| Zone Type | Model | Trades | Win Rate % | Avg R |
| --------- | ----- | -----: | ---------: | ----: |
| PRIMARY   | EPCH1 | 120    | 49.17      | 0.84  |
| PRIMARY   | EPCH2 | 1503   | 45.64      | 0.68  |
| SECONDARY | EPCH3 | 186    | 47.31      | 0.89  |
| SECONDARY | EPCH4 | 2190   | 48.86      | 0.90  |

## 7. Setup Risk-Reward vs Actual Outcomes

Does the calculated R:R at setup time predict actual max R achieved?

| Setup R:R | Trades | Win Rate % | Avg Actual R | Avg Setup R:R |
| --------- | -----: | ---------: | -----------: | ------------: |
| 3.0+ R:R  | 3999   | 47.59      | 0.82         | 23.47         |

## 8. Your Final 4: Structure Alignment

Were your selected tickers more aligned with setup direction?

| Selection  | Alignment | Trades | Win Rate % | Avg R |
| ---------- | --------- | -----: | ---------: | ----: |
| YOUR PICKS | COUNTER   | 315    | 54.92      | 1.54  |
| SKIPPED    | COUNTER   | 261    | 51.34      | 0.79  |

## 9. Key Findings

**Review the tables above to answer:**
1. Does ALIGNED outperform COUNTER? By how much?
2. Which direction + model combo is the sweet spot?
3. Does setup R:R predict actual R achieved?
4. Were your picks structurally better-aligned than skipped tickers?
5. Should you filter out counter-trend setups entirely, or do they add value?

---
