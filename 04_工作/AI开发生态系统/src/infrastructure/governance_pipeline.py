#!/usr/bin/env python3
"""
Governance Pipeline - 治理管道
统一入口: 所有 agent / skill / executor 必须经过此入口

Step 1: global_governor.py (soft) - 全局软限制
Step 2: runtime_governor.py (hard) - 运行时硬约束
Step 3: GovernancePipeline - 统一调用入口
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading


# ========== Soft Governor (Global) ==========

class GovernorAction(Enum):
    ALLOW = "allow"
    THROTTLE = "throttle"
    BLOCK = "block"
    FORCE_DETERMINISTIC = "force_deterministic"


@dataclass
class GlobalGovernorConfig:
    max_recursion_depth: int = 5
    max_reflection_per_hour: int = 10
    max_self_mod_per_minute: int = 3
    ai_reasoning_ratio: float = 0.2
    oscillation_window: int = 30
    oscillation_threshold: int = 3


class OscillationDetector:
    def __init__(self, window: int = 30, threshold: int = 3):
        self.window = window
        self.threshold = threshold
        self.history: Dict[str, List[float]] = {}

    def record(self, action: str) -> bool:
        import time
        now = time.time()
        if action not in self.history:
            self.history[action] = []
        self.history[action] = [t for t in self.history[action] if now - t < self.window]
        self.history[action].append(now)
        return len(self.history[action]) >= self.threshold

    def is_oscillating(self) -> bool:
        return any(len(times) >= self.threshold for times in self.history.values())


class GlobalGovernor:
    """
    Global Execution Governor - 全局软限制
    80% deterministic / 20% AI reasoning
    限制递归深度、反射频率、防止振荡
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self, config: GlobalGovernorConfig = None):
        self.config = config or GlobalGovernorConfig()
        self.osc = OscillationDetector(self.config.oscillation_window, self.config.oscillation_threshold)
        self.recursion_stack: List[str] = []
        self.ai_count = 0
        self.det_count = 0
        self.reflection_count = 0
        self.last_reflection = None
        self.last_self_mod = None
        self.self_mod_count = 0

    @classmethod
    def get_instance(cls) -> 'GlobalGovernor':
        with cls._lock:
            if cls._instance is None:
                cls._instance = GlobalGovernor()
            return cls._instance

    def should_use_ai(self) -> bool:
        total = self.ai_count + self.det_count
        if total == 0:
            return True
        return (self.ai_count / total) < self.config.ai_reasoning_ratio

    def check_recursion(self, name: str) -> bool:
        if len(self.recursion_stack) >= self.config.max_recursion_depth:
            return False
        self.recursion_stack.append(name)
        return True

    def leave_recursion(self):
        if self.recursion_stack:
            self.recursion_stack.pop()

    def decide(self, action: str) -> GovernorAction:
        if self.osc.record(action):
            return GovernorAction.THROTTLE
        if len(self.recursion_stack) >= self.config.max_recursion_depth:
            return GovernorAction.BLOCK
        if not self.should_use_ai():
            self.det_count += 1
            return GovernorAction.FORCE_DETERMINISTIC
        self.ai_count += 1
        return GovernorAction.ALLOW

    def execute(self, ai_fn, det_fn, *args, **kwargs):
        if self.should_use_ai():
            self.ai_count += 1
            try:
                return ai_fn(*args, **kwargs)
            except:
                self.det_count += 1
                return det_fn(*args, **kwargs)
        else:
            self.det_count += 1
            return det_fn(*args, **kwargs)

    def get_status(self) -> Dict[str, Any]:
        return {
            "ratio": f"{self.config.ai_reasoning_ratio*100:.0f}% AI / {100-self.config.ai_reasoning_ratio*100:.0f}% Det",
            "counts": f"AI {self.ai_count} / Det {self.det_count}",
            "recursion": f"{len(self.recursion_stack)}/{self.config.max_recursion_depth}",
            "oscillating": self.osc.is_oscillating(),
            "type": "soft_global"
        }


# ========== Hard Governor (Runtime) ==========

