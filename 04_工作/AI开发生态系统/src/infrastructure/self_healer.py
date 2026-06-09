#!/usr/bin/env python3
"""
SelfHealer - L18 Self-Maintenance Layer
自愈引擎：自动检测并修复代码问题
"""

import os
import ast
import importlib
import traceback
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class HealthLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class HealthIssue:
    issue_type: str
    level: HealthLevel
    file_path: str
    description: str
    auto_fixable: bool = False
    fix_applied: bool = False
    error_detail: str = ""


@dataclass
class HealthReport:
    timestamp: str
    total_issues: int
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    auto_fixed: int = 0
    issues: List[HealthIssue] = field(default_factory=list)


class SelfHealer:
    """自愈引擎 - L18 自我维护层"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.src_path = os.path.join(self.project_path, "src")
        self.skills_path = os.path.join(self.src_path, "skills")
        self.issues: List[HealthIssue] = []

    def run_health_check(self) -> HealthReport:
        """运行全面健康检查"""
        self.issues = []

        print("  🔍 运行健康检查...")

        # 1. 检测循环导入
        self._check_circular_imports()

        # 2. 检测死代码
        self._check_dead_code()

        # 3. 检测缺失导入
        self._check_missing_imports()

        # 4. 检测语法错误
        self._check_syntax_errors()

        # 5. 检测空模块
        self._check_empty_modules()

        # 6. 自动修复可修复的问题
        self._apply_auto_fixes()

        return self._generate_report()

    def _check_circular_imports(self) -> None:
        """检测循环导入"""
        print("     - 检查循环导入...")
        try:
            # 简单检测：尝试导入每个模块，检查是否瞬间完成
            modules_to_check = []

            for root, dirs, files in os.walk(self.skills_path):
                for f in files:
                    if f.endswith("_skill.py") and not f.startswith("__"):
                        module_name = f[:-3]
                        modules_to_check.append(f"skills.{module_name}")

            for module_name in modules_to_check[:5]:  # 只检查前5个避免耗时过长
                try:
                    import sys
                    if module_name in sys.modules:
                        del sys.modules[module_name]
                    importlib.import_module(module_name)
                except ImportError as e:
                    error_str = str(e)
                    if "circular" in error_str.lower() or "import" in error_str.lower():
                        self.issues.append(HealthIssue(
                            issue_type="circular_import",
                            level=HealthLevel.HIGH,
                            file_path=module_name,
                            description=f"可能的循环导入: {module_name}",
                            error_detail=str(e)
                        ))
                except Exception:
                    pass
        except Exception as e:
            self.issues.append(HealthIssue(
                issue_type="circular_import_check",
                level=HealthLevel.INFO,
                file_path="",
                description=f"循环导入检查跳过: {e}"
            ))

    def _check_dead_code(self) -> None:
        """检测死代码（未使用的函数/类）"""
        print("     - 检查死代码...")
        try:
            # 使用 AST 分析未使用的定义
            for root, dirs, files in os.walk(self.skills_path):
                for f in files:
                    if f.endswith(".py") and not f.startswith("__"):
                        file_path = os.path.join(root, f)
                        self._analyze_dead_code(file_path)
        except Exception as e:
            self.issues.append(HealthIssue(
                issue_type="dead_code_check",
                level=HealthLevel.INFO,
                file_path="",
                description=f"死代码检查跳过: {e}"
            ))

    def _analyze_dead_code(self, file_path: str) -> None:
        """分析单个文件的死代码"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # 收集所有定义的名称
            defined_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    defined_names.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    defined_names.add(node.name)

            # 如果没有任何外部使用，检查是否是真正的死代码
            # 这里简化处理：标记空文件或只有 pass 的函数
            if not defined_names:
                self.issues.append(HealthIssue(
                    issue_type="dead_code",
                    level=HealthLevel.LOW,
                    file_path=file_path,
                    description="可能未使用的模块",
                    auto_fixable=True
                ))
        except SyntaxError as e:
            self.issues.append(HealthIssue(
                issue_type="syntax_error",
                level=HealthLevel.HIGH,
                file_path=file_path,
                description=f"语法错误: {e}",
                error_detail=traceback.format_exc()
            ))

    def _check_missing_imports(self) -> None:
        """检测缺失的导入"""
        print("     - 检查缺失导入...")
        try:
            # 尝试导入主模块，捕获 ImportError
            modules_to_test = [
                "ecosystem_orchestrator",
                "integrations.intent_adapter",
                "integrations.multi_agent_adapter",
                "skills.brainstorming_skill",
                "skills.tdd_skill",
                "skills.evolution_skill",
            ]

            for module_name in modules_to_test:
                try:
                    if module_name in globals():
                        del globals()[module_name]
                    importlib.import_module(module_name)
                except ImportError as e:
                    self.issues.append(HealthIssue(
                        issue_type="missing_import",
                        level=HealthLevel.HIGH,
                        file_path=module_name,
                        description=f"模块导入失败: {module_name}",
                        error_detail=str(e)
                    ))
                except Exception:
                    pass
        except Exception as e:
            self.issues.append(HealthIssue(
                issue_type="missing_import_check",
                level=HealthLevel.INFO,
                file_path="",
                description=f"缺失导入检查跳过: {e}"
            ))

    def _check_syntax_errors(self) -> None:
        """检测语法错误"""
        print("     - 检查语法错误...")
        try:
            for root, dirs, files in os.walk(self.src_path):
                # 跳过 __pycache__
                dirs[:] = [d for d in dirs if d != '__pycache__']

                for f in files:
                    if f.endswith(".py") and not f.startswith("__"):
                        file_path = os.path.join(root, f)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as file:
                                ast.parse(file.read())
                        except SyntaxError as e:
                            self.issues.append(HealthIssue(
                                issue_type="syntax_error",
                                level=HealthLevel.CRITICAL,
                                file_path=file_path,
                                description=f"语法错误在行 {e.lineno}: {e.msg}",
                                error_detail=traceback.format_exc()
                            ))
        except Exception as e:
            self.issues.append(HealthIssue(
                issue_type="syntax_check",
                level=HealthLevel.INFO,
                file_path="",
                description=f"语法检查跳过: {e}"
            ))

    def _check_empty_modules(self) -> None:
        """检测空模块"""
        print("     - 检查空模块...")
        try:
            for root, dirs, files in os.walk(self.skills_path):
                for f in files:
                    if f.endswith(".py") and not f.startswith("__"):
                        file_path = os.path.join(root, f)
                        file_size = os.path.getsize(file_path)

                        if file_size < 100:  # 小于100字节可能是空模块
                            with open(file_path, 'r', encoding='utf-8') as file:
                                content = file.read().strip()

                            if not content or len(content) < 50:
                                self.issues.append(HealthIssue(
                                    issue_type="empty_module",
                                    level=HealthLevel.MEDIUM,
                                    file_path=file_path,
                                    description="空模块或模块内容过少",
                                    auto_fixable=True
                                ))
        except Exception as e:
            self.issues.append(HealthIssue(
                issue_type="empty_module_check",
                level=HealthLevel.INFO,
                file_path="",
                description=f"空模块检查跳过: {e}"
            ))

    def _apply_auto_fixes(self) -> None:
        """应用自动修复"""
        print("     - 应用自动修复...")
        fixed_count = 0

        for issue in self.issues:
            if issue.auto_fixable and not issue.fix_applied:
                if issue.issue_type == "empty_module":
                    # 为空模块添加占位符
                    self._fix_empty_module(issue)
                    fixed_count += 1
                elif issue.issue_type == "dead_code":
                    # 标记死代码待删除
                    print(f"       标记待删除: {issue.file_path}")

        print(f"       已自动修复: {fixed_count} 项")

    def _fix_empty_module(self, issue: HealthIssue) -> None:
        """修复空模块"""
        try:
            placeholder = f'''"""自动生成的空模块占位符"""

# 此模块待实现
PASS
'''
            with open(issue.file_path, 'w', encoding='utf-8') as f:
                f.write(placeholder)
            issue.fix_applied = True
            print(f"       已修复空模块: {issue.file_path}")
        except Exception as e:
            print(f"       修复失败: {issue.file_path}, {e}")

    def _generate_report(self) -> HealthReport:
        """生成健康报告"""
        report = HealthReport(
            timestamp=datetime.now().isoformat(),
            total_issues=len(self.issues)
        )

        for issue in self.issues:
            if issue.level == HealthLevel.CRITICAL:
                report.critical += 1
            elif issue.level == HealthLevel.HIGH:
                report.high += 1
            elif issue.level == HealthLevel.MEDIUM:
                report.medium += 1
            elif issue.level == HealthLevel.LOW:
                report.low += 1

            if issue.fix_applied:
                report.auto_fixed += 1

        return report

    def get_status(self) -> Dict[str, Any]:
        """获取自愈系统状态"""
        return {
            "self_healing_enabled": True,
            "checks_enabled": [
                "circular_imports",
                "dead_code",
                "missing_imports",
                "syntax_errors",
                "empty_modules"
            ],
            "auto_fix_enabled": True
        }


def run_self_healing(project_path: str = None) -> HealthReport:
    """运行自愈检查的快捷函数"""
    healer = SelfHealer(project_path)
    return healer.run_health_check()
__exports__ = ['HealthIssue', 'HealthLevel', 'HealthReport', 'SelfHealer', 'run_self_healing']


