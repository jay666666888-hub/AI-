#!/usr/bin/env python3
"""
Container Adapter - 容器化和部署层集成
L12 基础设施层 & L13 容器编排层 & L14 部署自动化层
"""

import subprocess
import json
from typing import Dict, Any, List, Optional


class DockerAdapter:
    """Docker 容器化适配器"""

    def __init__(self):
        self.cli = "docker"

    def build(self, path: str = ".", tag: str = None,
              dockerfile: str = "Dockerfile") -> Dict[str, Any]:
        """构建镜像"""
        cmd = [self.cli, "build", "-f", dockerfile]
        if tag:
            cmd.extend(["-t", tag])
        cmd.append(path)

        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def run(self, image: str, name: str = None,
            ports: Dict[str, str] = None, detach: bool = True,
            env: Dict[str, str] = None, volumes: Dict[str, str] = None) -> Dict[str, Any]:
        """运行容器"""
        cmd = [self.cli, "run"]
        if detach:
            cmd.append("-d")
        if name:
            cmd.extend(["--name", name])
        if ports:
            for host, container in ports.items():
                cmd.extend(["-p", f"{host}:{container}"])
        if env:
            for k, v in env.items():
                cmd.extend(["-e", f"{k}={v}"])
        if volumes:
            for host_path, container_path in volumes.items():
                cmd.extend(["-v", f"{host_path}:{container_path}"])
        cmd.append(image)

        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "container_id": result.stdout.strip() if result.returncode == 0 else None,
            "error": result.stderr
        }

    def ps(self, all: bool = False) -> List[Dict[str, Any]]:
        """列出容器"""
        cmd = [self.cli, "ps"]
        if all:
            cmd.append("-a")
        cmd.extend(["--format", "{{json .}}"])

        result = subprocess.run(cmd, capture_output=True, text=True)
        containers = []
        for line in result.stdout.splitlines():
            if line.strip():
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return containers

    def stop(self, container_id: str) -> bool:
        """停止容器"""
        result = subprocess.run([self.cli, "stop", container_id],
                               capture_output=True, text=True)
        return result.returncode == 0

    def rm(self, container_id: str, force: bool = False) -> bool:
        """删除容器"""
        cmd = [self.cli, "rm"]
        if force:
            cmd.append("-f")
        cmd.append(container_id)
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0


class KubernetesAdapter:
    """Kubernetes 编排适配器"""

    def __init__(self, context: str = None):
        self.cli = "kubectl"
        self.context = context

    def apply(self, manifest_path: str) -> Dict[str, Any]:
        """应用 manifest"""
        cmd = [self.cli, "apply", "-f", manifest_path]
        if self.context:
            cmd.extend(["--context", self.context])

        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def get_pods(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """获取 pods"""
        cmd = [self.cli, "get", "pods", "-n", namespace, "-o", "json"]
        if self.context:
            cmd.extend(["--context", self.context])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("items", [])
        return []

    def delete(self, resource_type: str, name: str,
              namespace: str = "default") -> bool:
        """删除资源"""
        cmd = [self.cli, "delete", resource_type, name, "-n", namespace]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def scale(self, deployment: str, replicas: int,
              namespace: str = "default") -> bool:
        """扩缩容"""
        cmd = [self.cli, "scale", f"deployment/{deployment}",
               f"--replicas={replicas}", "-n", namespace]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0


class HelmAdapter:
    """Helm 包管理适配器"""

    def __init__(self):
        self.cli = "helm"

    def install(self, chart: str, name: str = None,
                namespace: str = "default", values: Dict = None) -> Dict[str, Any]:
        """安装 chart"""
        cmd = [self.cli, "install"]
        if name:
            cmd.append(name)
        else:
            cmd.append(chart)
            name = chart

        cmd.append(chart)
        if namespace:
            cmd.extend(["--namespace", namespace])
        if values:
            for k, v in values.items():
                cmd.extend(["--set", f"{k}={v}"])

        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "release": name,
            "output": result.stdout,
            "error": result.stderr
        }

    def list(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """列出 releases"""
        cmd = [self.cli, "list", "-n", namespace, "-o", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []

    def uninstall(self, name: str, namespace: str = "default") -> bool:
        """卸载 release"""
        cmd = [self.cli, "uninstall", name, "-n", namespace]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0


class ArgoCDAdapter:
    """ArgoCD GitOps 部署适配器"""

    def __init__(self, server: str = "http://localhost:8080",
                 token: str = None):
        self.server = server
        self.token = token
        import os
        self.cli = os.path.expanduser("~/bin/argocd") if os.path.exists(os.path.expanduser("~/bin/argocd")) else "argocd"

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """登录 ArgoCD"""
        cmd = [self.cli, "login", self.server, "--username", username,
               "--password", password, "--insecure"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "error": result.stderr
        }

    def sync(self, app: str) -> Dict[str, Any]:
        """同步应用"""
        cmd = [self.cli, "app", "sync", app]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def get_app(self, app: str) -> Optional[Dict[str, Any]]:
        """获取应用状态"""
        cmd = [self.cli, "app", "get", app, "-o", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None


class NomadAdapter:
    """Nomad 工作负载编排适配器"""

    def __init__(self, address: str = "http://localhost:4646"):
        self.address = address
        self.cli = "nomad"

    def run_job(self, job_file: str) -> Dict[str, Any]:
        """运行 job"""
        cmd = [self.cli, "job", "run", job_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def status(self, job: str = None) -> Dict[str, Any]:
        """获取状态"""
        cmd = [self.cli, "job", "status"]
        if job:
            cmd.append(job)
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout
        }