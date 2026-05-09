from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatFilters, ChatRequest, ChatResponse
from app.services.chat import handle_chat_message

router = APIRouter(prefix="/chat", tags=["chat"])


def get_current_user_id_for_demo() -> UUID:
    # TODO: replace with real authentication dependency.
    return UUID("00000000-0000-0000-0000-000000000001")


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    filters = ChatFilters.model_validate(request.model_dump(exclude={"message"}))
    return handle_chat_message(db=db, user_id=get_current_user_id_for_demo(), message=request.message, filters=filters)
