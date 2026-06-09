#!/usr/bin/env python3
"""
AIOps Adapter - 运维自动化层集成
L18 运维自动化层
"""

import subprocess
import json
from typing import Dict, Any, List, Optional


class N8NAdapter:
    """n8n 工作流自动化适配器"""

    def __init__(self, url: str = "http://localhost:5678"):
        self.url = url.rstrip("/")
        self.api_key = None

    def set_api_key(self, api_key: str) -> None:
        """设置 API Key"""
        self.api_key = api_key

    def list_workflows(self) -> List[Dict[str, Any]]:
        """列出所有工作流"""
        import requests
        headers = {"X-N8N-API-KEY": self.api_key} if self.api_key else {}
        resp = requests.get(
            f"{self.url}/rest/workflows",
            headers=headers,
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("data", [])
        return []

    def trigger_workflow(self, workflow_id: str,
                         body: Dict = None) -> Dict[str, Any]:
        """触发工作流"""
        import requests
        headers = {"X-N8N-API-KEY": self.api_key} if self.api_key else {}
        resp = requests.post(
            f"{self.url}/rest/webhook/{workflow_id}/trigger",
            json=body or {},
            headers=headers,
            timeout=30
        )
        return {
            "success": resp.status_code in (200, 201),
            "output": resp.json() if resp.status_code == 200 else None,
            "error": resp.text if resp.status_code != 200 else None
        }

    def activate_workflow(self, workflow_id: str) -> bool:
        """激活工作流"""
        import requests
        headers = {"X-N8N-API-KEY": self.api_key} if self.api_key else {}
        resp = requests.post(
            f"{self.url}/rest/workflows/{workflow_id}/activate",
            headers=headers,
            timeout=10
        )
        return resp.status_code == 200


class FastAPIAdapter:
    """FastAPI 应用管理适配器"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()

    def start_server(self, host: str = "0.0.0.0",
                     port: int = 8000, reload: bool = True) -> Dict[str, Any]:
        """启动 FastAPI 服务器"""
        cmd = ["uvicorn", "main:app", "--host", host, "--port", str(port)]
        if reload:
            cmd.append("--reload")

        result = subprocess.run(
            cmd,
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def run_tests(self) -> Dict[str, Any]:
        """运行测试"""
        result = subprocess.run(
            ["pytest", "-v"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout
        }


class GrafanaAlertingAdapter:
    """Grafana 智能告警适配器"""

    def __init__(self, url: str = "http://localhost:3000",
                 api_key: str = None):
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def create_alert_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """创建告警规则"""
        import requests
        resp = requests.post(
            f"{self.url}/api/ruler/provisioning/alert-rules",
            json=rule,
            headers=self.headers,
            timeout=10
        )
        return {
            "success": resp.status_code in (200, 201),
            "error": resp.text if resp.status_code != 200 else None
        }

    def list_alert_rules(self, folder: str = "ai-ecosystem",
                         group: str = "default") -> List[Dict]:
        """列出告警规则"""
        import requests
        resp = requests.get(
            f"{self.url}/api/ruler/provisioning/alert-rules",
            headers=self.headers,
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json()
        return []


class KEDAAdapter:
    """KEDA Kubernetes 事件驱动自动扩缩适配器"""

    def __init__(self, context: str = None):
        self.context = context
        self.cli = "kubectl"

    def apply_scaled_object(self, manifest_path: str) -> Dict[str, Any]:
        """应用 ScaledObject"""
        cmd = [self.cli, "apply", "-f", manifest_path]
        if self.context:
            cmd.extend(["--context", self.context])

        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def get_scaled_objects(self, namespace: str = "default") -> List[Dict]:
        """获取 ScaledObjects"""
        cmd = [
            self.cli, "get", "ScaledObject",
            "-n", namespace,
            "-o", "json"
        ]
        if self.context:
            cmd.extend(["--context", self.context])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("items", [])
        return []


class PrometheusAdapter:
    """Prometheus 指标适配器"""

    def __init__(self, server: str = "http://localhost:9090"):
        self.server = server
        self.cli = "promtool"

    def query(self, query: str) -> Dict[str, Any]:
        """查询 Prometheus"""
        import requests
        resp = requests.get(
            f"{self.server}/api/v1/query",
            params={"query": query},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json()
        return {"status": "error"}

    def query_range(self, query: str, start: int,
                    end: int, step: str = "1m") -> Dict[str, Any]:
        """范围查询"""
        import requests
        resp = requests.get(
            f"{self.server}/api/v1/query_range",
            params={
                "query": query,
                "start": start,
                "end": end,
                "step": step
            },
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json()
        return {"status": "error"}