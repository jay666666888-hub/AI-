#!/usr/bin/env python3
"""
Near-Miss Event Tracker - Phase: Reality Alignment
极重要的数据：差点rollback、差点timeout、差点failure

虽然没失败：
但属于 hidden risk

这些数据对calibration非常值钱。
"""

import sys
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


class NearMissType(Enum):
    ROLLBACK_NEAR_MISS = "rollback_near_miss"  # 差点rollback
    TIMEOUT_NEAR_MISS = "timeout_near_miss"  # 差点timeout
    DEPENDENCY_FAILURE_NEAR_MISS = "dependency_failure_near_miss"  # 差点依赖失败
    CONCURRENCY_NEAR_MISS = "concurrency_near_miss"  # 差点并发冲突
    RESOURCE_NEAR_MISS = "resource_near_miss"  # 差点资源耗尽


@dataclass
class NearMissEvent:
    event_id: str
    timestamp: str
    task_id: str
    task_type: str

    # Near-miss type
    near_miss_type: str  # NearMissType.value
    near_miss_severity: float  # 0-1，越高越严重

    # What almost happened
    what_almost_happened: str
    how_close: float  # 0-1，越接近1越近
    threshold_that_was_almost_breached: float

    # Context
    agent_id: str
    system_decision: str
    external_dependencies: int

    # Outcome (still succeeded despite near-miss)
    still_succeeded: bool
    success_margin: float  # 成功有多勉强


