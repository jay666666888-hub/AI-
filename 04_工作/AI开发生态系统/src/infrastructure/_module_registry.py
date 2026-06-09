#!/usr/bin/env python3
"""
Infrastructure Module Registry - SSOT (Single Source of Truth)
所有基础设施模块的 export 清单
禁止在 __init__.py 中手动猜测，必须由此文件生成
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ModuleExports:
    module_name: str
    exports: List[str]
    description: str


INFRASTRUCTURE_MODULES: Dict[str, ModuleExports] = {

    # ===== Core =====
    "monitor": ModuleExports(
        module_name="monitor",
        exports=["Monitor"],
        description="监控告警模块"
    ),
    "container": ModuleExports(
        module_name="container",
        exports=["ContainerManager"],
        description="容器化管理"
    ),
    "deploy": ModuleExports(
        module_name="deploy",
        exports=["Deployer"],
        description="部署自动化"
    ),

    # ===== P0: Utility Function System =====
    "utility_function": ModuleExports(
        module_name="utility_function",
        exports=[
            "RewardShaper",
            "PreferenceModel",
            "TradeoffEngine",
            "DecisionEngine",
            "OutcomeType",
            "create_utility_system",
            # Internal
            "RewardShapingResult",
            "TradeoffResult",
            "TradeoffStrategy",
            "UtilitySignal",
            "Preference",
            "Decision",
        ],
        description="P0: Utility Function System - 奖励塑形、偏好模型、决策引擎"
    ),

    # ===== P1: Policy Update Engine =====
    "policy_update_engine": ModuleExports(
        module_name="policy_update_engine",
        exports=[
            "PatternExtractor",
            "PolicyUpdater",
            "BiasStabilizer",
            "LearningRateGovernor",
            "PolicyUpdate",
            "UpdateResult",
            "create_policy_update_engine",
            # Internal
            "Experience",
            "PolicySnapshot",
            "PolicyDelta",
            "PolicyType",
        ],
        description="P1: Policy Update Engine - 模式提取、策略更新、偏置稳定"
    ),

    # ===== P2-lite: Long-horizon Autonomy =====
    "long_horizon_autonomy": ModuleExports(
        module_name="long_horizon_autonomy",
        exports=[
            "GoalGenerator",
            "GoalPrioritizer",
            "Scheduler",
            "AutonomyGovernor",
            "LongHorizonAutonomy",
            "Quota",
            "QuotaType",
            "GoalCategory",
            "create_long_horizon_autonomy",
            # Internal
            "Goal",
            "GoalStatus",
            "AutonomyMetrics",
        ],
        description="P2-lite: Long-horizon Autonomy - 受限目标生成、优先级调度"
    ),

    # ===== Governance Pipeline =====
    "governance_pipeline": ModuleExports(
        module_name="governance_pipeline",
        exports=[
            "GovernancePipeline",
            "GovernanceDecision",
            "GlobalGovernor",
            "RuntimeGovernor",
            "GovernorAction",
            "GateDecision",
            "ConstraintType",
            "get_governance",
            "validate_action",
            "can_proceed",
            # Internal
            "ConstraintViolation",
            "HardConstraint",
            "RuntimeConstraintEngine",
            "RuntimeGovernorDecision",
        ],
        description="Governance Pipeline - 统一入口、软硬双层治理"
    ),

    # ===== Stabilization =====
    "stabilization": ModuleExports(
        module_name="stabilization",
        exports=[
            "StabilizationEngine",
            "create_stabilization_engine",
            "SystemFreezeTest",
            "SystemHealth",
            "FreezeTestResult",
            # Internal
            "DriftEvent",
            "DriftMonitor",
            "DriftType",
            "FailureMode",
            "FailureModeMap",
        ],
        description="Stabilization Engine - 稳定化引擎、系统健康检查"
    ),

    "system_compression": ModuleExports(
        module_name="system_compression",
        exports=[
            "SystemCompressor",
            "CoreLoopConfig",
            "UnifiedPath",
            "PathMerger",
            "DecisionGraphSimplifier",
            "create_system_compressor",
            # Internal
            "MutationPermission",
            "PathType",
            "PolicyMutationSurface",
        ],
        description="System Compressor - 系统压缩、核心循环提取"
    ),

    "behavior_locking": ModuleExports(
        module_name="behavior_locking",
        exports=[
            "BehaviorLock",
            "ArchitectureLock",
            "ParameterLock",
            "LockType",
            "LockValidationResult",
            "create_behavior_lock",
            # Internal
            "LockedComponent",
            "ParameterSnapshot",
        ],
        description="Behavior Locking - 行为锁定、参数冻结"
    ),

    "long_run_simulation": ModuleExports(
        module_name="long_run_simulation",
        exports=[
            "LongRunSimulator",
            "SimulationResult",
            "SystemState",
            "UtilityMetrics",
            "PolicyDriftMetrics",
            "GoalEntropyMetrics",
            "LoopMetrics",
            "create_long_run_simulator",
            # Internal
            "UtilityStabilityAnalyzer",
            "PolicyDriftAnalyzer",
            "GoalEntropyAnalyzer",
            "LoopBehaviorAnalyzer",
            "TrendDirection",
        ],
        description="Long-run Simulation - 长期模拟、漂移预测"
    ),

    # ===== Tracing & Compilation =====
    "execution_trace": ModuleExports(
        module_name="execution_trace",
        exports=[
            "ExecutionTracer",
            "TraceNode",
            "CausalEdge",
            "DecisionReplay",
            "TraceNodeType",
            "create_execution_tracer",
        ],
        description="Execution Trace System - 执行追踪、因果图、决策回放"
    ),

    "policy_compiler": ModuleExports(
        module_name="policy_compiler",
        exports=[
            "PolicyCompiler",
            "CompiledNode",
            "CompiledEdge",
            "EdgeType",
            "ExecutionGraph",
            "NodeType",
            "PolicyRule",
            "create_policy_compiler",
        ],
        description="Policy Compiler - 策略编译为可执行图"
    ),

    "simulation_sandbox": ModuleExports(
        module_name="simulation_sandbox",
        exports=[
            "SimulationSandbox",
            "DriftPrediction",
            "SandboxEnvironment",
            "SimulationSnapshot",
            "SimulationState",
            "StressTestReport",
            "StressTestResult",
            "create_simulation_sandbox",
        ],
        description="Simulation Sandbox - 沙箱模拟、压力测试"
    ),

    # ===== Invariants & Learning =====
    "invariant_engine": ModuleExports(
        module_name="invariant_engine",
        exports=[
            "SystemInvariantEngine",
            "Invariant",
            "InvariantViolation",
            "InvariantType",
            "ViolationSeverity",
            "create_invariant_engine",
            # Internal
            "InvariantStatus",
        ],
        description="System Invariant Engine - 系统不变量、防悄悄变坏"
    ),

    "causal_learning": ModuleExports(
        module_name="causal_learning",
        exports=[
            "CausalLearningLayer",
            "CausalGraphBuilder",
            "CausalEdge",
            "CausalInsight",
            "create_causal_learning_layer",
            # Internal
            "CausalPath",
            "CausalRelationship",
            "PolicyUpdateFromCausal",
        ],
        description="Causal Learning Layer - 因果学习、过滤伪相关"
    ),

    "meta_controller": ModuleExports(
        module_name="meta_controller",
        exports=[
            "MetaController",
            "ControllerMode",
            "StrictnessLevel",
            "GovernanceStrengthAdapter",
            "ExplorationSafetyBalancer",
            "create_meta_controller",
            # Internal
            "ControllerConfig",
            "ControllerState",
            "AdaptationAction",
        ],
        description="Meta Controller - 元控制、治理强度自适应"
    ),

    # ===== Execution Support =====
    "retry_engine": ModuleExports(
        module_name="retry_engine",
        exports=[
            "RetryEngine",
            "RetryConfig",
            "RetryResult",
            "get_retry_engine",
            # Internal
            "RetryStrategy",
            "CircuitBreaker",
            "CircuitBreakerConfig",
            "CircuitBreakerState",
            "CircuitBreakerOpenError",
        ],
        description="Retry Engine - 重试引擎、熔断器"
    ),

    "state_recovery": ModuleExports(
        module_name="state_recovery",
        exports=[
            "Checkpoint",
            "get_state_manager",
            # Internal
            "RecoveryManager",
            "StateManager",
            "CheckpointStatus",
        ],
        description="State Recovery - 状态恢复、检查点管理"
    ),

    "transaction": ModuleExports(
        module_name="transaction",
        exports=[
            "TransactionStatus",
            "create_transaction",
            # Internal
            "TransactionContext",
            "TransactionRecord",
            "FileSnapshot",
            "RollbackRegistry",
        ],
        description="Transaction Manager - 事务管理、回滚注册"
    ),

    "self_healer": ModuleExports(
        module_name="self_healer",
        exports=[
            "SelfHealer",
            "run_self_healing",
            # Internal
            "HealthIssue",
            "HealthLevel",
            "HealthReport",
        ],
        description="Self Healer - 自修复、自维护"
    ),

    "partial_success": ModuleExports(
        module_name="partial_success",
        exports=[
            "PartialSuccessHandler",
            "StageResult",
            "StageStatus",
            "PipelineResult",
        ],
        description="Partial Success Handler - 部分成功处理链"
    ),

    # ===== Reflection & Goals =====
    "reflection_engine": ModuleExports(
        module_name="reflection_engine",
        exports=[
            "ReflectionEngine",
            "Reflection",
            "ReflectionLevel",
            "Pattern",
        ],
        description="Reflection Engine - 反思引擎、模式识别"
    ),

    "goal_system": ModuleExports(
        module_name="goal_system",
        exports=[
            "GoalScheduler",
            "Goal",
            "GoalStatus",
            "GoalPriority",
            "SubGoal",
            "create_goal_system",
        ],
        description="Goal System - 目标管理、优先级调度"
    ),
}


def get_all_public_exports() -> List[str]:
    """获取所有公开 export（不含 Internal 标记的）"""
    public = []
    for mod in INFRASTRUCTURE_MODULES.values():
        public.extend([e for e in mod.exports if not e.startswith("_")])
    return sorted(set(public))


def verify_module_exports(module_name: str) -> Dict[str, any]:
    """
    验证模块的 export 是否与 registry 一致
    Returns: {"valid": bool, "missing": [], "extra": [], "errors": []}
    """
    import sys
    sys.path.insert(0, "/mnt/e/黑曜石/04_工作/AI开发生态系统/src/infrastructure")

    result = {"valid": True, "missing": [], "extra": [], "errors": []}

    if module_name not in INFRASTRUCTURE_MODULES:
        result["valid"] = False
        result["errors"].append(f"Module '{module_name}' not found in registry")
        return result

    expected = set(INFRASTRUCTURE_MODULES[module_name].exports)

    try:
        mod = __import__(module_name, fromlist=["*"])
        actual_names = [n for n in dir(mod) if not n.startswith("_")]
        actual = set(actual_names)
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Import error: {e}")
        return result

    # Check missing (in registry but not in module)
    missing = expected - actual
    if missing:
        result["valid"] = False
        result["missing"] = sorted(missing)

    # Check extra (in module but not in registry, excluding private)
    # Allow module-level functions/classes not in registry for flexibility
    extra = actual - expected
    result["extra"] = sorted(extra) if extra else []

    return result


def generate_init_content() -> str:
    """生成 __init__.py 内容"""
    lines = [
        '"""',
        "基础设施层 (Infrastructure)",
        "包含: 监控告警, 容器化, 向量搜索/RAG, 部署自动化",
        '"""',
        "",
        "from .monitor import Monitor",
        "from .container import ContainerManager",
        "from .deploy import Deployer",
        "",
    ]

    # Group by category
    categories = {
        "P0: Utility Function System": ["utility_function"],
        "P1: Policy Update Engine": ["policy_update_engine"],
        "P2-lite: Long-horizon Autonomy": ["long_horizon_autonomy"],
        "Governance Pipeline": ["governance_pipeline"],
        "Stabilization": ["stabilization", "system_compression", "behavior_locking", "long_run_simulation"],
        "Tracing & Compilation": ["execution_trace", "policy_compiler", "simulation_sandbox"],
        "Invariants & Learning": ["invariant_engine", "causal_learning", "meta_controller"],
        "Execution Support": ["retry_engine", "state_recovery", "transaction", "self_healer", "partial_success"],
        "Reflection & Goals": ["reflection_engine", "goal_system"],
    }

    for category, modules in categories.items():
        lines.append(f"# ===== {category} =====")
        for mod_name in modules:
            if mod_name not in INFRASTRUCTURE_MODULES:
                continue
            mod = INFRASTRUCTURE_MODULES[mod_name]
            imports = [f"    {e}" for e in mod.exports if not e.startswith("_")]
            if imports:
                lines.append(f"from .{mod_name} import (")
                lines.append(",\n".join(imports))
                lines.append(")")
                lines.append("")
        lines.append("")

    # Generate __all__
    all_exports = get_all_public_exports()
    lines.append("__all__ = [")
    for exp in all_exports:
        lines.append(f'    "{exp}",')
    lines.append("]")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/mnt/e/黑曜石/04_工作/AI开发生态系统/src/infrastructure")

    print("=" * 60)
    print("SSOT Module Registry - Validation Report")
    print("=" * 60)

    all_valid = True
    for module_name in INFRASTRUCTURE_MODULES:
        result = verify_module_exports(module_name)
        status = "✓" if result["valid"] else "✗"
        print(f"\n{status} {module_name}")

        if result["missing"]:
            print(f"    MISSING in module: {result['missing']}")
            all_valid = False
        if result["extra"]:
            print(f"    EXTRA in module (not in registry): {result['extra']}")
        if result["errors"]:
            print(f"    ERRORS: {result['errors']}")
            all_valid = False

    print("\n" + "=" * 60)
    if all_valid:
        print("✓ ALL MODULES VALID - Registry matches actual exports")
    else:
        print("✗ VALIDATION FAILED - Fix missing items before proceeding")
        sys.exit(1)