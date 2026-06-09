#!/usr/bin/env python3
"""
Simulation Sandbox - 模拟沙箱
最关键缺口: 系统在未来行为预测能力

核心功能:
- 7-day simulation rollout (7天模拟推演)
- 30-day drift prediction (30天漂移预测)
- Policy stress test (策略压力测试)

这是预测性 governance 的核心
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random


class SimulationState(Enum):
    """模拟状态"""
    RUNNING = "running"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    FAILED = "failed"


class StressTestResult(Enum):
    STRESS_PASS = "pass"      # 通过
    STRESS_WARNING = "warning"  # 警告
    STRESS_FAIL = "fail"       # 失败
    STRESS_CRITICAL = "critical"  # 严重失败


@dataclass
class SimulationSnapshot:
    """模拟快照"""
    tick: int
    timestamp: str
    
    # 状态指标
    utility_score: float
    policy_drift: float
    goal_expansion: float
    failure_rate: float
    recursion_depth: int
    
    # 预测
    predicted_state: str  # stable/converging/diverging/oscillating
    confidence: float
    
    # 事件
    events: List[str]
    warnings: List[str]


@dataclass
class DriftPrediction:
    """漂移预测"""
    prediction_id: str
    horizon_days: int  # 7 或 30
    
    predicted_utility: float
    predicted_drift: float
    predicted_goal_count: int
    predicted_failure_rate: float
    
    confidence: float
    risk_factors: List[str]
    
    recommendation: str


@dataclass
class StressTestReport:
    """压力测试报告"""
    test_id: str
    test_name: str
    
    # 测试结果
    result: StressTestResult
    
    # 各维度测试
    utility_stability: float      # 0-1
    goal_boundedness: float       # 0-1
    policy_convergence: float     # 0-1
    loop_resistance: float       # 0-1
    governance_effectiveness: float  # 0-1
    
    # 失败点
    failure_points: List[Dict[str, Any]]
    bottlenecks: List[str]
    
    # 建议
    recommendations: List[str]


class SandboxEnvironment:
    """
    Sandbox Environment - 沙箱环境模拟
    
    模拟系统运行环境
    """
    
    def __init__(self):
        self.current_state = {
            "utility_score": 0.8,
            "policy_drift": 0.05,
            "goal_count": 5,
            "failure_rate": 0.1,
            "recursion_depth": 1,
            "self_trigger_ratio": 0.15,
            "active_goals": [],
            "pending_goals": []
        }
    
    def reset(self):
        """重置环境"""
        self.current_state = {
            "utility_score": 0.8,
            "policy_drift": 0.05,
            "goal_count": 5,
            "failure_rate": 0.1,
            "recursion_depth": 1,
            "self_trigger_ratio": 0.15,
            "active_goals": [],
            "pending_goals": []
        }
    
    def apply_tick(self, actions: List[Dict[str, Any]]) -> SimulationSnapshot:
        """
        应用一次Tick
        
        Args:
            actions: 模拟执行的行动
        
        Returns:
            SimulationSnapshot
        """
        tick = len(actions) + 1
        
        # 模拟状态变化
        # Utility drift
        utility_change = random.uniform(-0.05, 0.08)
        self.current_state["utility_score"] = max(0.0, min(1.0, 
            self.current_state["utility_score"] + utility_change))
        
        # Policy drift
        policy_change = random.uniform(-0.02, 0.04)
        self.current_state["policy_drift"] = max(0.0, 
            self.current_state["policy_drift"] + policy_change)
        
        # Goal expansion
        if random.random() < 0.3:
            self.current_state["goal_count"] += random.randint(0, 2)
        
        # Failure rate
        if random.random() < 0.2:
            self.current_state["failure_rate"] = min(1.0, 
                self.current_state["failure_rate"] + 0.05)
        
        # Recursion depth
        if random.random() < 0.1:
            self.current_state["recursion_depth"] = min(5, 
                self.current_state["recursion_depth"] + 1)
        elif self.current_state["recursion_depth"] > 1:
            self.current_state["recursion_depth"] -= 1
        
        # 预测状态
        predicted_state = self._predict_state()
        
        # 生成事件和警告
        events = []
        warnings = []
        
        if self.current_state["utility_score"] < 0.3:
            warnings.append("Utility critically low")
        
        if self.current_state["policy_drift"] > 0.15:
            warnings.append("Policy drift exceeds threshold")
        
        if self.current_state["goal_count"] > 15:
            warnings.append("Goal expansion uncontrolled")
        
        if self.current_state["failure_rate"] > 0.3:
            warnings.append("Failure rate exceeds limit")
        
        return SimulationSnapshot(
            tick=tick,
            timestamp=datetime.now().isoformat(),
            utility_score=self.current_state["utility_score"],
            policy_drift=self.current_state["policy_drift"],
            goal_expansion=self.current_state["goal_count"],
            failure_rate=self.current_state["failure_rate"],
            recursion_depth=self.current_state["recursion_depth"],
            predicted_state=predicted_state,
            confidence=0.7 + random.random() * 0.2,
            events=events,
            warnings=warnings
        )
    
    def _predict_state(self) -> str:
        """预测当前状态"""
        if self.current_state["utility_score"] < 0.3:
            return "critical"
        elif self.current_state["failure_rate"] > 0.3:
            return "diverging"
        elif self.current_state["policy_drift"] > 0.15:
            return "drifting"
        elif self.current_state["goal_count"] > 20:
            return "unstable"
        elif self.current_state["utility_score"] > 0.7 and self.current_state["failure_rate"] < 0.2:
            return "stable"
        else:
            return "converging"


class SimulationSandbox:
    """
    Simulation Sandbox - 模拟沙箱主引擎
    
    核心能力:
    - 7-day simulation rollout
    - 30-day drift prediction
    - Policy stress test
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/sandbox"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.env = SandboxEnvironment()
        self.snapshots: List[SimulationSnapshot] = []
        self.predictions: List[DriftPrediction] = []
        self.stress_reports: List[StressTestReport] = []
        
        self._load_history()
    
    def _load_history(self):
        predictions_file = os.path.join(self.storage_path, "predictions.json")
        if os.path.exists(predictions_file):
            try:
                with open(predictions_file, 'r', encoding='utf-8') as f:
                    self.predictions = [DriftPrediction(**p) for p in json.load(f)]
            except:
                self.predictions = []
        
        stress_file = os.path.join(self.storage_path, "stress_reports.json")
        if os.path.exists(stress_file):
            try:
                with open(stress_file, 'r', encoding='utf-8') as f:
                    self.stress_reports = [StressTestReport(**r) for r in json.load(f)]
            except:
                self.stress_reports = []
    
    def _save_history(self):
        predictions_file = os.path.join(self.storage_path, "predictions.json")
        with open(predictions_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "prediction_id": p.prediction_id,
                "horizon_days": p.horizon_days,
                "predicted_utility": p.predicted_utility,
                "predicted_drift": p.predicted_drift,
                "predicted_goal_count": p.predicted_goal_count,
                "predicted_failure_rate": p.predicted_failure_rate,
                "confidence": p.confidence,
                "risk_factors": p.risk_factors,
                "recommendation": p.recommendation
            } for p in self.predictions[-20:]], f, ensure_ascii=False, indent=2)
        
        stress_file = os.path.join(self.storage_path, "stress_reports.json")
        with open(stress_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "test_id": r.test_id,
                "test_name": r.test_name,
                "result": r.result.value,
                "utility_stability": r.utility_stability,
                "goal_boundedness": r.goal_boundedness,
                "policy_convergence": r.policy_convergence,
                "loop_resistance": r.loop_resistance,
                "governance_effectiveness": r.governance_effectiveness,
                "failure_points": r.failure_points,
                "bottlenecks": r.bottlenecks,
                "recommendations": r.recommendations
            } for r in self.stress_reports[-10:]], f, ensure_ascii=False, indent=2)
    
    def simulate_7_days(self, initial_state: Dict[str, Any] = None) -> List[SimulationSnapshot]:
        """
        7天模拟推演
        
        每4小时一个tick, 7天 = 42 ticks
        """
        self.env.reset()
        
        if initial_state:
            self.env.current_state.update(initial_state)
        
        self.snapshots = []
        
        # 7天, 每4小时一个tick = 42 ticks
        tick_count = 42
        
        for i in range(tick_count):
            # 模拟这个tick可能的行动
            actions = self._generate_simulated_actions()
            
            snapshot = self.env.apply_tick(actions)
            self.snapshots.append(snapshot)
            
            # 检查是否需要终止
            if snapshot.predicted_state == "critical":
                break
        
        return self.snapshots
    
    def simulate_30_days(self, initial_state: Dict[str, Any] = None) -> List[SimulationSnapshot]:
        """
        30天模拟推演
        
        每12小时一个tick, 30天 = 60 ticks
        """
        self.env.reset()
        
        if initial_state:
            self.env.current_state.update(initial_state)
        
        self.snapshots = []
        
        # 30天, 每12小时一个tick = 60 ticks
        tick_count = 60
        
        for i in range(tick_count):
            actions = self._generate_simulated_actions()
            
            snapshot = self.env.apply_tick(actions)
            self.snapshots.append(snapshot)
            
            if snapshot.predicted_state == "critical":
                break
        
        return self.snapshots
    
    def _generate_simulated_actions(self) -> List[Dict[str, Any]]:
        """生成模拟行动"""
        actions = []
        
        # 模拟 goal 生成
        if random.random() < 0.2:
            actions.append({
                "type": "goal_propose",
                "category": random.choice(["improve_speed", "reduce_failure", "code_quality"])
            })
        
        # 模拟 policy 更新
        if random.random() < 0.3:
            actions.append({
                "type": "policy_update",
                "feature": random.choice(["skill_rank", "utility_weight"])
            })
        
        # 模拟 governance 检查
        actions.append({
            "type": "governance_validate"
        })
        
        return actions
    
    def predict_30_day_drift(self, current_metrics: Dict[str, float]) -> DriftPrediction:
        """
        30天漂移预测
        
        基于当前指标预测30天后的系统状态
        """
        # 使用简单的线性外推 + 随机波动
        days = 30
        
        # Utility 趋势
        utility_trend = (random.uniform(-0.1, 0.15) * days / 30)
        predicted_utility = max(0.0, min(1.0, current_metrics.get("utility", 0.8) + utility_trend))
        
        # Policy drift 累积
        drift_trend = (random.uniform(0.02, 0.08) * days / 30)
        predicted_drift = min(1.0, current_metrics.get("policy_drift", 0.05) + drift_trend)
        
        # Goal 膨胀
        goal_trend = int(random.uniform(0, 3) * days / 30)
        predicted_goal_count = int(current_metrics.get("goal_count", 5)) + goal_trend
        
        # Failure rate
        failure_trend = (random.uniform(-0.05, 0.1) * days / 30)
        predicted_failure_rate = max(0.0, min(1.0, 
            current_metrics.get("failure_rate", 0.1) + failure_trend))
        
        # 风险因素
        risk_factors = []
        if predicted_utility < 0.3:
            risk_factors.append("Utility prediction below critical threshold")
        if predicted_drift > 0.15:
            risk_factors.append("Policy drift prediction exceeds limit")
        if predicted_failure_rate > 0.3:
            risk_factors.append("Failure rate prediction exceeds 30%")
        if predicted_goal_count > 20:
            risk_factors.append("Goal explosion predicted")
        
        # 建议
        recommendation = "System is predicted to be stable"
        if risk_factors:
            recommendation = f"WARNING: {len(risk_factors)} risk factors identified. Consider intervention."
        
        prediction = DriftPrediction(
            prediction_id=f"pred_30d_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            horizon_days=30,
            predicted_utility=predicted_utility,
            predicted_drift=predicted_drift,
            predicted_goal_count=predicted_goal_count,
            predicted_failure_rate=predicted_failure_rate,
            confidence=0.65 + random.random() * 0.2,
            risk_factors=risk_factors,
            recommendation=recommendation
        )
        
        self.predictions.append(prediction)
        self._save_history()
        
        return prediction
    
    def predict_7_day_drift(self, current_metrics: Dict[str, float]) -> DriftPrediction:
        """7天漂移预测"""
        days = 7
        
        utility_trend = (random.uniform(-0.03, 0.05) * days / 7)
        predicted_utility = max(0.0, min(1.0, current_metrics.get("utility", 0.8) + utility_trend))
        
        drift_trend = (random.uniform(0.01, 0.03) * days / 7)
        predicted_drift = min(1.0, current_metrics.get("policy_drift", 0.05) + drift_trend)
        
        goal_trend = int(random.uniform(0, 1) * days / 7)
        predicted_goal_count = int(current_metrics.get("goal_count", 5)) + goal_trend
        
        failure_trend = (random.uniform(-0.02, 0.04) * days / 7)
        predicted_failure_rate = max(0.0, min(1.0,
            current_metrics.get("failure_rate", 0.1) + failure_trend))
        
        risk_factors = []
        if predicted_utility < 0.3:
            risk_factors.append("Utility critically low in 7 days")
        if predicted_drift > 0.15:
            risk_factors.append("Policy drift will exceed threshold")
        
        recommendation = "System is predicted to remain stable" if not risk_factors else f"CAUTION: {len(risk_factors)} risks"
        
        prediction = DriftPrediction(
            prediction_id=f"pred_7d_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            horizon_days=7,
            predicted_utility=predicted_utility,
            predicted_drift=predicted_drift,
            predicted_goal_count=predicted_goal_count,
            predicted_failure_rate=predicted_failure_rate,
            confidence=0.75 + random.random() * 0.15,
            risk_factors=risk_factors,
            recommendation=recommendation
        )
        
        self.predictions.append(prediction)
        self._save_history()
        
        return prediction
    
    def stress_test(self, test_name: str = "default") -> StressTestReport:
        """
        策略压力测试
        
        测试系统在极端条件下的表现
        """
        test_id = f"stress_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 运行多个场景的压力测试
        scenarios = [
            {"name": "high_goal_load", "goal_count": 50, "utility": 0.7},
            {"name": "low_utility", "goal_count": 10, "utility": 0.25},
            {"name": "high_failure_rate", "goal_count": 10, "utility": 0.6, "failure_rate": 0.4},
            {"name": "rapid_drift", "goal_count": 20, "utility": 0.5, "policy_drift": 0.2},
            {"name": "deep_recursion", "goal_count": 10, "utility": 0.7, "recursion_depth": 5},
        ]
        
        failure_points = []
        
        for scenario in scenarios:
            self.env.reset()
            self.env.current_state.update(scenario)
            
            snapshots = self.simulate_7_days()
            
            # 检查失败点
            for snap in snapshots:
                if snap.predicted_state == "critical":
                    failure_points.append({
                        "scenario": scenario["name"],
                        "tick": snap.tick,
                        "reason": snap.warnings
                    })
        
        # 计算各维度分数
        utility_stability = max(0.0, 1.0 - len([fp for fp in failure_points if "utility" in str(fp)]))
        goal_boundedness = max(0.0, 1.0 - len([fp for fp in failure_points if "goal" in str(fp)]) / 5)
        policy_convergence = 0.8 if len([fp for fp in failure_points if "drift" in str(fp)]) < 2 else 0.5
        loop_resistance = 0.9 if len([fp for fp in failure_points if "loop" in str(fp)]) == 0 else 0.6
        governance_effectiveness = 0.75 if len(failure_points) < 3 else 0.5
        
        # 确定测试结果
        avg_score = (utility_stability + goal_boundedness + policy_convergence + 
                    loop_resistance + governance_effectiveness) / 5
        
        if avg_score >= 0.8:
            result = StressTestResult.STRESS_PASS
        elif avg_score >= 0.6:
            result = StressTestResult.STRESS_WARNING
        elif avg_score >= 0.4:
            result = StressTestResult.STRESS_FAIL
        else:
            result = StressTestResult.STRESS_CRITICAL
        
        # 生成建议
        recommendations = []
        if utility_stability < 0.7:
            recommendations.append("Improve utility stability mechanism")
        if goal_boundedness < 0.7:
            recommendations.append("Implement stricter goal quota")
        if policy_convergence < 0.7:
            recommendations.append("Review policy drift controls")
        if loop_resistance < 0.7:
            recommendations.append("Strengthen loop detection")
        if governance_effectiveness < 0.7:
            recommendations.append("Enhance governance constraints")
        
        # 瓶颈
        bottlenecks = [fp["scenario"] for fp in failure_points[:3]]
        
        report = StressTestReport(
            test_id=test_id,
            test_name=test_name,
            result=result,
            utility_stability=utility_stability,
            goal_boundedness=goal_boundedness,
            policy_convergence=policy_convergence,
            loop_resistance=loop_resistance,
            governance_effectiveness=governance_effectiveness,
            failure_points=failure_points,
            bottlenecks=bottlenecks,
            recommendations=recommendations
        )
        
        self.stress_reports.append(report)
        self._save_history()
        
        return report
    
    def get_simulation_summary(self) -> Dict[str, Any]:
        """获取模拟摘要"""
        return {
            "recent_snapshots": len(self.snapshots),
            "predictions_count": len(self.predictions),
            "stress_reports_count": len(self.stress_reports),
            "latest_prediction": self.predictions[-1].prediction_id if self.predictions else None,
            "latest_stress_result": self.stress_reports[-1].result.value if self.stress_reports else None
        }


def create_simulation_sandbox() -> SimulationSandbox:
    """工厂函数"""
    return SimulationSandbox()

__exports__ = ['DriftPrediction', 'SandboxEnvironment', 'SimulationSandbox', 'SimulationSnapshot', 'SimulationState', 'StressTestReport', 'StressTestResult', 'create_simulation_sandbox']