class NearMissTracker:
    """
    跟踪Near-miss事件。

    这是"隐藏风险"的直接测量：
    - 没有near-miss数据 = 不知道系统的边界在哪里
    - near-miss多的task_type = 风险被低估
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "/mnt/e/黑曜石/04_工作/AI开发生态系统/telemetry/nearmiss"
        self.events: List[NearMissEvent] = []
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        import os
        os.makedirs(self.storage_path, exist_ok=True)

    def record(
        self,
        task_id: str,
        task_type: str,
        near_miss_type: NearMissType,
        what_almost_happened: str,
        how_close: float,
        threshold_breached: float,
        agent_id: str,
        system_decision: str,
        external_dependencies: int,
        still_succeeded: bool,
        success_margin: float
    ) -> str:
        """记录一次near-miss事件"""
        event_id = str(uuid.uuid4())[:12]

        # 计算severity（基于how_close和success_margin）
        # 越接近失败、越勉强成功，越严重
        severity = how_close * (1.0 - success_margin)

        event = NearMissEvent(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            task_type=task_type,
            near_miss_type=near_miss_type.value,
            near_miss_severity=severity,
            what_almost_happened=what_almost_happened,
            how_close=how_close,
            threshold_that_was_almost_breached=threshold_breached,
            agent_id=agent_id,
            system_decision=system_decision,
            external_dependencies=external_dependencies,
            still_succeeded=still_succeeded,
            success_margin=success_margin
        )

        self.events.append(event)
        return event_id

    def get_near_miss_rate(self) -> Dict[str, float]:
        """
        获取各task_type的near-miss率。

        near-miss率高的task_type = 风险被低估
        """
        by_type = {}
        for event in self.events:
            if event.task_type not in by_type:
                by_type[event.task_type] = {"total": 0, "near_misses": 0}

            by_type[event.task_type]["total"] += 1
            if event.near_miss_severity > 0.3:  # 超过0.3算真正的near-miss
                by_type[event.task_type]["near_misses"] += 1

        return {
            tt: data["near_misses"] / data["total"] if data["total"] > 0 else 0.0
            for tt, data in by_type.items()
        }

    def get_severity_distribution(self) -> Dict[str, int]:
        """获取severity分布"""
        dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for event in self.events:
            if event.near_miss_severity < 0.25:
                dist["low"] += 1
            elif event.near_miss_severity < 0.5:
                dist["medium"] += 1
            elif event.near_miss_severity < 0.75:
                dist["high"] += 1
            else:
                dist["critical"] += 1
        return dist

    def get_risk_signals(self) -> List[Dict[str, Any]]:
        """
        发现risk signals。

        例如：
        - 某个task_type的near-miss severity越来越高
        - 某个agent_id的near-miss特别多
        - 某个时间段的near-miss集中爆发
        """
        signals = []

        # 按task_type分析
        by_type = {}
        for event in self.events:
            if event.task_type not in by_type:
                by_type[event.task_type] = []
            by_type[event.task_type].append(event)

        for tt, events in by_type.items():
            if len(events) < 3:
                continue

            avg_severity = sum(e.near_miss_severity for e in events) / len(events)
            max_severity = max(e.near_miss_severity for e in events)
            critical_count = sum(1 for e in events if e.near_miss_severity > 0.7)

            if avg_severity > 0.4 or critical_count > 2:
                signals.append({
                    "type": "task_type_risk",
                    "task_type": tt,
                    "avg_severity": avg_severity,
                    "max_severity": max_severity,
                    "critical_count": critical_count,
                    "message": f"{tt} task_type has elevated near-miss risk (avg={avg_severity:.2f})"
                })

        # 按agent分析
        by_agent = {}
        for event in self.events:
            if event.agent_id not in by_agent:
                by_agent[event.agent_id] = []
            by_agent[event.agent_id].append(event)

        for agent_id, events in by_agent.items():
            if len(events) >= 5:
                avg_severity = sum(e.near_miss_severity for e in events) / len(events)
                if avg_severity > 0.5:
                    signals.append({
                        "type": "agent_risk",
                        "agent_id": agent_id,
                        "avg_severity": avg_severity,
                        "count": len(events),
                        "message": f"{agent_id} has high near-miss severity ({avg_severity:.2f})"
                    })

        return signals

    def calculate_hidden_risk_score(self, task_type: str, base_utility: float) -> Tuple[float, Dict]:
        """
        计算隐藏风险评分。

        用于调整utility预测：
        - near-miss率高 → 系统在冒险但没失败
        - 应该降低utility预测
        """
        type_events = [e for e in self.events if e.task_type == task_type]

        if not type_events:
            return base_utility, {"risk_data": "insufficient"}

        near_miss_rate = len([e for e in type_events if e.near_miss_severity > 0.3]) / len(type_events)
        avg_severity = sum(e.near_miss_severity for e in type_events) / len(type_events)

        # 隐藏风险因子
        hidden_risk_factor = near_miss_rate * avg_severity * 2  # 放大因子

        # 风险调整：utility降低
        risk_adjustment = hidden_risk_factor * 0.3  # 最多降低30%
        adjusted_utility = max(0.0, base_utility - risk_adjustment)

        return adjusted_utility, {
            "near_miss_rate": near_miss_rate,
            "avg_severity": avg_severity,
            "hidden_risk_factor": hidden_risk_factor,
            "risk_adjustment": risk_adjustment,
            "sample_count": len(type_events)
        }

    def save(self, date: str = None):
        """保存到文件"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        path = f"{self.storage_path}/nearmiss_{date}.json"
        data = {
            "date": date,
            "events": [asdict(e) for e in self.events],
            "near_miss_rate": self.get_near_miss_rate(),
            "severity_distribution": self.get_severity_distribution(),
            "risk_signals": self.get_risk_signals()
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

        return path


if __name__ == "__main__":
    print("=" * 60)
    print("NEAR-MISS EVENT TRACKER - Reality Alignment")
    print("=" * 60)

    tracker = NearMissTracker()

    # 模拟near-miss事件
    print("\n[1] Recording sample near-miss events...")

    near_misses = [
        ("deploy_001", "deploy", NearMissType.ROLLBACK_NEAR_MISS,
         "差点触发rollback", 0.9, 1.0, "planner", "approved", 5, True, 0.1),

        ("deploy_002", "deploy", NearMissType.TIMEOUT_NEAR_MISS,
         "差点超时", 0.7, 30.0, "deployer", "approved", 3, True, 0.2),

        ("build_001", "build", NearMissType.DEPENDENCY_FAILURE_NEAR_MISS,
         "差点依赖失败", 0.6, 1.0, "coder", "approved", 4, True, 0.3),

        ("fix_001", "fix", NearMissType.RESOURCE_NEAR_MISS,
         "差点内存耗尽", 0.8, 0.95, "coder", "conditional", 2, True, 0.15),

        ("deploy_003", "deploy", NearMissType.CONCURRENCY_NEAR_MISS,
         "差点并发冲突", 0.95, 1.0, "deployer", "approved", 6, True, 0.05),
    ]

    for args in near_misses:
        event_id = tracker.record(*args)
        print(f"  Recorded: {event_id}")

    print("\n[2] Near-Miss Rate by Task Type:")
    rate = tracker.get_near_miss_rate()
    for tt, r in rate.items():
        print(f"  {tt}: {r:.1%}")

    print("\n[3] Severity Distribution:")
    for sev, count in tracker.get_severity_distribution().items():
        print(f"  {sev}: {count}")

    print("\n[4] Risk Signals:")
    signals = tracker.get_risk_signals()
    if signals:
        for s in signals:
            print(f"  ! {s['message']}")
    else:
        print("  No critical signals")

    print("\n[5] Hidden Risk Score for DEPLOY:")
    adj_utility, details = tracker.calculate_hidden_risk_score("deploy", 0.8)
    print(f"  Base utility: 0.80")
    print(f"  Hidden risk adjusted: {adj_utility:.3f}")
    print(f"  Details: {details}")

    print("\n[6] Saving...")
    path = tracker.save()
    print(f"  Saved to: {path}")

    print("\n" + "=" * 60)
    print("KEY INSIGHT:")
    print("  Near-miss = 隐藏的风险")
    print("  没失败 ≠ 没风险")
    print("  → near-miss多的task_typeutility被高估")
    print("  → 这是校准risk-adjusted utility的关键数据")
    print("=" * 60)