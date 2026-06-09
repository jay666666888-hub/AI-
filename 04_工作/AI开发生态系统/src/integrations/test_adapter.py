#!/usr/bin/env python3
"""
Test Adapter - 测试质量层集成
L9 测试质量层
"""

import subprocess
import os
from typing import Dict, Any, List, Optional


class PlaywrightAdapter:
    """Playwright E2E 测试适配器"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()
        self.test_dir = os.path.join(self.project_path, "tests")

    def install(self) -> Dict[str, Any]:
        """安装 Playwright"""
        result = subprocess.run(
            ["npx", "playwright", "install", "--with-deps"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def run_tests(self, test_file: str = None, headed: bool = False,
                  timeout: int = 30000) -> Dict[str, Any]:
        """运行测试"""
        cmd = ["npx", "playwright", "test"]
        if test_file:
            cmd.append(test_file)
        if headed:
            cmd.append("--headed")

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

    def screenshot(self, url: str, path: str, selectors: List[str] = None) -> bool:
        """截图"""
        # 使用 Playwright CLI
        cmd = ["npx", "playwright", "screenshot", url, path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0


class ReactDoctorAdapter:
    """React Doctor - AI 生成 React 坏代码检测"""

    def __init__(self):
        self.path = "/usr/local/bin/react-doctor"

    def analyze(self, project_path: str) -> Dict[str, Any]:
        """分析 React 项目"""
        result = subprocess.run(
            ["npx", "react-doctor", project_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "issues": self._parse_issues(result.stdout)
        }

    def _parse_issues(self, output: str) -> List[Dict[str, Any]]:
        """解析问题"""
        issues = []
        current_issue = None

        for line in output.splitlines():
            if "[ISSUE]" in line:
                if current_issue:
                    issues.append(current_issue)
                current_issue = {"type": "react-issue", "details": []}
            elif current_issue and line.strip():
                current_issue["details"].append(line.strip())

        if current_issue:
            issues.append(current_issue)
        return issues


class JestAdapter:
    """Jest 测试适配器"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()

    def run(self, test_name: str = None, coverage: bool = False,
            watch: bool = False) -> Dict[str, Any]:
        """运行 Jest 测试"""
        cmd = ["npx", "jest"]
        if test_name:
            cmd.extend(["--testNamePattern", test_name])
        if coverage:
            cmd.append("--coverage")
        if watch:
            cmd.append("--watch")

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

    def coverage_report(self) -> Dict[str, Any]:
        """生成覆盖率报告"""
        result = subprocess.run(
            ["npx", "jest", "--coverage", "--coverageReporters=json"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout
        }


class GoTestAdapter:
    """Googletest C++ 测试框架适配器"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()

    def configure(self, build_type: str = "Debug") -> Dict[str, Any]:
        """配置 CMake"""
        result = subprocess.run(
            ["cmake", "-B", "build", f"-DCMAKE_BUILD_TYPE={build_type}"],
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
        """构建测试"""
        result = subprocess.run(
            ["cmake", "--build", "build"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    def run(self, test_filter: str = "*") -> Dict[str, Any]:
        """运行测试"""
        result = subprocess.run(
            ["./build/tests", f"--gtest_filter={test_filter}"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }