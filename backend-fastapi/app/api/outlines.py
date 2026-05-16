from __future__ import annotations
import json
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.novel import Outline
from app.schemas.novel import OutlineUpdate, OutlineOut
from app.services.ai_service import chat_stream, WRITING_MODEL
from app.services.rag_service import search_similar_chunks, get_pinned_examples, STYLE_RULES
import uuid

router = APIRouter(prefix="/api/novels", tags=["outlines"])


def _build_rag_context(outline: Outline) -> str:
    parts = []
    if outline.core_seed:
        parts.append(outline.core_seed)
    if outline.character_setting:
        parts.append(outline.character_setting)
    if outline.world_setting:
        parts.append(outline.world_setting)
    return " ".join(parts)


def _prev_volume_context(volumes: list, volume_number: int) -> str:
    if not volumes:
        return ""
    prev_vol = None
    for v in volumes:
        if v.get("volume_number") == volume_number - 1:
            prev_vol = v
            break
    if not prev_vol or not prev_vol.get("chapters"):
        return ""
    last_chapters = prev_vol["chapters"][-3:]
    lines = ["上一卷结尾剧情："]
    for ch in last_chapters:
        lines.append(f"  第{ch['chapter_number']}章 {ch.get('title', '')}：{ch.get('summary', '')}")
    return "\n".join(lines)


async def _build_volume_prompt(outline: Outline, volume_number: int, chapter_count: int, db: AsyncSession) -> str:
    rag_context = _build_rag_context(outline)
    prev_context = _prev_volume_context(outline.volumes or [], volume_number)

    start_ch = (volume_number - 1) * chapter_count + 1
    end_ch = volume_number * chapter_count

    # 从仿写 RAG 引擎检索相关范例
    style_refs_text = ""
    if rag_context:
        try:
            refs = await search_similar_chunks(rag_context, "", 5, db)
            if refs:
                style_refs_text = "\n".join([
                    f"【范例{i+1}·{r['source_name']}·{r.get('scene_type', '')}】\n{r['content']}"
                    for i, r in enumerate(refs)
                ])
        except Exception:
            pass

    # 检索精选范例
    examples_text = ""
    try:
        examples = await get_pinned_examples("日常", db)
        if not examples:
            examples = await get_pinned_examples("打脸", db)
        if examples:
            examples_text = "\n\n".join([f"【精选范例{i+1}】\n{e}" for i, e in enumerate(examples[:3])])
    except Exception:
        pass

    prompt_parts = [
        f"请为一部小说生成第{volume_number}卷的大纲（第{start_ch}章 ~ 第{end_ch}章，共{chapter_count}章）。",
    ]
    if rag_context:
        prompt_parts.append(f"\n核心设定：{rag_context}")
    if prev_context:
        prompt_parts.append(f"\n{prev_context}")
    if style_refs_text:
        prompt_parts.append(f"\n以下为优秀小说范例，模仿其节奏和风格来规划本卷大纲：\n{style_refs_text}")
    if examples_text:
        prompt_parts.append(f"\n以下为精选写作范例：\n{examples_text}")
    prompt_parts.append(f"""
要求：
1. 每章用1-2句话描述核心剧情，包含本章爽点和推进点
2. 章节之间步步递进，3章一小爽，10章一大爽
3. 本卷要有独立的起承转合，同时与整体设定一致
4. 模仿上述范例的行文节奏和爽感设计
5. 直接输出大纲，格式为：第X章 章名：剧情概要
6. 不要前言后语，从第{start_ch}章开始输出""")
    return "\n".join(prompt_parts)


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
async def generate_outline(
    novel_id: uuid.UUID,
    volume_number: int = Query(default=1, ge=1, description="要生成的卷号"),
    chapter_count: int = Query(default=200, ge=10, le=300, description="本卷章数"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Outline).where(Outline.novel_id == novel_id)
    result = await db.execute(stmt)
    outline = result.scalar_one_or_none()
    if not outline:
        outline = Outline(novel_id=novel_id)
        db.add(outline)
        await db.flush()

    system_prompt = (
        "你是一个资深的网文编辑，擅长为玄幻/仙侠小说规划章级大纲。"
        "你的大纲节奏紧凑，每章都有明确的爽点或推进。"
        "输出格式：每行一章，格式为 '第X章 章名：剧情概要'。\n"
        + STYLE_RULES
    )

    user_prompt = await _build_volume_prompt(outline, volume_number, chapter_count, db)

    generator = chat_stream(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=WRITING_MODEL,
        temperature=0.7,
        max_tokens=16000,
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
            chapters = _parse_outline_to_chapters(full)
            volumes = list(outline.volumes or [])
            existing_idx = None
            for i, v in enumerate(volumes):
                if v.get("volume_number") == volume_number:
                    existing_idx = i
                    break

            vol_data = {
                "volume_number": volume_number,
                "title": f"第{volume_number}卷",
                "chapters": chapters,
            }

            if existing_idx is not None:
                volumes[existing_idx] = vol_data
            else:
                volumes.append(vol_data)
                volumes.sort(key=lambda v: v.get("volume_number", 0))

            outline.volumes = volumes
            outline.full_outline = _volumes_to_text(volumes)
            outline.version += 1
            await db.flush()

        yield f"event: done\ndata: {json.dumps({'length': len(full), 'volume_number': volume_number, 'chapters_parsed': len(chapters)})}\n\n"

    return StreamingResponse(
        save_and_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


def _parse_outline_to_chapters(text: str) -> list[dict]:
    """将 AI 生成的大纲文本解析为章节列表"""
    import re
    chapters = []
    pattern = re.compile(r'第(\d+)章\s*[：:]\s*(.*?)[：:]\s*(.*)')
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            chapters.append({
                "chapter_number": int(m.group(1)),
                "title": m.group(2).strip(),
                "summary": m.group(3).strip(),
            })
        else:
            # 尝试匹配不规范的格式
            simple = re.match(r'第(\d+)章\s+(.+)', line)
            if simple:
                chapters.append({
                    "chapter_number": int(simple.group(1)),
                    "title": "",
                    "summary": simple.group(2).strip(),
                })
    return chapters


def _volumes_to_text(volumes: list) -> str:
    """将所有卷的章节拼接为纯文本大纲"""
    lines = []
    for vol in volumes:
        lines.append(f"\n## 第{vol.get('volume_number')}卷 {vol.get('title', '')}\n")
        for ch in vol.get("chapters", []):
            title = ch.get("title", "")
            summary = ch.get("summary", "")
            if title:
                lines.append(f"第{ch['chapter_number']}章 {title}：{summary}")
            else:
                lines.append(f"第{ch['chapter_number']}章 {summary}")
    return "\n".join(lines)
