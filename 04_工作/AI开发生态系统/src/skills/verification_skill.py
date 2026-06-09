#!/usr/bin/env python3
"""
Verification Skill - 完成前验证
基于 Superpowers verification-before-completion 检查清单
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class VerificationCheck:
    name: str
    passed: bool
    message: str
    suggestion: Optional[str] = None


class VerificationSkill:
    """
    完成前验证技能
    确保代码符合质量标准
    """

    CHECKLIST = [
        {"id": "readable", "name": "代码可读性", "desc": "代码可读且命名良好"},
        {"id": "small_functions", "name": "函数大小", "desc": "函数 < 50 行"},
        {"id": "focused_files", "name": "文件聚焦", "desc": "文件 < 800 行"},
        {"id": "no_deep_nesting", "name": "嵌套深度", "desc": "无深层嵌套 (>4 层)"},
        {"id": "error_handling", "name": "错误处理", "desc": "正确的错误处理"},
        {"id": "no_hardcoded", "name": "硬编码", "desc": "无硬编码值"},
        {"id": "no_mutation", "name": "不可变性", "desc": "无变更 (使用不可变模式)"},
        {"id": "tests_exist", "name": "测试", "desc": "新功能有测试"},
    ]

    def __init__(self):
        self.checks: List[VerificationCheck] = []

    def verify(self, code: str, context: str = "") -> Dict[str, Any]:
        """
        验证代码
        
        Args:
            code: 要验证的代码
            context: 额外上下文信息
        """
        self.checks = []
        
        self._check_readability(code)
        self._check_function_size(code)
        self._check_file_size(code)
        self._check_nesting(code)
        self._check_error_handling(code)
        self._check_hardcoded(code)
        self._check_mutation(code)
        
        return self._build_report()

    def _check_readability(self, code: str) -> None:
        """检查可读性"""
        lines = code.split("\n")
        issues = []
        
        # 检查命名
        import re
        for i, line in enumerate(lines, 1):
            # 模糊命名
            if re.search(r"\b(tmp|x|y|z|data|result)\b", line) and "for" not in line:
                issues.append(f"第{i}行: 考虑使用更描述性的命名")
        
        self.checks.append(VerificationCheck(
            name="代码可读性",
            passed=len(issues) == 0,
            message="命名清晰且有描述性" if not issues else f"{len(issues)}处可改进",
            suggestion="\n".join(issues) if issues else None
        ))

    def _check_function_size(self, code: str) -> None:
        """检查函数大小"""
        import re
        lines = code.split("\n")
        long_functions = []
        
        in_function = []
        start_line = 0
        for i, line in enumerate(lines, 1):
            if re.search(r"def |function |func ", line):
                if len(in_function) > 50:
                    long_functions.append(f"第{start_line}行: {len(in_function)}行")
                in_function = []
                start_line = i
            in_function.append(line)
        
        self.checks.append(VerificationCheck(
            name="函数大小",
            passed=len(long_functions) == 0,
            message="所有函数 < 50 行" if not long_functions else f"{len(long_functions)}个函数过长",
            suggestion="\n".join(long_functions) if long_functions else None
        ))

    def _check_file_size(self, code: str) -> None:
        """检查文件大小"""
        lines = code.split("\n")
        line_count = len(lines)
        
        self.checks.append(VerificationCheck(
            name="文件聚焦",
            passed=line_count < 800,
            message=f"{line_count} 行 (< 800)" if line_count < 800 else f"文件过长: {line_count} 行",
            suggestion="考虑拆分文件" if line_count >= 800 else None
        ))

    def _check_nesting(self, code: str) -> None:
        """检查嵌套深度"""
        import re
        max_nesting = 0
        current_nesting = 0
        problem_lines = []
        lines = code.split("\n")
        
        for i, line in enumerate(lines, 1):
            current_nesting = len(re.findall(r"^\s*(if|for|while|with|except)\b", line))
            if current_nesting > 4:
                problem_lines.append(f"第{i}行: 嵌套 {current_nesting} 层")
        
        self.checks.append(VerificationCheck(
            name="嵌套深度",
            passed=len(problem_lines) == 0,
            message="嵌套深度正常" if not problem_lines else f"{len(problem_lines)}处过深",
            suggestion="\n".join(problem_lines[:3]) if problem_lines else None
        ))

    def _check_error_handling(self, code: str) -> None:
        """检查错误处理"""
        import re
        
        # 检查 bare except
        bare_except = re.search(r"except\s*:\s*\n\s*pass", code)
        
        # 检查过于宽泛的异常
        too_broad = re.search(r"except\s+Exception\s*:\s*\n\s*(?!.*(?:log|raise|print))", code)
        
        issues = []
        if bare_except:
            issues.append("发现空的 except 子句")
        if too_broad:
            issues.append("异常处理过于宽泛")
        
        self.checks.append(VerificationCheck(
            name="错误处理",
            passed=len(issues) == 0,
            message="错误处理正确" if not issues else f"{len(issues)}处问题",
            suggestion="\n".join(issues) if issues else None
        ))

    def _check_hardcoded(self, code: str) -> None:
        """检查硬编码"""
        import re
        
        # 检查数字硬编码
        magic_numbers = re.findall(r"(?<![\"\w])\d{2,}(?![\"\w.])", code)
        magic_numbers = [n for n in magic_numbers if int(n) > 10]
        
        # 检查路径硬编码
        hardcoded_paths = re.findall(r"['\"][/\w]+\.(json|yaml|yml|txt|csv)['\"]", code)
        
        issues = []
        if magic_numbers:
            issues.append(f"发现 {len(magic_numbers)} 处魔法数字")
        if hardcoded_paths:
            issues.append(f"发现 {len(hardcoded_paths)} 处硬编码路径")
        
        self.checks.append(VerificationCheck(
            name="硬编码",
            passed=len(issues) == 0,
            message="无硬编码值" if not issues else f"{len(issues)}处硬编码",
            suggestion="使用常量或配置" if issues else None
        ))

    def _check_mutation(self, code: str) -> None:
        """检查变更模式"""
        import re
        
        # 检查 += [] 而不是 new_list = old_list + []
        mutations = re.findall(r"\w+\s*\+=\s*\[\]", code)
        
        self.checks.append(VerificationCheck(
            name="不可变性",
            passed=len(mutations) == 0,
            message="使用不可变模式" if not mutations else f"发现 {len(mutations)} 处变更",
            suggestion="使用新对象而非修改" if mutations else None
        ))

    def _build_report(self) -> Dict[str, Any]:
        """构建验证报告"""
        passed = sum(1 for c in self.checks if c.passed)
        total = len(self.checks)
        
        return {
            "passed": passed,
            "total": total,
            "pass_rate": f"{passed/total*100:.0f}%",
            "approval": "VERIFIED" if passed == total else "NEEDS_WORK",
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "suggestion": c.suggestion
                }
                for c in self.checks
            ],
            "summary": f"{passed}/{total} 项检查通过"
        }


def run_verification(code: str, context: str = "") -> Dict[str, Any]:
    """快捷验证函数"""
    skill = VerificationSkill()
    return skill.verify(code, context)
