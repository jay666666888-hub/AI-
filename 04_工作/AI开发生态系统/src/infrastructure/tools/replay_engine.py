#!/usr/bin/env python3
"""
Replay Engine - 因果重放系统
支持：单点重放、轨迹重建、因果链分析
"""

import sys
import json
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


@dataclass
class ReplayStep:
    """重放步骤"""
    t: int  # 时间步
    action_id: str
    timestamp: str
    event_type: str
    description: str
    data: Dict[str, Any]


@dataclass
class ReplayResult:
    """重放结果"""
    action_id: str
    steps: List[ReplayStep]
    duration_ms: float
    success: bool
    summary: str


@dataclass
class CausalityChain:
    """因果链"""
    causes: List[str]
    effects: List[str]
    chain: List[Tuple[str, str]]  # (cause, effect)
    confidence: float


class ReplayEngine:
    """
    Replay Engine - 因果重放系统
    
    能力：
    A. 单点重放 - replay(action_id="build_001")
    B. 轨迹重建 - replay_timeline(from="10:00", to="10:10")
    C. 因果链分析 - policy_drift → governance_degrade → execution_fallback
    """

    def __init__(self, timeline_store=None):
        self.timeline_store = timeline_store
        self.events: List[Dict] = []
        self._event_index: Dict[str, Dict] = {}

    def load_events(self, events: List[Dict]):
        """加载事件"""
        self.events = sorted(events, key=lambda x: x.get('timestamp', ''))
        self._event_index = {e.get('action_id'): e for e in self.events}

    def load_from_file(self, filepath: str):
        """从文件加载事件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            events = json.load(f)
        self.load_events(events)

    def replay(self, action_id: str) -> ReplayResult:
        """
        A. 单点重放
        
        replay(action_id="build_001")
        输出：
        t0 → routing: CREATE
        t1 → selected agent: python-coder
        t2 → utility evaluated: 0.85
        t3 → runtime governor: ALLOW
        t4 → execution path: full
        """
        steps = []
        step_t = 0

        # 找到目标事件
        target = self._event_index.get(action_id)
        if not target:
            return ReplayResult(
                action_id=action_id,
                steps=[],
                duration_ms=0,
                success=False,
                summary=f"Action {action_id} not found"
            )

        # 收集相关事件（同一个 action_id 的所有事件）
        related_events = [e for e in self.events if e.get('action_id') == action_id]

        # 构建重放步骤
        for event in related_events:
            step = ReplayStep(
                t=step_t,
                action_id=event.get('action_id'),
                timestamp=event.get('timestamp'),
                event_type=event.get('event_type'),
                description=self._describe_event(event),
                data=event
            )
            steps.append(step)
            step_t += 1

        # 计算时间范围
        first_ts = related_events[0].get('timestamp', '') if related_events else ''
        last_ts = related_events[-1].get('timestamp', '') if related_events else ''

        try:
            if first_ts and last_ts:
                dt = datetime.fromisoformat(last_ts) - datetime.fromisoformat(first_ts)
                duration_ms = dt.total_seconds() * 1000
            else:
                duration_ms = 0
        except:
            duration_ms = 0

        return ReplayResult(
            action_id=action_id,
            steps=steps,
            duration_ms=duration_ms,
            success=True,
            summary=f"Replayed {len(steps)} steps"
        )

    def _describe_event(self, event: Dict) -> str:
        """描述事件"""
        etype = event.get('event_type', '')
        agent = event.get('agent_id', '')
        option = event.get('selected_option', '')
        utility = event.get('utility_score')
        governance = event.get('governance_decision', '')
        runtime = event.get('runtime_decision', '')

        if etype == 'routing':
            return f"routing: {option or agent or 'unknown'}"
        elif etype == 'utility_eval':
            return f"utility evaluated: {utility}" if utility else "utility evaluated"
        elif etype == 'governance_decision':
            return f"governance: {governance or runtime or 'unknown'}"
        elif etype == 'execution_end':
            path = event.get('execution_path', [])
            return f"execution path: {' -> '.join(path)}"
        else:
            return etype

    def replay_timeline(self, start: str = None, end: str = None) -> List[ReplayStep]:
        """
        B. 轨迹重建
        
        replay_timeline(from="10:00", to="10:10")
        输出：
        - routing drift
        - utility shifts
        - governance decisions
        - failure points
        """
        steps = []
        step_t = 0

        # 过滤时间范围
        filtered = self.events
        if start:
            filtered = [e for e in filtered if e.get('timestamp', '') >= start]
        if end:
            filtered = [e for e in filtered if e.get('timestamp', '') <= end]

        # 构建步骤
        for event in filtered:
            step = ReplayStep(
                t=step_t,
                action_id=event.get('action_id'),
                timestamp=event.get('timestamp'),
                event_type=event.get('event_type'),
                description=self._describe_event(event),
                data=event
            )
            steps.append(step)
            step_t += 1

        return steps

    def analyze_causality(self) -> CausalityChain:
        """
        C. 因果链分析
        
        policy_drift → governance_degrade → execution_fallback
        """
        # 构建事件序列
        event_sequence = [(e.get('event_type'), e.get('action_id')) for e in self.events]

        # 简化的因果分析：查找模式
        causes = []
        effects = []
        chain = []

        # 查找 policy_update → governance_decision → execution_end 模式
        for i in range(len(self.events) - 2):
            e1 = self.events[i]
            e2 = self.events[i + 1]
            e3 = self.events[i + 2]

            if e1.get('event_type') == 'policy_update' and \
               e2.get('event_type') == 'governance_decision':
                causes.append(f"policy_drift at {e1.get('action_id')}")
                effects.append(f"governance change at {e2.get('action_id')}")
                chain.append((f"policy_update:{e1.get('action_id')}", 
                             f"governance:{e2.get('action_id')}"))

            if e2.get('event_type') == 'governance_decision' and \
               e3.get('event_type') == 'execution_end':
                causes.append(f"governance_degrade at {e2.get('action_id')}")
                effects.append(f"execution_fallback at {e3.get('action_id')}")
                chain.append((f"governance:{e2.get('action_id')}",
                             f"execution:{e3.get('action_id')}"))

        # 计算置信度（基于模式匹配次数）
        confidence = min(1.0, len(chain) * 0.2)

        return CausalityChain(
            causes=list(set(causes)),
            effects=list(set(effects)),
            chain=chain[:10],  # 只返回前10个
            confidence=confidence
        )

    def find_pattern(self, pattern: List[str]) -> List[List[Dict]]:
        """
        查找事件模式
        
        pattern = ['routing', 'utility_eval', 'governance_decision']
        返回匹配的所有序列
        """
        if len(pattern) < 2:
            return []

        matches = []
        i = 0

        while i <= len(self.events) - len(pattern):
            sequence = self.events[i:i+len(pattern)]
            types = [e.get('event_type') for e in sequence]

            if types == pattern:
                matches.append(sequence)
                i += 1
            else:
                i += 1

        return matches

    def get_routing_drift(self) -> Dict[str, Any]:
        """
        分析 routing drift
        """
        routing_events = [e for e in self.events if e.get('event_type') == 'routing']

        if not routing_events:
            return {"drift_detected": False}

        # 分析 agent 选择的变化
        agent_sequence = [e.get('agent_id') for e in routing_events]

        # 计算 unique agents 比例
        unique_agents = len(set(agent_sequence))
        total_routing = len(agent_sequence)

        # 检测是否有主导 agent
        from collections import Counter
        agent_counts = Counter(agent_sequence)
        dominant_ratio = agent_counts.most_common(1)[0][1] / total_routing if total_routing > 0 else 0

        # 检测 agent 切换频率
        switches = sum(1 for i in range(1, len(agent_sequence)) 
                      if agent_sequence[i] != agent_sequence[i-1])
        switch_rate = switches / (total_routing - 1) if total_routing > 1 else 0

        return {
            "drift_detected": unique_agents > 3 and switch_rate > 0.3,
            "unique_agents": unique_agents,
            "dominant_agent": agent_counts.most_common(1)[0][0] if agent_counts else None,
            "dominant_ratio": dominant_ratio,
            "switch_rate": switch_rate,
            "total_routing": total_routing
        }

    def get_utility_shifts(self) -> Dict[str, Any]:
        """
        分析 utility shifts
        """
        utility_events = [e for e in self.events if e.get('event_type') == 'utility_eval']

        if not utility_events:
            return {"shifts_detected": False}

        scores = [e.get('utility_score') for e in utility_events if e.get('utility_score') is not None]

        if not scores:
            return {"shifts_detected": False}

        # 计算分数变化
        score_changes = [scores[i] - scores[i-1] for i in range(1, len(scores))]

        # 计算平均变化
        avg_change = sum(score_changes) / len(score_changes) if score_changes else 0
        max_change = max(abs(c) for c in score_changes) if score_changes else 0

        # 检测 drift（持续下降或上升）
        is_drift = avg_change < -0.01 or avg_change > 0.01

        return {
            "shifts_detected": abs(avg_change) > 0.05,
            "avg_change": avg_change,
            "max_change": max_change,
            "min_score": min(scores) if scores else None,
            "max_score": max(scores) if scores else None,
            "score_variance": (sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)) if scores and len(scores) > 1 else 0
        }

    def print_replay(self, result: ReplayResult):
        """打印重放结果"""
        print(f"\n{'='*60}")
        print(f"REPLAY: {result.action_id}")
        print(f"{'='*60}")
        print(f"Duration: {result.duration_ms:.2f}ms")
        print(f"Steps: {len(result.steps)}")
        print(f"Success: {result.success}")
        print()

        for step in result.steps:
            print(f"  t{step.t} [{step.event_type}] {step.timestamp[11:19]}")
            print(f"      {step.description}")
            if step.data:
                for k, v in step.data.items():
                    if k not in ('action_id', 'timestamp', 'event_type') and v:
                        print(f"      {k}: {v}")
            print()

    def print_timeline(self, steps: List[ReplayStep]):
        """打印时间线"""
        print(f"\n{'='*60}")
        print(f"TIMELINE: {len(steps)} events")
        print(f"{'='*60}")

        for step in steps:
            print(f"  t{step.t} {step.timestamp[11:19]} [{step.event_type}]")
            print(f"      {step.description}")

    def print_causality(self, chain: CausalityChain):
        """打印因果链"""
        print(f"\n{'='*60}")
        print(f"CAUSALITY CHAIN (confidence: {chain.confidence:.2f})")
        print(f"{'='*60}")

        print("\nCauses:")
        for c in chain.causes[:5]:
            print(f"  - {c}")

        print("\nEffects:")
        for e in chain.effects[:5]:
            print(f"  - {e}")

        print("\nChain:")
        for cause, effect in chain.chain[:5]:
            print(f"  {cause} → {effect}")


# Global instance
_engine: Optional[ReplayEngine] = None


def get_replay_engine() -> ReplayEngine:
    global _engine
    if _engine is None:
        _engine = ReplayEngine()
    return _engine


if __name__ == "__main__":
    print("=" * 60)
    print("Replay Engine - Causality Replay System")
    print("=" * 60)

    from execution_logger import get_logger, ExecutionEvent, EventType
    from timeline_store import get_timeline_store

    logger = get_logger()
    store = get_timeline_store()

    # 生成测试事件
    print("\n[1] Generating test events...")

    import random

    for i in range(20):
        action_id = f"build_{i:03d}"

        # Routing
        event = ExecutionEvent(
            action_id=action_id,
            timestamp=datetime.now().isoformat(),
            event_type=EventType.ROUTING.value,
            agent_id=random.choice(['planner', 'coder', 'reviewer', 'tester']),
            task_type="build",
            selected_option=random.choice(['A', 'B', 'C'])
        )
        store.append(event.to_dict())

        # Utility
        event = ExecutionEvent(
            action_id=action_id,
            timestamp=datetime.now().isoformat(),
            event_type=EventType.UTILITY_EVAL.value,
            utility_score=random.uniform(0.5, 0.9)
        )
        store.append(event.to_dict())

        # Governance
        event = ExecutionEvent(
            action_id=action_id,
            timestamp=datetime.now().isoformat(),
            event_type=EventType.GOVERNANCE_DECISION.value,
            governance_decision=random.choice(['ALLOW', 'THROTTLE', 'BLOCK'])
        )
        store.append(event.to_dict())

    print(f"    Generated 60 events (20 action chains)")

    # 加载到 replay engine
    print("\n[2] Loading events into replay engine...")
    engine = get_replay_engine()
    engine.load_from_file("/tmp/telemetry/timeline/2026-05-15/exec_000001.json")

    # 单点重放
    print("\n[3] Single point replay:")
    result = engine.replay("build_000")
    engine.print_replay(result)

    # 轨迹重建
    print("\n[4] Timeline replay:")
    steps = engine.replay_timeline()
    engine.print_timeline(steps[:10])

    # 因果链分析
    print("\n[5] Causality analysis:")
    chain = engine.analyze_causality()
    engine.print_causality(chain)

    # Routing drift
    print("\n[6] Routing drift:")
    drift = engine.get_routing_drift()
    for k, v in drift.items():
        print(f"    {k}: {v}")

    # Utility shifts
    print("\n[7] Utility shifts:")
    shifts = engine.get_utility_shifts()
    for k, v in shifts.items():
        print(f"    {k}: {v}")

    print("\n" + "=" * 60)
    print("Replay Engine ready - causality verification")
    print("=" * 60)
