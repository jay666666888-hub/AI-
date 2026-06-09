"""
Skill Loader - Hermes Skill 加载器
动态加载和管理 Claude Code skills
"""

from typing import Dict, List, Any, Optional, Callable
import os
import json
from pathlib import Path


class Skill:
    """Skill 定义"""

    def __init__(self, name: str, description: str, handler: Callable, metadata: Optional[Dict] = None):
        self.name = name
        self.description = description
        self.handler = handler
        self.metadata = metadata or {}

    def execute(self, *args, **kwargs) -> Any:
        """执行 skill"""
        return self.handler(*args, **kwargs)


class SkillLoader:
    """Skill 加载器，从文件系统加载 skills"""

    def __init__(self, skills_base_path: Optional[str] = None):
        self.skills_base_path = skills_base_path or os.path.expanduser("~/.claude/skills")
        self.skills: Dict[str, Skill] = {}
        self.categories: Dict[str, List[str]] = {}

    def load_from_path(self, path: Optional[str] = None) -> int:
        """
        从指定路径加载所有 skills

        Args:
            path: skills 目录路径

        Returns:
            加载的 skill 数量
        """
        base_path = path or self.skills_base_path
        loaded_count = 0

        if not os.path.exists(base_path):
            return 0

        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".md") or file == "SKILL.md":
                    skill_path = os.path.join(root, file)
                    skill = self._load_skill_from_file(skill_path)
                    if skill:
                        self.skills[skill.name] = skill
                        loaded_count += 1

                        # 按目录分类
                        category = os.path.basename(os.path.dirname(skill_path))
                        if category not in self.categories:
                            self.categories[category] = []
                        self.categories[category].append(skill.name)

        return loaded_count

    def _load_skill_from_file(self, file_path: str) -> Optional[Skill]:
        """从文件加载单个 skill"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 解析 skill 定义
            name = os.path.basename(file_path).replace(".md", "")
            description = self._extract_description(content)

            # 创建 skill（这里用简单的handler，实际应该从文件解析代码）
            def default_handler(*args, **kwargs):
                return {"skill": name, "content": content[:100], "message": "Skill loaded"}

            return Skill(
                name=name,
                description=description,
                handler=default_handler,
                metadata={"path": file_path}
            )
        except Exception as e:
            print(f"Error loading skill from {file_path}: {e}")
            return None

    def _extract_description(self, content: str) -> str:
        """从 skill 内容中提取描述"""
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("#"):
                return line.replace("#", "").strip()
        return content[:100]

    def get_skill(self, name: str) -> Optional[Skill]:
        """获取指定名称的 skill"""
        return self.skills.get(name)

    def list_skills(self, category: Optional[str] = None) -> List[str]:
        """列出所有 skills 或指定类别的 skills"""
        if category:
            return self.categories.get(category, [])
        return list(self.skills.keys())

    def list_categories(self) -> List[str]:
        """列出所有类别"""
        return list(self.categories.keys())

    def execute_skill(self, name: str, *args, **kwargs) -> Any:
        """执行指定 skill"""
        skill = self.get_skill(name)
        if not skill:
            return {"error": f"Skill not found: {name}"}
        return skill.execute(*args, **kwargs)

    def reload(self) -> int:
        """重新加载所有 skills"""
        self.skills = {}
        self.categories = {}
        return self.load_from_path()


if __name__ == "__main__":
    # 示例用法
    loader = SkillLoader()

    # 从默认路径加载
    count = loader.load_from_path()
    print(f"Loaded {count} skills")

    # 列出所有类别
    categories = loader.list_categories()
    print(f"Categories: {categories}")

    # 列出所有 skills
    skills = loader.list_skills()
    print(f"Total skills: {len(skills)}")

    # 执行 skill
    result = loader.execute_skill("example_skill")
    print(result)