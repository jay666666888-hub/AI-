"""
Hermes Integration Layer
连接 CrewAI 系统与 Hermes Hook 系统
"""

from .hook_manager import HookManager
from .skill_loader import SkillLoader

__all__ = ["HookManager", "SkillLoader"]
__version__ = "1.0.0"