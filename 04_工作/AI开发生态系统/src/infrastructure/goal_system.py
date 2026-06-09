#!/usr/bin/env python3
"""
Goal System - 目标管理系统
长期目标追踪、分解、优先级调度
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid


class GoalStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    ABANDONED = "abandoned"
    SUSPENDED = "suspended"


class GoalPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class SubGoal:
    id: str
    description: str
    status: GoalStatus


@dataclass
class Goal:
    id: str
    title: str
    description: str
    status: GoalStatus
    priority: GoalPriority
    created_at: str
    updated_at: str
    deadline: Optional[str] = None
    completed_at: Optional[str] = None
    progress: float = 0.0
    subgoals: List[SubGoal] = None


class GoalScheduler:
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/goals"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        self.goals: List[Goal] = []
        self.goal_handlers: Dict[str, Callable] = {}
        self._load_goals()

    def _load_goals(self):
        goals_file = os.path.join(self.storage_path, "goals.json")
        if os.path.exists(goals_file):
            try:
                with open(goals_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.goals = [Goal(**g) for g in data]
            except:
                self.goals = []

    def _save_goals(self):
        goals_file = os.path.join(self.storage_path, "goals.json")
        with open(goals_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(g) for g in self.goals], f, ensure_ascii=False, indent=2)

    def create_goal(self, title: str, description: str = "",
                    priority: GoalPriority = GoalPriority.MEDIUM,
                    deadline: str = None) -> Goal:
        goal_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        goal = Goal(
            id=goal_id, title=title, description=description,
            status=GoalStatus.ACTIVE, priority=priority,
            created_at=now, updated_at=now, deadline=deadline,
            subgoals=[]
        )
        self.goals.append(goal)
        self._save_goals()
        return goal

    def update_progress(self, goal_id: str, progress: float) -> bool:
        for goal in self.goals:
            if goal.id == goal_id:
                goal.progress = max(0.0, min(1.0, progress))
                goal.updated_at = datetime.now().isoformat()
                if goal.progress >= 1.0:
                    goal.status = GoalStatus.COMPLETED
                    goal.completed_at = datetime.now().isoformat()
                self._save_goals()
                return True
        return False

    def get_active_goals(self) -> List[Goal]:
        return [g for g in self.goals if g.status == GoalStatus.ACTIVE]

    def get_next_goal(self) -> Optional[Goal]:
        active = self.get_active_goals()
        if not active:
            return None
        return sorted(active, key=lambda g: (g.priority.value, g.created_at))[0]

    def get_schedule_summary(self) -> Dict[str, Any]:
        active = self.get_active_goals()
        by_priority = {p.name: [] for p in GoalPriority}
        for g in active:
            by_priority[g.priority.name].append({"id": g.id, "title": g.title, "progress": g.progress})
        return {
            "total_active": len(active),
            "by_priority": by_priority,
            "next_goal": self.get_next_goal().id if self.get_next_goal() else None
        }


def create_goal_system() -> GoalScheduler:
    return GoalScheduler()
__exports__ = ['Goal', 'GoalPriority', 'GoalScheduler', 'GoalStatus', 'SubGoal', 'create_goal_system']


