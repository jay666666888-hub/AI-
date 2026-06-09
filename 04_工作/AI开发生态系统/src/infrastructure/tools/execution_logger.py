#!/usr/bin/env python3
"""
Execution Logger - Immutable Event Stream Recorder
事实采集层：只记录"发生过的东西"，不允许加工/总结
"""

import sys
import json
import uuid
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


class EventType(Enum):
    ROUTING = "routing"
    UTILITY_EVAL = "utility_eval"
    GOVERNANCE_DECISION = "governance_decision"
    RUNTIME_DECISION = "runtime_decision"
    EXECUTION_START = "execution_start"
    EXECUTION_END = "execution_end"
    POLICY_UPDATE = "policy_update"
    GOAL_GENERATION = "goal_generation"
    REFLECTION = "reflection"
    HEARTBEAT = "heartbeat"


@dataclass
class ExecutionEvent:
    """
    不可变事件记录
    只记录事实，不加工
    """
    action_id: str  # 唯一标识
    timestamp: str  # ISO格式
    event_type: str  # EventType.value

    # 上下文
    agent_id: Optional[str] = None
    task_type: Optional[str] = None
    task_id: Optional[str] = None

    # 输入
    input_context: Dict[str, Any] = field(default_factory=dict)

    # 决策
    selected_option: Optional[str] = None
    decision_confidence: Optional[float] = None

    # Utility
    utility_input: Dict[str, Any] = field(default_factory=dict)
    utility_output: Optional[float] = None
    utility_score: Optional[float] = None

    # Governance
    governance_decision: Optional[str] = None
    runtime_decision: Optional[str] = None

    # 执行路径
    execution_path: List[str] = field(default_factory=list)

    # 元数据（不解释，只记录）
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ExecutionLogger:
    """
    Execution Logger - 不可变事件流记录器
    
    核心原则：
    ❌ 不允许加工
    ❌ 不允许总结  
    ✅ 只记录发生过的东西
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "/tmp/telemetry"
        self.events: List[ExecutionEvent] = []
        self._event_index: Dict[str, ExecutionEvent] = {}

    def log(self, event: ExecutionEvent) -> str:
        """
        记录事件，返回 action_id
        """
        if not event.action_id:
            event.action_id = str(uuid.uuid4())[:12]

        if not event.timestamp:
            event.timestamp = datetime.now().isoformat()

        # 存储到内存
        self.events.append(event)
        self._event_index[event.action_id] = event

        return event.action_id

    def log_routing(self, task_id: str, agent_id: str, 
                    routing_reason: str, selected_option: str,
                    metadata: Dict = None) -> str:
        """记录 routing 事件"""
        event = ExecutionEvent(
            action_id=str(uuid.uuid4())[:12],
            timestamp=datetime.now().isoformat(),
            event_type=EventType.ROUTING.value,
            agent_id=agent_id,
            task_type="routing",
            task_id=task_id,
            selected_option=selected_option,
            input_context={"routing_reason": routing_reason},
            metadata=metadata or {}
        )
        return self.log(event)

    def log_utility_eval(self, action_id: str,
                        utility_input: Dict, utility_output: float,
                        selected_option: str, score: float,
                        metadata: Dict = None) -> str:
        """记录 utility 评估事件"""
        event = ExecutionEvent(
            action_id=action_id,
            timestamp=datetime.now().isoformat(),
            event_type=EventType.UTILITY_EVAL.value,
            utility_input=utility_input,
            utility_output=utility_output,
            selected_option=selected_option,
            utility_score=score,
            metadata=metadata or {}
        )
        return self.log(event)

    def log_governance(self, action_id: str,
                       decision: str, context: Dict,
                       runtime_decision: str = None,
                       metadata: Dict = None) -> str:
        """记录 governance 决策事件"""
        event = ExecutionEvent(
            action_id=action_id,
            timestamp=datetime.now().isoformat(),
            event_type=EventType.GOVERNANCE_DECISION.value,
            governance_decision=decision,
            input_context=context,
            runtime_decision=runtime_decision,
            metadata=metadata or {}
        )
        return self.log(event)

    def log_execution(self, action_id: str, path: List[str],
                      outcome: str = None, metadata: Dict = None) -> str:
        """记录 execution 事件"""
        event = ExecutionEvent(
            action_id=action_id,
            timestamp=datetime.now().isoformat(),
            event_type=EventType.EXECUTION_END.value,
            execution_path=path,
            input_context={"outcome": outcome} if outcome else {},
            metadata=metadata or {}
        )
        return self.log(event)

    def get_event(self, action_id: str) -> Optional[ExecutionEvent]:
        """获取单个事件"""
        return self._event_index.get(action_id)

    def get_events_by_type(self, event_type: str) -> List[ExecutionEvent]:
        """获取特定类型的所有事件"""
        return [e for e in self.events if e.event_type == event_type]

    def get_events_by_agent(self, agent_id: str) -> List[ExecutionEvent]:
        """获取特定 agent 的所有事件"""
        return [e for e in self.events if e.agent_id == agent_id]

    def get_events_in_range(self, start: datetime, end: datetime) -> List[ExecutionEvent]:
        """获取时间范围内的事件"""
        return [e for e in self.events 
                if start.isoformat() <= e.timestamp <= end.isoformat()]

    def get_all_events(self) -> List[ExecutionEvent]:
        """获取所有事件"""
        return self.events

    def export_to_file(self, filepath: str) -> None:
        """导出事件到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([e.to_dict() for e in self.events], f, ensure_ascii=False, indent=2)

    def import_from_file(self, filepath: str) -> int:
        """从文件导入事件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for d in data:
            event = ExecutionEvent(**d)
            self.events.append(event)
            self._event_index[event.action_id] = event
            count += 1
        
        return count

    def get_timeline(self) -> List[Tuple[str, str, str]]:
        """
        返回时间线：[(action_id, timestamp, event_type), ...]
        """
        return sorted([(e.action_id, e.timestamp, e.event_type) 
                      for e in self.events], key=lambda x: x[1])

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        by_type = {}
        for e in self.events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1

        return {
            "total_events": len(self.events),
            "by_type": by_type,
            "first_event": self.events[0].timestamp if self.events else None,
            "last_event": self.events[-1].timestamp if self.events else None,
        }


# Global instance
_logger: Optional[ExecutionLogger] = None


def get_logger() -> ExecutionLogger:
    global _logger
    if _logger is None:
        _logger = ExecutionLogger()
    return _logger


if __name__ == "__main__":
    print("=" * 60)
    print("Execution Logger - Telemetry System")
    print("=" * 60)

    logger = get_logger()

    # 模拟记录事件
    print("\n[1] Logging test events...")

    action_id = logger.log_routing(
        task_id="task_001",
        agent_id="planner",
        routing_reason="complex task requires planning",
        selected_option="planner",
        metadata={"task_complexity": "high"}
    )
    print(f"    Logged routing event: {action_id}")

    logger.log_utility_eval(
        action_id=action_id,
        utility_input={"cost": 0.3, "speed": 0.8, "quality": 0.9},
        utility_output=0.72,
        selected_option="option_a",
        score=0.72,
        metadata={}
    )

    logger.log_governance(
        action_id=action_id,
        decision="ALLOW",
        context={"risk_level": "low"},
        runtime_decision="PROCEED"
    )

    logger.log_execution(
        action_id=action_id,
        path=["planner", "coder", "reviewer"],
        outcome="SUCCESS"
    )

    # 统计
    print("\n[2] Logger statistics:")
    stats = logger.get_stats()
    for k, v in stats.items():
        print(f"    {k}: {v}")

    # 时间线
    print("\n[3] Event timeline:")
    for action_id, ts, etype in logger.get_timeline():
        print(f"    {ts} [{etype}] {action_id}")

    print("\n" + "=" * 60)
    print("Execution Logger ready - append-only event stream")
    print("=" * 60)
