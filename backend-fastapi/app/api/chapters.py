from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.novel import Chapter, Novel
from app.schemas.novel import ChapterCreate, ChapterUpdate, ChapterOut, ChapterBrief
import uuid

router = APIRouter(prefix="/api", tags=["chapters"])


async def _get_novel(novel_id: uuid.UUID, db: AsyncSession):
    stmt = select(Novel).where(Novel.id == novel_id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/novels/{novel_id}/chapters", response_model=list[ChapterBrief])
async def list_chapters(novel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Chapter).where(Chapter.novel_id == novel_id).order_by(Chapter.chapter_number)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/novels/{novel_id}/chapters", response_model=ChapterOut, status_code=201)
async def create_chapter(novel_id: uuid.UUID, data: ChapterCreate, db: AsyncSession = Depends(get_db)):
    await _get_novel(novel_id, db)
    # 自动计算章节号
    stmt = select(func.coalesce(func.max(Chapter.chapter_number), 0)).where(Chapter.novel_id == novel_id)
    result = await db.execute(stmt)
    next_num = result.scalar() + 1
    chapter = Chapter(novel_id=novel_id, chapter_number=next_num, title=data.title, content=data.content)
    chapter.word_count = len(data.content) if data.content else 0
    db.add(chapter)
    # 更新小说的总章节数和总字数
    novel = await _get_novel(novel_id, db)
    novel.total_chapters = next_num
    novel.total_words = (novel.total_words or 0) + chapter.word_count
    await db.flush()
    await db.refresh(chapter)
    return chapter


@router.get("/chapters/{chapter_id}", response_model=ChapterOut)
async def get_chapter(chapter_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Chapter).where(Chapter.id == chapter_id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.put("/chapters/{chapter_id}", response_model=ChapterOut)
async def update_chapter(chapter_id: uuid.UUID, data: ChapterUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Chapter).where(Chapter.id == chapter_id)
    result = await db.execute(stmt)
    chapter = result.scalar_one()
    old_word_count = chapter.word_count
    for key, val in data.model_dump(exclude_unset=True).items():
        if key == "content" and val is not None:
            chapter.word_count = len(val)
        setattr(chapter, key, val)
    # 更新小说总字数
    if data.content is not None:
        stmt2 = select(Novel).where(Novel.id == chapter.novel_id)
        res2 = await db.execute(stmt2)
        novel = res2.scalar_one()
        novel.total_words = (novel.total_words or 0) - old_word_count + chapter.word_count
    await db.flush()
    await db.refresh(chapter)
    return chapter


@router.delete("/chapters/{chapter_id}", status_code=204)
async def delete_chapter(chapter_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Chapter).where(Chapter.id == chapter_id)
    result = await db.execute(stmt)
    chapter = result.scalar_one()
    # 更新小说统计
    stmt2 = select(Novel).where(Novel.id == chapter.novel_id)
    res2 = await db.execute(stmt2)
    novel = res2.scalar_one()
    novel.total_chapters = max(0, (novel.total_chapters or 1) - 1)
    novel.total_words = max(0, (novel.total_words or 0) - (chapter.word_count or 0))
    db.delete(chapter)
    await db.flush()
