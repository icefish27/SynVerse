from __future__ import annotations
import json
import uuid
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.writing import WritingSession, WritingMessage
from app.models.novel import Chapter, Novel
from app.schemas.writing import SessionCreate, SessionOut, MessageOut, GenerateRequest
from app.services.ai_service import chat_stream, LIGHT_MODEL, WRITING_MODEL
from app.services.rag_service import build_writing_prompt, build_review_prompt

router = APIRouter(prefix="/api", tags=["writing"])


@router.get("/novels/{novel_id}/sessions", response_model=list[SessionOut])
async def list_sessions(novel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(WritingSession).where(
        WritingSession.novel_id == novel_id
    ).order_by(WritingSession.updated_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/novels/{novel_id}/sessions", response_model=SessionOut, status_code=201)
async def create_session(novel_id: uuid.UUID, data: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = WritingSession(novel_id=novel_id, chapter_id=data.chapter_id, title=data.title)
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def list_messages(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(WritingMessage).where(
        WritingMessage.session_id == session_id
    ).order_by(WritingMessage.created_at)
    result = await db.execute(stmt)
    return result.scalars().all()


async def _sse_writer(generator, novel_id: str = None, chapter_id: str = None, session_id: str = None, db=None, refs: list = None):
    """SSE 流式输出包装器：reasoning → content → done。"""
    reasoning_buf = []
    content_buf = []

    yield f"event: start\ndata: {json.dumps({'session_id': session_id})}\n\n"

    async for chunk in generator:
        if "reasoning" in chunk:
            reasoning_buf.append(chunk["reasoning"])
            yield f"event: reasoning\ndata: {json.dumps({'content': chunk['reasoning']})}\n\n"
        if "content" in chunk:
            content_buf.append(chunk["content"])
            yield f"event: content\ndata: {json.dumps({'content': chunk['content']})}\n\n"

    reasoning_text = "".join(reasoning_buf)
    content_text = "".join(content_buf)

    if content_text.strip() and novel_id and db:
        try:
            stmt = select(func.coalesce(func.max(Chapter.chapter_number), 0)).where(Chapter.novel_id == uuid.UUID(novel_id))
            result = await db.execute(stmt)
            next_num = result.scalar() + 1
            chapter = Chapter(
                novel_id=uuid.UUID(novel_id),
                chapter_number=next_num,
                title=f"第{next_num}章",
                content=content_text,
                word_count=len(content_text),
                status="draft",
            )
            db.add(chapter)
            stmt_n = select(Novel).where(Novel.id == uuid.UUID(novel_id))
            res_n = await db.execute(stmt_n)
            novel = res_n.scalar_one()
            novel.total_chapters = next_num
            novel.total_words = (novel.total_words or 0) + chapter.word_count
            await db.flush()
            await db.refresh(chapter)
            chapter_id = str(chapter.id)
        except Exception:
            pass

    if session_id and db:
        try:
            refs_json = json.dumps(refs or [], ensure_ascii=False)
            user_msg = WritingMessage(session_id=uuid.UUID(session_id), role="assistant",
                                      content=content_text, reasoning_content=reasoning_text)
            db.add(user_msg)
            await db.flush()
        except Exception:
            pass

    yield f"event: done\ndata: {json.dumps({'chapter_id': chapter_id, 'word_count': len(content_text), 'refs': refs or []}, ensure_ascii=False)}\n\n"


@router.post("/sessions/{session_id}/generate")
async def generate(session_id: uuid.UUID, req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(WritingSession).where(WritingSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one()

    # 保存用户消息
    user_msg = WritingMessage(session_id=session_id, role="user", content=req.message)
    db.add(user_msg)
    await db.flush()

    # 获取历史消息
    stmt2 = select(WritingMessage).where(
        WritingMessage.session_id == session_id
    ).order_by(WritingMessage.created_at)
    result2 = await db.execute(stmt2)
    history = result2.scalars().all()

    # 检索引用段落
    from app.services.rag_service import search_similar_chunks
    refs = await search_similar_chunks(req.message, "", 3, db)

    # 组装消息
    writing_messages = await build_writing_prompt(
        req.message, str(session.novel_id),
        str(req.chapter_id) if req.chapter_id else None, db,
    )

    generator = chat_stream(
        messages=writing_messages,
        model=WRITING_MODEL,
        temperature=0.75,
        max_tokens=4000,
        enable_thinking=True,
    )

    return StreamingResponse(
        _sse_writer(generator, str(session.novel_id), str(req.chapter_id), str(session_id), db, refs),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/chapters/{chapter_id}/review")
async def review_chapter(chapter_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Chapter).where(Chapter.id == chapter_id)
    result = await db.execute(stmt)
    chapter = result.scalar_one()

    messages = await build_review_prompt(chapter.content or "", chapter.title or "")

    generator = chat_stream(
        messages=messages,
        model=LIGHT_MODEL,
        temperature=0.3,
        max_tokens=1024,
        enable_thinking=False,
    )

    return StreamingResponse(
        _sse_writer(generator, None, None, None, None),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
