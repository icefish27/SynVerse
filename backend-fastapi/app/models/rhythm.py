from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class RhythmAnalysis(Base):
    __tablename__ = "rhythm_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), unique=True, nullable=False)
    scores: Mapped[dict] = mapped_column(JSONB, default=dict)
    suggestions: Mapped[Optional[str]] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chapter = relationship("Chapter", back_populates="rhythm_analysis")
