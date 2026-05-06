# Analytics Engine (Phase 4)

## Endpoints
- `GET /analytics/summary`
- `GET /analytics/regime-sensitivity`
- `GET /analytics/execution-quality`
- `GET /analytics/risk-drift`
- `GET /analytics/edge-decay`
- `GET /analytics/backtest-live-comparison`

## Shared filters
All endpoints accept: `user_id` (required), `strategy_id`, `source_type`, `symbol`, `instrument`, `start_date`, `end_date`.

## Metric formulas
- `win_rate = winners / trades_with_outcome`
- `profit_factor = sum(positive outcomes) / abs(sum(negative outcomes))`
- `expectancy_r = average(r_multiple)`
- `max_drawdown_r = max peak-to-trough decline on cumulative R`
- `risk_delta = actual_risk - planned_risk`
- `risk_delta_pct = (actual_risk - planned_risk) / planned_risk`
- `rolling_win_rate = wins_in_window / window_size`
- `rolling_profit_factor = sum(positive R in window) / abs(sum(negative R in window))`

## Null behavior
- Null source fields are ignored for metric-specific calculations.
- Responses always include `sample_size` and return `null` metrics when unavailable.
- Regime/execution grouping emits key `"unknown"` for null grouping values.

## Sample size rules
- Backtest/live requires at least 5 non-null `r_multiple` trades in each population.
- Edge decay returns empty `points` with message when fewer trades than the requested window.

## Intentionally deferred
- Statistical significance testing (KS test): returns `ks_test: null` and a message.
- Alerts, narrative generation, dashboards, brokers, and market data integrations are deferred.
