"""
TDD Workflow - 测试驱动开发工作流
遵循: 红→绿→重构 循环
"""

from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import os


class TDDPhase(Enum):
    RED = "red"      # 写测试，测试应该失败
    GREEN = "green"  # 写最小实现让测试通过
    REFACTOR = "refactor"  # 重构改进代码


class TDDWorkflow:
    """测试驱动开发工作流管理器"""

    def __init__(self):
        self.current_phase = TDDPhase.RED
        self.test_results: List[Dict[str, Any]] = []
        self.coverage_threshold = 80  # 最低覆盖率要求

    def start_cycle(self, feature: str) -> Dict[str, Any]:
        """
        开始一个新的TDD周期

        Args:
            feature: 要开发的功能描述

        Returns:
            当前状态
        """
        self.current_phase = TDDPhase.RED
        return {
            "feature": feature,
            "phase": self.current_phase.value,
            "instruction": "编写测试用例，描述期望的行为（测试应该失败）",
            "next_phase": TDDPhase.GREEN.value
        }

    def proceed_to_green(self, test_code: str) -> Dict[str, Any]:
        """
        进入GREEN阶段：编写最小实现

        Args:
            test_code: 测试代码

        Returns:
            实现指导
        """
        self.current_phase = TDDPhase.GREEN
        return {
            "phase": TDDPhase.GREEN.value,
            "instruction": "编写最小实现让测试通过，不要过度设计",
            "focus": ["实现核心功能", "让测试变绿", "不考虑完美"],
            "next_phase": TDDPhase.REFACTOR.value
        }

    def proceed_to_refactor(self, implementation: str) -> Dict[str, Any]:
        """
        进入REFACTOR阶段：重构代码

        Args:
            implementation: 当前实现

        Returns:
            重构指导
        """
        self.current_phase = TDDPhase.REFACTOR
        return {
            "phase": TDDPhase.REFACTOR.value,
            "instruction": "重构代码提升质量，保持测试通过",
            "checklist": [
                "消除重复代码",
                "提取函数",
                "改善命名",
                "检查覆盖率 >= 80%"
            ],
            "next_phase": TDDPhase.RED.value
        }

    def complete_cycle(self) -> Dict[str, Any]:
        """完成当前TDD周期"""
        self.current_phase = TDDPhase.RED
        return {
            "status": "cycle_complete",
            "message": "准备开始下一个TDD周期"
        }

    def get_coverage_report(self) -> Dict[str, Any]:
        """获取覆盖率报告"""
        return {
            "current_coverage": 0,  # 待集成coverage工具
            "threshold": self.coverage_threshold,
            "meets_requirement": False
        }


if __name__ == "__main__":
    # 示例
    tdd = TDDWorkflow()

    # 开始功能开发
    state = tdd.start_cycle("用户登录功能")
    print(f"Phase: {state['phase']}")
    print(f"Instruction: {state['instruction']}")

    # 进入绿色阶段
    green = tdd.proceed_to_green("test_code_here")
    print(f"\nPhase: {green['phase']}")
    print(f"Instruction: {green['instruction']}")

    # 进入重构阶段
    refactor = tdd.proceed_to_refactor("impl_code_here")
    print(f"\nPhase: {refactor['phase']}")
    print(f"Checklist: {refactor['checklist']}")
