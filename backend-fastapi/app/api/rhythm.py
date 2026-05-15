from __future__ import annotations
import json, re
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.novel import Chapter
from app.models.rhythm import RhythmAnalysis
from app.services.ai_service import chat_simple, LIGHT_MODEL
from app.schemas.rhythm import RhythmOut
import uuid

router = APIRouter(prefix="/api/chapters", tags=["rhythm"])


@router.get("/{chapter_id}/rhythm", response_model=RhythmOut)
async def get_rhythm(chapter_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(RhythmAnalysis).where(RhythmAnalysis.chapter_id == chapter_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one()
    return analysis


@router.post("/{chapter_id}/rhythm", response_model=RhythmOut)
async def analyze_rhythm(chapter_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Chapter).where(Chapter.id == chapter_id)
    result = await db.execute(stmt)
    chapter = result.scalar_one()

    content = chapter.content or ""
    prompt = f"""分析以下小说章节的节奏。按 8 个维度评分（0-100），返回 JSON 格式。

维度：信息密度、情绪强度、悬念设计、冲突张力、爽点密度、节奏快慢、对话占比、描写占比

章节内容：
{content[:3000]}

请只返回 JSON：{{"scores": {{"信息密度": 70, ...}}, "suggestions": "改进建议..."}}"""

    ai_result = await chat_simple(prompt, "你是专业的小说节奏分析师。", LIGHT_MODEL, temperature=0.2, max_tokens=1024)

    try:
        clean = ai_result.strip().removeprefix("```json").removesuffix("```").strip()
        parsed = json.loads(clean)
        scores = parsed.get("scores", {})
        suggestions = parsed.get("suggestions", "")
    except Exception:
        scores = {"信息密度": 50, "情绪强度": 50, "悬念设计": 50, "冲突张力": 50, "爽点密度": 50, "节奏快慢": 50, "对话占比": 50, "描写占比": 50}
        suggestions = "AI 分析异常，显示默认值"

    stmt2 = select(RhythmAnalysis).where(RhythmAnalysis.chapter_id == chapter_id)
    result2 = await db.execute(stmt2)
    analysis = result2.scalar_one_or_none()

    if analysis:
        analysis.scores = scores
        analysis.suggestions = suggestions
    else:
        analysis = RhythmAnalysis(chapter_id=chapter_id, scores=scores, suggestions=suggestions)
        db.add(analysis)

    await db.flush()
    await db.refresh(analysis)
    return analysis
