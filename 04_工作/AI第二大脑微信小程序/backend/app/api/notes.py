from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.models.models import User, Note, Task, Project, Memory
from app.schemas.schemas import NoteCreate, NoteUpdate, NoteResponse, NoteConvertRequest, NoteConvertResponse
from app.api.deps import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def note_to_dict(note: Note) -> dict:
    """Convert SQLAlchemy Note model to dict for Pydantic v1"""
    # Convert PostgreSQL ARRAY to list and JSONB to dict
    tags = list(note.tags) if note.tags else []
    ai_metadata = dict(note.ai_metadata) if note.ai_metadata else None
    return {
        "id": note.id,
        "user_id": note.user_id,
        "content": note.content,
        "status": note.status,
        "tags": tags,
        "ai_metadata": ai_metadata,
        "created_at": note.created_at,
        "updated_at": note.updated_at,
    }

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
    return [NoteResponse.parse_obj(note_to_dict(n)) for n in notes]

@router.post("")
@limiter.limit("30/minute")
async def create_note(
    request: Request,
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建笔记（默认进入 Inbox）"""
    note = Note(**note_data.dict(), user_id=current_user.id, status="inbox")
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteResponse.parse_obj(note_to_dict(note))

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

    update_data = note_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)

    await db.commit()
    await db.refresh(note)
    return NoteResponse.parse_obj(note_to_dict(note))

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


@router.post("/{note_id}/convert", response_model=NoteConvertResponse)
async def convert_note(
    note_id: UUID,
    convert_data: NoteConvertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """将笔记转换为任务/项目/记忆"""
    # 获取原笔记
    result = await db.execute(
        select(Note)
        .where(Note.id == note_id)
        .where(Note.user_id == current_user.id)
        .where(Note.deleted_at.is_(None))
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")

    if note.status != "inbox":
        raise HTTPException(status_code=400, detail="只能转换 Inbox 中的笔记")

    target_type = convert_data.target_type
    if target_type not in ("task", "project", "memory"):
        raise HTTPException(status_code=400, detail="target_type 必须是 task/project/memory 之一")

    title = convert_data.title or note.content[:100]
    content = note.content

    if target_type == "task":
        #转换为任务
        task = Task(
            user_id=current_user.id,
            project_id=convert_data.project_id,
            type=convert_data.task_type or "todo",
            title=title,
            detail=content,
            detail_source="manual",
            status="active",
            tags=note.tags or [],
            ai_metadata={"source": "note_convert", "original_note_id": str(note.id)}
        )
        db.add(task)
        note.status = "processed"

    elif target_type == "project":
        # 转换为项目
        project = Project(
            user_id=current_user.id,
            title=title,
            description=content,
            status="active",
            tags=note.tags or [],
            ai_metadata={"source": "note_convert", "original_note_id": str(note.id)}
        )
        db.add(project)
        note.status = "processed"

    else:  # memory
        # 转换为记忆
        memory = Memory(
            user_id=current_user.id,
            title=title,
            content=content,
            tags=note.tags or [],
            memory_type="personal",
            ai_metadata={"source": "note_convert", "original_note_id": str(note.id)}
        )
        db.add(memory)
        note.status = "processed"

    await db.commit()

    return NoteConvertResponse(
        original_note_id=note.id,
        converted_to=target_type,
        converted_id=task.id if target_type == "task" else (project.id if target_type == "project" else memory.id),
        message=f"笔记已转换为{target_type}"
    )