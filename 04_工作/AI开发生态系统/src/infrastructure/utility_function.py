#!/usr/bin/env python3
"""
Utility Function System - 效用函数系统
P0: 所有 autonomous decision-making 的基础

包含:
- Reward Shaping (结果量化)
- Preference Model (偏好建模)
- Tradeoff Engine (权衡决策)
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class OutcomeType(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    UNKNOWN = "unknown"


class TradeoffStrategy(Enum):
    """多目标冲突时的裁决策略"""
    UTILITY_SUM = "utility_sum"           # 效用总和最大化
    WEIGHTED_LINEAR = "weighted_linear"   # 加权线性组合
    PARETO = "pareto"                     # Pareto 最优
    MINIMAX = "minimax"                    # 最小化最大损失
    SATISFICING = "satisficing"           # 满足阈值即可


@dataclass
class UtilitySignal:
    """单一目标的效用信号"""
    dimension: str           # 目标维度名称
    raw_value: float         # 原始值
    normalized_value: float  # 归一化值 [0, 1]
    weight: float            # 权重
    utility: float           # 加权效用 = normalized * weight


@dataclass
class RewardShapingResult:
    """Reward Shaping 输出"""
    total_utility: float
    signals: List[UtilitySignal]
    outcome_type: OutcomeType
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class Preference:
    """用户/系统偏好"""
    dimension: str
    preference_type: str      # "higher_is_better" | "lower_is_better" | "target" | "range"
    weight: float
    target_value: Optional[float] = None
    min_acceptable: Optional[float] = None
    max_acceptable: Optional[float] = None
    learned_from: Optional[str] = None  # experience_id


@dataclass
class TradeoffResult:
    """Tradeoff Engine 输出"""
    chosen_option: str
    utility_scores: Dict[str, float]  # option_id -> score
    reasoning: str
    tradeoffs_made: List[str]
    confidence: float


@dataclass
class Decision:
    """最终决策"""
    decision_id: str
    context: Dict[str, Any]
    available_options: List[str]
    chosen_option: str
    expected_utility: float
    reasoning: str
    tradeoff_result: Optional[TradeoffResult]
    timestamp: str


class RewardShaper:
    """
    Reward Shaping: 原始结果 → 效用分数
    
    设计原则:
    - 归一化所有维度到 [0, 1]
    - 支持多种 scaling 函数
    - 处理 partial success
    """
    
    def __init__(self):
        self.scaling_functions: Dict[str, Callable] = {
            "linear": self._linear_scale,
            "exponential": self._exponential_scale,
            "logarithmic": self._logarithmic_scale,
            "sigmoid": self._sigmoid_scale,
            "step": self._step_scale,
        }
    
    def shape(self, 
              raw_outcomes: Dict[str, float],
              preferences: Dict[str, Preference]) -> RewardShapingResult:
        """
        主入口: 将原始结果根据偏好映射为效用分数
        
        Args:
            raw_outcomes: {dimension: raw_value}
            preferences: {dimension: Preference}
        
        Returns:
            RewardShapingResult
        """
        signals = []
        
        for dimension, raw_value in raw_outcomes.items():
            pref = preferences.get(dimension)
            if not pref:
                continue
            
            # 归一化
            normalized = self._normalize(raw_value, pref)
            
            # 计算加权效用
            utility = normalized * pref.weight
            
            signals.append(UtilitySignal(
                dimension=dimension,
                raw_value=raw_value,
                normalized_value=normalized,
                weight=pref.weight,
                utility=utility
            ))
        
        # 计算总效用
        total_utility = sum(s.utility for s in signals)
        
        # 判断 outcome 类型
        outcome_type = self._classify_outcome(signals, raw_outcomes)
        
        # 置信度
        confidence = self._compute_confidence(signals)
        
        return RewardShapingResult(
            total_utility=total_utility,
            signals=signals,
            outcome_type=outcome_type,
            confidence=confidence,
            metadata={"raw_outcomes": raw_outcomes}
        )
    
    def _normalize(self, value: float, pref: Preference) -> float:
        """根据偏好类型归一化"""
        if pref.preference_type == "higher_is_better":
            # 需要定义上界来归一化，这里用 sigmoid 近似
            return self._sigmoid_scale(value, midpoint=0.5, steepness=2.0)
        
        elif pref.preference_type == "lower_is_better":
            return 1.0 - self._sigmoid_scale(value, midpoint=0.5, steepness=2.0)
        
        elif pref.preference_type == "target":
            if pref.target_value is None:
                return 0.5
            deviation = abs(value - pref.target_value)
            max_deviation = (pref.max_acceptable or 1.0) - pref.target_value
            return max(0.0, 1.0 - deviation / max_deviation if max_deviation > 0 else 0.5)
        
        elif pref.preference_type == "range":
            if pref.min_acceptable is None or pref.max_acceptable is None:
                return 0.5
            if pref.min_acceptable <= value <= pref.max_acceptable:
                return 1.0
            elif value < pref.min_acceptable:
                return max(0.0, 1.0 - (pref.min_acceptable - value) / pref.min_acceptable)
            else:
                return max(0.0, 1.0 - (value - pref.max_acceptable) / pref.max_acceptable)
        
        return 0.5
    
    def _linear_scale(self, value: float, **kwargs) -> float:
        return max(0.0, min(1.0, value))
    
    def _exponential_scale(self, value: float, steepness: float = 2.0, **kwargs) -> float:
        return 1.0 - (1.0 / (1.0 + value * steepness))
    
    def _logarithmic_scale(self, value: float, **kwargs) -> float:
        import math
        return math.log(1 + value) / math.log(2) if value >= 0 else 0.0
    
    def _sigmoid_scale(self, value: float, midpoint: float = 0.5, steepness: float = 2.0, **kwargs) -> float:
        import math
        return 1.0 / (1.0 + math.exp(-steepness * (value - midpoint)))
    
    def _step_scale(self, value: float, threshold: float = 0.5, **kwargs) -> float:
        return 1.0 if value >= threshold else 0.0
    
    def _classify_outcome(self, signals: List[UtilitySignal], raw: Dict[str, float]) -> OutcomeType:
        if not signals:
            return OutcomeType.UNKNOWN
        
        # 检查是否有失败维度
        failed = [s for s in signals if s.normalized_value < 0.2]
        if any(failed):
            return OutcomeType.FAILURE
        
        # 检查是否有 partial
        partial = [s for s in signals if s.normalized_value < 0.6]
        if any(partial):
            return OutcomeType.PARTIAL
        
        return OutcomeType.SUCCESS
    
    def _compute_confidence(self, signals: List[UtilitySignal]) -> float:
        if not signals:
            return 0.0
        # 置信度基于信号的一致性
        normalizeds = [s.normalized_value for s in signals]
        mean = sum(normalizeds) / len(normalizeds)
        variance = sum((x - mean) ** 2 for x in normalizeds) / len(normalizeds)
        # 低方差 = 高置信度
        return max(0.0, 1.0 - variance * 2)


class PreferenceModel:
    """
    Preference Model: 偏好追踪 + 演化
    
    功能:
    - 存储多维度偏好
    - 从 feedback 学习偏好
    - 偏好演化追踪
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/utility/preferences"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        self.preferences: Dict[str, Preference] = {}
        self.preference_history: List[Dict[str, Any]] = []
        self._load_preferences()
    
    def _load_preferences(self):
        pref_file = os.path.join(self.storage_path, "preferences.json")
        if os.path.exists(pref_file):
            try:
                with open(pref_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.preferences = {k: Preference(**v) for k, v in data.items()}
            except:
                self.preferences = {}
        
        history_file = os.path.join(self.storage_path, "preference_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.preference_history = json.load(f)
            except:
                self.preference_history = []
    
    def _save_preferences(self):
        pref_file = os.path.join(self.storage_path, "preferences.json")
        with open(pref_file, 'w', encoding='utf-8') as f:
            json.dump({k: {
                "dimension": v.dimension,
                "preference_type": v.preference_type,
                "weight": v.weight,
                "target_value": v.target_value,
                "min_acceptable": v.min_acceptable,
                "max_acceptable": v.max_acceptable,
                "learned_from": v.learned_from
            } for k, v in self.preferences.items()}, f, ensure_ascii=False, indent=2)
        
        history_file = os.path.join(self.storage_path, "preference_history.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.preference_history[-100:], f, ensure_ascii=False, indent=2)
    
    def set_preference(self, dimension: str, preference: Preference) -> None:
        """显式设置偏好"""
        self.preferences[dimension] = preference
        self._record_change(dimension, "explicit_set")
        self._save_preferences()
    
    def update_from_feedback(self, 
                            dimension: str,
                            feedback: float,  # 0-1 反馈
                            experience_id: str = None) -> None:
        """
        从反馈学习偏好调整
        
        Args:
            dimension: 目标维度
            feedback: 用户反馈 [0, 1]
            experience_id: 来源 experience
        """
        if dimension not in self.preferences:
            # 创建新偏好
            self.preferences[dimension] = Preference(
                dimension=dimension,
                preference_type="higher_is_better",
                weight=0.5,
                learned_from=experience_id
            )
        
        pref = self.preferences[dimension]
        
        # 调整权重: 反馈高 → 权重增加
        if feedback > 0.7:
            pref.weight = min(1.0, pref.weight * 1.1)
        elif feedback < 0.3:
            pref.weight = max(0.1, pref.weight * 0.9)
        
        self._record_change(dimension, "feedback_learning", {"feedback": feedback})
        self._save_preferences()
    
    def update_from_outcome(self,
                           dimension: str,
                           actual_value: float,
                           outcome_type: OutcomeType,
                           experience_id: str = None) -> None:
        """
        从结果学习偏好调整
        """
        if dimension not in self.preferences:
            return
        
        pref = self.preferences[dimension]
        
        if outcome_type == OutcomeType.SUCCESS:
            # 成功强化权重
            pref.weight = min(1.0, pref.weight * 1.05)
        elif outcome_type == OutcomeType.FAILURE:
            # 失败降低权重
            pref.weight = max(0.1, pref.weight * 0.95)
        
        self._record_change(dimension, "outcome_learning", {
            "actual_value": actual_value,
            "outcome": outcome_type.value
        })
        self._save_preferences()
    
    def get_preference(self, dimension: str) -> Optional[Preference]:
        return self.preferences.get(dimension)
    
    def get_all_preferences(self) -> Dict[str, Preference]:
        return self.preferences.copy()
    
    def get_normalized_weights(self) -> Dict[str, float]:
        """获取归一化权重"""
        total = sum(p.weight for p in self.preferences.values())
        if total == 0:
            return {k: 1.0 / len(self.preferences) for k in self.preferences}
        return {k: v.weight / total for k, v in self.preferences.items()}
    
    def _record_change(self, dimension: str, reason: str, metadata: Dict = None):
        self.preference_history.append({
            "dimension": dimension,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })


class TradeoffEngine:
    """
    Tradeoff Engine: 多目标冲突裁决
    
    当多个目标冲突时，使用策略进行裁决
    """
    
    def __init__(self, strategy: TradeoffStrategy = TradeoffStrategy.WEIGHTED_LINEAR):
        self.strategy = strategy
    
    def resolve(self,
               options: List[str],
               utility_scores: Dict[str, List[UtilitySignal]],
               preferences: Dict[str, Preference]) -> TradeoffResult:
        """
        裁决冲突
        
        Args:
            options: 选项列表
            utility_scores: {option_id: [UtilitySignal]}
            preferences: {dimension: Preference}
        
        Returns:
            TradeoffResult
        """
        if len(options) == 1:
            return TradeoffResult(
                chosen_option=options[0],
                utility_scores={options[0]: sum(s.utility for s in utility_scores[options[0]])},
                reasoning="唯一选项",
                tradeoffs_made=[],
                confidence=1.0
            )
        
        if self.strategy == TradeoffStrategy.UTILITY_SUM:
            return self._utility_sum(options, utility_scores)
        elif self.strategy == TradeoffStrategy.WEIGHTED_LINEAR:
            return self._weighted_linear(options, utility_scores, preferences)
        elif self.strategy == TradeoffStrategy.PARETO:
            return self._pareto(options, utility_scores)
        elif self.strategy == TradeoffStrategy.MINIMAX:
            return self._minimax(options, utility_scores)
        elif self.strategy == TradeoffStrategy.SATISFICING:
            return self._satisficing(options, utility_scores, preferences)
        
        return self._weighted_linear(options, utility_scores, preferences)
    
    def _utility_sum(self, options, utility_scores) -> TradeoffResult:
        scores = {opt: sum(s.utility for s in signals) for opt, signals in utility_scores.items()}
        chosen = max(scores, key=scores.get)
        return TradeoffResult(
            chosen_option=chosen,
            utility_scores=scores,
            reasoning="效用总和最大化",
            tradeoffs_made=[],
            confidence=0.8
        )
    
    def _weighted_linear(self, options, utility_scores, preferences) -> TradeoffResult:
        scores = {}
        for opt, signals in utility_scores.items():
            total = sum(s.utility for s in signals)
            scores[opt] = total
        
        chosen = max(scores, key=scores.get)
        
        # 检测 tradeoffs
        tradeoffs = []
        sorted_opts = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_opts) > 1:
            diff = sorted_opts[0][1] - sorted_opts[1][1]
            if diff > 0.2:
                tradeoffs.append(f"首选 vs 次选差距: {diff:.2f}")
        
        return TradeoffResult(
            chosen_option=chosen,
            utility_scores=scores,
            reasoning="加权线性组合",
            tradeoffs_made=tradeoffs,
            confidence=0.75
        )
    
    def _pareto(self, options, utility_scores) -> TradeoffResult:
        # 找 Pareto 最优解
        pareto_optimal = []
        
        for i, opt1 in enumerate(options):
            signals1 = utility_scores[opt1]
            is_pareto = True
            for j, opt2 in enumerate(options):
                if i == j:
                    continue
                signals2 = utility_scores[opt2]
                # 如果 opt2 在所有维度都不比 opt1 差，且至少一个维度更好
                all_worse_or_equal = all(
                    s2.normalized_value >= s1.normalized_value 
                    for s1, s2 in zip(signals1, signals2)
                )
                some_better = any(
                    s2.normalized_value > s1.normalized_value 
                    for s1, s2 in zip(signals1, signals2)
                )
                if all_worse_or_equal and some_better:
                    is_pareto = False
                    break
            if is_pareto:
                pareto_optimal.append(opt1)
        
        if not pareto_optimal:
            pareto_optimal = options
        
        # 从 Pareto 最优中选效用最高的
        scores = {opt: sum(s.utility for s in utility_scores[opt]) for opt in pareto_optimal}
        chosen = max(scores, key=scores.get)
        
        return TradeoffResult(
            chosen_option=chosen,
            utility_scores={opt: sum(s.utility for s in utility_scores[opt]) for opt in options},
            reasoning=f"Pareto 最优 (候选: {len(pareto_optimal)})",
            tradeoffs_made=[f"Pareto 前沿: {pareto_optimal}"],
            confidence=0.85
        )
    
    def _minimax(self, options, utility_scores) -> TradeoffResult:
        # 最小化最大损失
        worst_case = {}
        for opt, signals in utility_scores.items():
            min_signal = min(signals, key=lambda s: s.normalized_value)
            worst_case[opt] = min_signal.normalized_value
        
        chosen = max(worst_case, key=worst_case.get)
        
        return TradeoffResult(
            chosen_option=chosen,
            utility_scores={opt: sum(s.utility for s in utility_scores[opt]) for opt in options},
            reasoning="最小化最大损失 (Minimax)",
            tradeoffs_made=[f"各选项最差情况: {worst_case}"],
            confidence=0.7
        )
    
    def _satisficing(self, options, utility_scores, preferences) -> TradeoffResult:
        # 满足阈值即可
        satisfactory = []
        thresholds = {}
        
        for dim, pref in preferences.items():
            if pref.preference_type == "target" and pref.target_value:
                thresholds[dim] = pref.target_value * 0.8  # 80% of target
            elif pref.min_acceptable:
                thresholds[dim] = pref.min_acceptable
        
        for opt, signals in utility_scores.items():
            meets_all = True
            for signal in signals:
                thresh = thresholds.get(signal.dimension, 0.5)
                if signal.normalized_value < thresh:
                    meets_all = False
                    break
            if meets_all:
                satisfactory.append(opt)
        
        if not satisfactory:
            satisfactory = options
        
        scores = {opt: sum(s.utility for s in utility_scores[opt]) for opt in satisfactory}
        chosen = max(scores, key=scores.get)
        
        return TradeoffResult(
            chosen_option=chosen,
            utility_scores={opt: sum(s.utility for s in utility_scores[opt]) for opt in options},
            reasoning=f"满足阈值 (满足数: {len(satisfactory)}/{len(options)})",
            tradeoffs_made=[],
            confidence=0.8
        )


class DecisionEngine:
    """
    Decision Engine: 整合所有组件做决策
    
    这是 Utility Function System 的主入口
    """
    
    def __init__(self, 
                 storage_path: str = None,
                 tradeoff_strategy: TradeoffStrategy = TradeoffStrategy.WEIGHTED_LINEAR):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/utility"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.reward_shaper = RewardShaper()
        self.preference_model = PreferenceModel(storage_path)
        self.tradeoff_engine = TradeoffEngine(strategy=tradeoff_strategy)
        
        self.decisions: List[Decision] = []
        self._load_decisions()
    
    def _load_decisions(self):
        decisions_file = os.path.join(self.storage_path, "decisions.json")
        if os.path.exists(decisions_file):
            try:
                with open(decisions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.decisions = [Decision(**d) for d in data]
            except:
                self.decisions = []
    
    def _save_decisions(self):
        decisions_file = os.path.join(self.storage_path, "decisions.json")
        with open(decisions_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "decision_id": d.decision_id,
                "context": d.context,
                "available_options": d.available_options,
                "chosen_option": d.chosen_option,
                "expected_utility": d.expected_utility,
                "reasoning": d.reasoning,
                "timestamp": d.timestamp
            } for d in self.decisions[-100:]], f, ensure_ascii=False, indent=2)
    
    def decide(self,
              context: Dict[str, Any],
              options: List[str],
              evaluate_fn: Callable[[str], Dict[str, float]],
              tradeoff_strategy: TradeoffStrategy = None) -> Decision:
        """
        主决策入口
        
        Args:
            context: 决策上下文
            options: 可选方案列表
            evaluate_fn: 评估函数, 输入 option, 输出 raw_outcomes
            tradeoff_strategy: 可选覆盖策略
        
        Returns:
            Decision
        """
        if len(options) == 1:
            chosen = options[0]
            raw_outcomes = evaluate_fn(chosen)
            preferences = self.preference_model.get_all_preferences()
            result = self.reward_shaper.shape(raw_outcomes, preferences)
            
            decision = Decision(
                decision_id=str(uuid.uuid4())[:12],
                context=context,
                available_options=options,
                chosen_option=chosen,
                expected_utility=result.total_utility,
                reasoning="唯一选项",
                tradeoff_result=None,
                timestamp=datetime.now().isoformat()
            )
            self.decisions.append(decision)
            self._save_decisions()
            return decision
        
        # 评估所有选项
        utility_scores = {}
        raw_outcomes_all = {}
        
        for option in options:
            raw_outcomes = evaluate_fn(option)
            raw_outcomes_all[option] = raw_outcomes
            preferences = self.preference_model.get_all_preferences()
            result = self.reward_shaper.shape(raw_outcomes, preferences)
            utility_scores[option] = result.signals
        
        # 权衡裁决
        engine = self.tradeoff_engine
        if tradeoff_strategy:
            engine = TradeoffEngine(strategy=tradeoff_strategy)
        
        tradeoff_result = engine.resolve(
            options, 
            utility_scores, 
            self.preference_model.get_all_preferences()
        )
        
        # 记录决策
        decision = Decision(
            decision_id=str(uuid.uuid4())[:12],
            context=context,
            available_options=options,
            chosen_option=tradeoff_result.chosen_option,
            expected_utility=tradeoff_result.utility_scores[tradeoff_result.chosen_option],
            reasoning=tradeoff_result.reasoning,
            tradeoff_result=tradeoff_result,
            timestamp=datetime.now().isoformat()
        )
        
        self.decisions.append(decision)
        self._save_decisions()
        
        return decision
    
    def record_outcome(self, decision_id: str, actual_outcomes: Dict[str, float]) -> None:
        """
        记录决策的实际结果, 用于学习
        """
        decision = next((d for d in self.decisions if d.decision_id == decision_id), None)
        if not decision:
            return
        
        preferences = self.preference_model.get_all_preferences()
        result = self.reward_shaper.shape(actual_outcomes, preferences)
        
        # 更新偏好
        for dimension, value in actual_outcomes.items():
            self.preference_model.update_from_outcome(
                dimension, value, result.outcome_type, decision_id
            )
    
    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [{
            "decision_id": d.decision_id,
            "chosen_option": d.chosen_option,
            "expected_utility": d.expected_utility,
            "reasoning": d.reasoning,
            "timestamp": d.timestamp
        } for d in self.decisions[-limit:]]
    
    def get_preference_summary(self) -> Dict[str, Any]:
        prefs = self.preference_model.get_all_preferences()
        return {
            "total_dimensions": len(prefs),
            "weights": {k: v.weight for k, v in prefs.items()},
            "normalized_weights": self.preference_model.get_normalized_weights()
        }


def create_utility_system(tradeoff_strategy: TradeoffStrategy = TradeoffStrategy.WEIGHTED_LINEAR) -> DecisionEngine:
    """工厂函数"""
    return DecisionEngine(tradeoff_strategy=tradeoff_strategy)

__exports__ = ['Decision', 'DecisionEngine', 'OutcomeType', 'Preference', 'PreferenceModel', 'RewardShaper', 'RewardShapingResult', 'TradeoffEngine', 'TradeoffResult', 'TradeoffStrategy', 'UtilitySignal', 'create_utility_system']


