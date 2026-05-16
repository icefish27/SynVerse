from __future__ import annotations
import os, re, json, hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db, async_session
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.schemas.knowledge import KnowledgeDocOut, KnowledgeSearchResult, KnowledgeProgressOut
from app.services.embedding_service import embed
from app.services.rag_service import search_similar_chunks
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


SCENE_KEYWORDS = {
    "打斗": ["轰", "砸", "踢", "击出", "倒飞", "吐血", "一拳", "一剑", "一掌", "斩", "杀招", "出手", "闪避", "格挡", "闷哼", "砰", "暴起", "袭", "攻", "战", "交手", "对轰"],
    "打脸": ["跪下", "求饶", "饶命", "不敢", "饶了我", "服了", "跪地", "磕头", "认输", "饶过", "怕了", "崩溃"],
    "修炼": ["修炼", "突破", "灵力", "真气", "功法", "丹田", "经脉", "境界", "炼气", "筑基", "金丹", "元婴", "灵根", "打坐", "吐纳"],
    "感情": ["心动", "心跳", "脸红", "吻", "柔情", "温存", "柔软", "床", "拥抱", "牵手", "眼神", "温暖"],
    "阴谋": ["暗中", "阴谋", "算计", "陷阱", "悄悄", "秘密", "跟踪", "潜行", "密谋", "伪装", "偷听"],
}


def classify_scene_local(text: str) -> str:
    scores = {}
    for scene_type, keywords in SCENE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[scene_type] = score
    if scores:
        return max(scores, key=scores.get)
    return "日常"


def chunk_text(text: str, target_size: int = 350) -> list[str]:
    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) >= 5 and not is_noise(l.strip())]
    if not lines:
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
    if not chunks and lines:
        chunks.append("\n".join(lines))
    return chunks


# ── Step 1: Upload file only ──

@router.post("/upload", response_model=KnowledgeDocOut)
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    filename = file.filename or "unknown.txt"
    content = (await file.read()).decode("utf-8", errors="replace")

    # MD5 校验，防止重复入库
    file_md5 = hashlib.md5(content.encode()).hexdigest()
    existing = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.file_md5 == file_md5)
    )
    if existing.scalar_one_or_none():
        return JSONResponse(
            {"detail": f"文件已存在（MD5: {file_md5[:8]}...），请勿重复上传", "code": "duplicate"},
            status_code=409,
        )

    # 保存文件
    filepath = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{filename}")
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(content)

    doc = KnowledgeDocument(
        filename=filename,
        file_path=filepath,
        file_md5=file_md5,
        total_chars=len(content),
        status="uploaded",
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


# ── Step 2: Background processing ──


async def process_document(doc_id: uuid.UUID):
    """后台处理文档：切片 → 嵌入 → 分类 → 入库。进度写入 DB。"""
    try:
        async with async_session() as db:
            stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
            result = await db.execute(stmt)
            doc = result.scalar_one_or_none()
            if not doc:
                return
            doc.status = "processing"

            def add_log(stage, message, detail, progress):
                doc.processing_stage = stage
                doc.processing_progress = progress
                logs = list(doc.processing_log or [])
                logs.append({"stage": stage, "message": message, "detail": detail, "progress": progress})
                doc.processing_log = logs[-50:]

            async def flush_log(stage, message, detail, progress):
                add_log(stage, message, detail, progress)
                await db.flush()

            try:
                # 1. 读取文件
                await flush_log("reading", "读取文件...", doc.filename, 5)
                async with aiofiles.open(doc.file_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                total_chars = len(content)
                await flush_log("reading", "文件读取完成", f"{total_chars} 字符", 10)

                # 2. 切片
                await flush_log("chunking", "正在文本切片...", "按 350 字/段", 15)
                chunks = chunk_text(content, target_size=350)
                chunk_count = len(chunks)
                if chunk_count == 0:
                    await flush_log("error", "未能提取有效文本", "文件可能太短", 100)
                    doc.status = "error"
                    return
                await flush_log("chunking", "切片完成", f"共 {chunk_count} 段", 25)

                # 3. 嵌入
                await flush_log("embedding", "正在生成嵌入向量...", "加载 bge-small-zh-v1.5", 30)
                chunk_texts = list(chunks)
                embeddings = embed(chunk_texts)
                await flush_log("embedding", "向量生成完成", f"共 {len(embeddings)} 个", 60)

                # 4. 分类
                await flush_log("classifying", "正在场景分类...", f"本地关键词匹配 {chunk_count} 段", 65)
                scene_types = [classify_scene_local(c) for c in chunk_texts]
                await flush_log("classifying", "场景分类完成", f"{chunk_count} 段已标注", 80)

                # 5. 保存切片
                await flush_log("saving", "正在保存到数据库...", f"{chunk_count} 条记录", 85)
                for ct, emb, st in zip(chunks, embeddings, scene_types):
                    kc = KnowledgeChunk(
                        document_id=doc.id, content=ct, embedding=emb,
                        source_name=doc.filename.replace(".txt", ""),
                        scene_type=st, char_count=len(ct),
                    )
                    db.add(kc)

                doc.chunk_count = chunk_count
                doc.total_chars = total_chars
                doc.status = "ready"
                await flush_log("done", "入库完成", f"{chunk_count} 切片 · {total_chars} 字", 100)

            except Exception as e:
                add_log("error", f"处理失败: {str(e)[:100]}", "", 100)
                doc.status = "error"
                await db.flush()
            finally:
                await db.commit()
    except Exception as e:
        try:
            async with async_session() as db:
                stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
                result = await db.execute(stmt)
                doc = result.scalar_one_or_none()
                if doc:
                    doc.status = "error"
                    doc.processing_stage = "error"
                    doc.processing_progress = 100
                    doc.processing_log = [{"stage": "error", "message": f"致命错误: {str(e)[:100]}", "detail": "", "progress": 100}]
                    await db.commit()
        except Exception:
            pass


@router.post("/documents/{doc_id}/process")
async def start_processing(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc.status == "ready":
        return {"detail": "文档已处理完成", "status": "ready"}
    if doc.status == "processing":
        return {"detail": "文档正在处理中", "status": "processing"}

    doc.status = "processing"
    doc.processing_progress = 0
    doc.processing_log = []
    await db.flush()

    # 启动后台任务
    asyncio.create_task(process_document(doc_id))

    return {"detail": "处理已启动", "status": "processing", "doc_id": str(doc_id)}


@router.get("/documents/{doc_id}/progress", response_model=KnowledgeProgressOut)
async def get_progress(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc


@router.get("/documents/{doc_id}/content")
async def get_content(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from urllib.parse import quote
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not doc.file_path or not os.path.exists(doc.file_path):
        return Response("文件不存在", status_code=404)
    async with aiofiles.open(doc.file_path, "r", encoding="utf-8") as f:
        content = await f.read()
    safe_filename = quote(doc.filename)
    return Response(
        content, media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{safe_filename}",
        },
    )


# ── CRUD ──

@router.get("/documents", response_model=list[KnowledgeDocOut])
async def list_documents(db: AsyncSession = Depends(get_db)):
    stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    # 关联的 chunks 会被 cascade 删除
    db.delete(doc)
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
