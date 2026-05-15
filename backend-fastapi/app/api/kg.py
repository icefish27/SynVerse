from __future__ import annotations
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.neo4j import driver
from app.models.novel import Chapter, Character, Novel
from app.services.ai_service import chat_simple, LIGHT_MODEL
import uuid

router = APIRouter(prefix="/api/novels", tags=["knowledge-graph"])


async def _get_chapters_text(novel_id: uuid.UUID, db: AsyncSession) -> str:
    stmt = select(Chapter).where(Chapter.novel_id == novel_id, Chapter.content.isnot(None)).order_by(Chapter.chapter_number).limit(10)
    result = await db.execute(stmt)
    chapters = result.scalars().all()
    if not chapters:
        stmt2 = select(Novel).where(Novel.id == novel_id)
        result2 = await db.execute(stmt2)
        novel = result2.scalar_one_or_none()
        # 返回空内容，但小说存在
        return ""
    return "\n\n".join([f"第{c.chapter_number}章 {c.title or ''}\n{c.content[:1000]}" for c in chapters])


@router.post("/{novel_id}/kg/extract")
async def extract_entities(novel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    text = await _get_chapters_text(novel_id, db)
    if not text.strip():
        # 没有章节内容，返回角色的基本信息
        stmt = select(Character).where(Character.novel_id == novel_id)
        result = await db.execute(stmt)
        characters = result.scalars().all()
        nodes = [{"id": c.name, "name": c.name, "type": "Character", "description": f"{c.role_type} - {c.personality or ''}"} for c in characters]
        return {"nodes": nodes, "edges": []}

    prompt = f"""从以下小说片段提取实体和关系。返回 JSON 格式：{{"nodes": [...], "edges": [...]}}

每个 node 包含：id(name), name, type(Character/Location/Item/Event/Faction), description
每个 edge 包含：source(name), target(name), relation(BELONGS_TO/OWNS/LOCATED_AT/KNOWS/OPPOSES/ALLIED_WITH/INVOLVES)

小说内容：
{text[:6000]}

只返回 JSON，不要其他内容。"""

    result = await chat_simple(prompt, "你是实体关系提取专家。", LIGHT_MODEL, temperature=0.1, max_tokens=2048)
    try:
        clean = result.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(clean)
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
    except Exception:
        nodes, edges = [], []

    # 写入 Neo4j
    novel_id_str = str(novel_id)
    try:
        async with driver.session() as session:
            for node in nodes:
                await session.run(f"""
                    MERGE (n:{node['type']} {{name: $name, novel_id: $novel_id}})
                    SET n.description = $desc
                """, name=node.get("name", node.get("id", "")), novel_id=novel_id_str,
                   desc=node.get("description", "")[:500])
            for edge in edges:
                src = edge.get("source", "")
                tgt = edge.get("target", "")
                rel = edge.get("relation", "KNOWS").upper()
                if src and tgt:
                    await session.run(f"""
                        MATCH (a {{name: $src, novel_id: $novel_id}})
                        MATCH (b {{name: $tgt, novel_id: $novel_id}})
                        MERGE (a)-[r:{rel}]->(b)
                    """, src=src, tgt=tgt, novel_id=novel_id_str)
    except Exception:
        pass  # Neo4j 不可用时静默降级

    return {"nodes": nodes[:30], "edges": edges[:50]}


@router.get("/{novel_id}/kg/search")
async def search_kg(novel_id: uuid.UUID, q: str = Query(default=""), db: AsyncSession = Depends(get_db)):
    # 从 PG 查角色
    stmt = select(Character).where(Character.novel_id == novel_id)
    if q:
        stmt = stmt.where(Character.name.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    characters = result.scalars().all()
    nodes = [{"id": c.name, "name": c.name, "type": "Character", "description": f"{c.role_type} - {c.personality or ''}"} for c in characters]

    # 从 Neo4j 查关系
    edges = []
    novel_id_str = str(novel_id)
    try:
        async with driver.session() as session:
            if q:
                cypher = """MATCH (a)-[r]->(b) WHERE a.novel_id = $nid AND a.name CONTAINS $q RETURN a.name as source, type(r) as relation, b.name as target LIMIT 50"""
                neo_result = await session.run(cypher, nid=novel_id_str, q=q)
            else:
                cypher = """MATCH (a)-[r]->(b) WHERE a.novel_id = $nid RETURN a.name as source, type(r) as relation, b.name as target LIMIT 50"""
                neo_result = await session.run(cypher, nid=novel_id_str)

            async for record in neo_result:
                edges.append({"source": record["source"], "target": record["target"], "relation": record["relation"]})
    except Exception:
        pass

    return {"nodes": nodes, "edges": edges}


@router.get("/{novel_id}/kg/graph")
async def get_graph(novel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """获取完整的图数据用于可视化。"""
    novel_id_str = str(novel_id)
    nodes = []
    edges = []

    # 从 PG 获取角色
    stmt = select(Character).where(Character.novel_id == novel_id)
    result = await db.execute(stmt)
    for c in result.scalars().all():
        nodes.append({"id": c.name, "name": c.name, "type": "Character", "category": 0,
                       "description": f"{c.role_type}"})

    # 从 Neo4j 获取所有节点和关系
    try:
        async with driver.session() as session:
            neo_nodes = await session.run(
                "MATCH (n) WHERE n.novel_id = $nid RETURN n.name as name, labels(n)[0] as type, n.description as description",
                nid=novel_id_str)
            async for rec in neo_nodes:
                name = rec["name"]
                if not any(n["id"] == name for n in nodes):
                    type_map = {"Character": 0, "Location": 1, "Item": 2, "Event": 3, "Faction": 4}
                    nodes.append({"id": name, "name": name, "type": rec["type"] or "Unknown",
                                   "category": type_map.get(rec["type"], 5),
                                   "description": rec["description"] or ""})

            neo_edges = await session.run(
                "MATCH (a)-[r]->(b) WHERE a.novel_id = $nid RETURN a.name as source, type(r) as relation, b.name as target LIMIT 100",
                nid=novel_id_str)
            async for rec in neo_edges:
                edges.append({"source": rec["source"], "target": rec["target"], "label": rec["relation"]})
    except Exception:
        pass

    return {"nodes": nodes, "edges": edges}
