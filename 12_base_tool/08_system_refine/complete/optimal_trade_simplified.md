## Dev Rules

1. Do not generate any code without my explicit instructions
2. Do not assume anything (naming conventions, modules, directories). Ask for clarification or request files to read directly.
3. Once the documentation has been reviewed, please request additional information, questions, and specific scripts if not already apparent and obvious.
4. Always include .txt documentation at the end in two files:
   - **AI-readable**: Complete context for use in future AI conversations without requiring the full script directory
   - **Human-readable**: Teaching-focused explanation of how the script works and how to implement similar patterns elsewhere

---

## Business Domain

- Trading (Epoch, Meridian, backtesting) [X]
- Coaching (curriculum, student tools, content) []
- Investment Real Estate []
- W2 / Corporate []
- Other: ***_________*** []

## System / Module Affected

*(Name the specific system, file, or workflow this touches)*

> Optimal Trade: C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest\processor\optimal_trade

## The Problem or Opportunity

*(What happened, what's missing, or what could be better?)*

- > The current state of the optimal trade logic is too complex and does not meet the basic criteria for analysis.
- > The intent of the system is to pull the comparison of the overall health score and the total R / net P&L at the time of best exit so that over time the trader will be able to see the deterioration of the score and exit at a more optimal location.
- > Because the trader cannot see into the future, there is no way to know that a moment in price action is either the MFE or the MAE and so the data generated from hundreds of trades can assist in outlining the outcome. 
In it's current state the optimal_trade is a bit too complex and will need to be simplified so that a baseline of data can be generated and then improvements made over time as a clearer understanding is gleaned.

## Desired End State

*(When this is complete, what does success look like?)*

- > The desired end state is for the optimal_trade sheet to pull directly from the backtest worksheet for the total individual trades available for analysis.
- > Once the trades have been identified, the optimal_trade engine will review the exit_events worksheet and group by the trade_id and identify three different exit outcomes for analysis
   - > MFE - Understand the health score as well as the current state of each of the 10 calculations at the time of greatest profiatbility
   - > MAE - Understand the health score as well as the current state of each of the 10 calculations at the time of lowest profitability
   - > Exit - Understand the health score as well as the current state of each of the 10 calculations at the time of exit as outlined in the exit_events

## Known Touchpoints

*(List any files, databases, integrations, or dependencies you're aware of)*

> Upstream:
C:\XIIITradingSystems\Epoch\02_zone_system\09_backtest

Downstream:
C:\XIIITradingSystems\Epoch\02_zone_system\11_database_export
C:\XIIITradingSystems\Epoch\02_zone_system\13_documentation\20_maps\12_bt_optimal_trades.json
C:\XIIITradingSystems\Epoch\02_zone_system\13_documentation\12_bt_optimal_trade.txt

## Priority

- Urgent — blocking current work [X]
- Next cycle — planned development []
- Future — idea capture for later []

## Additional Context

*(Screenshots, file names, related conversations, or anything else helpful)*

> Once complete please provide an updated documentation as optimal_trade_simplified.md in C:\XIIITradingSystems\Epoch\08_system_refine\complete outlining the original state of the optimal_trade engine and the updated output and executable.