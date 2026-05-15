from typing import Optional
import uuid
from datetime import datetime
from pydantic import BaseModel


# ── Novel ──
class NovelCreate(BaseModel):
    title: str
    description: str = ""
    type_tags: list[str] = []
    target_chapters: int = 500
    target_words: int = 2000


class NovelUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type_tags: Optional[list[str]] = None
    target_chapters: Optional[int] = None
    target_words: Optional[int] = None


class NovelOut(BaseModel):
    id: uuid.UUID
    title: str
    cover_url: Optional[str]
    description: Optional[str]
    type_tags: list
    target_chapters: int
    target_words: int
    total_chapters: int
    total_words: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Chapter ──
class ChapterCreate(BaseModel):
    title: str = ""
    content: str = ""


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None


class ChapterOut(BaseModel):
    id: uuid.UUID
    novel_id: uuid.UUID
    chapter_number: int
    title: Optional[str]
    content: Optional[str]
    word_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChapterBrief(BaseModel):
    id: uuid.UUID
    chapter_number: int
    title: Optional[str]
    word_count: int
    status: str
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Outline ──
class OutlineUpdate(BaseModel):
    core_seed: Optional[str] = None
    character_setting: Optional[str] = None
    world_setting: Optional[str] = None
    full_outline: Optional[str] = None


class OutlineOut(BaseModel):
    id: uuid.UUID
    novel_id: uuid.UUID
    core_seed: Optional[str]
    character_setting: Optional[str]
    world_setting: Optional[str]
    full_outline: Optional[str]
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Character ──
class CharacterCreate(BaseModel):
    name: str
    role_type: str = "supporting"
    personality: str = ""
    motivation: str = ""
    appearance: str = ""
    background: str = ""


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    role_type: Optional[str] = None
    personality: Optional[str] = None
    motivation: Optional[str] = None
    appearance: Optional[str] = None
    background: Optional[str] = None
    status_history: Optional[list] = None


class CharacterOut(BaseModel):
    id: uuid.UUID
    novel_id: uuid.UUID
    name: str
    role_type: str
    personality: Optional[str]
    motivation: Optional[str]
    appearance: Optional[str]
    background: Optional[str]
    status_history: list
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
