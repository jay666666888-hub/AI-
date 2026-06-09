#!/usr/bin/env python3
"""
Grafana Adapter - 监控可观测层集成
L10 监控可观测层
"""

import requests
from typing import Optional, Dict, Any, List


class GrafanaAdapter:
    """Grafana 监控适配器"""

    def __init__(self, url: str = "http://localhost:3000",
                 api_key: str = None):
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    # ==================== Dashboard API ====================

    def list_dashboards(self) -> List[Dict[str, Any]]:
        """列出所有仪表盘"""
        resp = requests.get(
            f"{self.url}/api/search",
            headers=self.headers,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def get_dashboard(self, uid: str) -> Dict[str, Any]:
        """获取仪表盘"""
        resp = requests.get(
            f"{self.url}/api/dashboards/uid/{uid}",
            headers=self.headers,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def create_dashboard(self, dashboard: Dict[str, Any],
                        folder: str = "AI Ecosystem") -> Dict[str, Any]:
        """创建仪表盘"""
        payload = {
            "dashboard": dashboard,
            "folderName": folder,
            "overwrite": True
        }
        resp = requests.post(
            f"{self.url}/api/dashboards/db",
            json=payload,
            headers=self.headers,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def delete_dashboard(self, uid: str) -> bool:
        """删除仪表盘"""
        resp = requests.delete(
            f"{self.url}/api/dashboards/uid/{uid}",
            headers=self.headers,
            timeout=10
        )
        return resp.status_code in (200, 204)

    # ==================== DataSource API ====================

    def list_datasources(self) -> List[Dict[str, Any]]:
        """列出所有数据源"""
        resp = requests.get(
            f"{self.url}/api/datasources",
            headers=self.headers,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def create_datasource(self, datasource: Dict[str, Any]) -> int:
        """创建数据源"""
        resp = requests.post(
            f"{self.url}/api/datasources",
            json=datasource,
            headers=self.headers,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json().get("datasource", {}).get("id", 0)

    # ==================== Alert API ====================

    def list_alerts(self) -> List[Dict[str, Any]]:
        """列出所有告警"""
        resp = requests.get(
            f"{self.url}/api/alerts",
            headers=self.headers,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def create_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """创建告警规则"""
        resp = requests.post(
            f"{self.url}/api/alerts",
            json=alert,
            headers=self.headers,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()


class SigNozAdapter:
    """SigNoz 可观测性适配器"""

    def __init__(self, url: str = "http://localhost:3301",
                 api_key: str = None):
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}


class OpenObserveAdapter:
    """OpenObserve 日志/指标/链路适配器"""

    def __init__(self, url: str = "http://localhost:5080",
                 user: str = "admin", password: str = "admin"):
        self.url = url.rstrip("/")
        self.auth = (user, password)

    def list_logs(self, query: str = "*", limit: int = 100) -> List[Dict[str, Any]]:
        """查询日志"""
        resp = requests.get(
            f"{self.url}/api/default/_search",
            json={
                "query": {"sql": query, "stream": "logs"},
                "from": 0,
                "size": limit
            },
            auth=self.auth,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    def list_metrics(self, metric: str = None) -> List[Dict[str, Any]]:
        """列出指标"""
        params = {}
        if metric:
            params["name"] = metric
        resp = requests.get(
            f"{self.url}/api/default/metrics",
            params=params,
            auth=self.auth,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json().get("data", [])