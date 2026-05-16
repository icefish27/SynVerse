from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.knowledge import StyleExample
from app.schemas.knowledge import StyleExampleCreate, StyleExampleOut
import uuid

router = APIRouter(prefix="/api/style-examples", tags=["style-examples"])


@router.get("", response_model=list[StyleExampleOut])
async def list_examples(
    scene_type: str = Query(default="", description="场景类型"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(StyleExample).order_by(StyleExample.quality_rating.desc())
    if scene_type:
        stmt = stmt.where(StyleExample.scene_type == scene_type)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=StyleExampleOut, status_code=201)
async def create_example(data: StyleExampleCreate, db: AsyncSession = Depends(get_db)):
    example = StyleExample(**data.model_dump())
    db.add(example)
    await db.flush()
    await db.refresh(example)
    return example


@router.delete("/{example_id}", status_code=204)
async def delete_example(example_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(StyleExample).where(StyleExample.id == example_id)
    result = await db.execute(stmt)
    example = result.scalar_one()
    db.delete(example)
    await db.flush()
