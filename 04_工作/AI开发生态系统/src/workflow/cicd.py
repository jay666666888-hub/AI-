"""
CI/CD Executor - 持续集成/持续部署执行器
支持: GitHub Actions, GitLab CI, 本地构建
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import subprocess
import os


class PipelineStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass
class PipelineStep:
    name: str
    command: str
    working_dir: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    timeout: int = 300  # 5分钟默认超时


@dataclass
class Pipeline:
    name: str
    steps: List[PipelineStep]
    on_failure: str = "stop"  # stop, continue, notify


class CICDExecutor:
    """CI/CD 执行器"""

    def __init__(self):
        self.current_pipeline: Optional[Pipeline] = None
        self.step_results: List[Dict[str, Any]] = []

    def create_pipeline(self, name: str, steps: List[Dict[str, Any]]) -> Pipeline:
        """
        创建流水线

        Args:
            name: 流水线名称
            steps: 步骤列表，每项包含 name, command, working_dir, env, timeout

        Returns:
            Pipeline 对象
        """
        pipeline_steps = [
            PipelineStep(
                name=s["name"],
                command=s["command"],
                working_dir=s.get("working_dir"),
                env=s.get("env"),
                timeout=s.get("timeout", 300)
            )
            for s in steps
        ]
        return Pipeline(name=name, steps=pipeline_steps)

    def run_pipeline(self, pipeline: Pipeline) -> Dict[str, Any]:
        """
        执行流水线

        Args:
            pipeline: 要执行的流水线

        Returns:
            执行结果
        """
        self.current_pipeline = pipeline
        self.step_results = []

        print(f"开始执行流水线: {pipeline.name}")
        print("=" * 50)

        for i, step in enumerate(pipeline.steps):
            print(f"\n[{i+1}/{len(pipeline.steps)}] {step.name}")
            print(f"命令: {step.command}")

            result = self._execute_step(step)
            self.step_results.append(result)

            if result["status"] == "failed":
                print(f"❌ 步骤失败: {result.get('error', 'Unknown error')}")
                if pipeline.on_failure == "stop":
                    return self._build_report(status=PipelineStatus.FAILURE)
                elif pipeline.on_failure == "notify":
                    self._notify_failure(step, result)
            elif result["status"] == "success":
                print(f"✅ 步骤成功")

        status = PipelineStatus.SUCCESS
        return self._build_report(status=status)

    def _execute_step(self, step: PipelineStep) -> Dict[str, Any]:
        """执行单个步骤"""
        try:
            env = os.environ.copy()
            if step.env:
                env.update(step.env)

            result = subprocess.run(
                step.command,
                shell=True,
                cwd=step.working_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=step.timeout
            )

            return {
                "name": step.name,
                "status": "success" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout": result.stdout[:1000] if result.stdout else "",
                "stderr": result.stderr[:1000] if result.stderr else ""
            }
        except subprocess.TimeoutExpired:
            return {
                "name": step.name,
                "status": "failed",
                "error": f"步骤超时 ({step.timeout}s)"
            }
        except Exception as e:
            return {
                "name": step.name,
                "status": "failed",
                "error": str(e)
            }

    def _notify_failure(self, step: PipelineStep, result: Dict[str, Any]) -> None:
        """通知失败"""
        # 预留：可集成邮件、Slack、Webhook等通知
        print(f"通知: 流水线步骤 {step.name} 失败")

    def _build_report(self, status: PipelineStatus) -> Dict[str, Any]:
        """构建执行报告"""
        return {
            "pipeline": self.current_pipeline.name if self.current_pipeline else "unknown",
            "status": status.value,
            "total_steps": len(self.step_results),
            "successful_steps": len([r for r in self.step_results if r["status"] == "success"]),
            "failed_steps": len([r for r in self.step_results if r["status"] == "failed"]),
            "step_results": self.step_results,
            "duration": "N/A"  # 可添加时间追踪
        }

    def run_github_actions(self, workflow_file: str, event: str = "push") -> Dict[str, Any]:
        """
        运行 GitHub Actions 工作流

        Args:
            workflow_file: 工作流文件路径 (.yml/.yaml)
            event: 触发事件 (push, pull_request, etc.)

        Returns:
            执行结果
        """
        # 预留：与 GitHub CLI 集成
        cmd = f"gh workflow run {workflow_file} --event {event}"
        return {
            "command": cmd,
            "message": "需要安装 gh CLI 并登录",
            "docs": "https://cli.github.com/manual/workflow"
        }

    def generate_dockerfile(self, language: str, port: int = 8000) -> str:
        """
        生成 Dockerfile

        Args:
            language: 编程语言 (python, node, go, rust)
            port: 暴露端口

        Returns:
            Dockerfile 内容
        """
        dockerfiles = {
            "python": f'''FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
EXPOSE {port}
CMD ["python", "main.py"]
''',
            "node": f'''FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE {port}
CMD ["node", "index.js"]
''',
            "go": f'''FROM golang:1.22-alpine
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o main .
EXPOSE {port}
CMD ["./main"]
''',
        }
        return dockerfiles.get(language, f"# 不支持的语言: {language}")


if __name__ == "__main__":
    executor = CICDExecutor()

    # 创建测试流水线
    pipeline = executor.create_pipeline("build-and-test", [
        {"name": "安装依赖", "command": "pip install -r requirements.txt"},
        {"name": "运行测试", "command": "pytest tests/ -v"},
        {"name": "构建 Docker", "command": "docker build -t myapp .", "timeout": 600},
    ])

    # 执行
    result = executor.run_pipeline(pipeline)
    print(f"\n流水线状态: {result['status']}")
    print(f"成功步骤: {result['successful_steps']}/{result['total_steps']}")

    # 生成 Dockerfile 示例
    print("\n生成的 Dockerfile (Python):")
    print(executor.generate_dockerfile("python"))