class GateDecision(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    DEGRADE = "degrade"
    ROLLBACK = "rollback"


class ConstraintType(Enum):
    UTILITY_THRESHOLD = "utility_threshold"
    FAILURE_RATE = "failure_rate"
    RESOURCE_LIMIT = "resource_limit"
    TIME_LIMIT = "time_limit"
    DEPENDENCY_VIOLATION = "dependency_violation"
    RECURSION_DEPTH = "recursion_depth"
    POLICY_DRIFT = "policy_drift"


@dataclass
class HardConstraint:
    constraint_type: ConstraintType
    threshold: float
    severity: str  # "critical", "high", "medium"
    action_on_violation: GateDecision
    description: str


@dataclass
class ConstraintViolation:
    constraint_type: ConstraintType
    current_value: float
    threshold: float
    severity: str
    timestamp: str
    action_taken: GateDecision
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeGovernorDecision:
    decision_id: str
    action_id: str
    decision: GateDecision
    violations: List[ConstraintViolation]
    utility_score: float
    reasoning: str
    timestamp: str


class RuntimeConstraintEngine:
    def __init__(self):
        self.constraints = [
            HardConstraint(ConstraintType.UTILITY_THRESHOLD, 0.2, "critical", GateDecision.BLOCK,
                           "Utility低于20%立即阻止"),
            HardConstraint(ConstraintType.FAILURE_RATE, 0.3, "critical", GateDecision.ROLLBACK,
                           "失败率超过30%触发回滚"),
            HardConstraint(ConstraintType.RESOURCE_LIMIT, 0.9, "high", GateDecision.DEGRADE,
                           "资源使用超过90%降级执行"),
            HardConstraint(ConstraintType.TIME_LIMIT, 60000.0, "high", GateDecision.DEGRADE,
                           "执行超过60秒降级路径"),
            HardConstraint(ConstraintType.DEPENDENCY_VIOLATION, 0.0, "critical", GateDecision.BLOCK,
                           "依赖未满足立即阻止"),
            HardConstraint(ConstraintType.RECURSION_DEPTH, 5.0, "high", GateDecision.BLOCK,
                           "递归深度超过5阻止"),
            HardConstraint(ConstraintType.POLICY_DRIFT, 0.15, "high", GateDecision.DEGRADE,
                           "策略漂移超过15%降级执行"),
        ]

    def check_all(self, metrics: Dict[str, float]) -> List[ConstraintViolation]:
        violations = []
        for constraint in self.constraints:
            ct_str = constraint.constraint_type.value
            if ct_str in metrics:
                value = metrics[ct_str]
                if constraint.constraint_type in [ConstraintType.UTILITY_THRESHOLD,
                                                   ConstraintType.FAILURE_RATE,
                                                   ConstraintType.RECURSION_DEPTH,
                                                   ConstraintType.POLICY_DRIFT]:
                    is_violated = value < constraint.threshold
                else:
                    is_violated = value > constraint.threshold

                if is_violated:
                    violations.append(ConstraintViolation(
                        constraint_type=constraint.constraint_type,
                        current_value=value,
                        threshold=constraint.threshold,
                        severity=constraint.severity,
                        timestamp=datetime.now().isoformat(),
                        action_taken=constraint.action_on_violation,
                        context={}
                    ))
        return violations

    def evaluate(self, violations: List[ConstraintViolation]) -> GateDecision:
        if not violations:
            return GateDecision.ALLOW

        critical = [v for v in violations if v.severity == "critical"]
        if any(critical):
            for v in critical:
                if v.action_taken == GateDecision.ROLLBACK:
                    return GateDecision.ROLLBACK
                if v.action_taken == GateDecision.BLOCK:
                    return GateDecision.BLOCK
            return GateDecision.DEGRADE

        high = [v for v in violations if v.severity == "high"]
        if any(high):
            return GateDecision.DEGRADE

        return GateDecision.ALLOW


class RuntimeGovernor:
    """
    Runtime Governor - 运行时硬约束
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.engine = RuntimeConstraintEngine()
        self.decisions: List[RuntimeGovernorDecision] = []
        self.violations_history: List[ConstraintViolation] = []
        self.stats = {"total": 0, "allow": 0, "block": 0, "degrade": 0, "rollback": 0}

    @classmethod
    def get_instance(cls) -> 'RuntimeGovernor':
        with cls._lock:
            if cls._instance is None:
                cls._instance = RuntimeGovernor()
            return cls._instance

    def validate(self, action_id: str, metrics: Dict[str, float], context: Dict[str, Any] = None) -> RuntimeGovernorDecision:
        import uuid
        violations = self.engine.check_all(metrics)
        decision = self.engine.evaluate(violations)

        reasoning = self._build_reasoning(decision, violations)

        result = RuntimeGovernorDecision(
            decision_id=str(uuid.uuid4())[:12],
            action_id=action_id,
            decision=decision,
            violations=violations,
            utility_score=metrics.get(ConstraintType.UTILITY_THRESHOLD.value, 1.0),
            reasoning=reasoning,
            timestamp=datetime.now().isoformat()
        )

        self.decisions.append(result)
        self.violations_history.extend(violations)
        self.stats["total"] += 1

        if decision == GateDecision.ALLOW:
            self.stats["allow"] += 1
        elif decision == GateDecision.BLOCK:
            self.stats["block"] += 1
        elif decision == GateDecision.DEGRADE:
            self.stats["degrade"] += 1
        elif decision == GateDecision.ROLLBACK:
            self.stats["rollback"] += 1

        return result

    def _build_reasoning(self, decision: GateDecision, violations: List[ConstraintViolation]) -> str:
        if decision == GateDecision.ALLOW:
            return "所有约束检查通过"
        critical = [v for v in violations if v.severity == "critical"]
        if critical:
            return f"严重违规: {[v.constraint_type.value for v in critical]}"
        high = [v for v in violations if v.severity == "high"]
        if high:
            return f"高风险违规, 降级执行: {[v.constraint_type.value for v in high]}"
        return "未知决策"

    def get_status(self) -> Dict[str, Any]:
        total = self.stats["total"] if self.stats["total"] > 0 else 1
        return {
            "total_validations": self.stats["total"],
            "allow_rate": f"{self.stats['allow']/total*100:.1f}%",
            "block_rate": f"{self.stats['block']/total*100:.1f}%",
            "degrade_rate": f"{self.stats['degrade']/total*100:.1f}%",
            "rollback_rate": f"{self.stats['rollback']/total*100:.1f}%",
            "recent_violations": len(self.violations_history[-20:]),
            "type": "hard_runtime"
        }


# ========== Unified Governance Pipeline ==========

@dataclass
class GovernanceDecision:
    """统一治理决策"""
    action_id: str
    timestamp: str
    
    # Global Governor (Soft) 结果
    global_allowed: bool
    global_action: GovernorAction
    global_ratio: float
    global_recursion_depth: int
    global_oscillating: bool
    
    # Runtime Governor (Hard) 结果
    runtime_decision: GateDecision
    runtime_violations: List[str]
    runtime_reasoning: str
    
    # 最终决策
    final_allowed: bool
    final_decision: str  # "allow", "block", "degrade", "rollback"
    execution_path: str   # "full", "degraded", "safe", "blocked"
    reasoning: str
    
    def __str__(self) -> str:
        return (f"GovernanceDecision({self.action_id}): "
                f"global={'✓' if self.global_allowed else '✗'} | "
                f"runtime={self.runtime_decision.value} | "
                f"final={self.final_decision} | "
                f"path={self.execution_path}")


class GovernancePipeline:
    """
    Governance Pipeline - 统一治理入口
    
    所有 agent / skill / executor 必须经过此入口
    
    调用方式:
        result = governance.validate_action(
            action_id="build_001",
            action_type="build",
            utility=0.85,
            failure_rate=0.1,
            resource_usage=0.6,
            execution_time_ms=30000,
            recursion_depth=2,
            policy_drift=0.05
        )
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.global_governor = GlobalGovernor.get_instance()
        self.runtime_governor = RuntimeGovernor.get_instance()

    @classmethod
    def get_instance(cls) -> 'GovernancePipeline':
        with cls._lock:
            if cls._instance is None:
                cls._instance = GovernancePipeline()
            return cls._instance

    def validate_action(self,
                       action_id: str,
                       action_type: str = "unknown",
                       utility: float = 1.0,
                       failure_rate: float = 0.0,
                       resource_usage: float = 0.0,
                       execution_time_ms: int = 0,
                       recursion_depth: int = 0,
                       policy_drift: float = 0.0,
                       context: Dict[str, Any] = None) -> GovernanceDecision:
        """
        统一验证入口
        
        所有系统必须经过此方法
        """
        ctx = context or {}

        # Step 1: Global Governor (Soft) 评估
        global_action = self.global_governor.decide(action_id)
        global_allowed = global_action in [GovernorAction.ALLOW, GovernorAction.FORCE_DETERMINISTIC]

        # Step 2: Runtime Governor (Hard) 评估
        metrics = {
            ConstraintType.UTILITY_THRESHOLD.value: utility,
            ConstraintType.FAILURE_RATE.value: failure_rate,
            ConstraintType.RESOURCE_LIMIT.value: resource_usage,
            ConstraintType.TIME_LIMIT.value: float(execution_time_ms),
            ConstraintType.RECURSION_DEPTH.value: float(recursion_depth),
            ConstraintType.POLICY_DRIFT.value: policy_drift,
        }

        runtime_result = self.runtime_governor.validate(action_id, metrics, ctx)

        # Step 3: 综合最终决策
        final_allowed, final_decision, execution_path, reasoning = self._make_final_decision(
            global_allowed, global_action,
            runtime_result.decision, runtime_result.violations
        )

        return GovernanceDecision(
            action_id=action_id,
            timestamp=datetime.now().isoformat(),
            
            # Global
            global_allowed=global_allowed,
            global_action=global_action,
            global_ratio=self.global_governor.ai_count / max(1, self.global_governor.ai_count + self.global_governor.det_count),
            global_recursion_depth=len(self.global_governor.recursion_stack),
            global_oscillating=self.global_governor.osc.is_oscillating(),
            
            # Runtime
            runtime_decision=runtime_result.decision,
            runtime_violations=[v.constraint_type.value for v in runtime_result.violations],
            runtime_reasoning=runtime_result.reasoning,
            
            # Final
            final_allowed=final_allowed,
            final_decision=final_decision,
            execution_path=execution_path,
            reasoning=reasoning
        )

    def _make_final_decision(self,
                           global_allowed: bool,
                           global_action: GovernorAction,
                           runtime_decision: GateDecision,
                           runtime_violations: List[ConstraintViolation]) -> tuple[bool, str, str, str]:
        """
        综合软硬约束, 做出最终决策
        
        Returns:
            (final_allowed, final_decision, execution_path, reasoning)
        """

        # 1. Global 阻止 → 最终阻止
        if global_action == GovernorAction.BLOCK:
            return False, "block", "blocked", f"GlobalGovernor阻止: recursion或oscillation"

        # 2. Runtime Critical 阻止/回滚 → 最终阻止/回滚
        if runtime_decision == GateDecision.BLOCK:
            return False, "block", "blocked", f"RuntimeGovernor阻止: {runtime_violations}"

        if runtime_decision == GateDecision.ROLLBACK:
            return False, "rollback", "rollback", f"RuntimeGovernor触发回滚: {runtime_violations}"

        # 3. Runtime Degrade → 降级执行
        if runtime_decision == GateDecision.DEGRADE:
            return True, "degrade", "degraded", f"RuntimeGovernor降级: {runtime_violations}"

        # 4. Global Throttle → 降级执行
        if global_action == GovernorAction.THROTTLE:
            return True, "degrade", "degraded", "GlobalGovernor节流: oscillation检测"

        # 5. Global Force Deterministic → 强制确定性路径
        if global_action == GovernorAction.FORCE_DETERMINISTIC:
            return True, "allow", "deterministic", "GlobalGovernor强制确定性: AI比例超限"

        # 6. 全部允许 → 完全执行
        return True, "allow", "full", "所有检查通过"

    def can_proceed(self, action_id: str) -> tuple[bool, str]:
        """
        快速检查action是否可以继续
        """
        # 检查最近的 Runtime 决策
        for decision in reversed(self.runtime_governor.decisions):
            if decision.action_id == action_id:
                if decision.decision == GateDecision.BLOCK:
                    return False, f"blocked: {decision.reasoning}"
                if decision.decision == GateDecision.ROLLBACK:
                    return False, f"rollback: {decision.reasoning}"
                if decision.decision == GateDecision.DEGRADE:
                    return True, f"degraded: {decision.reasoning}"
                return True, "allowed"

        return True, "no prior decision, default allowed"

    def get_full_status(self) -> Dict[str, Any]:
        """获取完整治理状态"""
        return {
            "global_governor": self.global_governor.get_status(),
            "runtime_governor": self.runtime_governor.get_status(),
            "pipeline_type": "unified_governance"
        }

    def record_recursion(self, name: str) -> bool:
        """记录递归进入"""
        return self.global_governor.check_recursion(name)

    def leave_recursion(self):
        """记录递归退出"""
        self.global_governor.leave_recursion()

    def execute(self, action_id: str, ai_fn, det_fn, *args, **kwargs):
        """带治理的执行"""
        decision = self.validate_action(action_id)

        if not decision.final_allowed:
            raise RuntimeError(f"Action {action_id} blocked by governance: {decision.reasoning}")

        if decision.execution_path in ["deterministic", "degraded"]:
            return self.global_governor.execute(ai_fn, det_fn, *args, **kwargs)

        return ai_fn(*args, **kwargs)


# ========== 便捷函数 ==========

def get_governance() -> GovernancePipeline:
    """获取 Governance 单例"""
    return GovernancePipeline.get_instance()


def validate_action(action_id: str, **kwargs) -> GovernanceDecision:
    """快速验证 action (所有系统必须调用此函数)"""
    return get_governance().validate_action(action_id, **kwargs)


def can_proceed(action_id: str) -> tuple[bool, str]:
    """快速检查是否可以继续"""
    return get_governance().can_proceed(action_id)


# ========== 向后兼容 ==========

def governor() -> GlobalGovernor:
    """向后兼容: 返回 GlobalGovernor 单例"""
    return GlobalGovernor.get_instance()

__exports__ = ['ConstraintType', 'ConstraintViolation', 'GateDecision', 'GlobalGovernor', 'GlobalGovernorConfig', 'GovernanceDecision', 'GovernancePipeline', 'GovernorAction', 'HardConstraint', 'OscillationDetector', 'RuntimeConstraintEngine', 'RuntimeGovernor', 'RuntimeGovernorDecision', 'can_proceed', 'get_governance', 'governor', 'validate_action']


