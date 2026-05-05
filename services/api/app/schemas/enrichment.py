from pydantic import BaseModel


class BatchEnrichmentResponse(BaseModel):
    processed: int
    enriched: int
    skipped: int
    errors: int
