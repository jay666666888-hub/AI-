from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import WxLoginRequest, AuthResponse, UserResponse
from app.core.security import create_access_token
from app.config import settings

router = APIRouter()

@router.post("/wx-login", response_model=AuthResponse)
async def wx_login(request: WxLoginRequest, db: AsyncSession = Depends(get_db)):
    """微信登录"""
    # 调用微信接口获取 openid
    async with httpx.AsyncClient() as client:
        wx_url = f"https://api.weixin.qq.com/sns/jscode2session?appid={settings.WX_APPID}&secret={settings.WX_SECRET}&js_code={request.code}&grant_type=authorization_code"
        response = await client.get(wx_url)
        wx_data = response.json()

    if "openid" not in wx_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信登录失败"
        )

    openid = wx_data["openid"]
    unionid = wx_data.get("unionid")

    # 查询或创建用户
    result = await db.execute(select(User).where(User.wx_openid == openid))
    user = result.scalar_one_or_none()

    if user is None:
        # 新用户
        user = User(wx_openid=openid, wx_unionid=unionid)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 生成 JWT
    access_token = create_access_token(data={"sub": str(user.id)})

    return AuthResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
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
    return UserResponse.model_validate(current_user)