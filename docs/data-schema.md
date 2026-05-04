# TradeMirror Data Schema — Phase 1 Foundation

## Table overview
- `users`
- `strategies`
- `trades`
- `trade_context`
- `journal_entries`
- `backtest_runs`
- `analytics_snapshots`

## Relationship map
- User 1:N Strategy, Trade, JournalEntry, BacktestRun, AnalyticsSnapshot
- Strategy N:1 User; 1:N Trade, JournalEntry, BacktestRun, AnalyticsSnapshot
- Trade N:1 User, optional N:1 Strategy; 1:1 TradeContext; 1:N JournalEntry
- TradeContext 1:1 Trade
- JournalEntry N:1 User, optional N:1 Trade, optional N:1 Strategy
- BacktestRun N:1 User and Strategy
- AnalyticsSnapshot N:1 User and optional Strategy

## Field notes
- UUID primary keys across all tables.
- Timestamps are timezone-aware and default to `now()` where appropriate.
- `trades.source_type` constrained to `backtest|live|paper`.
- `trades.side` constrained to `long|short`.
- JSONB fields are used for evolving structured payloads (`parameters`, `setup_tags`, `context_payload`, etc.).

## Indexing strategy
- Unique: `users.email`, `trade_context.trade_id`.
- FK and access indexes on primary query dimensions: user, strategy, trade associations.
- Composite index: `trades(user_id, strategy_id, entry_time)`.
- Search/filter indexes on `trades` instrument/symbol/source_type and snapshot type.

## Commands
```bash
cd services/api
alembic upgrade head

python ../../scripts/seed_demo_data.py
```

## Out of scope in Phase 1
- CSV ingestion and broker integrations
- Market data ingestion
- Analytics calculations/business alpha
- RAG/vector retrieval or chatbot orchestration
- Frontend UI/dashboard changes
- Authentication and user management APIs
