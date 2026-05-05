from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import TradeContext
from app.schemas.domain import TradeContextRead
from app.schemas.enrichment import BatchEnrichmentResponse
from app.services.enrichment.trade_context_enrichment import batch_enrich_trade_context, enrich_trade_context

router = APIRouter(tags=["enrichment"])


@router.post("/trades/{trade_id}/enrich", response_model=TradeContextRead)
def enrich_single_trade(trade_id: UUID, db: Session = Depends(get_db)) -> TradeContextRead:
    try:
        context = enrich_trade_context(db=db, trade_id=trade_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"code": str(exc)}) from exc
    db.commit()
    return TradeContextRead.model_validate(context)


@router.get("/trades/{trade_id}/context", response_model=TradeContextRead)
def get_trade_context(trade_id: UUID, db: Session = Depends(get_db)) -> TradeContextRead:
    context = db.scalar(select(TradeContext).where(TradeContext.trade_id == trade_id))
    if context is None:
        raise HTTPException(status_code=404, detail={"code": "trade_context_not_found"})
    return TradeContextRead.model_validate(context)


@router.post("/analytics/enrich-context", response_model=BatchEnrichmentResponse)
def enrich_context_batch(
    strategy_id: UUID | None = None,
    source_type: str | None = None,
    symbol: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int | None = Query(default=None, ge=1),
    skip_existing: bool = False,
    db: Session = Depends(get_db),
) -> BatchEnrichmentResponse:
    summary = batch_enrich_trade_context(
        db=db,
        strategy_id=strategy_id,
        source_type=source_type,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        skip_existing=skip_existing,
    )
    return BatchEnrichmentResponse(**summary.__dict__)
