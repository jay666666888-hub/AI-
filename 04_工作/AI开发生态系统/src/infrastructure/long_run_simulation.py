#!/usr/bin/env python3
"""
Long-run Simulation - 长期模拟验证
Step 3: 系统验收工具

验证系统是否:
- stable (稳定)
- convergent (收敛)
- drifting (漂移)
- oscillating (震荡)

4 个核心指标:
1. Utility Stability
2. Policy Drift Curve
3. Goal Entropy
4. Loop Behavior
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import math


class SystemState(Enum):
    STABLE = "stable"
    CONVERGING = "converging"
    DIVERGING = "diverging"
    OSCILLATING = "oscillating"
    UNKNOWN = "unknown"


class TrendDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"


@dataclass
class UtilityMetrics:
    """Utility 稳定性指标"""
    decision_utility_variance: float
    reward_consistency: float
    avg_utility: float
    min_utility: float
    max_utility: float
    utility_trend: TrendDirection


@dataclass
class PolicyDriftMetrics:
    """Policy 漂移曲线指标"""
    daily_deltas: List[float]
    total_drift: float
    drift_direction: TrendDirection
    is_converging: bool
    convergence_rate: float


@dataclass
class GoalEntropyMetrics:
    """Goal 熵指标"""
    goal_diversity: float
    entropy_score: float
    expansion_rate: float
    is_stable: bool
    diversity_trend: TrendDirection


@dataclass
class LoopMetrics:
    """Loop 行为指标"""
    loop_count: int
    avg_loop_length: float
    self_reinforcing: bool
    loop_patterns: List[str]
    oscillation_amplitude: float


@dataclass
class SimulationResult:
    """模拟结果"""
    simulation_id: str
    duration_cycles: int
    start_time: str
    end_time: str
    system_state: SystemState
    
    utility_metrics: Dict[str, Any]
    policy_drift_metrics: Dict[str, Any]
    goal_entropy_metrics: Dict[str, Any]
    loop_metrics: Dict[str, Any]
    
    overall_score: float
    passed: bool
    recommendations: List[str]


class UtilityStabilityAnalyzer:
    def __init__(self, window_size: int = 50):
        self.window_size = window_size
        self.history: List[float] = []
    
    def record_utility(self, utility: float) -> None:
        self.history.append(utility)
        if len(self.history) > self.window_size:
            self.history.pop(0)
    
    def analyze(self) -> UtilityMetrics:
        if not self.history:
            return UtilityMetrics(
                decision_utility_variance=0.0,
                reward_consistency=0.0,
                avg_utility=0.0,
                min_utility=0.0,
                max_utility=0.0,
                utility_trend=TrendDirection.STABLE
            )
        
        values = self.history
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        consistency = max(0.0, 1.0 - math.sqrt(variance) * 2)
        
        if len(values) >= 10:
            recent_avg = sum(values[-5:]) / 5
            older_avg = sum(values[-10:-5]) / 5
            if recent_avg > older_avg + 0.05:
                trend = TrendDirection.IMPROVING
            elif recent_avg < older_avg - 0.05:
                trend = TrendDirection.DEGRADING
            else:
                trend = TrendDirection.STABLE
        else:
            trend = TrendDirection.STABLE
        
        return UtilityMetrics(
            decision_utility_variance=variance,
            reward_consistency=consistency,
            avg_utility=avg,
            min_utility=min(values),
            max_utility=max(values),
            utility_trend=trend
        )


class PolicyDriftAnalyzer:
    def __init__(self, convergence_threshold: float = 0.05):
        self.convergence_threshold = convergence_threshold
        self.daily_deltas: List[float] = []
        self.policy_snapshots: List[Dict[str, float]] = []
    
    def record_policy(self, policy_state: Dict[str, float]) -> None:
        if self.policy_snapshots:
            prev = self.policy_snapshots[-1]
            delta = sum(abs(policy_state.get(k, 0) - prev.get(k, 0))
                       for k in set(policy_state.keys()) | set(prev.keys()))
            self.daily_deltas.append(delta)
        
        self.policy_snapshots.append(policy_state.copy())
        
        if len(self.policy_snapshots) > 30:
            self.policy_snapshots.pop(0)
    
    def analyze(self) -> PolicyDriftMetrics:
        if len(self.daily_deltas) < 2:
            return PolicyDriftMetrics(
                daily_deltas=self.daily_deltas,
                total_drift=0.0,
                drift_direction=TrendDirection.STABLE,
                is_converging=True,
                convergence_rate=0.0
            )
        
        total_drift = sum(self.daily_deltas)
        
        if len(self.daily_deltas) >= 5:
            recent = sum(self.daily_deltas[-3:]) / 3
            older = sum(self.daily_deltas[-6:-3]) / 3 if len(self.daily_deltas) >= 6 else recent
            if recent < older - 0.01:
                drift_direction = TrendDirection.IMPROVING
            elif recent > older + 0.01:
                drift_direction = TrendDirection.DEGRADING
            else:
                drift_direction = TrendDirection.STABLE
        else:
            drift_direction = TrendDirection.STABLE
        
        recent_avg = sum(self.daily_deltas[-3:]) / min(3, len(self.daily_deltas))
        is_converging = recent_avg < self.convergence_threshold
        
        if len(self.daily_deltas) >= 2:
            convergence_rate = 1.0 - (recent_avg / (sum(self.daily_deltas) / len(self.daily_deltas)))
        else:
            convergence_rate = 0.0
        
        return PolicyDriftMetrics(
            daily_deltas=self.daily_deltas[-10:],
            total_drift=total_drift,
            drift_direction=drift_direction,
            is_converging=is_converging,
            convergence_rate=max(0.0, convergence_rate)
        )


class GoalEntropyAnalyzer:
    def __init__(self,
                 diversity_threshold: float = 0.7,
                 entropy_threshold: float = 2.0):
        self.diversity_threshold = diversity_threshold
        self.entropy_threshold = entropy_threshold
        self.goal_history: List[Dict[str, Any]] = []
        self.goal_types: Dict[str, int] = {}
    
    def record_goal(self, goal_category: str, goal_params: Dict[str, Any]) -> None:
        self.goal_history.append({
            "category": goal_category,
            "params": goal_params,
            "timestamp": datetime.now().isoformat()
        })
        
        self.goal_types[goal_category] = self.goal_types.get(goal_category, 0) + 1
        
        if len(self.goal_history) > 100:
            self.goal_history.pop(0)
    
    def analyze(self) -> GoalEntropyMetrics:
        if not self.goal_history:
            return GoalEntropyMetrics(
                goal_diversity=0.0,
                entropy_score=0.0,
                expansion_rate=0.0,
                is_stable=True,
                diversity_trend=TrendDirection.STABLE
            )
        
        total_goals = len(self.goal_history)
        unique_types = len(set(g["category"] for g in self.goal_history))
        diversity = unique_types / max(1, len(self.goal_types))
        
        type_counts = list(self.goal_types.values())
        total = sum(type_counts)
        if total > 0:
            probs = [c / total for c in type_counts]
            entropy = -sum(p * math.log(p) for p in probs if p > 0)
        else:
            entropy = 0.0
        
        if len(self.goal_history) >= 20:
            recent = len(self.goal_history[-10:])
            older = len(set(g["category"] for g in self.goal_history[-20:-10]))
            expansion_rate = (recent - older) / max(1, older)
        else:
            expansion_rate = 0.0
        
        is_stable = (diversity < self.diversity_threshold and
                    entropy < self.entropy_threshold and
                    expansion_rate < 0.5)
        
        if len(self.goal_history) >= 20:
            recent_diversity = len(set(g["category"] for g in self.goal_history[-10:]))
            older_diversity = len(set(g["category"] for g in self.goal_history[-20:-10]))
            if recent_diversity < older_diversity:
                diversity_trend = TrendDirection.IMPROVING
            elif recent_diversity > older_diversity:
                diversity_trend = TrendDirection.DEGRADING
            else:
                diversity_trend = TrendDirection.STABLE
        else:
            diversity_trend = TrendDirection.STABLE
        
        return GoalEntropyMetrics(
            goal_diversity=diversity,
            entropy_score=entropy,
            expansion_rate=expansion_rate,
            is_stable=is_stable,
            diversity_trend=diversity_trend
        )


class LoopBehaviorAnalyzer:
    def __init__(self, loop_threshold: int = 3):
        self.loop_threshold = loop_threshold
        self.action_history: List[str] = []
        self.loop_history: List[Dict[str, Any]] = []
    
    def record_action(self, action: str) -> None:
        self.action_history.append(action)
        
        if len(self.action_history) > 50:
            self.action_history.pop(0)
        
        self._detect_loop()
    
    def _detect_loop(self) -> None:
        if len(self.action_history) < 6:
            return
        
        last_6 = self.action_history[-6:]
        
        if last_6[:3] == last_6[3:]:
            loop = {
                "pattern": str(last_6[:3]),
                "length": 3,
                "timestamp": datetime.now().isoformat()
            }
            self.loop_history.append(loop)
    
    def analyze(self) -> LoopMetrics:
        if not self.action_history:
            return LoopMetrics(
                loop_count=0,
                avg_loop_length=0.0,
                self_reinforcing=False,
                loop_patterns=[],
                oscillation_amplitude=0.0
            )
        
        loop_count = len(self.loop_history)
        
        if loop_count > 0:
            avg_length = sum(l["length"] for l in self.loop_history) / loop_count
        else:
            avg_length = 0.0
        
        pattern_counts: Dict[str, int] = {}
        for loop in self.loop_history:
            pattern = loop["pattern"]
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        self_reinforcing = any(count >= 3 for count in pattern_counts.values())
        
        if len(self.action_history) >= 10:
            changes = sum(1 for i in range(1, len(self.action_history))
                        if self.action_history[i] != self.action_history[i-1])
            oscillation_amplitude = changes / (len(self.action_history) - 1)
        else:
            oscillation_amplitude = 0.0
        
        loop_patterns = list(set(l["pattern"] for l in self.loop_history[-10:]))
        
        return LoopMetrics(
            loop_count=loop_count,
            avg_loop_length=avg_length,
            self_reinforcing=self_reinforcing,
            loop_patterns=loop_patterns,
            oscillation_amplitude=oscillation_amplitude
        )


class LongRunSimulator:
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/simulation"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.utility_analyzer = UtilityStabilityAnalyzer()
        self.policy_drift_analyzer = PolicyDriftAnalyzer()
        self.goal_entropy_analyzer = GoalEntropyAnalyzer()
        self.loop_analyzer = LoopBehaviorAnalyzer()
        
        self.simulation_results: List[SimulationResult] = []
        
        self._load()
    
    def _load(self):
        results_file = os.path.join(self.storage_path, "simulation_results.json")
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.simulation_results = [
                        SimulationResult(
                            simulation_id=r["simulation_id"],
                            duration_cycles=r["duration_cycles"],
                            start_time=r["start_time"],
                            end_time=r["end_time"],
                            system_state=SystemState(r["system_state"]),
                            utility_metrics=r["utility_metrics"],
                            policy_drift_metrics=r["policy_drift_metrics"],
                            goal_entropy_metrics=r["goal_entropy_metrics"],
                            loop_metrics=r["loop_metrics"],
                            overall_score=r["overall_score"],
                            passed=r["passed"],
                            recommendations=r["recommendations"]
                        )
                        for r in data
                    ]
            except:
                self.simulation_results = []
    
    def _save(self):
        results_file = os.path.join(self.storage_path, "simulation_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "simulation_id": r.simulation_id,
                "duration_cycles": r.duration_cycles,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "system_state": r.system_state.value,
                "utility_metrics": r.utility_metrics,
                "policy_drift_metrics": r.policy_drift_metrics,
                "goal_entropy_metrics": r.goal_entropy_metrics,
                "loop_metrics": r.loop_metrics,
                "overall_score": r.overall_score,
                "passed": r.passed,
                "recommendations": r.recommendations
            } for r in self.simulation_results[-20:]], f, ensure_ascii=False, indent=2)
    
    def record_tick(self,
                   utility: float,
                   policy_state: Dict[str, float],
                   goal_category: str = None,
                   goal_params: Dict[str, Any] = None,
                   action: str = None) -> Dict[str, Any]:
        if utility is not None:
            self.utility_analyzer.record_utility(utility)
        
        if policy_state:
            self.policy_drift_analyzer.record_policy(policy_state)
        
        if goal_category:
            self.goal_entropy_analyzer.record_goal(goal_category, goal_params or {})
        
        if action:
            self.loop_analyzer.record_action(action)
        
        return {
            "recorded": True,
            "utility_history_size": len(self.utility_analyzer.history),
            "policy_snapshots": len(self.policy_drift_analyzer.policy_snapshots)
        }
    
    def run_simulation(self, cycles: int) -> SimulationResult:
        simulation_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now().isoformat()
        
        utility_metrics = self.utility_analyzer.analyze()
        policy_drift_metrics = self.policy_drift_analyzer.analyze()
        goal_entropy_metrics = self.goal_entropy_analyzer.analyze()
        loop_metrics = self.loop_analyzer.analyze()
        
        system_state = self._determine_system_state(
            utility_metrics, policy_drift_metrics,
            goal_entropy_metrics, loop_metrics
        )
        
        overall_score = self._calculate_overall_score(
            utility_metrics, policy_drift_metrics,
            goal_entropy_metrics, loop_metrics
        )
        
        passed = (
            overall_score >= 0.7 and
            utility_metrics.decision_utility_variance < 0.2 and
            policy_drift_metrics.is_converging and
            not loop_metrics.self_reinforcing
        )
        
        recommendations = self._generate_recommendations(
            utility_metrics, policy_drift_metrics,
            goal_entropy_metrics, loop_metrics, system_state
        )
        
        result = SimulationResult(
            simulation_id=simulation_id,
            duration_cycles=cycles,
            start_time=start_time,
            end_time=datetime.now().isoformat(),
            system_state=system_state,
            utility_metrics={
                "variance": utility_metrics.decision_utility_variance,
                "consistency": utility_metrics.reward_consistency,
                "avg": utility_metrics.avg_utility,
                "trend": utility_metrics.utility_trend.value
            },
            policy_drift_metrics={
                "total_drift": policy_drift_metrics.total_drift,
                "is_converging": policy_drift_metrics.is_converging,
                "convergence_rate": policy_drift_metrics.convergence_rate,
                "drift_direction": policy_drift_metrics.drift_direction.value
            },
            goal_entropy_metrics={
                "diversity": goal_entropy_metrics.goal_diversity,
                "entropy": goal_entropy_metrics.entropy_score,
                "expansion_rate": goal_entropy_metrics.expansion_rate,
                "is_stable": goal_entropy_metrics.is_stable
            },
            loop_metrics={
                "loop_count": loop_metrics.loop_count,
                "avg_loop_length": loop_metrics.avg_loop_length,
                "self_reinforcing": loop_metrics.self_reinforcing,
                "oscillation_amplitude": loop_metrics.oscillation_amplitude
            },
            overall_score=overall_score,
            passed=passed,
            recommendations=recommendations
        )
        
        self.simulation_results.append(result)
        self._save()
        
        return result
    
    def _determine_system_state(self,
                                 utility: UtilityMetrics,
                                 policy: PolicyDriftMetrics,
                                 goal: GoalEntropyMetrics,
                                 loop: LoopMetrics) -> SystemState:
        if loop.self_reinforcing or loop.oscillation_amplitude > 0.5:
            return SystemState.OSCILLATING
        
        if policy.drift_direction == TrendDirection.DEGRADING:
            return SystemState.DIVERGING
        
        if policy.is_converging and utility.decision_utility_variance < 0.1:
            return SystemState.CONVERGING
        
        if (utility.reward_consistency > 0.7 and
            policy.convergence_rate > 0.5 and
            goal.is_stable and
            loop.loop_count < 3):
            return SystemState.STABLE
        
        return SystemState.UNKNOWN
    
    def _calculate_overall_score(self,
                                 utility: UtilityMetrics,
                                 policy: PolicyDriftMetrics,
                                 goal: GoalEntropyMetrics,
                                 loop: LoopMetrics) -> float:
        utility_score = max(0.0, 1.0 - utility.decision_utility_variance * 2)
        policy_score = max(0.0, min(1.0, policy.convergence_rate))
        goal_score = 1.0 if goal.is_stable else max(0.0, 1.0 - goal.entropy_score / 3)
        
        if loop.self_reinforcing:
            loop_score = 0.0
        elif loop.loop_count > 5:
            loop_score = 0.3
        else:
            loop_score = max(0.0, 1.0 - loop.oscillation_amplitude)
        
        return (utility_score * 0.25 + policy_score * 0.25 +
                goal_score * 0.25 + loop_score * 0.25)
    
    def _generate_recommendations(self,
                                 utility: UtilityMetrics,
                                 policy: PolicyDriftMetrics,
                                 goal: GoalEntropyMetrics,
                                 loop: LoopMetrics,
                                 state: SystemState) -> List[str]:
        recommendations = []
        
        if state == SystemState.OSCILLATING:
            recommendations.append("CRITICAL: System is oscillating. Reduce learning rate and add momentum.")
        
        if state == SystemState.DIVERGING:
            recommendations.append("WARNING: Policy is drifting. Review recent changes.")
        
        if utility.decision_utility_variance > 0.15:
            recommendations.append("Utility variance is high. Stabilize reward shaping.")
        
        if not policy.is_converging:
            recommendations.append("Policy not converging. Check for conflicting updates.")
        
        if goal.expansion_rate > 0.5:
            recommendations.append("Goal expansion detected. Implement stricter goal filtering.")
        
        if loop.loop_count > 3:
            recommendations.append("Multiple loops detected. Add loop detection and break mechanism.")
        
        if loop.self_reinforcing:
            recommendations.append("Self-reinforcing behavior detected. This is critical.")
        
        if not recommendations:
            recommendations.append("System is healthy. Continue monitoring.")
        
        return recommendations
    
    def get_latest_result(self) -> Optional[SimulationResult]:
        return self.simulation_results[-1] if self.simulation_results else None
    
    def get_status_summary(self) -> Dict[str, Any]:
        latest = self.get_latest_result()
        
        if not latest:
            return {
                "has_results": False,
                "system_state": SystemState.UNKNOWN.value
            }
        
        return {
            "has_results": True,
            "simulation_count": len(self.simulation_results),
            "latest_simulation": latest.simulation_id,
            "system_state": latest.system_state.value,
            "overall_score": latest.overall_score,
            "passed": latest.passed,
            "recommendations": latest.recommendations
        }


def create_long_run_simulator() -> LongRunSimulator:
    return LongRunSimulator()

__exports__ = ['GoalEntropyAnalyzer', 'GoalEntropyMetrics', 'LongRunSimulator', 'LoopBehaviorAnalyzer', 'LoopMetrics', 'PolicyDriftAnalyzer', 'PolicyDriftMetrics', 'SimulationResult', 'SystemState', 'TrendDirection', 'UtilityMetrics', 'UtilityStabilityAnalyzer', 'create_long_run_simulator']


