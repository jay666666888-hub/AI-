#!/usr/bin/env python3
"""
Frontend Adapter - 前端生成层和创意设计层集成
L15 前端生成层 & L16 创意设计层
"""

import subprocess
import os
from typing import Dict, Any, List


class OpenUIAdapter:
    """OpenUI 开放标准 AI UI 生成适配器"""

    def __init__(self, api_url: str = "http://localhost:7860"):
        self.api_url = api_url.rstrip("/")

    def generate(self, prompt: str, output_format: str = "html") -> Dict[str, Any]:
        """
        生成 UI

        Args:
            prompt: UI 描述
            output_format: 输出格式 (html, react, vue)
        """
        import requests
        resp = requests.post(
            f"{self.api_url}/api/generate",
            json={"prompt": prompt, "format": output_format},
            timeout=60
        )
        if resp.status_code == 200:
            return {
                "success": True,
                "output": resp.json().get("output", ""),
                "format": output_format
            }
        return {
            "success": False,
            "error": resp.text
        }


class V0Adapter:
    """Vercel v0 AI UI 生成适配器"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.api_url = "https://api.v0.dev/v1"

    def generate(self, prompt: str, project_id: str = None) -> Dict[str, Any]:
        """生成 React 组件"""
        import requests
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "projectId": project_id
        }
        resp = requests.post(
            f"{self.api_url}/generate",
            json=payload,
            headers=headers,
            timeout=120
        )
        if resp.status_code == 200:
            return {
                "success": True,
                "code": resp.json().get("code", ""),
                "preview_url": resp.json().get("previewUrl", "")
            }
        return {
            "success": False,
            "error": resp.text
        }


class BoltAdapter:
    """StackBlitz Bolt AI 全栈开发适配器"""

    def __init__(self):
        self.cli = "npx"

    def create_project(self, template: str = "react-ts",
                       project_name: str = None) -> Dict[str, Any]:
        """创建 Bolt 项目"""
        cmd = [self.cli, "create-bolt", template]
        if project_name:
            cmd.append(project_name)

        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def dev(self, project_path: str = ".") -> Dict[str, Any]:
        """启动开发服务器"""
        result = subprocess.run(
            [self.cli, "bolt", "dev"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }


class DataFormulatorAdapter:
    """Microsoft Data Formulator AI 富可视化适配器"""

    def __init__(self, api_url: str = "http://localhost:3000"):
        self.api_url = api_url

    def generate_chart(self, data_source: str, chart_type: str,
                      x_field: str, y_field: str) -> Dict[str, Any]:
        """
        生成图表

        Args:
            data_source: 数据源
            chart_type: 图表类型
            x_field: X 字段
            y_field: Y 字段
        """
        import requests
        payload = {
            "dataSource": data_source,
            "chartType": chart_type,
            "xField": x_field,
            "yField": y_field
        }
        resp = requests.post(
            f"{self.api_url}/api/generate",
            json=payload,
            timeout=60
        )
        if resp.status_code == 200:
            return {
                "success": True,
                "spec": resp.json()
            }
        return {
            "success": False,
            "error": resp.text
        }


class GraphifyAdapter:
    """Graphify 代码知识图谱适配器"""

    def __init__(self, api_url: str = "http://localhost:4000"):
        self.api_url = api_url

    def create_knowledge_graph(self, repo_path: str,
                               max_depth: int = 3) -> Dict[str, Any]:
        """创建代码知识图谱"""
        import requests
        resp = requests.post(
            f"{self.api_url}/api/graph/create",
            json={
                "repoPath": repo_path,
                "maxDepth": max_depth
            },
            timeout=300
        )
        if resp.status_code == 200:
            return {
                "success": True,
                "graph_id": resp.json().get("graphId", "")
            }
        return {
            "success": False,
            "error": resp.text
        }

    def query_graph(self, graph_id: str, query: str) -> List[Dict[str, Any]]:
        """查询图谱"""
        import requests
        resp = requests.post(
            f"{self.api_url}/api/graph/query",
            json={
                "graphId": graph_id,
                "query": query
            },
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json().get("results", [])
        return []


class EvidenceAdapter:
    """Evidence BI as Code 适配器"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()

    def dev(self) -> Dict[str, Any]:
        """启动 Evidence 开发服务器"""
        result = subprocess.run(
            ["npx", "evidence", "dev", "--port", "3000"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def build(self) -> Dict[str, Any]:
        """构建静态站点"""
        result = subprocess.run(
            ["npx", "evidence", "build"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout
        }