#!/usr/bin/env python3
"""
Code Review Skill - 代码审查技能
基于 Superpowers 五轴审查 + security-reviewer 模式
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ReviewSeverity(Enum):
    CRITICAL = "critical"  # 阻止合并
    HIGH = "high"         # 合并前应修复
    MEDIUM = "medium"     # 考虑修复
    LOW = "low"           # 可选


class ReviewCategory(Enum):
    SECURITY = "security"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    CORRECTNESS = "correctness"


@dataclass
class ReviewIssue:
    severity: ReviewSeverity
    category: ReviewCategory
    type: str
    message: str
    line: Optional[int] = None
    suggestion: str = ""




class CodeReviewSkill:
    """代码审查技能"""

    SECURITY_PATTERNS = {
        "hardcoded_secret": r"(?i)(api_key|password|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]",
        "sql_injection": r"(?i)(execute|query)\s*\(.*\+.*\)",
        "eval_usage": r"\beval\s*\(",
        "pickle_load": r"\bpickle\.loads?\b",
        "command_injection": r"\bsystem\s*\(",
    }

    QUALITY_CHECKS = {
        "long_function": 50,
        "long_line": 120,
        "max_nesting": 4,
    }

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []

    def review(self, code: str, language: str = "python") -> Dict[str, Any]:
        """审查代码"""
        self.issues = []
        
        self._check_security(code)
        self._check_quality(code, language)
        self._check_performance(code)
        self._check_maintainability(code)
        self._check_correctness(code)

        return self._build_report()

    def _check_security(self, code: str) -> None:
        """安全检查"""
        import re
        for issue_type, pattern in self.SECURITY_PATTERNS.items():
            if re.search(pattern, code):
                severity = ReviewSeverity.CRITICAL if "secret" in issue_type else ReviewSeverity.HIGH
                self.issues.append({
                    "severity": severity.value,
                    "category": ReviewCategory.SECURITY.value,
                    "type": issue_type,
                    "message": f"安全问题: {issue_type}",
                    "suggestion": self._get_security_suggestion(issue_type)
                })

    def _get_security_suggestion(self, issue_type: str) -> str:
        suggestions = {
            "hardcoded_secret": "使用环境变量或密钥管理器",
            "sql_injection": "使用参数化查询",
            "eval_usage": "避免使用 eval，使用 ast.literal_eval",
            "pickle_load": "使用 JSON 或其他安全格式",
            "command_injection": "使用 subprocess.run 并验证输入",
        }
        return suggestions.get(issue_type, "修复安全问题")

    def _check_quality(self, code: str, language: str) -> None:
        """代码质量检查"""
        import re
        lines = code.split("\n")

        # 函数长度检查
        in_function = []
        function_start = 0
        for i, line in enumerate(lines, 1):
            if re.search(r"(def |function |func )", line):
                if len(in_function) > self.QUALITY_CHECKS["long_function"]:
                    self.issues.append({
                        "severity": ReviewSeverity.MEDIUM.value,
                        "category": ReviewCategory.QUALITY.value,
                        "type": "long_function",
                        "line": function_start,
                        "message": f"函数超过{self.QUALITY_CHECKS['long_function']}行",
                        "suggestion": "拆分为更小的函数"
                    })
                in_function = []
                function_start = i
            in_function.append(line)

        # TODO/FIXME 检查
        for i, line in enumerate(lines, 1):
            if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.IGNORECASE):
                self.issues.append({
                    "severity": ReviewSeverity.LOW.value,
                    "category": ReviewCategory.MAINTAINABILITY.value,
                    "type": "unresolved_marker",
                    "line": i,
                    "message": f"未解决标记: {line.strip()}",
                    "suggestion": "处理或创建Issue跟踪"
                })

    def _check_performance(self, code: str) -> None:
        """性能检查"""
        import re
        patterns = [
            ("nested_loop", r"for\s+\w+\s+in.*:\s*\n.*for\s+\w+\s+in", "嵌套循环"),
            ("list_append_in_loop", r"\w+\.append\(", "循环内列表操作"),
        ]
        for issue_type, pattern, desc in patterns:
            if re.search(pattern, code, re.MULTILINE):
                self.issues.append({
                    "severity": ReviewSeverity.MEDIUM.value,
                    "category": ReviewCategory.PERFORMANCE.value,
                    "type": issue_type,
                    "message": f"潜在性能问题: {desc}",
                    "suggestion": "考虑更高效的实现"
                })

    def _check_maintainability(self, code: str) -> None:
        """可维护性检查"""
        import re
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            if len(line) > self.QUALITY_CHECKS["long_line"]:
                self.issues.append({
                    "severity": ReviewSeverity.LOW.value,
                    "category": ReviewCategory.MAINTAINABILITY.value,
                    "type": "long_line",
                    "line": i,
                    "message": f"行超过{self.QUALITY_CHECKS['long_line']}字符",
                    "suggestion": "拆分或提取变量"
                })

    def _check_correctness(self, code: str) -> None:
        """正确性检查"""
        import re
        # 检查 except pass
        if re.search(r"except[^:]*:\s*\n\s*pass", code):
            self.issues.append({
                "severity": ReviewSeverity.MEDIUM.value,
                "category": ReviewCategory.CORRECTNESS.value,
                "type": "bare_except_pass",
                "message": "空的 except 子句",
                "suggestion": "至少记录日志或重新抛出异常"
            })

    def _build_report(self) -> Dict[str, Any]:
        """构建审查报告"""
        by_severity = {
            "critical": len([i for i in self.issues if i["severity"] == "critical"]),
            "high": len([i for i in self.issues if i["severity"] == "high"]),
            "medium": len([i for i in self.issues if i["severity"] == "medium"]),
            "low": len([i for i in self.issues if i["severity"] == "low"]),
        }

        if by_severity["critical"] > 0:
            approval = "BLOCKED"
        elif by_severity["high"] > 0:
            approval = "WARNING"
        else:
            approval = "APPROVED"

        return {
            "approval": approval,
            "issue_count": len(self.issues),
            "issues_by_severity": by_severity,
            "issues": self.issues,
            "summary": f"{by_severity['critical']} 关键, {by_severity['high']} 高, {by_severity['medium']} 中, {by_severity['low']} 低",
            "next_action": self._get_next_action(approval)
        }

    def _get_next_action(self, approval: str) -> str:
        actions = {
            "BLOCKED": "必须修复所有关键问题后才能合并",
            "WARNING": "建议修复高优先级问题",
            "APPROVED": "可以合并"
        }
        return actions.get(approval, "")


def run_code_review(code: str, language: str = "python") -> Dict[str, Any]:
    """快捷代码审查函数"""
    skill = CodeReviewSkill()
    return skill.review(code, language)
