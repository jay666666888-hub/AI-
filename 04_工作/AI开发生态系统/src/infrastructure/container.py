"""
Container Manager - 容器管理
支持 Docker 操作，镜像管理
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import subprocess
import json


@dataclass
class Container:
    id: str
    name: str
    image: str
    status: str
    ports: str
    created: str


class ContainerManager:
    """Docker 容器管理器"""

    def __init__(self):
        self.docker_available = self._check_docker()

    def _check_docker(self) -> bool:
        """检查 Docker 是否可用"""
        try:
            result = subprocess.run(["docker", "version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except subprocess.TimeoutExpired:
            return False

    def list_containers(self, all: bool = True) -> List[Container]:
        """列出容器"""
        if not self.docker_available:
            return []

        cmd = ["docker", "ps"]
        if all:
            cmd.append("-a")

        result = subprocess.run(cmd + ["--format", "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}|{{.CreatedAt}}"],
                                capture_output=True, text=True)

        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 6:
                    containers.append(Container(
                        id=parts[0],
                        name=parts[1],
                        image=parts[2],
                        status=parts[3],
                        ports=parts[4],
                        created=parts[5]
                    ))
        return containers

    def run(self, image: str, name: Optional[str] = None, ports: Optional[Dict[str, str]] = None,
            env: Optional[Dict[str, str]] = None, detach: bool = True) -> Dict[str, Any]:
        """运行容器"""
        if not self.docker_available:
            return {"error": "Docker 不可用"}

        cmd = ["docker", "run"]
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
        cmd.append(image)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                container_id = result.stdout.strip()[:12]
                return {"success": True, "container_id": container_id}
            return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop(self, container_id: str) -> bool:
        """停止容器"""
        if not self.docker_available:
            return False
        result = subprocess.run(["docker", "stop", container_id], capture_output=True, timeout=30)
        return result.returncode == 0

    def remove(self, container_id: str, force: bool = False) -> bool:
        """删除容器"""
        if not self.docker_available:
            return False
        cmd = ["docker", "rm"]
        if force:
            cmd.append("-f")
        cmd.append(container_id)
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0

    def logs(self, container_id: str, tail: int = 100) -> str:
        """获取容器日志"""
        if not self.docker_available:
            return ""
        result = subprocess.run(["docker", "logs", "--tail", str(tail), container_id],
                                capture_output=True, text=True)
        return result.stdout

    def pull(self, image: str) -> bool:
        """拉取镜像"""
        if not self.docker_available:
            return False
        result = subprocess.run(["docker", "pull", image], capture_output=True, timeout=300)
        return result.returncode == 0

    def compose(self, file_path: str, action: str = "up -d") -> Dict[str, Any]:
        """Docker Compose 操作"""
        if not self.docker_available:
            return {"error": "Docker 不可用"}

        try:
            result = subprocess.run(
                ["docker", "compose", "-f", file_path] + action.split(),
                capture_output=True,
                text=True,
                timeout=300
            )
            return {"success": result.returncode == 0, "output": result.stdout, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    manager = ContainerManager()
    print(f"Docker 可用: {manager.docker_available}")

    if manager.docker_available:
        containers = manager.list_containers()
        print(f"容器数量: {len(containers)}")

__exports__ = ['Container', 'ContainerManager']


