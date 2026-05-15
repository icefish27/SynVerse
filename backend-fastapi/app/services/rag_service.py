from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.knowledge import KnowledgeChunk, StyleExample
from app.models.novel import Outline, Chapter, Character
from app.services.embedding_service import embed_query, cosine_similarity
from app.agents.writer_agent import WRITER_SYSTEM_PROMPT, STYLE_RULES
from app.agents.reader_agent import READER_SYSTEM_PROMPT


async def search_similar_chunks(
    query: str,
    scene_type: str = "",
    top_k: int = 5,
    db: AsyncSession = None,
) -> list[dict]:
    """用嵌入向量检索最相似的段落。"""
    query_vec = embed_query(query)

    stmt = select(KnowledgeChunk).where(KnowledgeChunk.embedding.isnot(None))
    if scene_type:
        stmt = stmt.where(KnowledgeChunk.scene_type == scene_type)
    result = await db.execute(stmt)
    chunks = result.scalars().all()

    scored = []
    for chunk in chunks:
        if chunk.embedding and len(chunk.embedding) >= 128:
            score = cosine_similarity(query_vec, chunk.embedding)
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {"content": c.content[:400], "source_name": c.source_name, "scene_type": c.scene_type, "score": round(s, 3)}
        for s, c in scored[:top_k]
    ]


async def get_pinned_examples(scene_type: str, db: AsyncSession) -> list[str]:
    stmt = select(StyleExample).where(
        StyleExample.scene_type == scene_type,
        StyleExample.is_pinned == True,
    ).order_by(StyleExample.quality_rating.desc()).limit(3)
    result = await db.execute(stmt)
    examples = result.scalars().all()

    if not examples:
        stmt2 = select(StyleExample).where(
            StyleExample.scene_type == scene_type,
        ).order_by(StyleExample.quality_rating.desc()).limit(2)
        result2 = await db.execute(stmt2)
        examples = result2.scalars().all()

    return [e.content for e in examples]


async def build_writing_context(novel_id: str, chapter_id: str | None, db: AsyncSession) -> dict:
    stmt = select(Outline).where(Outline.novel_id == novel_id)
    result = await db.execute(stmt)
    outline = result.scalar_one_or_none()

    prev_chapter = None
    if chapter_id:
        stmt2 = select(Chapter).where(Chapter.id == chapter_id)
        result2 = await db.execute(stmt2)
        prev_chapter = result2.scalar_one_or_none()
    if not prev_chapter:
        stmt3 = select(Chapter).where(Chapter.novel_id == novel_id).order_by(Chapter.chapter_number.desc()).limit(1)
        result3 = await db.execute(stmt3)
        prev_chapter = result3.scalar_one_or_none()

    stmt4 = select(Character).where(Character.novel_id == novel_id)
    result4 = await db.execute(stmt4)
    characters = result4.scalars().all()

    return {
        "outline": outline.full_outline if outline else "",
        "core_seed": outline.core_seed if outline else "",
        "prev_chapter_title": prev_chapter.title if prev_chapter else "",
        "prev_chapter_content": (prev_chapter.content or "")[-1000:] if prev_chapter else "",
        "characters": [{"name": c.name, "role": c.role_type, "personality": c.personality} for c in characters],
    }


async def build_writing_prompt(
    message: str,
    novel_id: str,
    chapter_id: str | None,
    db: AsyncSession,
) -> list[dict]:
    ctx = await build_writing_context(novel_id, chapter_id, db)
    examples = await get_pinned_examples("日常", db)
    refs = await search_similar_chunks(message, "", 3, db)

    examples_text = "\n\n".join([f"【范例{i+1}】\n{e}" for i, e in enumerate(examples)])
    refs_text = "\n".join([f"【参考{i+1}·{r['source_name']}】\n{r['content']}" for i, r in enumerate(refs)])

    context_text = f"""## 小说设定
核心种子：{ctx['core_seed']}

## 上一章
{ctx['prev_chapter_title']}
{ctx['prev_chapter_content'][:800]}

## 角色列表
{chr(10).join(f'- {c["name"]}（{c["role"]}）：{c["personality"]}' for c in ctx['characters'])}"""

    user_prompt = f"""{context_text}

## 参考范例
{examples_text}

## 参考段落
{refs_text}

## 写作要求
{message}

直接写正文，不要前缀后缀。"""

    return [
        {"role": "system", "content": WRITER_SYSTEM_PROMPT + "\n\n" + STYLE_RULES},
        {"role": "user", "content": user_prompt},
    ]


async def build_review_prompt(chapter_content: str, chapter_title: str = "") -> list[dict]:
    user_prompt = f"""请阅读以下章节并进行审读：

## {chapter_title}
{chapter_content[:4000]}

请按照你的反馈清单逐项给出审读意见。"""

    return [
        {"role": "system", "content": READER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
