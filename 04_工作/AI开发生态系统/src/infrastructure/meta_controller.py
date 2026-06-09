#!/usr/bin/env python3
"""
Meta-Controller - 元控制器
终极层: 让系统拥有"调节自己治理强度"的能力

核心功能:
- Governance strength adaptive (治理强度自适应)
- Runtime strictness modulation (运行时严格度调节)
- Exploration vs safety balance (探索与安全平衡)

系统可以根据状态动态调整自己的治理策略
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class ControllerMode(Enum):
    """控制器模式"""
    EXPLORATION = "exploration"   # 探索模式 - 宽松, 允许尝试
    BALANCED = "balanced"        # 平衡模式 - 中等
    SAFETY = "safety"            # 安全模式 - 严格
    EMERGENCY = "emergency"       # 紧急模式 - 最严格


class StrictnessLevel(Enum):
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 1.0


@dataclass
class ControllerConfig:
    """控制器配置"""
    mode: ControllerMode
    strictness: StrictnessLevel
    
    # 阈值
    utility_low_threshold: float      # 进入 safety 模式的阈值
    failure_rate_threshold: float     # 触发 emergency 的阈值
    
    # 适应参数
    adaptation_rate: float             # 适应速率
    evaluation_window: int             # 评估窗口 (ticks)
    
    # 限制
    max_exploration_ratio: float     # 最大探索比例
    min_safety_margin: float          # 最小安全边界


@dataclass
class ControllerState:
    """控制器状态"""
    current_mode: ControllerMode
    current_strictness: StrictnessLevel
    
    # 统计
    mode_history: List[str]           # 模式切换历史
    strictness_history: List[float]   # 严格度历史
    recent_violations: int             # 最近违规数
    
    # 性能指标
    exploration_rate: float           # 探索率
    safety_score: float              # 安全分数
    governance_effectiveness: float  # 治理有效性
    
    # 预测
    predicted_mode: ControllerMode   # 预测下一步模式
    confidence: float


@dataclass
class AdaptationAction:
    """适应动作"""
    action_id: str
    timestamp: str
    
    # 动作类型
    action_type: str   # "mode_switch", "strictness_change", "threshold_adjust"
    
    # 内容
    from_value: str
    to_value: str
    reason: str
    
    # 效果
    expected_improvement: float
    actual_improvement: Optional[float] = None


class GovernanceStrengthAdapter:
    """
    Governance Strength Adapter - 治理强度适配器
    
    根据系统状态动态调整治理强度
    """
    
    def __init__(self, config: ControllerConfig = None):
        self.config = config or ControllerConfig(
            mode=ControllerMode.BALANCED,
            strictness=StrictnessLevel.MEDIUM,
            utility_low_threshold=0.4,
            failure_rate_threshold=0.25,
            adaptation_rate=0.1,
            evaluation_window=10,
            max_exploration_ratio=0.3,
            min_safety_margin=0.7
        )
        
        self.state = ControllerState(
            current_mode=self.config.mode,
            current_strictness=self.config.strictness,
            mode_history=[self.config.mode.value],
            strictness_history=[self.config.strictness.value],
            recent_violations=0,
            exploration_rate=0.2,
            safety_score=1.0,
            governance_effectiveness=0.8,
            predicted_mode=self.config.mode,
            confidence=0.5
        )
    
    def evaluate_state(self, metrics: Dict[str, float]) -> ControllerState:
        """
        评估当前状态并确定控制器状态
        
        Args:
            metrics: {"utility": 0.8, "failure_rate": 0.1, "policy_drift": 0.05, ...}
        
        Returns:
            ControllerState
        """
        utility = metrics.get("utility", 0.5)
        failure_rate = metrics.get("failure_rate", 0.0)
        policy_drift = metrics.get("policy_drift", 0.0)
        violations = metrics.get("recent_violations", 0)
        
        # 模式切换逻辑
        new_mode = self._determine_mode(utility, failure_rate, violations)
        
        # 严格度调整
        new_strictness = self._determine_strictness(
            utility, failure_rate, policy_drift
        )
        
        # 更新状态
        if new_mode != self.state.current_mode:
            self.state.mode_history.append(new_mode.value)
            self.state.current_mode = new_mode
        
        self.state.current_strictness = new_strictness
        self.state.strictness_history.append(new_strictness.value)
        
        # 统计更新
        self.state.recent_violations = violations
        
        # 计算指标
        self.state.exploration_rate = self._calculate_exploration_rate()
        self.state.safety_score = self._calculate_safety_score(utility, failure_rate)
        self.state.governance_effectiveness = self._calculate_effectiveness()
        
        # 预测下一步
        self.state.predicted_mode = self._predict_next_mode(metrics)
        
        return self.state
    
    def _determine_mode(self, utility: float, failure_rate: float, violations: int) -> ControllerMode:
        """确定控制器模式"""
        # Emergency: 严重违规或极低 utility
        if violations >= 5 or utility < 0.2 or failure_rate > 0.5:
            return ControllerMode.EMERGENCY
        
        # Safety: 低 utility 或 高失败率
        if utility < self.config.utility_low_threshold or failure_rate > self.config.failure_rate_threshold:
            return ControllerMode.SAFETY
        
        # Exploration: 高 utility 且低失败率 → 可以放松
        if utility > 0.75 and failure_rate < 0.1 and violations == 0:
            return ControllerMode.EXPLORATION
        
        # 默认: BALANCED
        return ControllerMode.BALANCED
    
    def _determine_strictness(self, utility: float, failure_rate: float, policy_drift: float) -> StrictnessLevel:
        """确定严格度"""
        # 综合评分
        score = utility * 0.4 + (1 - failure_rate) * 0.3 + (1 - policy_drift) * 0.3
        
        if score > 0.85:
            return StrictnessLevel.VERY_LOW
        elif score > 0.7:
            return StrictnessLevel.LOW
        elif score > 0.5:
            return StrictnessLevel.MEDIUM
        elif score > 0.35:
            return StrictnessLevel.HIGH
        else:
            return StrictnessLevel.VERY_HIGH
    
    def _calculate_exploration_rate(self) -> float:
        """计算探索率"""
        base = 0.2
        
        if self.state.current_mode == ControllerMode.EXPLORATION:
            return min(0.5, base + 0.2)
        elif self.state.current_mode == ControllerMode.BALANCED:
            return base
        elif self.state.current_mode == ControllerMode.SAFETY:
            return max(0.05, base - 0.15)
        else:  # EMERGENCY
            return 0.0
    
    def _calculate_safety_score(self, utility: float, failure_rate: float) -> float:
        """计算安全分数"""
        return utility * (1 - failure_rate)
    
    def _calculate_effectiveness(self) -> float:
        """计算治理有效性"""
        # 基于模式历史和当前严格度
        recent_modes = self.state.mode_history[-5:]
        stability = 1.0 - (len(set(recent_modes)) / len(recent_modes)) if recent_modes else 1.0
        
        strictness_factor = self.state.current_strictness.value
        
        return stability * 0.5 + strictness_factor * 0.5
    
    def _predict_next_mode(self, metrics: Dict[str, float]) -> ControllerMode:
        """预测下一步模式"""
        utility_trend = metrics.get("utility_trend", 0.0)
        failure_trend = metrics.get("failure_trend", 0.0)
        
        # 如果 utility 在下降或 failure 在上升, 预测更严格的模式
        if utility_trend < -0.05 or failure_trend > 0.05:
            if self.state.current_mode in [ControllerMode.BALANCED, ControllerMode.EXPLORATION]:
                return ControllerMode.SAFETY
        
        # 如果稳定, 预测当前模式
        return self.state.current_mode
    
    def get_adjusted_thresholds(self) -> Dict[str, float]:
        """
        获取调整后的阈值
        
        根据当前模式返回调整过的阈值
        """
        base_thresholds = {
            "utility_min": 0.2,
            "failure_max": 0.3,
            "drift_max": 0.15,
            "goal_quota_per_hour": 10
        }
        
        # 根据严格度调整
        multiplier = self.state.current_strictness.value
        
        return {
            "utility_min": base_thresholds["utility_min"] * multiplier,
            "failure_max": base_thresholds["failure_max"] * multiplier,
            "drift_max": base_thresholds["drift_max"] * multiplier,
            "goal_quota_per_hour": int(base_thresholds["goal_quota_per_hour"] * (2 - multiplier))
        }


class ExplorationSafetyBalancer:
    """
    Exploration-Safety Balancer - 探索与安全平衡器
    
    在探索新策略和保持安全之间取得平衡
    """
    
    def __init__(self):
        self.exploration_budget: float = 1.0  # 探索预算
        self.safety_margin: float = 0.8        # 安全边界
        self.balance_history: List[Dict[str, Any]] = []
    
    def compute_balance(self,
                       system_state: Dict[str, float],
                       proposed_action: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算平衡决策
        
        Args:
            system_state: 当前系统状态
            proposed_action: 提议的动作
        
        Returns:
            {
                "decision": "allow" / "block" / "modify",
                "exploration_cost": float,
                "safety_risk": float,
                "balanced_score": float,
                "reasoning": str
            }
        """
        # 计算探索成本
        exploration_cost = self._calculate_exploration_cost(proposed_action)
        
        # 计算安全风险
        safety_risk = self._calculate_safety_risk(system_state, proposed_action)
        
        # 计算平衡分数
        # 高探索 + 低风险 = 高分数
        # 低探索 + 高风险 = 低分数
        balanced_score = (1 - exploration_cost) * (1 - safety_risk) * self.safety_margin
        
        # 决策
        if safety_risk > 0.7:
            decision = "block"
            reasoning = f"High safety risk: {safety_risk:.2f}"
        elif safety_risk > 0.4:
            if exploration_cost < 0.3:
                decision = "allow"
                reasoning = "Moderate risk, low exploration cost"
            else:
                decision = "modify"
                reasoning = f"Reduce exploration: cost={exploration_cost:.2f}"
        else:
            decision = "allow"
            reasoning = "Low risk, safe to proceed"
        
        self.balance_history.append({
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "exploration_cost": exploration_cost,
            "safety_risk": safety_risk,
            "balanced_score": balanced_score
        })
        
        return {
            "decision": decision,
            "exploration_cost": exploration_cost,
            "safety_risk": safety_risk,
            "balanced_score": balanced_score,
            "reasoning": reasoning
        }
    
    def _calculate_exploration_cost(self, action: Dict[str, Any]) -> float:
        """计算探索成本"""
        action_type = action.get("type", "")
        
        # 新策略探索成本高
        if "new_strategy" in action_type:
            return 0.6
        elif "policy_update" in action_type:
            return 0.4
        elif "skill_usage" in action_type:
            return 0.2
        else:
            return 0.1
    
    def _calculate_safety_risk(self, state: Dict[str, float], action: Dict[str, Any]) -> float:
        """计算安全风险"""
        base_risk = 1.0 - state.get("safety_score", 0.5)
        
        # 动作类型风险
        action_type = action.get("type", "")
        if action_type in ["structural_change", "agent_modification"]:
            return min(1.0, base_risk + 0.4)
        elif action_type in ["policy_update", "threshold_adjust"]:
            return base_risk + 0.2
        else:
            return base_risk


