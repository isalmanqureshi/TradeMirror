# Data Ingestion

## Datetime Policy
- `entry_time` and `exit_time` must be ISO-8601 timezone-aware datetimes.
- Datetimes with timezone offsets are normalized to UTC before dedupe and persistence.
- Naive datetimes are rejected with `naive_datetime_not_allowed`.

## Upload Guardrails
- Maximum upload size: 5 MB (`file_too_large`).
- Maximum row count: 10,000 (`too_many_rows`).

## Duplicate Definition
A duplicate trade is any row with the same `(user_id, strategy_id, symbol, side, entry_time)` as an existing trade (or prior row in the same upload after UTC normalization).

## Structured Row Errors
Each row-level error uses: 
`{ row_number, code, field, error }`

Common codes: `missing_required_column`, `invalid_side`, `invalid_datetime`, `naive_datetime_not_allowed`, `invalid_numeric`, `duplicate_trade`, `too_many_rows`, `file_too_large`, `invalid_json`.
