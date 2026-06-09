#!/usr/bin/env python3
"""
Policy Update Engine - 策略更新引擎
P1: Learning from Experience 的正确实现

数据流:
    execution
      → utility evaluation
        → outcome comparison
          → delta analysis
            → policy update

核心组件:
    ① PatternExtractor    - 结构化模式提取
    ② PolicyUpdater       - 策略更新 (可回滚)
    ③ BiasStabilizer     - 偏差稳定器
    ④ LearningRateGovernor - 学习率控制
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import copy


class PolicyType(Enum):
    SKILL_USAGE = "skill_usage"
    AGENT_SELECTION = "agent_selection"
    PATH_CHOICE = "path_choice"
    RETRY_STRATEGY = "retry_strategy"
    RESOURCE_ALLOCATION = "resource_allocation"


class UpdateResult(Enum):
    APPLIED = "applied"
    THROTTLED = "throttled"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


@dataclass
class PolicyDelta:
    """策略变更记录"""
    feature: str
    delta: float
    context: str
    confidence: float
    sample_size: int
    variance: float


@dataclass
class PolicySnapshot:
    """策略快照 - 用于回滚"""
    snapshot_id: str
    timestamp: str
    policies: Dict[str, Any]
    reason: str


@dataclass
class PolicyUpdate:
    """策略更新记录"""
    update_id: str
    feature: str
    context: str
    delta: float
    previous_value: float
    new_value: float
    result: UpdateResult
    reason: str
    learning_rate: float
    timestamp: str


@dataclass
class Experience:
    """一次经验记录"""
    experience_id: str
    execution_id: str
    context: Dict[str, Any]
    action: str
    expected_utility: float
    actual_utility: float
    outcome_type: str
    duration_ms: int
    timestamp: str


@dataclass
class Pattern:
    """提取的结构化模式"""
    pattern_id: str
    pattern_type: str  # skill_success, path_stability, agent_reliability
    trigger_conditions: Dict[str, Any]
    success_indicators: Dict[str, float]
    frequency: int
    confidence: float
    policy_recommendations: List[Dict[str, Any]]


class LearningRateGovernor:
    """
    Learning Rate Governor
    
    policy_update_rate = f(variance, sample_size, confidence)
    
    防止:
    - 短期成功 → 错误强化
    - 偶然失败 → 全面换策略
    - 行为剧烈震荡
    """
    
    def __init__(self,
                 base_rate: float = 0.1,
                 min_samples: int = 5,
                 max_variance: float = 0.3,
                 confidence_threshold: float = 0.6):
        self.base_rate = base_rate
        self.min_samples = min_samples
        self.max_variance = max_variance
        self.confidence_threshold = confidence_threshold
    
    def compute_learning_rate(self,
                             variance: float,
                             sample_size: int,
                             confidence: float) -> float:
        """
        计算实际学习率
        
        公式: rate = base_rate * confidence * variance_penalty * sample_factor
        
        Returns:
            0.0 = 完全拒绝更新
            1.0 = 完全接受 (实际很少发生)
        """
        # 样本不足惩罚
        if sample_size < self.min_samples:
            sample_factor = sample_size / self.min_samples
        else:
            sample_factor = 1.0
        
        # 方差惩罚 (高方差 = 低学习率)
        if variance > self.max_variance:
            variance_penalty = self.max_variance / variance
        else:
            variance_penalty = 1.0
        
        # 置信度因子
        confidence_factor = max(0.0, min(1.0, confidence))
        
        rate = self.base_rate * confidence_factor * variance_penalty * sample_factor
        
        return max(0.0, min(self.base_rate, rate))
    
    def should_update(self,
                     variance: float,
                     sample_size: int,
                     confidence: float,
                     delta_magnitude: float) -> tuple[bool, float, str]:
        """
        判断是否应该更新
        
        Returns:
            (should_update, learning_rate, reason)
        """
        # 样本不足
        if sample_size < self.min_samples:
            reason = f"样本不足: {sample_size} < {self.min_samples}"
            return False, 0.0, reason
        
        # 方差过高
        if variance > self.max_variance * 2:
            reason = f"方差过高: {variance:.3f} > {self.max_variance * 2:.3f}"
            return False, 0.0, reason
        
        # 置信度过低
        if confidence < self.confidence_threshold:
            reason = f"置信度过低: {confidence:.2f} < {self.confidence_threshold}"
            return False, 0.0, reason
        
        # 计算学习率
        rate = self.compute_learning_rate(variance, sample_size, confidence)
        
        # 增量过大检查 (防止剧烈震荡)
        if delta_magnitude > 0.5 and rate < 0.05:
            reason = f"增量过大({delta_magnitude:.2f}) + 低学习率({rate:.3f})"
            return False, 0.0, reason
        
        return True, rate, "允许更新"


class BiasStabilizer:
    """
    Bias Stabilizer - 偏差稳定器
    
    防止:
    - 短期成功 → 错误强化
    - 偶然失败 → 错误惩罚
    - 近因偏差 (recency bias)
    - 幸存者偏差 (survivorship bias)
    """
    
    def __init__(self,
                 momentum: float = 0.7,
                 oscillation_window: int = 10,
                 oscillation_threshold: float = 0.4):
        self.momentum = momentum  # 动量: 70% 保留历史
        self.oscillation_window = oscillation_window
        self.oscillation_threshold = oscillation_threshold
        
        self.update_history: List[float] = []
        self.last_direction: Optional[str] = None
        self.direction_changes: int = 0
    
    def analyze_stability(self, recent_updates: List[float]) -> Dict[str, Any]:
        """
        分析最近更新是否稳定
        
        Returns:
            {
                "is_stable": bool,
                "oscillation_detected": bool,
                "direction": "increasing" | "decreasing" | "stable",
                "volatility": float
            }
        """
        if not recent_updates:
            return {
                "is_stable": True,
                "oscillation_detected": False,
                "direction": "stable",
                "volatility": 0.0
            }
        
        # 计算方向
        if len(recent_updates) >= 2:
            diffs = [recent_updates[i] - recent_updates[i-1] for i in range(1, len(recent_updates))]
            avg_diff = sum(diffs) / len(diffs)
            
            if avg_diff > 0.01:
                direction = "increasing"
            elif avg_diff < -0.01:
                direction = "decreasing"
            else:
                direction = "stable"
            
            # 检测震荡 (方向频繁变化)
            directions = ["up" if d > 0 else "down" if d < 0 else "flat" for d in diffs]
            changes = sum(1 for i in range(1, len(directions)) if directions[i] != directions[i-1])
            oscillation_detected = changes >= len(directions) * 0.5
            
            # 波动性
            volatility = sum(abs(d) for d in diffs) / len(diffs) if diffs else 0.0
        else:
            direction = "stable"
            oscillation_detected = False
            volatility = 0.0
        
        is_stable = not oscillation_detected and volatility < self.oscillation_threshold
        
        return {
            "is_stable": is_stable,
            "oscillation_detected": oscillation_detected,
            "direction": direction,
            "volatility": volatility,
            "recent_trend": recent_updates[-5:] if len(recent_updates) >= 5 else recent_updates
        }
    
    def apply_momentum(self, raw_delta: float, current_value: float) -> float:
        """
        应用动量, 防止剧烈变化
        
        new_delta = momentum * current_value + (1 - momentum) * raw_delta
        """
        return self.momentum * current_value + (1 - self.momentum) * raw_delta
    
    def check_direction_change(self, new_delta: float) -> bool:
        """检测方向变化"""
        current_direction = "up" if new_delta > 0 else "down" if new_delta < 0 else "flat"
        
        if self.last_direction and current_direction != self.last_direction:
            self.direction_changes += 1
        else:
            self.direction_changes = 0
        
        self.last_direction = current_direction
        
        # 频繁方向变化 = 震荡
        return self.direction_changes >= 3
    
    def should_apply_delta(self, 
                          raw_delta: float,
                          recent_updates: List[float],
                          current_value: float) -> tuple[bool, float, str]:
        """
        决定是否应用 delta
        
        Returns:
            (should_apply, adjusted_delta, reason)
        """
        # 检查震荡
        stability = self.analyze_stability(recent_updates)
        if stability["oscillation_detected"]:
            # 震荡中, 大幅降低更新幅度
            adjusted = raw_delta * 0.3
            return True, adjusted, "震荡检测: 降低更新幅度"
        
        # 检查方向变化
        if self.check_direction_change(raw_delta):
            adjusted = raw_delta * 0.5
            return True, adjusted, "方向变化检测: 降低更新幅度"
        
        # 应用动量
        adjusted = self.apply_momentum(raw_delta, current_value)
        
        return True, adjusted, "正常更新"


class PatternExtractor:
    """
    Pattern Extractor - 模式提取器
    
    从历史决策提取结构化模式:
    - 哪种 skill 更成功
    - 哪种路径更稳定
    - 哪种 agent 更可靠
    
    👉 不是总结, 是"结构化模式"
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/policy/patterns"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        self.patterns: Dict[str, Pattern] = {}
        self.experiences: List[Experience] = []
        self._load()
    
    def _load(self):
        patterns_file = os.path.join(self.storage_path, "patterns.json")
        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patterns = {k: Pattern(**v) for k, v in data.items()}
            except:
                self.patterns = {}
        
        exp_file = os.path.join(self.storage_path, "experiences.json")
        if os.path.exists(exp_file):
            try:
                with open(exp_file, 'r', encoding='utf-8') as f:
                    self.experiences = [Experience(**e) for e in json.load(f)]
            except:
                self.experiences = []
    
    def _save(self):
        patterns_file = os.path.join(self.storage_path, "patterns.json")
        with open(patterns_file, 'w', encoding='utf-8') as f:
            json.dump({k: {
                "pattern_id": v.pattern_id,
                "pattern_type": v.pattern_type,
                "trigger_conditions": v.trigger_conditions,
                "success_indicators": v.success_indicators,
                "frequency": v.frequency,
                "confidence": v.confidence,
                "policy_recommendations": v.policy_recommendations
            } for k, v in self.patterns.items()}, f, ensure_ascii=False, indent=2)
        
        exp_file = os.path.join(self.storage_path, "experiences.json")
        with open(exp_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "experience_id": e.experience_id,
                "execution_id": e.execution_id,
                "context": e.context,
                "action": e.action,
                "expected_utility": e.expected_utility,
                "actual_utility": e.actual_utility,
                "outcome_type": e.outcome_type,
                "duration_ms": e.duration_ms,
                "timestamp": e.timestamp
            } for e in self.experiences[-500:]], f, ensure_ascii=False, indent=2)
    
    def record_experience(self,
                         execution_id: str,
                         context: Dict[str, Any],
                         action: str,
                         expected_utility: float,
                         actual_utility: float,
                         outcome_type: str,
                         duration_ms: int) -> str:
        """记录一次经验"""
        exp_id = str(uuid.uuid4())[:12]
        exp = Experience(
            experience_id=exp_id,
            execution_id=execution_id,
            context=context,
            action=action,
            expected_utility=expected_utility,
            actual_utility=actual_utility,
            outcome_type=outcome_type,
            duration_ms=duration_ms,
            timestamp=datetime.now().isoformat()
        )
        self.experiences.append(exp)
        self._save()
        return exp_id
    
    def extract_skill_patterns(self, skill_name: str) -> Optional[Pattern]:
        """提取 skill 成功模式"""
        skill_exps = [e for e in self.experiences if e.action == skill_name]
        
        if len(skill_exps) < 3:
            return None
        
        successes = [e for e in skill_exps if e.outcome_type == "success"]
        avg_utility = sum(e.actual_utility for e in successes) / len(successes) if successes else 0
        
        # 分析触发条件
        contexts = [e.context for e in successes]
        common_contexts = self._find_common_contexts(contexts)
        
        return Pattern(
            pattern_id=str(uuid.uuid4())[:8],
            pattern_type="skill_success",
            trigger_conditions=common_contexts,
            success_indicators={
                "avg_utility": avg_utility,
                "success_rate": len(successes) / len(skill_exps),
                "sample_size": len(skill_exps)
            },
            frequency=len(skill_exps),
            confidence=min(1.0, len(skill_exps) / 10),
            policy_recommendations=[{
                "action": "increase_usage" if avg_utility > 0.7 else "decrease_usage",
                "weight_adjustment": (avg_utility - 0.5) * 0.2
            }]
        )
    
    def extract_path_patterns(self, path_name: str) -> Optional[Pattern]:
        """提取路径稳定性模式"""
        path_exps = [e for e in self.experiences if path_name in e.action]
        
        if len(path_exps) < 3:
            return None
        
        utilities = [e.actual_utility for e in path_exps]
        avg = sum(utilities) / len(utilities)
        variance = sum((u - avg) ** 2 for u in utilities) / len(utilities)
        
        successes = [e for e in path_exps if e.outcome_type == "success"]
        
        return Pattern(
            pattern_id=str(uuid.uuid4())[:8],
            pattern_type="path_stability",
            trigger_conditions={"path": path_name},
            success_indicators={
                "avg_utility": avg,
                "variance": variance,
                "success_rate": len(successes) / len(path_exps),
                "stability_score": 1.0 - min(1.0, variance * 2)
            },
            frequency=len(path_exps),
            confidence=min(1.0, len(path_exps) / 10),
            policy_recommendations=[{
                "action": "prefer" if variance < 0.1 else "caution",
                "stability_weight": 1.0 - variance
            }]
        )
    
    def extract_agent_patterns(self, agent_name: str) -> Optional[Pattern]:
        """提取 agent 可靠性模式"""
        agent_exps = [e for e in self.experiences if agent_name in e.action]
        
        if len(agent_exps) < 3:
            return None
        
        successes = [e for e in agent_exps if e.outcome_type == "success"]
        durations = [e.duration_ms for e in agent_exps]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return Pattern(
            pattern_id=str(uuid.uuid4())[:8],
            pattern_type="agent_reliability",
            trigger_conditions={"agent": agent_name},
            success_indicators={
                "success_rate": len(successes) / len(agent_exps),
                "avg_duration_ms": avg_duration,
                "reliability_score": len(successes) / len(agent_exps)
            },
            frequency=len(agent_exps),
            confidence=min(1.0, len(agent_exps) / 10),
            policy_recommendations=[{
                "action": "trust_more" if len(successes) / len(agent_exps) > 0.8 else "verify_outputs",
                "reliability_weight": len(successes) / len(agent_exps)
            }]
        )
    
    def run_extraction(self) -> List[Pattern]:
        """运行完整模式提取"""
        # 这个会在后台定期运行
        # 从 experiences 提取模式
        patterns = []
        
        # 这里需要从 context 解析出 skill/agent/path
        # 简化版本: 基于 action 名称模式匹配
        
        skill_names = set(e.action for e in self.experiences if e.action.startswith("skill:"))
        for skill in skill_names:
            p = self.extract_skill_patterns(skill)
            if p:
                patterns.append(p)
                self.patterns[p.pattern_id] = p
        
        path_names = set(e.action for e in self.experiences if "path" in e.action.lower())
        for path in path_names:
            p = self.extract_path_patterns(path)
            if p:
                patterns.append(p)
                self.patterns[p.pattern_id] = p
        
        agent_names = set(e.action for e in self.experiences if "agent:" in e.action)
        for agent in agent_names:
            p = self.extract_agent_patterns(agent)
            if p:
                patterns.append(p)
                self.patterns[p.pattern_id] = p
        
        self._save()
        return patterns
    
    def _find_common_contexts(self, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """找共同上下文特征"""
        if not contexts:
            return {}
        
        # 简化: 找所有 context 中相同的 key-value
        common = {}
        all_keys = set()
        for ctx in contexts:
            all_keys.update(ctx.keys())
        
        for key in all_keys:
            values = [ctx.get(key) for ctx in contexts if key in ctx]
            if values and all(v == values[0] for v in values):
                common[key] = values[0]
        
        return common
    
    def get_patterns_by_type(self, pattern_type: str) -> List[Pattern]:
        return [p for p in self.patterns.values() if p.pattern_type == pattern_type]
    
    def get_all_patterns(self) -> List[Pattern]:
        return list(self.patterns.values())


class PolicyUpdater:
    """
    Policy Updater - 策略更新器
    
    update_policy(
        feature="use_tdd",
        delta=+0.12,
        context="build_task"
    )
    
    👉 不是调整权重, 是策略更新
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/policy"
        )
        os.makedirs(self.storage_path, exist_ok=True)
        
        # 策略存储 {feature: {context: value}}
        self.policies: Dict[str, Dict[str, float]] = {}
        
        # 更新历史
        self.updates: List[PolicyUpdate] = []
        
        # 快照
        self.snapshots: List[PolicySnapshot] = []
        
        self._load()
    
    def _load(self):
        policies_file = os.path.join(self.storage_path, "policies.json")
        if os.path.exists(policies_file):
            try:
                with open(policies_file, 'r', encoding='utf-8') as f:
                    self.policies = json.load(f)
            except:
                self.policies = {}

        updates_file = os.path.join(self.storage_path, "updates.json")
        if os.path.exists(updates_file):
            try:
                with open(updates_file, 'r', encoding='utf-8') as f:
                    raw_updates = json.load(f)
                    self.updates = []
                    for u in raw_updates:
                        # Handle result as string (loaded from JSON) or Enum (in memory)
                        result_val = u.get("result", "applied")
                        if isinstance(result_val, str):
                            try:
                                result_val = UpdateResult(result_val)
                            except:
                                result_val = UpdateResult.APPLIED
                        u["result"] = result_val
                        self.updates.append(PolicyUpdate(**u))
            except Exception as e:
                self.updates = []

        snapshots_file = os.path.join(self.storage_path, "snapshots.json")
        if os.path.exists(snapshots_file):
            try:
                with open(snapshots_file, 'r', encoding='utf-8') as f:
                    self.snapshots = [PolicySnapshot(**s) for s in json.load(f)]
            except:
                self.snapshots = []
    
    def _save(self):
        policies_file = os.path.join(self.storage_path, "policies.json")
        with open(policies_file, 'w', encoding='utf-8') as f:
            json.dump(self.policies, f, ensure_ascii=False, indent=2)
        
        updates_file = os.path.join(self.storage_path, "updates.json")
        with open(updates_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "update_id": u.update_id,
                "feature": u.feature,
                "context": u.context,
                "delta": u.delta,
                "previous_value": u.previous_value,
                "new_value": u.new_value,
                "result": u.result.value if hasattr(u.result, 'value') else str(u.result),
                "reason": u.reason,
                "learning_rate": u.learning_rate,
                "timestamp": u.timestamp
            } for u in self.updates[-100:]], f, ensure_ascii=False, indent=2)
        
        snapshots_file = os.path.join(self.storage_path, "snapshots.json")
        with open(snapshots_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "snapshot_id": s.snapshot_id,
                "timestamp": s.timestamp,
                "policies": s.policies,
                "reason": s.reason
            } for s in self.snapshots[-20:]], f, ensure_ascii=False, indent=2)
    
    def get_policy(self, feature: str, context: str = "default") -> float:
        """获取策略值"""
        return self.policies.get(feature, {}).get(context, 0.5)
    
    def get_all_policies(self) -> Dict[str, Dict[str, float]]:
        return copy.deepcopy(self.policies)
    
    def update_policy(self,
                     feature: str,
                     delta: float,
                     context: str = "default",
                     learning_rate: float = 0.1,
                     bias_stabilizer: BiasStabilizer = None,
                     reason: str = "") -> PolicyUpdate:
        """
        更新策略
        
        Args:
            feature: 策略特征
            delta: 变化量
            context: 上下文
            learning_rate: 学习率
            bias_stabilizer: 偏差稳定器
            reason: 更新原因
        
        Returns:
            PolicyUpdate
        """
        update_id = str(uuid.uuid4())[:12]
        
        # 获取当前值
        if feature not in self.policies:
            self.policies[feature] = {}
        current_value = self.policies[feature].get(context, 0.5)
        
        # 获取最近更新历史用于稳定器
        recent_updates = [u.delta for u in self.updates[-10:] if u.feature == feature]
        
        # 应用偏差稳定器
        adjusted_delta = delta
        stabilizer_reason = ""
        if bias_stabilizer:
            should_apply, adjusted_delta, stabilizer_reason = bias_stabilizer.should_apply_delta(
                delta, recent_updates, current_value
            )
            if not should_apply:
                update = PolicyUpdate(
                    update_id=update_id,
                    feature=feature,
                    context=context,
                    delta=delta,
                    previous_value=current_value,
                    new_value=current_value,
                    result=UpdateResult.REJECTED,
                    reason=stabilizer_reason,
                    learning_rate=0.0,
                    timestamp=datetime.now().isoformat()
                )
                self.updates.append(update)
                self._save()
                return update
        
        # 应用学习率
        actual_delta = adjusted_delta * learning_rate
        
        # 计算新值 (clamp to [0, 1])
        new_value = max(0.0, min(1.0, current_value + actual_delta))
        
        # 记录更新
        result = UpdateResult.APPLIED if actual_delta != 0 else UpdateResult.THROTTLED
        if stabilizer_reason:
            result = UpdateResult.THROTTLED
        
        update = PolicyUpdate(
            update_id=update_id,
            feature=feature,
            context=context,
            delta=actual_delta,
            previous_value=current_value,
            new_value=new_value,
            result=result,
            reason=reason or stabilizer_reason or "normal_update",
            learning_rate=learning_rate,
            timestamp=datetime.now().isoformat()
        )
        
        self.updates.append(update)
        
        # 更新策略
        self.policies[feature][context] = new_value
        
        self._save()
        return update
    
    def create_snapshot(self, reason: str = "") -> str:
        """
        创建策略快照
        
        用于回滚
        """
        snapshot_id = str(uuid.uuid4())[:8]
        snapshot = PolicySnapshot(
            snapshot_id=snapshot_id,
            timestamp=datetime.now().isoformat(),
            policies=copy.deepcopy(self.policies),
            reason=reason
        )
        self.snapshots.append(snapshot)
        self._save()
        return snapshot_id
    
    def rollback_to_snapshot(self, snapshot_id: str) -> bool:
        """
        回滚到指定快照
        """
        snapshot = next((s for s in self.snapshots if s.snapshot_id == snapshot_id), None)
        if not snapshot:
            return False
        
        self.policies = copy.deepcopy(snapshot.policies)
        self._save()
        return True
    
    def rollback_latest(self, count: int = 1) -> bool:
        """
        回滚最近的 N 次更新
        """
        if len(self.updates) < count:
            return False
        
        # 获取要回滚到的状态
        target_update = self.updates[-(count + 1)] if len(self.updates) > count else self.updates[0]
        
        # 重建策略
        self.policies = {}
        for update in self.updates[:-(count)]:
            if update.result == UpdateResult.APPLIED:
                if update.feature not in self.policies:
                    self.policies[update.feature] = {}
                self.policies[update.feature][update.context] = update.new_value
        
        self._save()
        return True
    
    def get_update_history(self, feature: str = None, limit: int = 20) -> List[PolicyUpdate]:
        if feature:
            return [u for u in self.updates if u.feature == feature][-limit:]
        return self.updates[-limit:]
    
    def diff_snapshots(self, snapshot_id1: str, snapshot_id2: str) -> Dict[str, Any]:
        """对比两个快照的差异"""
        s1 = next((s for s in self.snapshots if s.snapshot_id == snapshot_id1), None)
        s2 = next((s for s in self.snapshots if s.snapshot_id == snapshot_id2), None)
        
        if not s1 or not s2:
            return {}
        
        diff = {
            "added": [],
            "removed": [],
            "changed": []
        }
        
        all_features = set(s1.policies.keys()) | set(s2.policies.keys())
        
        for feature in all_features:
            if feature not in s1.policies:
                diff["added"].append(feature)
            elif feature not in s2.policies:
                diff["removed"].append(feature)
            else:
                ctx1 = s1.policies[feature]
                ctx2 = s2.policies[feature]
                
                all_contexts = set(ctx1.keys()) | set(ctx2.keys())
                for ctx in all_contexts:
                    if ctx not in ctx1:
                        diff["added"].append(f"{feature}/{ctx}")
                    elif ctx not in ctx2:
                        diff["removed"].append(f"{feature}/{ctx}")
                    elif ctx1[ctx] != ctx2[ctx]:
                        diff["changed"].append({
                            "feature": feature,
                            "context": ctx,
                            "old": ctx1[ctx],
                            "new": ctx2[ctx]
                        })
        
        return diff


class PolicyUpdateEngine:
    """
    Policy Update Engine - 整合所有组件的主引擎
    
    数据流:
        execution
          → utility evaluation
            → outcome comparison
              → delta analysis
                → policy update
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser(
            "~/.claude/projects/-mnt-c-Users-Admin/policy"
        )
        
        self.pattern_extractor = PatternExtractor(storage_path)
        self.policy_updater = PolicyUpdater(storage_path)
        self.bias_stabilizer = BiasStabilizer()
        self.learning_rate_governor = LearningRateGovernor()
    
    def process_experience(self,
                          execution_id: str,
                          context: Dict[str, Any],
                          action: str,
                          expected_utility: float,
                          actual_utility: float,
                          outcome_type: str,
                          duration_ms: int) -> PolicyUpdate:
        """
        处理一次经验
        
        主入口
        """
        # 1. 记录经验
        exp_id = self.pattern_extractor.record_experience(
            execution_id, context, action,
            expected_utility, actual_utility,
            outcome_type, duration_ms
        )
        
        # 2. 计算 delta
        delta = actual_utility - expected_utility
        
        # 3. 方差分析 (使用该 action 的历史)
        recent_same_action = [
            e for e in self.pattern_extractor.experiences
            if e.action == action
        ][-10:]  # 最近 10 次
        
        if len(recent_same_action) > 1:
            utilities = [e.actual_utility for e in recent_same_action]
            mean = sum(utilities) / len(utilities)
            variance = sum((u - mean) ** 2 for u in utilities) / len(utilities)
            confidence = 1.0 - min(1.0, variance * 2)
            sample_size = len(recent_same_action)
        else:
            variance = 0.0
            confidence = 0.5
            sample_size = 1
        
        # 4. Learning Rate Governor 决策
        should_update, learning_rate, reason = self.learning_rate_governor.should_update(
            variance, sample_size, confidence, abs(delta)
        )
        
        if not should_update:
            # 创建拒绝更新记录
            return self.policy_updater.update_policy(
                feature=action,
                delta=delta,
                context=context.get("task_type", "default"),
                learning_rate=0.0,
                reason=reason
            )
        
        # 5. Policy Updater 更新
        update = self.policy_updater.update_policy(
            feature=action,
            delta=delta,
            context=context.get("task_type", "default"),
            learning_rate=learning_rate,
            bias_stabilizer=self.bias_stabilizer,
            reason=f"experience: {exp_id}"
        )
        
        return update
    
    def extract_all_patterns(self) -> List[Pattern]:
        """运行完整模式提取"""
        return self.pattern_extractor.run_extraction()
    
    def create_learning_snapshot(self, reason: str = "") -> str:
        """创建学习快照"""
        return self.policy_updater.create_snapshot(reason)
    
    def rollback_learning(self, snapshot_id: str = None, count: int = None) -> bool:
        """回滚学习"""
        if snapshot_id:
            return self.policy_updater.rollback_to_snapshot(snapshot_id)
        elif count:
            return self.policy_updater.rollback_latest(count)
        return False
    
    def get_learning_status(self) -> Dict[str, Any]:
        """获取学习系统状态"""
        patterns = self.pattern_extractor.get_all_patterns()
        recent_updates = self.policy_updater.get_update_history(limit=10)
        
        # 稳定性分析
        recent_deltas = [u.delta for u in recent_updates]
        stability = self.bias_stabilizer.analyze_stability(recent_deltas)
        
        return {
            "total_patterns": len(patterns),
            "patterns_by_type": {
                "skill": len([p for p in patterns if p.pattern_type == "skill_success"]),
                "path": len([p for p in patterns if p.pattern_type == "path_stability"]),
                "agent": len([p for p in patterns if p.pattern_type == "agent_reliability"])
            },
            "total_updates": len(self.policy_updater.updates),
            "recent_updates": len(recent_updates),
            "stability": stability,
            "total_snapshots": len(self.policy_updater.snapshots)
        }


def create_policy_update_engine() -> PolicyUpdateEngine:
    """工厂函数"""
    return PolicyUpdateEngine()

__exports__ = ['BiasStabilizer', 'Experience', 'LearningRateGovernor', 'Pattern', 'PatternExtractor', 'PolicyDelta', 'PolicySnapshot', 'PolicyType', 'PolicyUpdate', 'PolicyUpdateEngine', 'PolicyUpdater', 'UpdateResult', 'create_policy_update_engine']


