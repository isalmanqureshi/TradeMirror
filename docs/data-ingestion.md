# Trade CSV Ingestion

## Endpoint

`POST /uploads/trades`

- Content type: `multipart/form-data`
- Fields:
  - `file` (required): CSV file
  - `strategy_name` (required): strategy name used to resolve/create strategy for user
  - `source_type` (required): `backtest` | `live` | `paper`

## Supported CSV Columns

Required columns:
- `symbol`
- `side`
- `entry_time`
- `entry_price`

Optional columns:
- `exit_time`
- `exit_price`
- `quantity`
- `pnl`
- `r_multiple`
- `fees`
- `slippage`
- `planned_risk`
- `actual_risk`
- `order_type`
- `session_label`
- `setup_tags`
- `journal_note`

Column normalization:
- lowercases names
- trims spaces
- alias mapping:
  - `entry price` / `EntryPrice` -> `entry_price`
  - `P&L` -> `pnl`

## Validation Rules

Per-row validation:
- `symbol` is required
- `side` must be `long` or `short`
- `entry_time` must parse as datetime
- `entry_price` must parse as numeric
- if `exit_time` exists, it must be `>= entry_time`
- optional numeric columns must parse as numeric

Invalid rows are collected into the error list and ingestion continues.

## Example Request

```bash
curl -X POST http://localhost:8000/uploads/trades \
  -F "file=@trades.csv" \
  -F "strategy_name=Breakout" \
  -F "source_type=live"
```

## Example Success Response

```json
{
  "summary": {
    "total_rows": 2,
    "inserted": 2,
    "skipped": 0,
    "errors": 0
  },
  "errors": []
}
```

## Example Partial Success Response

```json
{
  "summary": {
    "total_rows": 2,
    "inserted": 1,
    "skipped": 0,
    "errors": 1
  },
  "errors": [
    {
      "row_number": 3,
      "error": "side must be one of: long, short"
    }
  ]
}
```
