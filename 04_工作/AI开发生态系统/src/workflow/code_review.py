"""
Code Review - 代码审查系统
自动分析代码质量、安全性、可维护性
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import os


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


class CodeReviewer:
    """代码审查引擎"""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.severity_rules = {
            ReviewSeverity.CRITICAL: self._check_critical,
            ReviewSeverity.HIGH: self._check_high,
            ReviewSeverity.MEDIUM: self._check_medium,
            ReviewSeverity.LOW: self._check_low
        }

    def review(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        审查代码

        Args:
            code: 要审查的代码
            language: 编程语言

        Returns:
            审查结果
        """
        self.issues = []

        # 安全检查
        self._check_security(code)

        # 代码质量检查
        self._check_quality(code, language)

        # 性能检查
        self._check_performance(code)

        # 可维护性检查
        self._check_maintainability(code)

        return self._build_report()

    def _check_security(self, code: str) -> None:
        """安全检查"""
        security_patterns = {
            "hardcoded_secret": r"(?i)(api_key|password|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]",
            "sql_injection": r"(?i)(execute|query)\s*\(.*\+.*\)",
            "eval_usage": r"\beval\s*\(",
            "pickle_load": r"\bpickle\.loads?\b",
            "hardcoded_url": r"https?://[^'\"\\]+",
        }

        for issue_type, pattern in security_patterns.items():
            import re
            if re.search(pattern, code):
                self.issues.append({
                    "severity": ReviewSeverity.CRITICAL if "secret" in issue_type else ReviewSeverity.HIGH,
                    "category": ReviewCategory.SECURITY.value,
                    "type": issue_type,
                    "message": f"Security issue: {issue_type}",
                    "suggestion": "使用环境变量或密钥管理器"
                })

    def _check_quality(self, code: str, language: str) -> None:
        """代码质量检查"""
        lines = code.split("\n")

        # 检查函数长度
        current_function = []
        for i, line in enumerate(lines, 1):
            if "def " in line or "function " in line:
                if len(current_function) > 50:
                    self.issues.append({
                        "severity": ReviewSeverity.MEDIUM,
                        "category": ReviewCategory.QUALITY.value,
                        "type": "long_function",
                        "line": i - len(current_function),
                        "message": f"函数超过50行 ({len(current_function)}行)",
                        "suggestion": "拆分为更小的函数"
                    })
                current_function = []
            current_function.append(line)

        # 检查TODO/FIXME
        import re
        for i, line in enumerate(lines, 1):
            if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.IGNORECASE):
                self.issues.append({
                    "severity": ReviewSeverity.LOW,
                    "category": ReviewCategory.MAINTAINABILITY.value,
                    "type": "unresolved_marker",
                    "line": i,
                    "message": f"未解决标记: {line.strip()}",
                    "suggestion": "处理或创建Issue跟踪"
                })

    def _check_performance(self, code: str) -> None:
        """性能检查"""
        performance_issues = [
            ("for_for_nested", r"for\s+\w+\s+in\s+.*:\s*\n.*for\s+\w+\s+in\s+", "嵌套循环"),
            ("list_concatenation", r"\+\s*\[", "列表拼接"),
        ]

        for issue_type, pattern, desc in performance_issues:
            import re
            if re.search(pattern, code):
                self.issues.append({
                    "severity": ReviewSeverity.MEDIUM,
                    "category": ReviewCategory.PERFORMANCE.value,
                    "type": issue_type,
                    "message": f"潜在性能问题: {desc}",
                    "suggestion": "考虑使用更高效的算法或数据结构"
                })

    def _check_maintainability(self, code: str) -> None:
        """可维护性检查"""
        import re

        # 检查过长行
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.issues.append({
                    "severity": ReviewSeverity.LOW,
                    "category": ReviewCategory.MAINTAINABILITY.value,
                    "type": "long_line",
                    "line": i,
                    "message": f"行超过120字符 ({len(line)}字符)",
                    "suggestion": "拆分或提取变量"
                })

    def _check_critical(self, code: str) -> List[Dict]:
        return [i for i in self.issues if i["severity"] == ReviewSeverity.CRITICAL]

    def _check_high(self, code: str) -> List[Dict]:
        return [i for i in self.issues if i["severity"] == ReviewSeverity.HIGH]

    def _check_medium(self, code: str) -> List[Dict]:
        return [i for i in self.issues if i["severity"] == ReviewSeverity.MEDIUM]

    def _check_low(self, code: str) -> List[Dict]:
        return [i for i in self.issues if i["severity"] == ReviewSeverity.LOW]

    def _build_report(self) -> Dict[str, Any]:
        """构建审查报告"""
        by_severity = {
            "critical": len([i for i in self.issues if i["severity"] == ReviewSeverity.CRITICAL]),
            "high": len([i for i in self.issues if i["severity"] == ReviewSeverity.HIGH]),
            "medium": len([i for i in self.issues if i["severity"] == ReviewSeverity.MEDIUM]),
            "low": len([i for i in self.issues if i["severity"] == ReviewSeverity.LOW]),
        }

        approval = "APPROVED"
        if by_severity["critical"] > 0:
            approval = "BLOCKED"
        elif by_severity["high"] > 0:
            approval = "WARNING"

        return {
            "approval": approval,
            "issue_count": len(self.issues),
            "issues_by_severity": by_severity,
            "issues": self.issues,
            "summary": f"{by_severity['critical']} 关键, {by_severity['high']} 高, {by_severity['medium']} 中, {by_severity['low']} 低"
        }


if __name__ == "__main__":
    reviewer = CodeReviewer()

    sample_code = '''
def calculate_user_score(user_id, data):
    api_key = "sk-1234567890abcdef"  # 硬编码密钥
    query = "SELECT * FROM users WHERE id = " + user_id  # SQL注入风险
    result = eval("{" + data + "}")  # eval危险

    # 太长的函数
    total = 0
    for i in range(1000):
        for j in range(1000):  # 嵌套循环
            total += i * j

    # TODO: 优化这个算法
    return total
'''

    report = reviewer.review(sample_code, "python")
    print(f"审查结果: {report['approval']}")
    print(f"问题汇总: {report['summary']}")
    for issue in report['issues']:
        print(f"  [{issue['severity'].value}] {issue['message']}")
