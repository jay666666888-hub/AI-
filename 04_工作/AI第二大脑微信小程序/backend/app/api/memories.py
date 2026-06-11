"""
记忆库 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.models.models import User, Memory
from app.schemas.schemas import MemoryCreate, MemoryResponse, MemoryUpdate
from app.api.deps import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def memory_to_dict(m: Memory) -> dict:
    return {
        "id": m.id,
        "user_id": m.user_id,
        "title": m.title,
        "content": m.content,
        "tags": m.tags or [],
        "memory_type": m.memory_type,
        "ai_metadata": m.ai_metadata,
        "created_at": m.created_at,
        "updated_at": m.updated_at,
    }


@router.get("", response_model=List[MemoryResponse])
async def get_memories(
    tag: Optional[str] = None,
    memory_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取记忆列表"""
    query = select(Memory).where(Memory.user_id == current_user.id)

    if tag:
        query = query.where(Memory.tags.contains([tag]))
    if memory_type:
        query = query.where(Memory.memory_type == memory_type)

    query = query.order_by(Memory.created_at.desc())
    result = await db.execute(query)
    memories = result.scalars().all()
    return [MemoryResponse.parse_obj(memory_to_dict(m)) for m in memories]


@router.post("", response_model=MemoryResponse)
@limiter.limit("30/minute")
async def create_memory(
    request: Request,
    memory_data: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建记忆"""
    memory = Memory(
        user_id=current_user.id,
        title=memory_data.title,
        content=memory_data.content,
        tags=memory_data.tags,
        memory_type=memory_data.memory_type,
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return MemoryResponse.parse_obj(memory_to_dict(memory))


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个记忆"""
    query = select(Memory).where(
        and_(Memory.id == memory_id, Memory.user_id == current_user.id)
    )
    result = await db.execute(query)
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    return MemoryResponse.parse_obj(memory_to_dict(memory))


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: UUID,
    memory_data: MemoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新记忆"""
    query = select(Memory).where(
        and_(Memory.id == memory_id, Memory.user_id == current_user.id)
    )
    result = await db.execute(query)
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")

    if memory_data.title is not None:
        memory.title = memory_data.title
    if memory_data.content is not None:
        memory.content = memory_data.content
    if memory_data.tags is not None:
        memory.tags = memory_data.tags
    if memory_data.memory_type is not None:
        memory.memory_type = memory_data.memory_type

    await db.commit()
    await db.refresh(memory)
    return MemoryResponse.parse_obj(memory_to_dict(memory))


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除记忆"""
    query = select(Memory).where(
        and_(Memory.id == memory_id, Memory.user_id == current_user.id)
    )
    result = await db.execute(query)
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")

    await db.delete(memory)
    await db.commit()
    return {"message": "已删除"}