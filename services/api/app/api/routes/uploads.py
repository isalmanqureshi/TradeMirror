import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.ingestion.trade_ingestion import ingest_trade_csv

router = APIRouter(prefix="/uploads", tags=["uploads"])


class UploadError(BaseModel):
    row_number: int
    error: str


class UploadSummary(BaseModel):
    total_rows: int
    inserted: int
    skipped: int
    errors: int


class UploadResponse(BaseModel):
    summary: UploadSummary
    errors: list[UploadError]


@router.post("/trades", response_model=UploadResponse)
def upload_trades(
    file: UploadFile = File(...),
    strategy_name: str = Form(...),
    source_type: str = Form(...),
    db: Session = Depends(get_db),
) -> UploadResponse:
    if source_type not in {"backtest", "live", "paper"}:
        raise HTTPException(status_code=400, detail={"error": "invalid source_type"})

    try:
        result = ingest_trade_csv(
            file=file,
            db=db,
            user_id=None,
            strategy_name=strategy_name,
            source_type=source_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": str(exc)}) from exc

    errors = [UploadError(**item) for item in result["errors"]]
    return UploadResponse(
        summary=UploadSummary(
            total_rows=result["total_rows"],
            inserted=result["inserted"],
            skipped=result["skipped"],
            errors=len(errors),
        ),
        errors=errors,
    )
