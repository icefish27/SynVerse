from __future__ import annotations
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.novel import Outline
from app.schemas.novel import OutlineUpdate, OutlineOut
from app.services.ai_service import chat_stream, WRITING_MODEL
import uuid

router = APIRouter(prefix="/api/novels", tags=["outlines"])


@router.get("/{novel_id}/outline", response_model=OutlineOut)
async def get_outline(novel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Outline).where(Outline.novel_id == novel_id)
    result = await db.execute(stmt)
    outline = result.scalar_one_or_none()
    if not outline:
        outline = Outline(novel_id=novel_id)
        db.add(outline)
        await db.flush()
        await db.refresh(outline)
    return outline


@router.put("/{novel_id}/outline", response_model=OutlineOut)
async def update_outline(novel_id: uuid.UUID, data: OutlineUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Outline).where(Outline.novel_id == novel_id)
    result = await db.execute(stmt)
    outline = result.scalar_one_or_none()
    if not outline:
        outline = Outline(novel_id=novel_id)
        db.add(outline)
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(outline, key, val)
    outline.version += 1
    await db.flush()
    await db.refresh(outline)
    return outline


@router.post("/{novel_id}/outline/generate")
async def generate_outline(novel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Outline).where(Outline.novel_id == novel_id)
    result = await db.execute(stmt)
    outline = result.scalar_one_or_none()
    if not outline:
        outline = Outline(novel_id=novel_id)
        db.add(outline)
        await db.flush()

    system_prompt = "你是一个资深的网文编辑，擅长为玄幻/仙侠小说规划章级大纲。你的大纲节奏紧凑，每章都有明确的爽点或推进。输出格式：每行一章，格式为 '第X章 章名：剧情概要'。"
    user_prompt = f"""请根据以下设定，为一部小说生成{500}章的分章大纲。每章用1-2句话描述核心剧情。

核心种子：{outline.core_seed or '未填写'}

角色设定：{outline.character_setting or '未填写'}

世界观：{outline.world_setting or '未填写'}

要求：
1. 按章节推进，步步递进
2. 每段有反派被踩或主角突破
3. 3章一小爽，10章一大爽
4. 直接输出大纲，不要前言后语"""

    generator = chat_stream(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=WRITING_MODEL,
        temperature=0.7,
        max_tokens=8000,
        enable_thinking=True,
    )

    async def save_and_stream():
        contents = []
        reasoning_parts = []
        async for chunk in generator:
            if "reasoning" in chunk:
                reasoning_parts.append(chunk["reasoning"])
                yield f"event: reasoning\ndata: {json.dumps({'content': chunk['reasoning']})}\n\n"
            if "content" in chunk:
                contents.append(chunk["content"])
                yield f"event: content\ndata: {json.dumps({'content': chunk['content']})}\n\n"

        full = "".join(contents)
        if full.strip():
            outline.full_outline = full
            outline.version += 1
            await db.flush()

        yield f"event: done\ndata: {json.dumps({'length': len(full)})}\n\n"

    return StreamingResponse(
        save_and_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
