"""
Uptime Kuma 集成适配器
将 uptime-kuma (https://github.com/louislam/uptime-kuma) 作为监控平台集成
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import requests
import os


@dataclass
class Monitor:
    """监控项"""
    id: int
    name: str
    url: str
    status: str  # up, down, paused
    uptime: float  # 百分比
    latency: float  # ms


class UptimeKumaAdapter:
    """
    Uptime Kuma 适配器 - 自托管监控工具 (86k stars)

    功能:
    - HTTP/HTTPS/TCP 监控
    - 多种通知渠道
    - 状态页面
    - API 集成
    """

    def __init__(self, base_url: str = "http://localhost:3001", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("UPKUMA_API_KEY", "")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def is_connected(self) -> bool:
        """检查连接状态"""
        try:
            response = self.session.get(f"{self.base_url}/api/abouts", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_monitors(self) -> List[Monitor]:
        """列出所有监控项"""
        try:
            response = self.session.get(f"{self.base_url}/api/monitors", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [
                    Monitor(
                        id=m.get("id", 0),
                        name=m.get("name", ""),
                        url=m.get("url", ""),
                        status=m.get("status", "unknown"),
                        uptime=m.get("uptime", 0),
                        latency=m.get("latency", 0)
                    )
                    for m in data
                ]
        except Exception as e:
            print(f"获取监控列表失败: {e}")
        return []

    def add_monitor(self, name: str, url: str, monitor_type: str = "http", interval: int = 60) -> Dict[str, Any]:
        """添加监控项"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/monitors",
                json={
                    "name": name,
                    "url": url,
                    "type": monitor_type,
                    "interval": interval
                },
                timeout=10
            )
            if response.status_code in (200, 201):
                return {"success": True, "id": response.json().get("monitorID")}
            return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def remove_monitor(self, monitor_id: int) -> bool:
        """删除监控项"""
        try:
            response = self.session.delete(f"{self.base_url}/api/monitors/{monitor_id}", timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def get_heartbeats(self, monitor_id: int, limit: int = 100) -> List[Dict]:
        """获取监控心跳历史"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/monitors/{monitor_id}/heartbeats",
                params={"limit": limit},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("heartbeats", [])
        except Exception:
            pass
        return []

    def push_status(self, monitor_id: int, status: str = "up", msg: str = "OK", ping: float = None) -> bool:
        """
        通过 API push 状态

        用于监控系统自检或第三方集成
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/push/{monitor_id}",
                params={
                    "status": status,
                    "msg": msg,
                    "ping": ping
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False


class MonitorManager:
    """监控管理器 - 集成到 Hermes"""

    def __init__(self, uptime_kuma_url: Optional[str] = None):
        self.adapter = UptimeKumaAdapter(uptime_kuma_url)
        self.monitored_services: Dict[str, Dict] = {}

    def add_service(self, name: str, url: str, check_interval: int = 60) -> Dict[str, Any]:
        """添加服务监控"""
        result = self.adapter.add_monitor(name, url, interval=check_interval)
        if result.get("success"):
            self.monitored_services[name] = {"url": url, "id": result.get("id")}
        return result

    def check_service(self, name: str) -> Dict[str, Any]:
        """检查服务状态"""
        if name not in self.monitored_services:
            return {"error": f"未知服务: {name}"}

        service = self.monitored_services[name]
        # 使用 push_status 自检
        # 实际使用时应该在服务端配置 push

        return {
            "name": name,
            "url": service["url"],
            "status": "unknown",  # 需要通过 heartbeat API 获取
            "last_check": "需通过 Uptime Kuma UI 查看"
        }

    def get_all_status(self) -> List[Dict[str, Any]]:
        """获取所有服务状态"""
        monitors = self.adapter.list_monitors()
        return [
            {
                "id": m.id,
                "name": m.name,
                "status": m.status,
                "uptime": f"{m.uptime:.2f}%",
                "latency": f"{m.latency:.0f}ms"
            }
            for m in monitors
        ]

    def generate_docker_compose(self) -> str:
        """生成 Uptime Kuma Docker Compose"""
        return '''version: '3.8'

services:
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    container_name: uptime-kuma
    restart: always
    ports:
      - "3001:3001"
    volumes:
      - uptime-kuma-data:/app/data
    environment:
      - UPTIME_KUMA_PORT=3001

volumes:
  uptime-kuma-data:
'''


if __name__ == "__main__":
    print("=== Uptime Kuma 集成适配器 ===\n")

    adapter = UptimeKumaAdapter()

    print(f"Uptime Kuma 连接状态: {'已连接' if adapter.is_connected() else '未连接 (请启动 Uptime Kuma)'}")
    print(f"监控项数量: {len(adapter.list_monitors())}")

    print("\nDocker 启动命令:")
    print("  docker run -d -p 3001:3001 --name uptime-kuma louislam/uptime-kuma:latest")

    print("\n✓ Uptime Kuma 适配器就绪")
