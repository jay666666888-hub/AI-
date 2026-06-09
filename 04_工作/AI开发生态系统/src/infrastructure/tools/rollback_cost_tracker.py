#!/usr/bin/env python3
"""
Rollback Cost Tracker - Phase: Reality Alignment
真实rollback severity数据

Deploy calibration最大问题：
缺真实rollback cost

现在需要记录：
- rollback time
- service downtime
- dependency blast radius
- recovery complexity

这会极大提高deploy的校准精度。
"""

import sys
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


class RollbackSeverity(Enum):
    NONE = "none"  # 没有rollback
    MINOR = "minor"  # <5分钟，影响小
    MODERATE = "moderate"  # 5-30分钟，中等影响
    MAJOR = "major"  # 30分钟-2小时，重大影响
    CRITICAL = "critical"  # >2小时或服务中断

    @classmethod
    def from_minutes(cls, minutes: float) -> "RollbackSeverity":
        if minutes < 5:
            return cls.MINOR
        elif minutes < 30:
            return cls.MODERATE
        elif minutes < 120:
            return cls.MAJOR
        else:
            return cls.CRITICAL


@dataclass
class RollbackCost:
    event_id: str
    timestamp: str
    task_id: str
    task_type: str

    # Rollback details
    rollback_initiated: bool
    rollback_time_seconds: float

    # Impact dimensions
    service_downtime_seconds: float
    affected_services: List[str]
    user_impact: int  # 受影响用户数

    # Dependency blast radius
    downstream_failures: int
    upstream_dependencies: int

    # Recovery complexity
    manual_steps: int
    data_loss: bool
    requires_rollback: bool

    # Calculated
    severity: str  # RollbackSeverity.value
    total_cost_score: float  # 综合成本评分


