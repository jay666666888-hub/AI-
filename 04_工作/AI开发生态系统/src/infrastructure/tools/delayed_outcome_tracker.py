#!/usr/bin/env python3
"""
Delayed Outcome Tracker - Phase: Reality Alignment
事后reconciliation：T+1h, T+6h, T+24h

很多deploy：当时成功，6小时后炸

需要：
- 记录初始outcome
- 在T+1h, T+6h, T+24h重新评估
- 更新actual outcome

这会极大提高calibration精度。
"""

import sys
import uuid
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import json
import threading

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


class DelayedCheckpoints(Enum):
    T_PLUS_1H = "t+1h"
    T_PLUS_6H = "t+6h"
    T_PLUS_24H = "t+24h"


@dataclass
class TrackedTask:
    task_id: str
    task_type: str
    timestamp: str
    initial_outcome: float  # 当时的结果
    initial_success: bool

    # Re-evaluation checkpoints
    t1h_outcome: Optional[float] = None
    t6h_outcome: Optional[float] = None
    t24h_outcome: Optional[float] = None

    # Final reconciled outcome
    final_outcome: Optional[float] = None
    outcome_changed: bool = False
    delayed_failure: bool = False  # 初始成功但后来失败


class DelayedOutcomeTracker:
    """
    跟踪延迟结果。

    工作流程：
    1. record_initial() - 记录初始outcome
    2. re-evaluate at T+1h, T+6h, T+24h
    3. get_final_outcome() - 获取最终校准后的outcome
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "/mnt/e/黑曜石/04_工作/AI开发生态系统/telemetry/delayed"
        self.tracked_tasks: Dict[str, TrackedTask] = {}
        self.pending_tasks: Dict[str, Dict[str, Any]] = {}  # 持久化：task_id → 调度信息
        self.checkpoint_handlers: Dict[str, List[Callable]] = {
            DelayedCheckpoints.T_PLUS_1H.value: [],
            DelayedCheckpoints.T_PLUS_6H.value: [],
            DelayedCheckpoints.T_PLUS_24H.value: [],
        }
        self._ensure_storage_dir()
        self._load_pending_tasks()
        self._load_tracked_tasks()
        self._lock = threading.Lock()

    def _ensure_storage_dir(self):
        import os
        os.makedirs(self.storage_path, exist_ok=True)

    def _load_pending_tasks(self):
        """从文件加载待处理的延迟任务"""
        import os
        import json
        pending_file = os.path.join(self.storage_path, "pending_tasks.json")
        if os.path.exists(pending_file):
            try:
                with open(pending_file, 'r') as f:
                    self.pending_tasks = json.load(f)
                # 清理已过期的任务
                now = datetime.now().isoformat()
                self.pending_tasks = {
                    k: v for k, v in self.pending_tasks.items()
                    if v.get("recheck_at", now) > now
                }
            except:
                self.pending_tasks = {}

    def _load_tracked_tasks(self):
        """从文件加载已追踪的任务"""
        import os
        import json
        tracked_file = os.path.join(self.storage_path, "tracked_tasks.json")
        if os.path.exists(tracked_file):
            try:
                with open(tracked_file, 'r') as f:
                    data = json.load(f)
                    for task_id, task_data in data.items():
                        self.tracked_tasks[task_id] = TrackedTask(**task_data)
            except:
                self.tracked_tasks = {}

    def _save_pending_tasks(self):
        """保存待处理的延迟任务到文件"""
        import os
        import json
        pending_file = os.path.join(self.storage_path, "pending_tasks.json")
        with open(pending_file, 'w') as f:
            json.dump(self.pending_tasks, f, indent=2)

    def _save_tracked_tasks(self):
        """保存已追踪的任务到文件"""
        import os
        import json
        tracked_file = os.path.join(self.storage_path, "tracked_tasks.json")
        with open(tracked_file, 'w') as f:
            json.dump({k: asdict(v) for k, v in self.tracked_tasks.items()}, f, indent=2)

    def register_checkpoint_handler(self, checkpoint: DelayedCheckpoints, handler: Callable):
        """注册checkpoint回调handler"""
        self.checkpoint_handlers[checkpoint.value].append(handler)

    def track(
        self,
        task_id: str,
        task_type: str,
        initial_outcome: float,
        initial_success: bool
    ) -> str:
        """开始追踪一个任务，同时调度延迟检查点"""
        with self._lock:
            tracked = TrackedTask(
                task_id=task_id,
                task_type=task_type,
                timestamp=datetime.now().isoformat(),
                initial_outcome=initial_outcome,
                initial_success=initial_success
            )
            self.tracked_tasks[task_id] = tracked

            # 调度持久化的延迟检查点
            checkpoints = [
                (DelayedCheckpoints.T_PLUS_1H, 1),
                (DelayedCheckpoints.T_PLUS_6H, 6),
                (DelayedCheckpoints.T_PLUS_24H, 24),
            ]
            for checkpoint, hours in checkpoints:
                recheck_at = (datetime.now() + timedelta(hours=hours)).isoformat()
                self.pending_tasks[f"{task_id}_{checkpoint.value}"] = {
                    "task_id": task_id,
                    "checkpoint": checkpoint.value,
                    "recheck_at": recheck_at,
                    "scheduled_at": datetime.now().isoformat()
                }

            self._save_pending_tasks()
            self._save_tracked_tasks()

        return task_id

    def update(self, task_id: str, checkpoint: DelayedCheckpoints, outcome: float) -> bool:
        """
        更新某个checkpoint的outcome。

        Returns: outcome是否改变了
        """
        with self._lock:
            if task_id not in self.tracked_tasks:
                return False

            tracked = self.tracked_tasks[task_id]
            changed = False

            if checkpoint == DelayedCheckpoints.T_PLUS_1H:
                tracked.t1h_outcome = outcome
                changed = True
            elif checkpoint == DelayedCheckpoints.T_PLUS_6H:
                tracked.t6h_outcome = outcome
                changed = True
            elif checkpoint == DelayedCheckpoints.T_PLUS_24H:
                tracked.t24h_outcome = outcome
                changed = True

            # 计算最终outcome（取最后一个可用的）
            if tracked.t24h_outcome is not None:
                tracked.final_outcome = tracked.t24h_outcome
            elif tracked.t6h_outcome is not None:
                tracked.final_outcome = tracked.t6h_outcome
            elif tracked.t1h_outcome is not None:
                tracked.final_outcome = tracked.t1h_outcome
            else:
                tracked.final_outcome = tracked.initial_outcome

            # 检查是否从成功变成失败（延迟失败）
            if tracked.initial_success and tracked.final_outcome is not None:
                tracked.delayed_failure = tracked.final_outcome < 0.5

            tracked.outcome_changed = (
                tracked.final_outcome is not None and
                abs(tracked.final_outcome - tracked.initial_outcome) > 0.1
            )

            self._save_tracked_tasks()
            return changed

    def get_final_outcome(self, task_id: str) -> Optional[float]:
        """获取某个任务的最终（延迟）outcome"""
        if task_id not in self.tracked_tasks:
            return None
        return self.tracked_tasks[task_id].final_outcome

    def get_delayed_failure_rate(self) -> Dict[str, float]:
        """获取各task_type的延迟失败率"""
        by_type = {}
        for task_id, tracked in self.tracked_tasks.items():
            if tracked.task_type not in by_type:
                by_type[tracked.task_type] = {"total": 0, "delayed_failures": 0}

            by_type[tracked.task_type]["total"] += 1
            if tracked.delayed_failure:
                by_type[tracked.task_type]["delayed_failures"] += 1

        return {
            tt: data["delayed_failures"] / data["total"] if data["total"] > 0 else 0.0
            for tt, data in by_type.items()
        }

    def get_outcome_change_rate(self) -> Dict[str, float]:
        """获取各task_type的outcome改变率"""
        by_type = {}
        for task_id, tracked in self.tracked_tasks.items():
            if tracked.task_type not in by_type:
                by_type[tracked.task_type] = {"total": 0, "changed": 0}

            by_type[tracked.task_type]["total"] += 1
            if tracked.outcome_changed:
                by_type[tracked.task_type]["changed"] += 1

        return {
            tt: data["changed"] / data["total"] if data["total"] > 0 else 0.0
            for tt, data in by_type.items()
        }

    def get_summary(self) -> Dict[str, Any]:
        """获取追踪摘要"""
        total = len(self.tracked_tasks)
        if total == 0:
            return {"total": 0}

        tracked_list = list(self.tracked_tasks.values())
        with_final = sum(1 for t in tracked_list if t.final_outcome is not None)
        outcome_changed = sum(1 for t in tracked_list if t.outcome_changed)
        delayed_failures = sum(1 for t in tracked_list if t.delayed_failure)

        return {
            "total_tracked": total,
            "with_final_outcome": with_final,
            "outcome_changed": outcome_changed,
            "outcome_change_rate": outcome_changed / total,
            "delayed_failures": delayed_failures,
            "delayed_failure_rate": delayed_failures / total,
            "pending_checks": len(self.pending_tasks),
            "by_task_type": {
                "delayed_failure_rate": self.get_delayed_failure_rate(),
                "outcome_change_rate": self.get_outcome_change_rate()
            }
        }

    def process_due_checks(self, outcome_evaluator: Callable[[str], float] = None) -> List[Dict]:
        """
        处理所有到期的延迟检查点

        Args:
            outcome_evaluator: 可选，评估任务真实结果的回调函数
                             如果不提供，使用模拟结果
        Returns:
            处理结果列表
        """
        import os
        results = []
        now = datetime.now()
        now_iso = now.isoformat()
        still_pending = {}

        for key, task_info in self.pending_tasks.items():
            recheck_at = task_info.get("recheck_at", now_iso)
            if recheck_at <= now_iso:
                task_id = task_info["task_id"]
                checkpoint_str = task_info["checkpoint"]
                checkpoint = DelayedCheckpoints(checkpoint_str)

                # 评估真实结果
                if outcome_evaluator:
                    outcome = outcome_evaluator(task_id)
                else:
                    outcome = self._simulate_outcome_check(task_id)

                updated = self.update(task_id, checkpoint, outcome)
                results.append({
                    "task_id": task_id,
                    "checkpoint": checkpoint_str,
                    "outcome": outcome,
                    "updated": updated,
                    "processed_at": now_iso
                })
            else:
                still_pending[key] = task_info

        self.pending_tasks = still_pending
        self._save_pending_tasks()
        return results

    def generate_cron_script(self) -> str:
        """
        生成 cron 脚本用于定期处理延迟检查点

        在 crontab 中添加:
        */5 * * * * /path/to/process_delayed_outcomes.sh
        """
        return '''#!/bin/bash
# Delayed Outcome Tracker 处理脚本
# 每5分钟执行一次，处理到期的延迟检查点

cd /mnt/e/黑曜石/04_工作/AI开发生态系统
source venv/bin/activate
python -c "
import sys
sys.path.insert(0, 'src')
from infrastructure.tools.delayed_outcome_tracker import DelayedOutcomeTracker

tracker = DelayedOutcomeTracker()
results = tracker.process_due_checks()

if results:
    print(f'Processed {len(results)} delayed checks')
    for r in results:
        print(f\"  {r['task_id']}: {r['checkpoint']} → {r['outcome']}\")
"
'''

    def save(self, date: str = None):
        """保存到文件"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        path = f"{self.storage_path}/delayed_{date}.json"
        data = {
            "date": date,
            "summary": self.get_summary(),
            "tracked_tasks": {k: asdict(v) for k, v in self.tracked_tasks.items()}
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

        return path


# ==============================================================================
# Simple Reconciliation Scheduler (for demo)
# ==============================================================================

class ReconciliationScheduler:
    """
    简单的reconciliation调度器。

    在真实系统中会使用定时任务（如Celery、Airflow）。
    这里只是一个模拟实现。
    """

    def __init__(self, tracker: DelayedOutcomeTracker):
        self.tracker = tracker
        self.pending_tasks: List[Tuple[str, datetime, DelayedCheckpoints]] = []

    def schedule_recheck(self, task_id: str, delay_hours: int, checkpoint: DelayedCheckpoints):
        """调度一次recheck"""
        recheck_time = datetime.now() + timedelta(hours=delay_hours)
        self.pending_tasks.append((task_id, recheck_time, checkpoint))

    def process_due_checks(self) -> List[Tuple[str, bool]]:
        """
        处理到期的checks。

        Returns: [(task_id, was_updated), ...]
        """
        results = []
        now = datetime.now()
        still_pending = []

        for task_id, due_time, checkpoint in self.pending_tasks:
            if now >= due_time:
                # 模拟outcome（实际应该调用监控系统）
                outcome = self._simulate_outcome_check(task_id)
                updated = self.tracker.update(task_id, checkpoint, outcome)
                results.append((task_id, updated))
            else:
                still_pending.append((task_id, due_time, checkpoint))

        self.pending_tasks = still_pending
        return results

    def _simulate_outcome_check(self, task_id: str) -> float:
        """模拟outcome检查（实际应该查询监控/健康检查）"""
        import random
        # 模拟：10%的机会发现延迟失败
        if random.random() < 0.1:
            return 0.3  # 延迟失败
        return 0.8  # 正常


if __name__ == "__main__":
    print("=" * 60)
    print("DELAYED OUTCOME TRACKER - Reality Alignment")
    print("=" * 60)

    tracker = DelayedOutcomeTracker()

    # 模拟追踪
    print("\n[1] Recording initial outcomes...")

    tasks = [
        ("task_001", "deploy", 0.8, True),
        ("task_002", "deploy", 0.85, True),
        ("task_003", "build", 0.75, True),
        ("task_004", "research", 0.9, True),
    ]

    for task_id, task_type, outcome, success in tasks:
        tracker.track(task_id, task_type, outcome, success)
        print(f"  Tracked: {task_id}")

    # 模拟延迟更新
    print("\n[2] Simulating delayed outcomes...")

    # 模拟task_001在T+6h变成失败
    tracker.update("task_001", DelayedCheckpoints.T_PLUS_6H, 0.3)
    tracker.update("task_002", DelayedCheckpoints.T_PLUS_1H, 0.85)
    tracker.update("task_003", DelayedCheckpoints.T_PLUS_24H, 0.75)

    print("\n[3] Summary:")
    summary = tracker.get_summary()
    print(f"  Total tracked: {summary['total_tracked']}")
    print(f"  Outcome changed: {summary['outcome_changed']} ({summary['outcome_change_rate']:.1%})")
    print(f"  Delayed failures: {summary['delayed_failures']} ({summary['delayed_failure_rate']:.1%})")

    print("\n[4] Per-task-type rates:")
    print(f"  Delayed failure rate: {summary['by_task_type']['delayed_failure_rate']}")
    print(f"  Outcome change rate: {summary['by_task_type']['outcome_change_rate']}")

    print("\n[5] Final outcomes:")
    for task_id in ["task_001", "task_002", "task_003", "task_004"]:
        tracked = tracker.tracked_tasks[task_id]
        print(f"  {task_id}: initial={tracked.initial_outcome:.2f} -> final={tracked.final_outcome:.2f} "
              f"(changed={tracked.outcome_changed}, delayed_failure={tracked.delayed_failure})")

    print("\n[6] Saving...")
    path = tracker.save()
    print(f"  Saved to: {path}")

    print("\n" + "=" * 60)
    print("KEY INSIGHT:")
    print("  Deploy任务：初始看起来成功，6小时后可能炸")
    print("  → 需要T+6h重新评估actual outcome")
    print("  → 这会大幅提高deploy的ECE校准精度")
    print("=" * 60)