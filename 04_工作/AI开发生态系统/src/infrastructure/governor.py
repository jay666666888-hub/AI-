#!/usr/bin/env python3
"""
Global Execution Governor - 全局执行控制器
80% deterministic / 20% AI reasoning
限制递归深度、反射频率、防止振荡
"""

from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import threading
import time


class GovernorAction(Enum):
    ALLOW = "allow"
    THROTTLE = "throttle"
    BLOCK = "block"
    FORCE_DETERMINISTIC = "force_deterministic"


@dataclass
class GovernorConfig:
    max_recursion_depth: int = 5
    max_reflection_per_hour: int = 10
    max_self_mod_per_minute: int = 3
    ai_reasoning_ratio: float = 0.2
    oscillation_window: int = 30
    oscillation_threshold: int = 3


class OscillationDetector:
    def __init__(self, window: int = 30, threshold: int = 3):
        self.window = window
        self.threshold = threshold
        self.history: Dict[str, List[float]] = {}

    def record(self, action: str) -> bool:
        now = time.time()
        if action not in self.history:
            self.history[action] = []
        self.history[action] = [t for t in self.history[action] if now - t < self.window]
        self.history[action].append(now)
        return len(self.history[action]) >= self.threshold

    def is_oscillating(self) -> bool:
        return any(len(times) >= self.threshold for times in self.history.values())


class GlobalExecutionGovernor:
    _instance: Optional['GlobalExecutionGovernor'] = None
    _lock = threading.Lock()

    def __init__(self, config: GovernorConfig = None):
        self.config = config or GovernorConfig()
        self.osc = OscillationDetector(self.config.oscillation_window, self.config.oscillation_threshold)
        self.recursion_stack: List[str] = []
        self.ai_count = 0
        self.det_count = 0
        self.reflection_count = 0
        self.last_reflection = None
        self.last_self_mod = None
        self.self_mod_count = 0

    @classmethod
    def get_instance(cls) -> 'GlobalExecutionGovernor':
        with cls._lock:
            if cls._instance is None:
                cls._instance = GlobalExecutionGovernor()
            return cls._instance

    def should_use_ai(self) -> bool:
        total = self.ai_count + self.det_count
        if total == 0:
            return True
        return (self.ai_count / total) < self.config.ai_reasoning_ratio

    def check_recursion(self, name: str) -> bool:
        if len(self.recursion_stack) >= self.config.max_recursion_depth:
            return False
        self.recursion_stack.append(name)
        return True

    def leave_recursion(self):
        if self.recursion_stack:
            self.recursion_stack.pop()

    def check_reflection(self) -> GovernorAction:
        now = datetime.now()
        if self.last_reflection:
            if (now - self.last_reflection).seconds < 3600 and self.reflection_count >= self.config.max_reflection_per_hour:
                return GovernorAction.THROTTLE
        self.last_reflection = now
        self.reflection_count += 1
        return GovernorAction.ALLOW

    def check_self_mod(self) -> GovernorAction:
        now = datetime.now()
        if self.last_self_mod:
            if (now - self.last_self_mod).seconds < 60 and self.self_mod_count >= self.config.max_self_mod_per_minute:
                return GovernorAction.BLOCK
        self.last_self_mod = now
        self.self_mod_count += 1
        return GovernorAction.ALLOW

    def decide(self, action: str) -> GovernorAction:
        if self.osc.record(action):
            return GovernorAction.THROTTLE
        if len(self.recursion_stack) >= self.config.max_recursion_depth:
            return GovernorAction.BLOCK
        if not self.should_use_ai():
            self.det_count += 1
            return GovernorAction.FORCE_DETERMINISTIC
        self.ai_count += 1
        return GovernorAction.ALLOW

    def execute(self, ai_fn: Callable, det_fn: Callable, *args, **kwargs) -> Any:
        if self.should_use_ai():
            self.ai_count += 1
            try:
                return ai_fn(*args, **kwargs)
            except:
                self.det_count += 1
                return det_fn(*args, **kwargs)
        else:
            self.det_count += 1
            return det_fn(*args, **kwargs)

    def status(self) -> Dict[str, Any]:
        return {
            "ratio": f"{self.config.ai_reasoning_ratio*100:.0f}% AI, {100-self.config.ai_reasoning_ratio*100:.0f}% Det",
            "current": f"AI {self.ai_count} / Det {self.det_count}",
            "recursion": f"{len(self.recursion_stack)}/{self.config.max_recursion_depth}",
            "oscillation": "YES" if self.osc.is_oscillating() else "no"
        }


def governor() -> GlobalExecutionGovernor:
    return GlobalExecutionGovernor.get_instance()

__exports__ = ['GlobalExecutionGovernor', 'GovernorAction', 'GovernorConfig', 'OscillationDetector', 'governor']


