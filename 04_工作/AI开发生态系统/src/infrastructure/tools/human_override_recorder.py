#!/usr/bin/env python3
"""
Human Override Recorder - Phase: Reality Alignment
最值钱的数据：记录"系统错在哪"

核心数据：
- system_decision: 系统的原始决策
- human_decision: 人类的最终决策
- override_reason: 为什么人类override

这是校准"系统误差"的黄金标签。
"""

import sys
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import json

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


class OverrideReason(Enum):
    SAFETY_CONCERN = "safety_concern"
    POLITICAL = "political"  # 组织政治
    DOMAIN_KNOWLEDGE = "domain_knowledge"  # 系统不懂的领域知识
    CONTEXT_MISSING = "context_missing"  # 系统缺少上下文
    RISK_TOLERANCE = "risk_tolerance"  # 风险偏好不同
    TIMING = "timing"  # 时机问题
    DEPENDENCY = "dependency"  # 依赖问题
    OTHER = "other"


class OverrideType(Enum):
    BLOCK_OVERRIDE = "block_override"  # 系统阻止，人类放行
    APPROVE_OVERRIDE = "approve_override"  # 系统批准，人类阻止
    MODIFY = "modify"  # 修改决策参数
    ESCALATE = "escalate"  # 升级处理


@dataclass
class OverrideEvent:
    event_id: str
    timestamp: str

    # Context
    task_id: str
    task_type: str
    agent_id: str

    # Decisions
    system_decision: str
    system_confidence: float
    system_reasoning: str

    human_decision: str
    override_type: str

    override_reason: str
    override_detail: str

    # Value
    wait_time_seconds: float  # 人类介入等待时间
    system_was_right: bool  # 回溯：系统是否正确


