# Trade Context Enrichment (Phase 3)

## Endpoints
- `POST /trades/{trade_id}/enrich`: enrich one trade and upsert `trade_context`.
- `POST /analytics/enrich-context`: batch enrich by optional filters (`strategy_id`, `source_type`, `symbol`, `start_date`, `end_date`, `limit`, `skip_existing`).
- `GET /trades/{trade_id}/context`: fetch stored trade context.

## Deterministic Rules
- Session windows (UTC):
  - `asia`: 00:00-06:59
  - `london`: 07:00-12:59
  - `ny_open`: 13:00-15:59
  - `ny_mid`: 16:00-19:59
  - `ny_close`: 20:00-21:59
  - `after_hours`: all other times
- `holding_minutes`: `(exit_time - entry_time)` in minutes, null if no `exit_time`.
- `volatility_regime` from ATR percentile:
  - `0-33`: `low`
  - `34-66`: `medium`
  - `67-100`: `high`
- `trend_regime`:
  - `trending_up` if `close > ma_50` and `ma_50_slope > threshold`
  - `trending_down` if `close < ma_50` and `ma_50_slope < -threshold`
  - `volatile` if realized vol percentile > 80
  - otherwise `ranging`
- Event proximity:
  - nearest event minutes distance <= 120 => `macro_event_nearby=true`; else false.

## Null Behavior
When market or event providers are unavailable, enrichment still upserts `trade_context` with partial null fields and no crash.

## Provider Abstractions
Service supports optional providers:
- `MarketDataProvider`: snapshot, ATR percentile, realized vol percentile, trend inputs.
- `EventProvider`: nearest event around timestamp.

Phase 3 uses null/stub providers by default via API dependency injection.
Real market/event integrations are intentionally deferred to later phases.
Provider-backed tests demonstrate how concrete providers can plug in without changing service contracts.

## Idempotent Upsert
`trade_context` is one row per trade. Re-running enrichment updates existing row fields instead of creating duplicates.

## Example Context Payload
```json
{
  "session_source": "computed",
  "session_label": "ny_open",
  "holding_minutes": 24,
  "atr_source": "market_data_provider",
  "trend_inputs": {
    "close": 18820.5,
    "ma_50": 18810.1,
    "ma_50_slope": 0.12
  }
}
```
