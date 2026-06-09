from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.models.models import User, Note
from app.schemas.schemas import NoteCreate, NoteUpdate, NoteResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("")
async def get_notes(
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取笔记列表"""
    query = select(Note).where(Note.user_id == current_user.id).where(Note.deleted_at.is_(None))

    if status:
        query = query.where(Note.status == status)

    query = query.order_by(Note.created_at.desc())
    result = await db.execute(query)
    notes = result.scalars().all()
    return [NoteResponse.model_validate(n) for n in notes]

@router.post("")
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建笔记（默认进入 Inbox）"""
    note = Note(**note_data.model_dump(), user_id=current_user.id, status="inbox")
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)

@router.put("/{note_id}")
async def update_note(
    note_id: UUID,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新笔记"""
    result = await db.execute(
        select(Note)
        .where(Note.id == note_id)
        .where(Note.user_id == current_user.id)
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")

    update_data = note_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)

    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)

@router.delete("/{note_id}")
async def delete_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除笔记（软删除）"""
    result = await db.execute(
        select(Note)
        .where(Note.id == note_id)
        .where(Note.user_id == current_user.id)
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")

    note.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "笔记已删除"}

@router.get("/inbox/count")
async def get_inbox_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取 Inbox数量"""
    from sqlalchemy import func
    result = await db.execute(
        select(func.count(Note.id))
        .where(Note.user_id == current_user.id)
        .where(Note.status == "inbox")
        .where(Note.deleted_at.is_(None))
    )
    count = result.scalar()
    return {"count": count}