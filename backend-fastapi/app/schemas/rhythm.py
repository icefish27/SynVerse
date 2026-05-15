from typing import Optional
import uuid
from datetime import datetime
from pydantic import BaseModel


class RhythmOut(BaseModel):
    id: uuid.UUID
    chapter_id: uuid.UUID
    scores: dict
    suggestions: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
