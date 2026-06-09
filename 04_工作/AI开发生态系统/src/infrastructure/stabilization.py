#!/usr/bin/env python3
"""
Stabilization Phase - P2 稳定性验证
P2 Stabilization = "可以变聪明，但不能再随意变结构"

包含:
1. System Freeze Test - 长时间运行观测
2. Drift Monitor - 漂移监控
3. Failure Mode Map - 失败模式记录
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time
import threading


class DriftType(Enum):
    POLICY_DRIFT = "policy_drift"
    GOAL_EXPANSION = "goal_expansion"
    DECISION_VARIANCE = "decision_variance"
    RECURSION_DEPTH = "recursion_depth"
    LOOP_DETECTION = "loop_detection"


class SystemHealth(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


@dataclass
class DriftEvent:
    """漂移事件"""
    event_id: str
    drift_type: DriftType
    timestamp: str
    magnitude: float
    threshold: float
    current_value: float
    previous_value: float
    context: Dict[str, Any]


@dataclass
class FreezeTestResult:
    """冻结测试结果"""
    test_id: str
    duration_seconds: int
    start_time: str
    end_time: str
    cycles_executed: int
    goals_proposed: int
    goals_completed: int
    policy_changes: int
    drift_events: List[Dict]
    health_score: float
    passed: bool


@dataclass
class FailureMode:
    """失败模式"""
    mode_id: str
    pattern_type: str  # loop, conflict, oscillation
    trigger_conditions: Dict[str, Any]
    frequency: int
    first_seen: str
    last_seen: str
    severity: str  # low, medium, high, critical
    mitigation: str
    occurrence_history: List[str]


class DriftMonitor:
    """
    Drift Monitor - 漂移监控
    
    监控:
    - policy drift rate
    - goal expansion rate
    - decision variance
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/stabilization/drift"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        # 漂移阈值
        self.thresholds = {
            DriftType.POLICY_DRIFT: 0.15,      # 15% 策略漂移阈值
            DriftType.GOAL_EXPANSION: 2.0,     # 目标膨胀率 (每日)
            DriftType.DECISION_VARIANCE: 0.25,  # 25% 决策方差阈值
            DriftType.RECURSION_DEPTH: 5,       # 最大递归深度
            DriftType.LOOP_DETECTION: 3,        # 3次循环 = 危险
        }
        
        self.drift_events: List[DriftEvent] = []
        self.baseline: Dict[str, Any] = {}
        self._load_baseline()
    
    def _load_baseline(self):
        baseline_file = os.path.join(self.storage_path, "baseline.json")
        if os.path.exists(baseline_file):
            try:
                with open(baseline_file, 'r', encoding='utf-8') as f:
                    self.baseline = json.load(f)
            except:
                self.baseline = {}
    
    def _save_baseline(self):
        baseline_file = os.path.join(self.storage_path, "baseline.json")
        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(self.baseline, f, ensure_ascii=False, indent=2)
    
    def _save_drift_events(self):
        events_file = os.path.join(self.storage_path, "drift_events.json")
        with open(events_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "event_id": e.event_id,
                "drift_type": e.drift_type.value,
                "timestamp": e.timestamp,
                "magnitude": e.magnitude,
                "threshold": e.threshold,
                "current_value": e.current_value,
                "previous_value": e.previous_value,
                "context": e.context
            } for e in self.drift_events[-100:]], f, ensure_ascii=False, indent=2)
    
    def set_baseline(self, 
                    policy_state: Dict[str, Any],
                    goal_count: int,
                    decision_variance: float,
                    recursion_depth: int):
        """设置基线"""
        self.baseline = {
            "policy_state": policy_state,
            "goal_count": goal_count,
            "decision_variance": decision_variance,
            "recursion_depth": recursion_depth,
            "set_at": datetime.now().isoformat()
        }
        self._save_baseline()
    
    def check_drift(self,
                   current_policy: Dict[str, Any],
                   current_goal_count: int,
                   current_decision_variance: float,
                   current_recursion_depth: int,
                   context: Dict[str, Any] = None) -> List[DriftEvent]:
        """检查漂移"""
        if not self.baseline:
            return []
        
        events = []
        ctx = context or {}
        
        # Policy Drift
        policy_drift = self._calculate_policy_drift(
            self.baseline.get("policy_state", {}),
            current_policy
        )
        
        if abs(policy_drift) > self.thresholds[DriftType.POLICY_DRIFT]:
            event = DriftEvent(
                event_id=str(time.time())[:12],
                drift_type=DriftType.POLICY_DRIFT,
                timestamp=datetime.now().isoformat(),
                magnitude=abs(policy_drift),
                threshold=self.thresholds[DriftType.POLICY_DRIFT],
                current_value=policy_drift,
                previous_value=self.baseline.get("last_policy_drift", 0),
                context=ctx
            )
            events.append(event)
            self.drift_events.append(event)
        
        # Goal Expansion
        baseline_goals = self.baseline.get("goal_count", 0)
        if baseline_goals > 0:
            goal_expansion_rate = (current_goal_count - baseline_goals) / baseline_goals
        else:
            goal_expansion_rate = 0
        
        if goal_expansion_rate > self.thresholds[DriftType.GOAL_EXPANSION]:
            event = DriftEvent(
                event_id=str(time.time())[:12],
                drift_type=DriftType.GOAL_EXPANSION,
                timestamp=datetime.now().isoformat(),
                magnitude=goal_expansion_rate,
                threshold=self.thresholds[DriftType.GOAL_EXPANSION],
                current_value=current_goal_count,
                previous_value=baseline_goals,
                context=ctx
            )
            events.append(event)
            self.drift_events.append(event)
        
        # Decision Variance
        baseline_variance = self.baseline.get("decision_variance", 0)
        variance_change = abs(current_decision_variance - baseline_variance)
        
        if variance_change > self.thresholds[DriftType.DECISION_VARIANCE]:
            event = DriftEvent(
                event_id=str(time.time())[:12],
                drift_type=DriftType.DECISION_VARIANCE,
                timestamp=datetime.now().isoformat(),
                magnitude=variance_change,
                threshold=self.thresholds[DriftType.DECISION_VARIANCE],
                current_value=current_decision_variance,
                previous_value=baseline_variance,
                context=ctx
            )
            events.append(event)
            self.drift_events.append(event)
        
        # Recursion Depth
        if current_recursion_depth > self.thresholds[DriftType.RECURSION_DEPTH]:
            event = DriftEvent(
                event_id=str(time.time())[:12],
                drift_type=DriftType.RECURSION_DEPTH,
                timestamp=datetime.now().isoformat(),
                magnitude=current_recursion_depth,
                threshold=self.thresholds[DriftType.RECURSION_DEPTH],
                current_value=current_recursion_depth,
                previous_value=self.baseline.get("recursion_depth", 0),
                context=ctx
            )
            events.append(event)
            self.drift_events.append(event)
        
        if events:
            self._save_drift_events()
        
        return events
    
    def _calculate_policy_drift(self, baseline: Dict, current: Dict) -> float:
        """计算策略漂移"""
        if not baseline or not current:
            return 0.0
        
        total_diff = 0.0
        total_keys = set(baseline.keys()) | set(current.keys())
        
        if len(total_keys) == 0:
            return 0.0
        
        for key in total_keys:
            base_val = baseline.get(key, 0.5)
            curr_val = current.get(key, 0.5)
            total_diff += abs(curr_val - base_val)
        
        return total_diff / len(total_keys)
    
    def get_drift_summary(self) -> Dict[str, Any]:
        """获取漂移摘要"""
        if not self.drift_events:
            return {
                "total_events": 0,
                "by_type": {},
                "health_status": SystemHealth.HEALTHY.value
            }
        
        by_type = {}
        for drift_type in DriftType:
            type_events = [e for e in self.drift_events if e.drift_type == drift_type]
            if type_events:
                by_type[drift_type.value] = {
                    "count": len(type_events),
                    "avg_magnitude": sum(e.magnitude for e in type_events) / len(type_events),
                    "max_magnitude": max(e.magnitude for e in type_events)
                }
        
        # 健康状态判断
        critical_events = [e for e in self.drift_events 
                         if e.magnitude > e.threshold * 2]
        
        if len(critical_events) >= 3:
            health = SystemHealth.CRITICAL
        elif any(e for e in self.drift_events if e.magnitude > e.threshold):
            health = SystemHealth.WARNING
        else:
            health = SystemHealth.HEALTHY
        
        return {
            "total_events": len(self.drift_events),
            "by_type": by_type,
            "health_status": health.value,
            "baseline_set_at": self.baseline.get("set_at", "not set")
        }


