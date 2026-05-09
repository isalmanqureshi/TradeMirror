# Chat Orchestration (Phase 5)

Deterministic backend chat layer for `/chat` that classifies intent, routes to existing analytics, retrieves SQL evidence, and returns grounded answers.

## Endpoint
- `POST /chat`
- Request supports: `message`, `strategy_id`, `symbol`, `instrument`, `source_type`, `start_date`, `end_date`, `limit`.
- Response includes: `intent`, `secondary_intents`, `answer`, `evidence`, `filters`, `warnings`, `suggested_questions`.

## Supported intents
- `performance_summary`, `regime_analysis`, `execution_quality`, `risk_drift`, `edge_decay`, `backtest_live_comparison`, `trade_lookup`, `journal_lookup`, `trade_context_lookup`, `unknown`.

## Routing rules
- Rule-based keyword classifier chooses primary/secondary intents.
- Orchestrator reuses Phase 4 analytics services; no analytics formulas are duplicated.
- Retrieval is SQL-backed for trades/journal/context.

## Evidence payload
- Always includes keys: `analytics`, `trades`, `journal_entries`, `trade_context`.
- Values are structured JSON-serializable objects (UUID/datetime preserved via Pydantic; Decimal converted to float where needed).

## Safety limitations
- Direct trading advice prompts are refused.
- Composer uses analytical framing only and avoids recommendation language.

## Demo user limitation
- Route currently uses an explicit `get_current_user_id_for_demo()` TODO until auth is implemented.

## Why deterministic first
- Keeps behavior testable, explainable, and CI-stable before introducing probabilistic/LLM components.

## Deferred after Phase 5
- Vector search / embeddings
- External LLM answer generation
- Frontend chat UI
- Authentication integration
- Broker integrations / live alerts
