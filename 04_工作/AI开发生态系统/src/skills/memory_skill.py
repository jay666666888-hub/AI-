#!/usr/bin/env python3
"""
Memory Skill - 持久记忆系统
基于 ECC 的自动记忆更新模式
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import os
import json


@dataclass
class MemoryEntry:
    content: str
    type: str  # user, project, feedback, reference, skill
    created_at: str
    updated_at: str
    tags: List[str]
    importance: int  # 1-5


class MemorySkill:
    """
    持久记忆技能
    自动管理用户信息、项目状态、决策记录
    """

    MEMORY_DIR = os.path.expanduser("~/.claude/projects/-mnt-c-Users-Admin/memory")

    def __init__(self):
        self.memory_dir = self.MEMORY_DIR
        os.makedirs(self.memory_dir, exist_ok=True)
        self.entries: List[MemoryEntry] = []
        self._load_memory()

    def _load_memory(self):
        """加载已有记忆"""
        for filename in os.listdir(self.memory_dir):
            if filename.endswith(".md") and filename != "MEMORY.md":
                path = os.path.join(self.memory_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    entry_type = self._detect_type(content)
                    self.entries.append(MemoryEntry(
                        content=content,
                        type=entry_type,
                        created_at=self._extract_date(content) or "",
                        updated_at=self._extract_date(content) or "",
                        tags=self._extract_tags(content),
                        importance=self._assess_importance(content)
                    ))
                except:
                    pass

    def _detect_type(self, content: str) -> str:
        """检测记忆类型"""
        if "user" in content.lower():
            return "user"
        elif "feedback" in content.lower():
            return "feedback"
        elif "project" in content.lower():
            return "project"
        elif "reference" in content.lower():
            return "reference"
        return "general"

    def _extract_date(self, content: str) -> Optional[str]:
        """提取日期"""
        import re
        match = re.search(r"\d{4}-\d{2}-\d{2}", content)
        return match.group(0) if match else None

    def _extract_tags(self, content: str) -> List[str]:
        """提取标签"""
        import re
        tags = re.findall(r"#(\w+)", content)
        return tags[:10]  # 最多10个标签

    def _assess_importance(self, content: str) -> int:
        """评估重要性"""
        score = 2
        if len(content) > 500:
            score += 1
        if any(kw in content.lower() for kw in ["重要", "关键", "必须", "禁止"]):
            score += 1
        return min(score, 5)

    def remember(self, content: str, entry_type: str = "general", 
                 tags: List[str] = None) -> Dict[str, Any]:
        """记忆新内容"""
        entry = MemoryEntry(
            content=content,
            type=entry_type,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            tags=tags or [],
            importance=3
        )
        self.entries.append(entry)
        
        # 保存到文件
        filename = f"{entry_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
        path = os.path.join(self.memory_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return {
            "status": "remembered",
            "filename": filename,
            "entry_count": len(self.entries)
        }

    def recall(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """召回相关内容"""
        results = []
        query_lower = query.lower()
        
        for entry in self.entries:
            # 文本匹配
            if query_lower in entry.content.lower():
                results.append({
                    "content": entry.content[:200],
                    "type": entry.type,
                    "tags": entry.tags,
                    "score": 1.0
                })
            # 标签匹配
            elif any(query_lower in tag.lower() for tag in entry.tags):
                results.append({
                    "content": entry.content[:200],
                    "type": entry.type,
                    "tags": entry.tags,
                    "score": 0.8
                })
        
        return results[:top_k]

    def update(self, key: str, value: str) -> Dict[str, Any]:
        """更新记忆"""
        updated = False
        for entry in self.entries:
            if key.lower() in entry.content.lower():
                entry.content += f"\n\n## Update {datetime.now().isoformat()}\n{value}"
                entry.updated_at = datetime.now().isoformat()
                updated = True
        
        return {
            "status": "updated" if updated else "not_found",
            "entries_modified": 1 if updated else 0
        }

    def get_user_profile(self) -> Dict[str, Any]:
        """获取用户画像"""
        user_entries = [e for e in self.entries if e.type == "user"]
        return {
            "total_entries": len(self.entries),
            "user_entries": len(user_entries),
            "recent_memory": [asdict(e) for e in self.entries[-5:]]
        }

    def get_status(self) -> Dict[str, Any]:
        """获取记忆状态"""
        by_type = {}
        for entry in self.entries:
            by_type[entry.type] = by_type.get(entry.type, 0) + 1
        
        return {
            "total": len(self.entries),
            "by_type": by_type,
            "memory_dir": self.memory_dir
        }


def run_memory(action: str, content: str = "", 
               entry_type: str = "general", 
               tags: List[str] = None) -> Dict[str, Any]:
    """快捷记忆函数"""
    skill = MemorySkill()
    
    if action == "remember":
        return skill.remember(content, entry_type, tags)
    elif action == "recall":
        return skill.recall(content)
    elif action == "update":
        return skill.update(content, "")
    elif action == "status":
        return skill.get_status()
    else:
        return {"error": f"Unknown action: {action}"}
