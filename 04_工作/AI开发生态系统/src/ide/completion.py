"""
AI Completion - AI 智能补全
基于上下文感知的代码补全
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import os


@dataclass
class Completion:
    text: str
    type: str  # function, variable, class, snippet
    confidence: float
    source: str  # local, model, template


class AICompletion:
    """AI 智能补全引擎"""

    def __init__(self, llm_provider: str = "local"):
        self.llm_provider = llm_provider
        self.context_window = 10  # 行
        self.snippets: Dict[str, List[str]] = {}

    def get_completions(self, code: str, cursor_pos: int, language: str = "python") -> List[Completion]:
        """获取补全建议"""
        completions = []

        # 1. 关键字补全
        completions.extend(self._keyword_completions(language))

        # 2. 模板片段补全
        completions.extend(self._snippet_completions(code, language))

        # 3. 上下文感知补全（需要 LLM）
        if self.llm_provider != "disabled":
            completions.extend(self._context_completions(code, cursor_pos, language))

        # 按置信度排序
        completions.sort(key=lambda x: x.confidence, reverse=True)
        return completions[:10]

    def _keyword_completions(self, language: str) -> List[Completion]:
        """关键字补全"""
        keywords = {
            "python": ["def", "class", "if", "elif", "else", "for", "while", "try", "except", "return", "import", "from", "async", "await"],
            "javascript": ["function", "const", "let", "var", "if", "else", "for", "while", "return", "import", "export", "async", "await"],
            "typescript": ["function", "const", "let", "var", "interface", "type", "if", "else", "for", "while", "return", "import", "export"],
        }
        return [
            Completion(text=kw, type="keyword", confidence=0.8, source="local")
            for kw in keywords.get(language, keywords["python"])
        ]

    def _snippet_completions(self, code: str, language: str) -> List[Completion]:
        """模板片段补全"""
        snippets = {
            "python": {
                "def": "def ${1:function_name}(${2:args}):\n    ${3:pass}",
                "class": "class ${1:ClassName}:\n    def __init__(self${2: args}):\n        ${3:pass}",
                "if": "if ${1:condition}:\n    ${2:pass}",
                "try": "try:\n    ${1:pass}\nexcept ${2:Exception} as e:\n    ${3:pass}",
                "for": "for ${1:item} in ${2:iterable}:\n    ${3:pass}",
            },
            "javascript": {
                "function": "function ${1:name}(${2:args}) {\n    ${3:pass}\n}",
                "const": "const ${1:name} = ${2:value};",
                "arrow": "const ${1:name} = (${2:args}) => {\n    ${3:pass}\n};",
                "async": "const ${1:name} = async (${2:args}) => {\n    ${3:pass}\n};",
            }
        }

        completions = []
        lang_snippets = snippets.get(language, snippets["python"])

        for trigger, template in lang_snippets.items():
            completions.append(Completion(
                text=template,
                type="snippet",
                confidence=0.7,
                source="template"
            ))

        return completions

    def _context_completions(self, code: str, cursor_pos: int, language: str) -> List[Completion]:
        """基于 LLM 的上下文补全"""
        # 预留：集成 Ollama / OpenAI
        return []

    def add_snippet(self, language: str, trigger: str, template: str) -> None:
        """添加自定义片段"""
        if language not in self.snippets:
            self.snippets[language] = []
        self.snippets[language].append(template)

    def learn_from_file(self, file_path: str) -> int:
        """从文件学习代码模式"""
        if not os.path.exists(file_path):
            return 0

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 简单模式提取（函数定义等）
        import re
        patterns = re.findall(r'def\s+(\w+)\s*\(', content)

        return len(patterns)


if __name__ == "__main__":
    completer = AICompletion()
    completions = completer.get_completions("def ", 4, "python")
    print(f"获取到 {len(completions)} 个补全建议")
