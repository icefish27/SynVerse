from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Novel(Base):
    __tablename__ = "novels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    cover_url: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, default="")
    type_tags: Mapped[list] = mapped_column(JSONB, default=list)
    target_chapters: Mapped[int] = mapped_column(Integer, default=500)
    target_words: Mapped[int] = mapped_column(Integer, default=2000)
    total_chapters: Mapped[int] = mapped_column(Integer, default=0)
    total_words: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    chapters = relationship("Chapter", back_populates="novel", cascade="all, delete-orphan")
    outline = relationship("Outline", back_populates="novel", uselist=False, cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="novel", cascade="all, delete-orphan")
    writing_sessions = relationship("WritingSession", back_populates="novel", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(300), default="")
    content: Mapped[Optional[str]] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("novel_id", "chapter_number"),)

    novel = relationship("Novel", back_populates="chapters")
    rhythm_analysis = relationship("RhythmAnalysis", back_populates="chapter", uselist=False, cascade="all, delete-orphan")


class Outline(Base):
    __tablename__ = "outlines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("novels.id", ondelete="CASCADE"), unique=True, nullable=False)
    core_seed: Mapped[Optional[str]] = mapped_column(Text, default="")
    character_setting: Mapped[Optional[str]] = mapped_column(Text, default="")
    world_setting: Mapped[Optional[str]] = mapped_column(Text, default="")
    full_outline: Mapped[Optional[str]] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    novel = relationship("Novel", back_populates="outline")


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role_type: Mapped[str] = mapped_column(String(50), default="supporting")
    personality: Mapped[Optional[str]] = mapped_column(Text, default="")
    motivation: Mapped[Optional[str]] = mapped_column(Text, default="")
    appearance: Mapped[Optional[str]] = mapped_column(Text, default="")
    background: Mapped[Optional[str]] = mapped_column(Text, default="")
    status_history: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    novel = relationship("Novel", back_populates="characters")
