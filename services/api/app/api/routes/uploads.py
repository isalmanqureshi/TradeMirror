import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.domain import SourceType
from app.services.ingestion.trade_ingestion import ingest_trade_csv

router = APIRouter(prefix="/uploads", tags=["uploads"])


class UploadError(BaseModel):
    row_number: int
    code: str
    field: str | None
    error: str


class UploadSummary(BaseModel):
    total_rows: int
    inserted: int
    skipped: int
    errors: int


class UploadResponse(BaseModel):
    summary: UploadSummary
    errors: list[UploadError]


def get_demo_user_id(db: Session) -> uuid.UUID:
    user = db.scalar(select(User).where(User.email == "demo@trademirror.local"))
    if user is None:
        user = User(email="demo@trademirror.local", full_name="Demo User")
        db.add(user)
        db.flush()
    return user.id


@router.post("/trades", response_model=UploadResponse)
def upload_trades(file: UploadFile = File(...), strategy_name: str = Form(...), source_type: SourceType = Form(...), db: Session = Depends(get_db)) -> UploadResponse:
    try:
        result = ingest_trade_csv(file=file, db=db, user_id=get_demo_user_id(db), strategy_name=strategy_name, source_type=source_type.value)
    except ValueError as exc:
        code = str(exc)
        raise HTTPException(status_code=400, detail={"code": code, "error": code.replace("_", " ")}) from exc
    errors = [UploadError(**item) for item in result["errors"]]
    return UploadResponse(summary=UploadSummary(total_rows=result["total_rows"], inserted=result["inserted"], skipped=result["skipped"], errors=len(errors)), errors=errors)