class FailureModeMap:
    """
    Failure Mode Map - 失败模式记录
    
    记录:
    - 哪些结构会循环
    - 哪些 agent 会冲突
    - 哪些 loop 会震荡
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/stabilization/failures"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.failure_modes: Dict[str, FailureMode] = {}
        self.loop_history: List[Dict[str, Any]] = []
        self.conflict_history: List[Dict[str, Any]] = []
        self.oscillation_history: List[Dict[str, Any]] = []
        
        self._load()
    
    def _load(self):
        modes_file = os.path.join(self.storage_path, "failure_modes.json")
        if os.path.exists(modes_file):
            try:
                with open(modes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.failure_modes = {k: FailureMode(**v) for k, v in data.items()}
            except:
                self.failure_modes = {}
        
        loop_file = os.path.join(self.storage_path, "loop_history.json")
        if os.path.exists(loop_file):
            try:
                with open(loop_file, 'r', encoding='utf-8') as f:
                    self.loop_history = json.load(f)
            except:
                self.loop_history = []
        
        conflict_file = os.path.join(self.storage_path, "conflict_history.json")
        if os.path.exists(conflict_file):
            try:
                with open(conflict_file, 'r', encoding='utf-8') as f:
                    self.conflict_history = json.load(f)
            except:
                self.conflict_history = []
        
        osc_file = os.path.join(self.storage_path, "oscillation_history.json")
        if os.path.exists(osc_file):
            try:
                with open(osc_file, 'r', encoding='utf-8') as f:
                    self.oscillation_history = json.load(f)
            except:
                self.oscillation_history = []
    
    def _save(self):
        modes_file = os.path.join(self.storage_path, "failure_modes.json")
        with open(modes_file, 'w', encoding='utf-8') as f:
            json.dump({k: {
                "mode_id": v.mode_id,
                "pattern_type": v.pattern_type,
                "trigger_conditions": v.trigger_conditions,
                "frequency": v.frequency,
                "first_seen": v.first_seen,
                "last_seen": v.last_seen,
                "severity": v.severity,
                "mitigation": v.mitigation,
                "occurrence_history": v.occurrence_history
            } for k, v in self.failure_modes.items()}, f, ensure_ascii=False, indent=2)
        
        loop_file = os.path.join(self.storage_path, "loop_history.json")
        with open(loop_file, 'w', encoding='utf-8') as f:
            json.dump(self.loop_history[-100:], f, ensure_ascii=False, indent=2)
        
        conflict_file = os.path.join(self.storage_path, "conflict_history.json")
        with open(conflict_file, 'w', encoding='utf-8') as f:
            json.dump(self.conflict_history[-100:], f, ensure_ascii=False, indent=2)
        
        osc_file = os.path.join(self.storage_path, "oscillation_history.json")
        with open(osc_file, 'w', encoding='utf-8') as f:
            json.dump(self.oscillation_history[-100:], f, ensure_ascii=False, indent=2)
    
    def record_loop(self,
                   loop_id: str,
                    cycle: List[str],
                   length: int,
                   context: Dict[str, Any]) -> None:
        """记录循环"""
        event = {
            "loop_id": loop_id,
            "cycle": cycle,
            "length": length,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        self.loop_history.append(event)
        
        # 检查是否已知的失败模式
        mode_key = f"loop_{length}"
        if mode_key in self.failure_modes:
            mode = self.failure_modes[mode_key]
            mode.frequency += 1
            mode.last_seen = datetime.now().isoformat()
            mode.occurrence_history.append(datetime.now().isoformat())
        else:
            self.failure_modes[mode_key] = FailureMode(
                mode_id=str(len(self.failure_modes)) + 1,
                pattern_type="loop",
                trigger_conditions={"cycle_length": length},
                frequency=1,
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
                severity="high" if length > 3 else "medium",
                mitigation="添加循环检测 + 强制打断",
                occurrence_history=[datetime.now().isoformat()]
            )
        
        self._save()
    
    def record_conflict(self,
                       agent1: str,
                       agent2: str,
                       conflict_type: str,
                       resolution: str,
                       context: Dict[str, Any]) -> None:
        """记录冲突"""
        event = {
            "agent1": agent1,
            "agent2": agent2,
            "conflict_type": conflict_type,
            "resolution": resolution,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        self.conflict_history.append(event)
        
        mode_key = f"conflict_{agent1}_{agent2}"
        if mode_key in self.failure_modes:
            mode = self.failure_modes[mode_key]
            mode.frequency += 1
            mode.last_seen = datetime.now().isoformat()
        else:
            self.failure_modes[mode_key] = FailureMode(
                mode_id=str(len(self.failure_modes)) + 1,
                pattern_type="conflict",
                trigger_conditions={"agent1": agent1, "agent2": agent2},
                frequency=1,
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
                severity="medium",
                mitigation="添加 agent 协调层",
                occurrence_history=[datetime.now().isoformat()]
            )
        
        self._save()
    
    def record_oscillation(self,
                         pattern: str,
                         amplitude: float,
                         frequency: float,
                         context: Dict[str, Any]) -> None:
        """记录震荡"""
        event = {
            "pattern": pattern,
            "amplitude": amplitude,
            "frequency": frequency,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        self.oscillation_history.append(event)
        
        mode_key = f"oscillation_{pattern}"
        if mode_key in self.failure_modes:
            mode = self.failure_modes[mode_key]
            mode.frequency += 1
            mode.last_seen = datetime.now().isoformat()
        else:
            self.failure_modes[mode_key] = FailureMode(
                mode_id=str(len(self.failure_modes)) + 1,
                pattern_type="oscillation",
                trigger_conditions={"pattern": pattern},
                frequency=1,
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
                severity="critical" if amplitude > 0.5 else "high",
                mitigation="降低学习率 + 添加动量",
                occurrence_history=[datetime.now().isoformat()]
            )
        
        self._save()
    
    def get_failure_summary(self) -> Dict[str, Any]:
        """获取失败模式摘要"""
        return {
            "total_modes": len(self.failure_modes),
            "by_pattern": {
                "loops": len([m for m in self.failure_modes.values() if m.pattern_type == "loop"]),
                "conflicts": len([m for m in self.failure_modes.values() if m.pattern_type == "conflict"]),
                "oscillations": len([m for m in self.failure_modes.values() if m.pattern_type == "oscillation"])
            },
            "critical_modes": [m.mode_id for m in self.failure_modes.values() if m.severity == "critical"],
            "recent_occurrences": {
                "loops": len(self.loop_history[-10:]),
                "conflicts": len(self.conflict_history[-10:]),
                "oscillations": len(self.oscillation_history[-10:])
            }
        }


class SystemFreezeTest:
    """
    System Freeze Test - 系统冻结测试
    
    跑系统:
    - 1天
    - 7天
    - 30天
    
    观察:
    - goal 是否膨胀
    - policy 是否漂移
    - utility 是否稳定
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/stabilization/freeze_tests"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.tests: List[FreezeTestResult] = []
        self._load()
    
    def _load(self):
        tests_file = os.path.join(self.storage_path, "tests.json")
        if os.path.exists(tests_file):
            try:
                with open(tests_file, 'r', encoding='utf-8') as f:
                    self.tests = [FreezeTestResult(**t) for t in json.load(f)]
            except:
                self.tests = []
    
    def _save(self):
        tests_file = os.path.join(self.storage_path, "tests.json")
        with open(tests_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "test_id": t.test_id,
                "duration_seconds": t.duration_seconds,
                "start_time": t.start_time,
                "end_time": t.end_time,
                "cycles_executed": t.cycles_executed,
                "goals_proposed": t.goals_proposed,
                "goals_completed": t.goals_completed,
                "policy_changes": t.policy_changes,
                "drift_events": t.drift_events,
                "health_score": t.health_score,
                "passed": t.passed
            } for t in self.tests], f, ensure_ascii=False, indent=2)
    
    def run_freeze_test(self,
                       duration_hours: int,
                       tick_interval_seconds: int = 60,
                       tick_fn: Callable[[int], Dict[str, Any]] = None) -> FreezeTestResult:
        """
        运行冻结测试
        
        Args:
            duration_hours: 测试时长 (小时)
            tick_interval_seconds: 每次Tick间隔 (秒)
            tick_fn: Tick函数, 接收已运行的秒数, 返回状态
            
        Returns:
            FreezeTestResult
        """
        test_id = f"freeze_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        duration_seconds = duration_hours * 3600
        
        ticks = 0
        cycles_executed = 0
        goals_proposed = 0
        goals_completed = 0
        policy_changes = 0
        drift_events = []
        
        prev_policy = None
        prev_goal_count = None
        
        while ticks < duration_seconds:
            time.sleep(min(tick_interval_seconds, duration_seconds - ticks))
            ticks += tick_interval_seconds
            
            # 获取当前状态
            if tick_fn:
                status = tick_fn(ticks)
                cycles_executed += status.get("cycles", 1)
                goals_proposed += status.get("goals_proposed", 0)
                goals_completed += status.get("goals_completed", 0)
                policy_changes += status.get("policy_changes", 0)
                
                # 检查漂移
                if "policy" in status and "goal_count" in status:
                    drift = self._check_single_drift(
                        prev_policy, status["policy"],
                        prev_goal_count, status["goal_count"]
                    )
                    if drift:
                        drift_events.append(drift)
                    
                    prev_policy = status["policy"]
                    prev_goal_count = status["goal_count"]
        
        end_time = datetime.now()
        
        # 计算健康分数
        health_score = self._calculate_health_score(
            cycles_executed, goals_proposed, goals_completed,
            policy_changes, len(drift_events)
        )
        
        result = FreezeTestResult(
            test_id=test_id,
            duration_seconds=duration_seconds,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            cycles_executed=cycles_executed,
            goals_proposed=goals_proposed,
            goals_completed=goals_completed,
            policy_changes=policy_changes,
            drift_events=drift_events,
            health_score=health_score,
            passed=health_score >= 0.7
        )
        
        self.tests.append(result)
        self._save()
        
        return result
    
    def _check_single_drift(self, prev_policy, current_policy, prev_goals, current_goals) -> Optional[Dict]:
        if prev_policy is None or prev_goals is None:
            return None
        
        policy_drift = sum(abs(current_policy.get(k, 0.5) - prev_policy.get(k, 0.5)) 
                          for k in set(current_policy.keys()) | set(prev_policy.keys()))
        
        goal_expansion = current_goals - prev_goals
        
        if policy_drift > 0.1 or goal_expansion > 2:
            return {
                "timestamp": datetime.now().isoformat(),
                "policy_drift": policy_drift,
                "goal_expansion": goal_expansion
            }
        
        return None
    
    def _calculate_health_score(self,
                               cycles: int,
                               goals_proposed: int,
                               goals_completed: int,
                               policy_changes: int,
                               drift_events: int) -> float:
        """计算健康分数"""
        if cycles == 0:
            return 0.0
        
        # 完成率 (40%)
        completion_rate = goals_completed / max(1, goals_proposed)
        
        # 策略稳定性 (30%) - policy_changes 应该低
        policy_stability = max(0.0, 1.0 - policy_changes / max(1, cycles) * 10)
        
        # 漂移控制 (30%) - drift_events 应该低
        drift_control = max(0.0, 1.0 - drift_events / max(1, cycles) * 5)
        
        score = completion_rate * 0.4 + policy_stability * 0.3 + drift_control * 0.3
        
        return max(0.0, min(1.0, score))
    
    def get_test_results(self) -> List[FreezeTestResult]:
        return self.tests
    
    def get_latest_test(self) -> Optional[FreezeTestResult]:
        return self.tests[-1] if self.tests else None