class RollbackCostTracker:
    """
    跟踪真实rollback cost。

    这是校准deploy任务的关键数据：
    - 没有真实cost数据，deploy ECE永远不准
    - cost数据要事后注入（真实发生后）
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "/mnt/e/黑曜石/04_工作/AI开发生态系统/telemetry/rollbacks"
        self.events: List[RollbackCost] = []
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        import os
        os.makedirs(self.storage_path, exist_ok=True)

    def record(
        self,
        task_id: str,
        task_type: str,
        rollback_initiated: bool = False,
        rollback_time_seconds: float = 0.0,
        service_downtime_seconds: float = 0.0,
        affected_services: List[str] = None,
        user_impact: int = 0,
        downstream_failures: int = 0,
        upstream_dependencies: int = 0,
        manual_steps: int = 0,
        data_loss: bool = False
    ) -> str:
        """记录一次rollback cost"""
        event_id = str(uuid.uuid4())[:12]
        affected_services = affected_services or []

        # 计算severity
        severity = RollbackSeverity.NONE
        if rollback_initiated:
            severity = RollbackSeverity.from_minutes(rollback_time_seconds / 60)

        # 计算总成本评分 (0-1)
        time_component = min(1.0, rollback_time_seconds / 7200)  # 2小时为1.0
        downtime_component = min(1.0, service_downtime_seconds / 7200)
        user_component = min(1.0, user_impact / 10000)  # 1万用户为1.0
        blast_component = min(1.0, downstream_failures / 10)
        manual_component = min(1.0, manual_steps / 10)
        data_loss_component = 0.5 if data_loss else 0.0

        total_cost_score = (
            0.25 * time_component +
            0.25 * downtime_component +
            0.15 * user_component +
            0.15 * blast_component +
            0.10 * manual_component +
            0.10 * data_loss_component
        )

        event = RollbackCost(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            task_type=task_type,
            rollback_initiated=rollback_initiated,
            rollback_time_seconds=rollback_time_seconds,
            service_downtime_seconds=service_downtime_seconds,
            affected_services=affected_services,
            user_impact=user_impact,
            downstream_failures=downstream_failures,
            upstream_dependencies=upstream_dependencies,
            manual_steps=manual_steps,
            data_loss=data_loss,
            requires_rollback=rollback_initiated,
            severity=severity.value,
            total_cost_score=total_cost_score
        )

        self.events.append(event)
        return event_id

    def get_cost_by_task_type(self) -> Dict[str, Dict[str, float]]:
        """按task_type统计rollback cost"""
        by_type = {}
        for event in self.events:
            if event.task_type not in by_type:
                by_type[event.task_type] = {
                    "count": 0,
                    "total_cost": 0.0,
                    "avg_cost": 0.0,
                    "total_downtime": 0.0,
                    "total_user_impact": 0
                }

            by_type[event.task_type]["count"] += 1
            by_type[event.task_type]["total_cost"] += event.total_cost_score
            by_type[event.task_type]["total_downtime"] += event.service_downtime_seconds
            by_type[event.task_type]["total_user_impact"] += event.user_impact

        for tt in by_type:
            if by_type[tt]["count"] > 0:
                by_type[tt]["avg_cost"] = by_type[tt]["total_cost"] / by_type[tt]["count"]

        return by_type

    def get_severity_distribution(self) -> Dict[str, int]:
        """获取severity分布"""
        dist = {}
        for event in self.events:
            dist[event.severity] = dist.get(event.severity, 0) + 1
        return dist

    def calculate_risk_adjusted_cost(self, task_type: str, base_utility: float) -> Tuple[float, Dict]:
        """
        计算风险调整后的真实成本。

        用于校准deploy任务的utility：
        - 如果过去deploy平均cost很高，应该降低utility预测
        - 如果cost波动大，增加uncertainty penalty
        """
        costs = [e.total_cost_score for e in self.events if e.task_type == task_type]

        if not costs:
            return base_utility, {"cost_data": "insufficient"}

        avg_cost = sum(costs) / len(costs)
        max_cost = max(costs)
        cost_variance = sum((c - avg_cost) ** 2 for c in costs) / len(costs)

        # 风险调整：utility降低一个cost factor
        risk_adjustment = avg_cost * 0.5  # 50%的cost要计入风险
        risk_adjusted_utility = max(0.0, base_utility - risk_adjustment)

        return risk_adjusted_utility, {
            "avg_cost": avg_cost,
            "max_cost": max_cost,
            "cost_variance": cost_variance,
            "sample_count": len(costs),
            "risk_adjustment": risk_adjustment
        }

    def save(self, date: str = None):
        """保存到文件"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        path = f"{self.storage_path}/rollbacks_{date}.json"
        data = {
            "date": date,
            "events": [asdict(e) for e in self.events],
            "cost_by_type": self.get_cost_by_task_type(),
            "severity_distribution": self.get_severity_distribution()
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

        return path


if __name__ == "__main__":
    print("=" * 60)
    print("ROLLBACK COST TRACKER - Reality Alignment")
    print("=" * 60)

    tracker = RollbackCostTracker()

    # 模拟rollback事件
    print("\n[1] Recording sample rollback events...")

    rollbacks = [
        ("deploy_001", "deploy", True, 1800, 1800, ["api-gateway"], 500, 3, 5, 2, False),
        ("deploy_002", "deploy", False, 0, 0, [], 0, 0, 0, 0, False),
        ("deploy_003", "deploy", True, 7200, 7200, ["api-gateway", "auth-service", "payment"], 5000, 5, 8, 5, True),
        ("build_001", "build", True, 300, 300, ["build-server"], 50, 1, 2, 1, False),
        ("fix_001", "fix", False, 0, 0, [], 0, 0, 0, 0, False),
    ]

    for args in rollbacks:
        event_id = tracker.record(*args)
        print(f"  Recorded: {event_id}")

    print("\n[2] Cost by Task Type:")
    cost_by_type = tracker.get_cost_by_task_type()
    for tt, data in cost_by_type.items():
        print(f"  {tt}: count={data['count']}, avg_cost={data['avg_cost']:.3f}, "
              f"total_downtime={data['total_downtime']:.0f}s")

    print("\n[3] Severity Distribution:")
    for sev, count in tracker.get_severity_distribution().items():
        print(f"  {sev}: {count}")

    print("\n[4] Risk-Adjusted Cost for DEPLOY:")
    adj_cost, details = tracker.calculate_risk_adjusted_cost("deploy", 0.8)
    print(f"  Base utility: 0.80")
    print(f"  Risk-adjusted: {adj_cost:.3f}")
    print(f"  Details: {details}")

    print("\n[5] Saving...")
    path = tracker.save()
    print(f"  Saved to: {path}")

    print("\n" + "=" * 60)
    print("KEY INSIGHT:")
    print("  没有真实rollback cost数据")
    print("  → deploy ECE永远会高估utility")
    print("  → 需要真实cost注入才能校准")
    print("=" * 60)