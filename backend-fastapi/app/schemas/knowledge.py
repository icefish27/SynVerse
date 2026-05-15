from typing import Optional
import uuid
from datetime import datetime
from pydantic import BaseModel


class StyleExampleCreate(BaseModel):
    scene_type: str
    content: str
    quality_rating: int = 3
    is_pinned: bool = False


class StyleExampleOut(BaseModel):
    id: uuid.UUID
    scene_type: str
    content: str
    quality_rating: int
    is_pinned: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeDocOut(BaseModel):
    id: uuid.UUID
    filename: str
    chunk_count: int
    total_chars: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeSearchResult(BaseModel):
    content: str
    scene_type: Optional[str]
    source_name: Optional[str]
    similarity: float
