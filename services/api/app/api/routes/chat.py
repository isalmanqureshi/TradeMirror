from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatFilters, ChatRequest, ChatResponse
from app.services.chat import handle_chat_message

router = APIRouter(prefix="/chat", tags=["chat"])

DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def get_current_user_id_for_demo(
    x_demo_user_id: UUID | None = Header(default=None, alias="X-Demo-User-Id"),
) -> UUID:
    if x_demo_user_id is not None:
        return x_demo_user_id
    return DEMO_USER_ID


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id_for_demo),
) -> ChatResponse:
    filters = ChatFilters.model_validate(request.model_dump(exclude={"message"}))
    return handle_chat_message(db=db, user_id=user_id, message=request.message, filters=filters)
