from __future__ import annotations
import os, re
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.schemas.knowledge import KnowledgeDocOut, KnowledgeSearchResult
from app.services.embedding_service import embed
from app.services.rag_service import search_similar_chunks
from app.services.ai_service import chat_simple, LIGHT_MODEL
import uuid
import aiofiles
import asyncio

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

UPLOAD_DIR = "uploads/knowledge"
os.makedirs(UPLOAD_DIR, exist_ok=True)

NOISE_PATTERNS = [
    r'^第[一二三四五六七八九十百千\d]+章',
    r'^第[一二三四五六七八九十百千\d]+卷',
    r'^[\(（].*[\)）]$',
    r'^──+$',
    r'^════+$',
]


def is_noise(line: str) -> bool:
    line = line.strip()
    if not line or len(line) < 10:
        return True
    for pat in NOISE_PATTERNS:
        if re.match(pat, line):
            return True
    return False


SCENE_TYPES = ["日常", "打斗", "打脸", "修炼", "感情", "阴谋"]

async def classify_scene(text: str) -> str:
    """用 AI 分类文本片段属于哪个场景类型。"""
    prompt = f"""请判断以下小说片段属于哪种场景类型。只能从以下选项中选择一个：{", ".join(SCENE_TYPES)}

文本：
{text[:300]}

只返回场景类型名称，不要其他内容。"""
    try:
        result = await chat_simple(prompt, "你是小说场景分类专家。", LIGHT_MODEL, temperature=0.1, max_tokens=20)
        result = result.strip()
        for t in SCENE_TYPES:
            if t in result:
                return t
        return "日常"
    except Exception:
        return "日常"


def chunk_text(text: str, target_size: int = 350) -> list[str]:
    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) >= 5 and not is_noise(l.strip())]
    if not lines:
        # 极短文本：整体作为一个切片
        clean = text.strip()
        return [clean] if len(clean) >= 20 else []
    chunks = []
    buf = []
    buf_len = 0
    for line in lines:
        buf.append(line)
        buf_len += len(line)
        if buf_len >= target_size:
            chunks.append("\n".join(buf))
            buf = []
            buf_len = 0
    if buf and buf_len >= 50:
        chunks.append("\n".join(buf))
    # 如果没有任何切片，将全部内容作为一个切片
    if not chunks and lines:
        chunks.append("\n".join(lines))
    return chunks


@router.get("/documents", response_model=list[KnowledgeDocOut])
async def list_documents(db: AsyncSession = Depends(get_db)):
    stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/upload", response_model=KnowledgeDocOut, status_code=201)
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    filename = file.filename or "unknown.txt"
    filepath = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{filename}")
    content = (await file.read()).decode("utf-8", errors="replace")

    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(content)

    doc = KnowledgeDocument(filename=filename, file_path=filepath, status="processing")
    db.add(doc)
    await db.flush()

    chunks = chunk_text(content, target_size=350)
    if chunks:
        chunk_texts = list(chunks)
        embeddings = embed(chunk_texts)

        # 批量 AI 场景分类（每批 3 个，并发）
        scene_types = []
        for i in range(0, len(chunk_texts), 3):
            batch = chunk_texts[i:i+3]
            tasks = [classify_scene(c) for c in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                scene_types.append(r if isinstance(r, str) else "日常")

        for chunk, emb, st in zip(chunks, embeddings, scene_types):
            kc = KnowledgeChunk(
                document_id=doc.id, content=chunk, embedding=emb,
                source_name=filename.replace(".txt", ""),
                scene_type=st, char_count=len(chunk),
            )
            db.add(kc)
    else:
        for chunk in chunks:
            kc = KnowledgeChunk(
                document_id=doc.id, content=chunk,
                source_name=filename.replace(".txt", ""),
                char_count=len(chunk),
            )
            db.add(kc)

    doc.chunk_count = len(chunks)
    doc.total_chars = len(content)
    doc.status = "ready"
    await db.flush()
    await db.refresh(doc)
    return doc


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    result = await db.execute(stmt)
    doc = result.scalar_one()
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    await db.delete(doc)
    await db.flush()


@router.get("/search", response_model=list[KnowledgeSearchResult])
async def search_knowledge(
    q: str = Query(..., description="搜索文本"),
    scene_type: str = Query(default="", description="场景类型"),
    top_k: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    results = await search_similar_chunks(q, scene_type, top_k, db)
    return [KnowledgeSearchResult(
        content=r["content"], scene_type=r.get("scene_type"),
        source_name=r.get("source_name"), similarity=r["score"],
    ) for r in results]
