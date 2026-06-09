"""
Monitor - 监控告警系统
集成 Uptime Kuma, 指标收集
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import subprocess
import requests
import os


@dataclass
class Metric:
    name: str
    value: float
    unit: str
    timestamp: datetime


@dataclass
class Alert:
    id: str
    severity: str  # critical, warning, info
    message: str
    timestamp: datetime
    resolved: bool = False


class Monitor:
    """监控告警系统"""

    def __init__(self, uptime_kuma_url: Optional[str] = None):
        self.uptime_kuma_url = uptime_kuma_url or os.getenv("UPKUMA_URL", "http://localhost:3001")
        self.metrics: List[Metric] = []
        self.alerts: List[Alert] = []

    def check_service(self, name: str, url: str) -> Dict[str, Any]:
        """检查服务状态"""
        try:
            start = datetime.now()
            response = requests.get(url, timeout=10)
            duration = (datetime.now() - start).total_seconds()

            status = "up" if response.status_code < 500 else "down"
            return {
                "name": name,
                "status": status,
                "url": url,
                "latency_ms": round(duration * 1000, 2),
                "status_code": response.status_code,
                "checked_at": datetime.now().isoformat()
            }
        except requests.exceptions.RequestException as e:
            return {
                "name": name,
                "status": "down",
                "url": url,
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }

    def record_metric(self, name: str, value: float, unit: str = "") -> None:
        """记录指标"""
        self.metrics.append(Metric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now()
        ))

    def get_metrics(self, name: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """获取指标历史"""
        metrics = self.metrics
        if name:
            metrics = [m for m in metrics if m.name == name]
        return [
            {"name": m.name, "value": m.value, "unit": m.unit, "timestamp": m.timestamp.isoformat()}
            for m in metrics[-limit:]
        ]

    def create_alert(self, severity: str, message: str) -> Alert:
        """创建告警"""
        alert = Alert(
            id=f"alert_{len(self.alerts) + 1}",
            severity=severity,
            message=message,
            timestamp=datetime.now()
        )
        self.alerts.append(alert)
        return alert

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                return True
        return False

    def get_active_alerts(self) -> List[Dict]:
        """获取活跃告警"""
        return [
            {"id": a.id, "severity": a.severity, "message": a.message, "timestamp": a.timestamp.isoformat()}
            for a in self.alerts if not a.resolved
        ]

    def push_to_uptime_kuma(self, monitor_id: int, status: str) -> bool:
        """推送到 Uptime Kuma"""
        try:
            import os
            api_key = os.getenv("UPKUMA_API_KEY")
            if not api_key:
                return False

            response = requests.post(
                f"{self.uptime_kuma_url}/api/push/{monitor_id}",
                json={"status": status, "msg": "OK", "ping": ""},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False


if __name__ == "__main__":
    import os
    monitor = Monitor()

    # 示例：检查服务
    result = monitor.check_service("Google", "https://google.com")
    print(f"服务状态: {result['status']}, 延迟: {result.get('latency_ms', 'N/A')}ms")

__exports__ = ['Alert', 'Metric', 'Monitor']


