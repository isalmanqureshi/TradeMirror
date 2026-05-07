from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AnalyticsFiltersQuery(BaseModel):
    user_id: UUID
    strategy_id: UUID | None = None
    source_type: str | None = None
    symbol: str | None = None
    instrument: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class GroupByQuery(BaseModel):
    group_by: str


class EdgeDecayQuery(BaseModel):
    window_size: int = Field(default=20, ge=2)
