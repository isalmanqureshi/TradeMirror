# Chat Orchestration (Phase 5.1)

Deterministic backend chat layer for `/chat` with intent classification, analytics routing, evidence retrieval, structured composition, caveats, and safety constraints.

## Response structure
- Analytics intents: direct answer, key metrics, evidence summary, caveat (if any), and a suggested next-step question.
- Lookup intents: what was found, top evidence summary, filters mention, and limited-result caveat when relevant.
- Unknown intents: explicit capability summary plus 3 useful example questions.

## Evidence ranking (deterministic)
- Performance/underperformance: `r_multiple ASC`, then `pnl ASC`, then most recent `entry_time DESC`.
- Best trades: excludes rows with both `r_multiple` and `pnl` null; ranks `r_multiple DESC NULLS LAST`, `pnl DESC NULLS LAST`, then recency.
- Recent trades: `entry_time DESC`.
- Journal entries: keyword relevance (title > body) when query provided, then newest entry.
- Trade context: records with non-null context first, then newest trade entry.

## Evidence payload
Always includes:
- `evidence.analytics`
- `evidence.trades`
- `evidence.journal_entries`
- `evidence.trade_context`

Payload is JSON-safe (UUID/datetime serialized by schema; Decimal converted in retrieval).

## Caveats / warnings strategy
Warnings are intent-aware and returned in `warnings`:
- small sample caveat when sample size < 10
- backtest/live low-sample caveat when either side is too small
- journal no-match caveat
- missing context caveat for context-heavy intents
- unknown-intent capability caveat

## Suggested questions strategy
Each intent maps to three deterministic follow-up questions tailored to the topic (performance, regime, execution, risk, edge decay, backtest/live, trade lookup, journal lookup, context lookup, unknown).

## Safety refusal examples
Direct advice requests are refused with wording similar to:
- “I cannot tell you whether to buy, sell, short, enter, exit, or use leverage.”
- Followed by a safe alternative: analysis of historical outcomes for similar setups.

Composer sanitizes prohibited direct-advice phrases before response.

## Metadata and debuggability
Responses optionally include `metadata` with:
- `sample_size`
- `evidence_counts` (trades, journal entries, trade_context)
- `data_quality` flags for analytics and evidence presence

## Current limitations
- Deterministic, keyword-based intent classification.
- No semantic retrieval or generated free-form narratives.

## Deferred to later phases
- vector retrieval / embeddings
- external LLM-generated narratives
- frontend chat UI
- real auth
- broker/live alerts
