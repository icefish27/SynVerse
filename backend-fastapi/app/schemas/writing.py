from typing import Optional
import uuid
from datetime import datetime
from pydantic import BaseModel


class SessionCreate(BaseModel):
    chapter_id: Optional[uuid.UUID] = None
    title: str = "新对话"


class SessionOut(BaseModel):
    id: uuid.UUID
    novel_id: uuid.UUID
    chapter_id: Optional[uuid.UUID]
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: Optional[str]
    reasoning_content: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerateRequest(BaseModel):
    message: str
    chapter_id: Optional[uuid.UUID] = None