class StabilizationEngine:
    """
    Stabilization Engine - 整合所有组件的主引擎
    
    P2 Stabilization = "可以变聪明，但不能再随意变结构"
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/stabilization"
        )
        
        self.drift_monitor = DriftMonitor(storage_path)
        self.failure_mode_map = FailureModeMap(storage_path)
        self.freeze_test = SystemFreezeTest(storage_path)
        
        # 稳定性配置
        self.stability_window = 100  # 最近 N 次决策
        self.max_policy_drift_per_hour = 0.1
        self.max_goal_expansion_per_day = 2.0
        
        self._is_baseline_set = False
    
    def initialize_baseline(self,
                          policy_state: Dict[str, Any],
                          goal_count: int,
                          decision_variance: float,
                          recursion_depth: int) -> None:
        """初始化基线"""
        self.drift_monitor.set_baseline(
            policy_state, goal_count, decision_variance, recursion_depth
        )
        self._is_baseline_set = True
    
    def record_tick(self,
                   policy_state: Dict[str, Any],
                   goal_count: int,
                   decision_variance: float,
                   recursion_depth: int,
                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        记录一次Tick
        
        主入口: 每个执行周期调用
        """
        if not self._is_baseline_set:
            return {"status": "baseline_not_set"}
        
        # 检查漂移
        drift_events = self.drift_monitor.check_drift(
            policy_state, goal_count, decision_variance,
            recursion_depth, context
        )
        
        # 检测循环
        if context and "action_history" in context:
            action_hist = context["action_history"]
            if self._detect_loop(action_hist):
                self.failure_mode_map.record_loop(
                    loop_id=str(time.time())[:8],
                    cycle=self._extract_loop_cycle(action_hist),
                    length=len(action_hist[-5:]),
                    context=context
                )
        
        # 检测震荡
        if context and "oscillation_pattern" in context:
            self.failure_mode_map.record_oscillation(
                pattern=context["oscillation_pattern"],
                amplitude=context.get("amplitude", 0.0),
                frequency=context.get("frequency", 0.0),
                context=context
            )
        
        # 状态摘要
        health = self.drift_monitor.get_drift_summary()
        
        return {
            "drift_detected": len(drift_events) > 0,
            "drift_events": [{"type": e.drift_type.value, "magnitude": e.magnitude} 
                           for e in drift_events],
            "system_health": health.get("health_status", "unknown"),
            "drift_events_total": health.get("total_events", 0),
            "is_stable": health.get("health_status") == SystemHealth.HEALTHY.value
        }
    
    def _detect_loop(self, action_history: List[str]) -> bool:
        """检测循环"""
        if len(action_history) < 6:
            return False
        
        # 检查最近5个动作是否形成循环
        last_5 = action_history[-5:]
        if len(set(last_5)) <= 2:  # 只有1-2个不同的动作
            return True
        
        return False
    
    def _extract_loop_cycle(self, action_history: List[str]) -> List[str]:
        """提取循环周期"""
        if len(action_history) >= 6:
            return action_history[-5:]
        return action_history
    
    def run_short_test(self, hours: int = 1) -> FreezeTestResult:
        """运行短测试 (1小时)"""
        return self.freeze_test.run_freeze_test(hours)
    
    def run_medium_test(self, days: int = 7) -> FreezeTestResult:
        """运行中等测试 (7天)"""
        return self.freeze_test.run_freeze_test(days * 24)
    
    def run_long_test(self, days: int = 30) -> FreezeTestResult:
        """运行长测试 (30天)"""
        return self.freeze_test.run_freeze_test(days * 24)
    
    def get_stabilization_status(self) -> Dict[str, Any]:
        """获取稳定性状态"""
        drift_summary = self.drift_monitor.get_drift_summary()
        failure_summary = self.failure_mode_map.get_failure_summary()
        latest_test = self.freeze_test.get_latest_test()
        
        # 综合健康判断
        health_factors = []
        
        if drift_summary.get("health_status") == SystemHealth.HEALTHY.value:
            health_factors.append(1.0)
        elif drift_summary.get("health_status") == SystemHealth.WARNING.value:
            health_factors.append(0.6)
        else:
            health_factors.append(0.2)
        
        critical_failures = len([m for m in self.failure_mode_map.failure_modes.values() 
                                if m.severity == "critical"])
        if critical_failures > 0:
            health_factors.append(0.3)
        else:
            health_factors.append(1.0)
        
        if latest_test:
            health_factors.append(latest_test.health_score)
        else:
            health_factors.append(0.5)
        
        overall_health = sum(health_factors) / len(health_factors)
        
        return {
            "overall_health": overall_health,
            "health_status": "stable" if overall_health >= 0.7 else "warning" if overall_health >= 0.5 else "critical",
            "drift_monitor": drift_summary,
            "failure_modes": failure_summary,
            "baseline_established": self._is_baseline_set,
            "latest_test": {
                "test_id": latest_test.test_id if latest_test else None,
                "duration_hours": latest_test.duration_seconds / 3600 if latest_test else 0,
                "health_score": latest_test.health_score if latest_test else 0,
                "passed": latest_test.passed if latest_test else False
            } if latest_test else None
        }


def create_stabilization_engine() -> StabilizationEngine:
    """工厂函数"""
    return StabilizationEngine()

__exports__ = ['DriftEvent', 'DriftMonitor', 'DriftType', 'FailureMode', 'FailureModeMap', 'FreezeTestResult', 'StabilizationEngine', 'SystemFreezeTest', 'SystemHealth', 'create_stabilization_engine']


