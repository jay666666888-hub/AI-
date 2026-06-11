"""
微信通知服务 - 发送模板消息
"""
import httpx
from app.config import settings

async def get_wechat_access_token() -> str:
    """获取微信 access_token"""
    wx_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={settings.WX_APPID}&secret={settings.WX_SECRET}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(wx_url)
        data = response.json()
        if "access_token" in data:
            return data["access_token"]
        raise Exception(f"Failed to get access_token: {data}")

async def send_reminder_notification(wx_openid: str, title: str, remind_time: str) -> bool:
    """发送微信模板消息提醒"""
    try:
        access_token = await get_wechat_access_token()

        # 模板消息接口
        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"

        # 模板消息内容
        payload = {
            "touser": wx_openid,
            "template_id": "YOUR_TEMPLATE_ID",  # 需要在微信公众平台配置
            "page": "pages/index/index",  # 点击后跳转的页面
            "data": {
                "thing1": {"value": title},  # 任务标题
                "date2": {"value": remind_time},  # 提醒时间
                "phrase3": {"value": "待处理"}
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            result = response.json()
            if result.get("errcode") == 0:
                print(f"[WxNotifier] Sent notification to {wx_openid}")
                return True
            else:
                print(f"[WxNotifier] Failed: {result}")
                return False

    except Exception as e:
        print(f"[WxNotifier] Error: {e}")
        return False

async def send_habit_reminder(wx_openid: str, habit_title: str) -> bool:
    """发送习惯打卡提醒"""
    try:
        access_token = await get_wechat_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"

        payload = {
            "touser": wx_openid,
            "template_id": "YOUR_HABIT_TEMPLATE_ID",
            "page": "pages/habits/index",
            "data": {
                "thing1": {"value": f"习惯打卡: {habit_title}"},
                "date2": {"value": "现在"},
                "remark3": {"value": "点击完成打卡"}
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            result = response.json()
            return result.get("errcode") == 0

    except Exception as e:
        print(f"[WxNotifier] Habit reminder error: {e}")
        return False