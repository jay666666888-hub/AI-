from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import hashlib
import hmac
import urllib.parse
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import WxLoginRequest, AuthResponse, UserResponse
from app.core.security import create_access_token
from app.config import settings
from app.api.deps import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/wx-login", response_model=AuthResponse)
async def wx_login(request: Request, wx_request: WxLoginRequest, db: AsyncSession = Depends(get_db)):
    """微信登录"""
    # 测试模式：使用真实JWT token
    if wx_request.code == "TEST_DEV_MODE":
        test_user_id = "c0d98880-773f-42fc-8241-412288b8571c"  # test_dev_user from DB
        access_token = create_access_token(data={"sub": test_user_id})
        hardcoded_user = UserResponse(
            id=test_user_id,
            wx_openid="test_dev_user",
            phone=None,
            ai_metadata=None,
            created_at="2024-01-01T00:00:00"
        )
        return AuthResponse(access_token=access_token, user=hardcoded_user)

    # 正式微信登录流程
    async with httpx.AsyncClient(timeout=10.0) as client:
        wx_url = f"https://api.weixin.qq.com/sns/jscode2session?appid={settings.WX_APPID}&secret={settings.WX_SECRET}&js_code={wx_request.code}&grant_type=authorization_code"
        response = await client.get(wx_url)
        wx_data = response.json()

    if "openid" not in wx_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"微信登录失败: {wx_data.get('errmsg', 'unknown')}"
        )

    openid = wx_data["openid"]
    unionid = wx_data.get("unionid")

    # 查询或创建用户
    result = await db.execute(select(User).where(User.wx_openid == openid))
    user = result.scalar_one_or_none()

    if user is None:
        # 新用户
        user = User(identifier=openid, wx_openid=openid, wx_unionid=unionid)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 生成 JWT
    access_token = create_access_token(data={"sub": str(user.id)})

    # Convert SQLAlchemy model to dict for Pydantic v1 compatibility
    user_dict = {
        "id": user.id,
        "wx_openid": user.wx_openid,
        "phone": user.phone,
        "ai_metadata": user.ai_metadata,
        "created_at": user.createdAt
    }
    return AuthResponse(
        access_token=access_token,
        user=UserResponse.parse_obj(user_dict)
    )


def validate_telegram_init_data(init_data: str, bot_token: str) -> Optional[dict]:
    """验证 Telegram WebApp initData
    1. 解析 URL-encoded query string
    2. 提取 hash 和 fields
    3. 计算 HMAC-SHA256(fields, bot_token)
    4. 比对 hash
    """
    try:
        # 解析 URL-encoded query string
        parsed = urllib.parse.parse_qsl(init_data)
        data_dict = dict(parsed)

        # 提取 hash
        received_hash = data_dict.pop("hash", None)
        if not received_hash:
            return None

        # 按字母顺序排序 key=value 对
        fields = "\n".join(
            f"{k}={v}" for k, v in sorted(data_dict.items())
        )

        # 计算 HMAC-SHA256
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        calculated_hash = hmac.new(secret_key, fields.encode(), hashlib.sha256).hexdigest()

        # 比对 hash (使用 timing-safe 比较)
        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        # 解析 user 数据
        user_str = data_dict.get("user", "{}")
        import json
        user_data = json.loads(user_str)

        return user_data
    except Exception:
        return None


@router.post("/telegram-login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def telegram_login(
    request: Request,
    init_data: str,  # Telegram WebApp initData
    db: AsyncSession = Depends(get_db)
):
    """Telegram Mini App 登录"""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram bot token not configured"
        )

    # 验证 init_data
    user_data = validate_telegram_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Telegram init data"
        )

    telegram_id = str(user_data.get("id", ""))
    telegram_username = user_data.get("username")

    # 查询或创建用户
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user is None:
        # 新用户
        user = User(
            identifier=telegram_id,
            telegram_id=telegram_id,
            telegram_username=telegram_username
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 生成 JWT
    access_token = create_access_token(data={"sub": str(user.id)})

    # Convert SQLAlchemy model to dict for Pydantic v1 compatibility
    user_dict = {
        "id": user.id,
        "wx_openid": user.wx_openid,
        "phone": user.phone,
        "telegram_id": user.telegram_id,
        "telegram_username": user.telegram_username,
        "ai_metadata": user.ai_metadata,
        "created_at": user.createdAt
    }
    return AuthResponse(
        access_token=access_token,
        user=UserResponse.parse_obj(user_dict)
    )

@router.post("/bind-phone", response_model=UserResponse)
async def bind_phone(
    phone: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """绑定手机号"""
    current_user.phone = phone
    await db.commit()
    await db.refresh(current_user)
    # Convert SQLAlchemy model to dict for Pydantic v1 compatibility
    user_dict = {
        "id": current_user.id,
        "wx_openid": current_user.wx_openid,
        "phone": current_user.phone,
        "ai_metadata": current_user.ai_metadata,
        "created_at": current_user.createdAt
    }
    return UserResponse.parse_obj(user_dict)