class HumanOverrideRecorder:
    """
    记录人类override事件。

    这是最值钱的数据，因为：
    1. 直接标记"系统错在哪"
    2. 可用于校准系统决策边界
    3. 发现系统性偏见
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "/mnt/e/黑曜石/04_工作/AI开发生态系统/telemetry/overrides"
        self.events: List[OverrideEvent] = []
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        import os
        os.makedirs(self.storage_path, exist_ok=True)

    def record(
        self,
        task_id: str,
        task_type: str,
        agent_id: str,
        system_decision: str,
        system_confidence: float,
        system_reasoning: str,
        human_decision: str,
        override_type: OverrideType,
        override_reason: OverrideReason,
        override_detail: str,
        wait_time_seconds: float = 0.0
    ) -> str:
        """记录一次override事件"""
        event_id = str(uuid.uuid4())[:12]

        # 判断系统是否正确（回溯）
        system_was_right = (
            (override_type == OverrideType.BLOCK_OVERRIDE and human_decision == "approved") or
            (override_type in [OverrideType.APPROVE_OVERRIDE, OverrideType.ESCALATE] and human_decision == "blocked")
        )

        event = OverrideEvent(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            task_type=task_type,
            agent_id=agent_id,
            system_decision=system_decision,
            system_confidence=system_confidence,
            system_reasoning=system_reasoning,
            human_decision=human_decision,
            override_type=override_type.value,
            override_reason=override_reason.value,
            override_detail=override_detail,
            wait_time_seconds=wait_time_seconds,
            system_was_right=system_was_right
        )

        self.events.append(event)
        return event_id

    def get_override_rate(self) -> float:
        """Override率（相对于总决策数）"""
        # 需要从外部注入总决策数
        return 0.0  # 外部注入

    def get_system_accuracy_on_overrides(self) -> Dict[str, float]:
        """
        统计系统在override事件中的准确率。
        当人类override时，系统是否其实是对的？
        """
        if not self.events:
            return {"accuracy": 0.0, "total": 0}

        correct = sum(1 for e in self.events if e.system_was_right)
        total = len(self.events)

        # 按task_type分类
        by_type = {}
        for event in self.events:
            if event.task_type not in by_type:
                by_type[event.task_type] = {"correct": 0, "total": 0}
            if event.system_was_right:
                by_type[event.task_type]["correct"] += 1
            by_type[event.task_type]["total"] += 1

        return {
            "accuracy": correct / total if total > 0 else 0.0,
            "total": total,
            "by_task_type": {
                tt: data["correct"] / data["total"] if data["total"] > 0 else 0.0
                for tt, data in by_type.items()
            }
        }

    def get_override_patterns(self) -> Dict[str, Any]:
        """
        发现override模式。
        例如：
        - 某些task_type的override率特别高
        - 某些agent_id的override行为
        - override的常见原因
        """
        if not self.events:
            return {}

        # 按override_reason统计
        reason_counts = {}
        for event in self.events:
            reason_counts[event.override_reason] = reason_counts.get(event.override_reason, 0) + 1

        # 按task_type统计
        type_counts = {}
        for event in self.events:
            type_counts[event.task_type] = type_counts.get(event.task_type, 0) + 1

        # 按agent统计
        agent_counts = {}
        for event in self.events:
            agent_counts[event.agent_id] = agent_counts.get(event.agent_id, 0) + 1

        # 平均wait_time
        avg_wait = sum(e.wait_time_seconds for e in self.events) / len(self.events) if self.events else 0

        return {
            "total_overrides": len(self.events),
            "by_reason": reason_counts,
            "by_task_type": type_counts,
            "by_agent": agent_counts,
            "avg_wait_time_seconds": avg_wait,
            "system_correct_rate": self.get_system_accuracy_on_overrides()["accuracy"]
        }

    def save(self, date: str = None):
        """保存到文件"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        path = f"{self.storage_path}/overrides_{date}.json"
        data = {
            "date": date,
            "events": [asdict(e) for e in self.events],
            "patterns": self.get_override_patterns()
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

        return path


class OverrideAnalyzer:
    """
    分析override数据，生成校准建议。
    """

    def __init__(self, recorder: HumanOverrideRecorder):
        self.recorder = recorder

    def analyze_calibration_gaps(self) -> Dict[str, Any]:
        """
        发现校准差距。

        例如：
        - deploy task被系统高估 → 经常被block但人类放行
        - 说明deploy的uncertainty penalty可能太高
        """
        patterns = self.recorder.get_override_patterns()

        # 按task_type分析
        gaps = {}
        for tt, count in patterns.get("by_task_type", {}).items():
            by_reason = {}
            for event in self.recorder.events:
                if event.task_type == tt:
                    by_reason[event.override_reason] = by_reason.get(event.override_reason, 0) + 1

            gaps[tt] = {
                "count": count,
                "reasons": by_reason,
                "system_wrong_rate": 1.0 - patterns.get("by_task_type", {}).get(tt, 0)
            }

        return {
            "gaps": gaps,
            "recommendations": self._generate_recommendations(gaps)
        }

    def _generate_recommendations(self, gaps: Dict) -> List[str]:
        recs = []
        for tt, data in gaps.items():
            if data["system_wrong_rate"] > 0.5:
                recs.append(f"{tt}: 系统错误率{data['system_wrong_rate']:.1%}，需要重新校准")
        return recs


if __name__ == "__main__":
    print("=" * 60)
    print("HUMAN OVERRIDE RECORDER - Reality Alignment")
    print("=" * 60)

    recorder = HumanOverrideRecorder()

    # 模拟override事件
    print("\n[1] Recording sample override events...")

    overrides = [
        ("task_001", "deploy", "planner", "blocked", 0.7, "high uncertainty",
         "approved", OverrideType.BLOCK_OVERRIDE, OverrideReason.SAFETY_CONCERN,
         "人类确认环境安全", 120.0),

        ("task_002", "deploy", "planner", "approved", 0.6, "low uncertainty",
         "blocked", OverrideType.APPROVE_OVERRIDE, OverrideReason.RISK_TOLERANCE,
         "组织风险偏好低", 90.0),

        ("task_003", "build", "coder", "approved", 0.8, "confident",
         "blocked", OverrideType.APPROVE_OVERRIDE, OverrideReason.CONTEXT_MISSING,
         "缺少业务上下文", 60.0),

        ("task_004", "research", "reviewer", "approved", 0.9, "very confident",
         "approved", OverrideType.MODIFY, OverrideReason.DOMAIN_KNOWLEDGE,
         "参数调整", 30.0),
    ]

    for args in overrides:
        event_id = recorder.record(*args)
        print(f"  Recorded: {event_id}")

    print("\n[2] Override Patterns:")
    patterns = recorder.get_override_patterns()
    print(f"  Total overrides: {patterns['total_overrides']}")
    print(f"  System correct rate: {patterns['system_correct_rate']:.1%}")
    print(f"  By task type: {patterns['by_task_type']}")
    print(f"  By reason: {patterns['by_reason']}")

    print("\n[3] System Accuracy on Overrides:")
    accuracy = recorder.get_system_accuracy_on_overrides()
    print(f"  Overall accuracy: {accuracy['accuracy']:.1%}")
    for tt, acc in accuracy.get("by_task_type", {}).items():
        print(f"    {tt}: {acc:.1%}")

    print("\n[4] Saving...")
    path = recorder.save()
    print(f"  Saved to: {path}")

    print("\n" + "=" * 60)
    print("KEY INSIGHT:")
    print("  Human Override = 黄金标签")
    print("  记录'系统错在哪' → 用于校准系统")
    print("=" * 60)