from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.core.database import get_db
from app.core.minio import minio_client, ensure_bucket
from app.models.novel import Novel
from app.schemas.novel import NovelCreate, NovelUpdate, NovelOut
import uuid

router = APIRouter(prefix="/api/novels", tags=["novels"])


@router.get("", response_model=list[NovelOut])
async def list_novels(
    search: str = Query(default="", description="搜索标题"),
    sort: str = Query(default="updated_at", description="排序字段"),
    tag: str = Query(default="", description="类型标签筛选"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Novel)
    if search:
        stmt = stmt.where(Novel.title.ilike(f"%{search}%"))
    if tag:
        stmt = stmt.where(Novel.type_tags.contains([tag]))
    if sort == "created_at":
        stmt = stmt.order_by(Novel.created_at.desc())
    else:
        stmt = stmt.order_by(Novel.updated_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=NovelOut, status_code=201)
async def create_novel(data: NovelCreate, db: AsyncSession = Depends(get_db)):
    novel = Novel(**data.model_dump())
    db.add(novel)
    await db.flush()
    await db.refresh(novel)
    return novel


@router.get("/{novel_id}", response_model=NovelOut)
async def get_novel(novel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Novel).where(Novel.id == novel_id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.put("/{novel_id}", response_model=NovelOut)
async def update_novel(novel_id: uuid.UUID, data: NovelUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Novel).where(Novel.id == novel_id)
    result = await db.execute(stmt)
    novel = result.scalar_one()
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(novel, key, val)
    await db.flush()
    await db.refresh(novel)
    return novel


@router.delete("/{novel_id}", status_code=204)
async def delete_novel(novel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Novel).where(Novel.id == novel_id)
    result = await db.execute(stmt)
    novel = result.scalar_one()
    await db.delete(novel)
    await db.flush()


@router.post("/{novel_id}/cover", response_model=NovelOut)
async def upload_cover(
    novel_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Novel).where(Novel.id == novel_id)
    result = await db.execute(stmt)
    novel = result.scalar_one()

    bucket = ensure_bucket()
    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "png"
    object_name = f"covers/{novel_id}.{ext}"
    minio_client.put_object(
        bucket, object_name, file.file, length=-1, part_size=5 * 1024 * 1024,
        content_type=file.content_type or "image/png",
    )
    novel.cover_url = f"/api/files/{object_name}"
    await db.flush()
    await db.refresh(novel)
    return novel
