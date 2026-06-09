#!/usr/bin/env python3
"""
Ralph Adapter - Ralph 自主循环系统集成
L1 自主代理层核心执行引擎
"""

import subprocess
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class RalphAdapter:
    """Ralph 自主循环适配器"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()
        self.ralph_path = "/home/admin1/.claude/plugins/marketplaces/ralph-claude-code"
        self.ralphrc_path = os.path.join(project_path, ".ralphrc") if project_path else None

    def is_ralph_enabled(self) -> bool:
        """检查项目是否启用 Ralph"""
        if not self.ralphrc_path:
            return False
        return os.path.exists(self.ralphrc_path)

    def enable_ralph(self, task_source: str = "beads", **kwargs) -> Dict[str, Any]:
        """
        在项目中启用 Ralph

        Args:
            task_source: 任务来源 (beads, github, prd)
            **kwargs: 额外参数
        """
        cmd = [
            os.path.join(self.ralph_path, "ralph_enable.sh"),
            f"--from", task_source
        ]

        if kwargs.get("project_type"):
            cmd.extend(["--project-type", kwargs["project_type"]])

        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def run_loop(self, monitor: bool = True, calls: int = None,
                prompt_file: str = None) -> Dict[str, Any]:
        """
        启动 Ralph 循环

        Args:
            monitor: 是否启用 tmux 监控
            calls: 最大调用次数
            prompt_file: 提示文件路径
        """
        ralph_script = os.path.join(self.ralph_path, "ralph_loop.sh")
        cmd = [ralph_script]

        if monitor:
            cmd.append("--monitor")
        if calls:
            cmd.extend(["--calls", str(calls)])
        if prompt_file:
            cmd.extend(["--prompt", prompt_file])

        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def import_prd(self, prd_path: str) -> Dict[str, Any]:
        """
        从 PRD 文档导入任务

        Args:
            prd_path: PRD 文件路径
        """
        ralph_import = os.path.join(self.ralph_path, "ralph_import.sh")
        cmd = [ralph_import, prd_path]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # 解析输出
        tasks = []
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.strip().startswith("-"):
                    tasks.append(line.strip().lstrip("- ").strip())

        return {
            "success": result.returncode == 0,
            "tasks": tasks,
            "output": result.stdout,
            "error": result.stderr
        }

    def check_status(self) -> Dict[str, Any]:
        """获取 Ralph 状态"""
        ralph_script = os.path.join(self.ralph_path, "ralph_loop.sh")
        cmd = [ralph_script, "--status"]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def reset_circuit(self) -> Dict[str, Any]:
        """重置电路 breaker"""
        ralph_script = os.path.join(self.ralph_path, "ralph_loop.sh")
        result = subprocess.run([ralph_script, "--reset-circuit"],
                             capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout
        }


# 快捷函数
def get_ralph_status() -> Optional[Dict[str, Any]]:
    """获取 Ralph 全局状态"""
    adapter = RalphAdapter()
    try:
        return adapter.check_status()
    except Exception:
        return None