class MetaController:
    """
    Meta-Controller - 元控制器主引擎
    
    整合所有自适应治理功能
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/meta_controller"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.governance_adapter = GovernanceStrengthAdapter()
        self.exploration_balancer = ExplorationSafetyBalancer()
        
        self.adaptation_history: List[AdaptationAction] = []
        
        self._load_history()
    
    def _load_history(self):
        history_file = os.path.join(self.storage_path, "adaptation_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.adaptation_history = [AdaptationAction(**a) for a in json.load(f)]
            except:
                self.adaptation_history = []
    
    def _save_history(self):
        history_file = os.path.join(self.storage_path, "adaptation_history.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "action_id": a.action_id,
                "timestamp": a.timestamp,
                "action_type": a.action_type,
                "from_value": a.from_value,
                "to_value": a.to_value,
                "reason": a.reason,
                "expected_improvement": a.expected_improvement,
                "actual_improvement": a.actual_improvement
            } for a in self.adaptation_history[-100:]], f, ensure_ascii=False, indent=2)
    
    def evaluate(self, metrics: Dict[str, float]) -> ControllerState:
        """
        评估系统状态并返回控制器状态
        
        Args:
            metrics: 系统指标
        
        Returns:
            ControllerState
        """
        return self.governance_adapter.evaluate_state(metrics)
    
    def decide(self,
              action: Dict[str, Any],
              system_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        对动作做出决策
        
        Args:
            action: 提议的动作
            system_metrics: 系统指标
        
        Returns:
            决策结果
        """
        # 1. 先评估当前状态
        state = self.evaluate(system_metrics)
        
        # 2. 获取调整后的阈值
        adjusted_thresholds = self.governance_adapter.get_adjusted_thresholds()
        
        # 3. 计算平衡决策
        balance_result = self.exploration_balancer.compute_balance(
            system_metrics, action
        )
        
        # 4. 如果需要调整, 记录适应动作
        if state.current_mode != state.predicted_mode:
            adaptation = AdaptationAction(
                action_id=f"adapt_{len(self.adaptation_history)}",
                timestamp=datetime.now().isoformat(),
                action_type="mode_switch",
                from_value=state.current_mode.value,
                to_value=state.predicted_mode.value,
                reason=f"Based on metrics: utility={system_metrics.get('utility', 0)}",
                expected_improvement=0.1
            )
            self.adaptation_history.append(adaptation)
            self._save_history()
        
        return {
            "controller_state": {
                "mode": state.current_mode.value,
                "strictness": state.current_strictness.value,
                "predicted_mode": state.predicted_mode.value,
                "exploration_rate": state.exploration_rate,
                "safety_score": state.safety_score
            },
            "adjusted_thresholds": adjusted_thresholds,
            "balance_decision": balance_result,
            "recommendation": self._make_recommendation(state, balance_result)
        }
    
    def _make_recommendation(self, state: ControllerState, balance: Dict[str, Any]) -> str:
        """生成建议"""
        if state.current_mode == ControllerMode.EMERGENCY:
            return "STOP: Emergency mode activated. Only safe operations allowed."
        
        if state.current_mode == ControllerMode.SAFETY:
            return "CAUTION: Safety mode. Reduce exploration, prioritize stability."
        
        if balance["decision"] == "block":
            return "BLOCKED: Safety risk too high"
        
        if balance["decision"] == "modify":
            return f"MODIFY: Reduce exploration cost ({balance['exploration_cost']:.2f})"
        
        if state.current_mode == ControllerMode.EXPLORATION:
            return "ALLOW: Exploration mode - safe to try new strategies"
        
        return "ALLOW: Normal operation"
    
    def get_meta_controller_status(self) -> Dict[str, Any]:
        """获取元控制器状态"""
        state = self.governance_adapter.state
        
        return {
            "current_mode": state.current_mode.value,
            "current_strictness": state.current_strictness.value,
            "exploration_rate": state.exploration_rate,
            "safety_score": state.safety_score,
            "governance_effectiveness": state.governance_effectiveness,
            "predicted_mode": state.predicted_mode.value,
            "adaptations_count": len(self.adaptation_history),
            "recent_violations": state.recent_violations
        }


def create_meta_controller() -> MetaController:
    """工厂函数"""
    return MetaController()

__exports__ = ['AdaptationAction', 'ControllerConfig', 'ControllerMode', 'ControllerState', 'ExplorationSafetyBalancer', 'GovernanceStrengthAdapter', 'MetaController', 'StrictnessLevel', 'create_meta_controller']


