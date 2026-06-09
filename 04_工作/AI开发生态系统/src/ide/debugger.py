"""
Smart Debugger - 智能调试器
自动诊断错误，提供修复建议
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import traceback
import re


@dataclass
class DebugInsight:
    type: str  # error, warning, suggestion
    title: str
    description: str
    line: Optional[int] = None
    fix_suggestion: Optional[str] = None


class SmartDebugger:
    """智能调试器"""

    def __init__(self):
        self.error_patterns: Dict[str, Dict[str, str]] = {
            "Python": {
                r"NameError:\s*name\s*'(\w+)'": "变量未定义",
                r"TypeError:\s*'(\w+)'.*object": "类型错误",
                r"IndentationError": "缩进错误",
                r"SyntaxError": "语法错误",
                r"AttributeError": "属性错误",
                r"ImportError": "导入错误",
                r"KeyError": "字典键不存在",
                r"IndexError": "列表索引越界",
                r"ZeroDivisionError": "除数为零",
            },
            "JavaScript": {
                r"ReferenceError:\s*(\w+)\s*is not defined": "变量未定义",
                r"TypeError:\s*Cannot read": "读取未定义属性",
                r"SyntaxError": "语法错误",
                r"RangeError": "范围错误",
            }
        }

    def analyze_error(self, error: Exception, language: str = "Python") -> DebugInsight:
        """分析错误并提供修复建议"""
        error_type = type(error).__name__
        error_msg = str(error)

        insight = DebugInsight(
            type="error",
            title=error_type,
            description=str(error),
            fix_suggestion=None
        )

        # 匹配错误模式
        patterns = self.error_patterns.get(language, self.error_patterns["Python"])
        for pattern, desc in patterns.items():
            if re.search(pattern, error_msg):
                insight.title = desc
                insight.fix_suggestion = self._get_fix_suggestion(error_type)
                break

        return insight

    def analyze_traceback(self, tb_str: str) -> List[DebugInsight]:
        """分析堆栈跟踪"""
        insights = []

        lines = tb_str.strip().split('\n')
        for line in lines:
            if 'File "' in line:
                match = re.search(r'File "([^"]+)", line (\d+)', line)
                if match:
                    insights.append(DebugInsight(
                        type="warning",
                        title="错误位置",
                        description=line.strip(),
                        line=int(match.group(2)),
                        fix_suggestion=None
                    ))

        return insights

    def _get_fix_suggestion(self, error_type: str) -> str:
        """获取修复建议"""
        suggestions = {
            "NameError": "检查变量名是否正确，或是否已导入",
            "TypeError": "检查变量类型是否正确，使用类型转换",
            "IndentationError": "使用一致的缩进（4个空格或Tab）",
            "SyntaxError": "检查语法是否正确，括号是否匹配",
            "AttributeError": "检查对象是否有该属性",
            "ImportError": "检查模块是否已安装，或路径是否正确",
            "KeyError": "使用 dict.get() 或检查键是否存在",
            "IndexError": "检查索引是否越界",
            "ZeroDivisionError": "添加除数检查",
        }
        return suggestions.get(error_type, "查看官方文档获取更多信息")

    def debug_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """静态代码调试（无需运行）"""
        insights = []

        if language.lower() == "python":
            insights = self._debug_python(code)
        elif language.lower() in ("javascript", "typescript"):
            insights = self._debug_js(code)

        return {
            "total_issues": len(insights),
            "insights": insights,
            "has_critical": any(i.type == "error" for i in insights)
        }

    def _debug_python(self, code: str) -> List[DebugInsight]:
        """Python 静态调试"""
        insights = []
        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            # 检查常见问题
            if '=' in line and '==' in line:
                if line.count('=') > 1 and '==' not in line:
                    insights.append(DebugInsight(
                        type="warning",
                        title="可能的赋值错误",
                        description=f"第{i}行: {line.strip()}",
                        line=i,
                        fix_suggestion="使用 == 进行比较，= 进行赋值"
                    ))

            # 检查未使用的变量
            if line.strip().startswith('#'):
                pass  # 跳过注释

        return insights

    def _debug_js(self, code: str) -> List[DebugInsight]:
        """JavaScript 静态调试"""
        insights = []

        # 检查 console.log
        if 'console.log' in code:
            insights.append(DebugInsight(
                type="warning",
                title="调试代码残留",
                description="发现 console.log",
                fix_suggestion="提交前删除 console.log"
            ))

        return insights


if __name__ == "__main__":
    debugger = SmartDebugger()

    # 示例
    try:
        x = 1 / 0
    except Exception as e:
        insight = debugger.analyze_error(e, "Python")
        print(f"错误: {insight.title}")
        print(f"建议: {insight.fix_suggestion}")
