#!/usr/bin/env python3
"""
Telemetry Hooks - 自动采集真实轨迹
将 hooks 插入现有系统，自动记录 telemetry

用法：
from telemetry_hooks import attach_hooks, telemetry_hook

# 在关键函数前加 @telemetry_hook 即可自动记录
@telemetry_hook("routing")
def select_agent(task):
    ...
"""
from functools import wraps
from typing import Callable, Any, Optional, List, Dict
from datetime import datetime

# 全局 hook 配置
_HOOKS_ENABLED = True
_HOOK_CONTEXT = {}


def set_hook_context(**kwargs):
    """设置 hook 上下文（task_id, agent_id 等）"""
    _HOOK_CONTEXT.update(kwargs)


def get_hook_context() -> Dict[str, Any]:
    return _HOOK_CONTEXT.copy()


def telemetry_hook(event_type: str, extract_fields: Callable = None):
    """
    装饰器：为函数自动添加 telemetry 记录
    
    @telemetry_hook("routing")
    def select_agent(task_id, context):
        ...
    
    自动记录：
    - event_type
    - timestamp
    - 函数参数
    - 返回值
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not _HOOKS_ENABLED:
                return func(*args, **kwargs)
            
            start = datetime.now()
            context = get_hook_context()
            
            # 调用原函数
            result = func(*args, **kwargs)
            
            end = datetime.now()
            duration_ms = int((end - start).total_seconds() * 1000)
            
            # 提取字段
            fields = {}
            if extract_fields:
                fields = extract_fields(*args, **kwargs, result=result)
            else:
                # 默认提取
                fields = {
                    'function': func.__name__,
                    'args': str(args)[:100],
                    'kwargs': str(kwargs)[:100],
                    'result': str(result)[:100] if result else None,
                }
            
            # 获取 logger 并记录
            try:
                from execution_logger import get_logger
                logger = get_logger()
                
                ctx = get_hook_context()
                task_id = ctx.get('task_id', 'unknown')
                agent_id = ctx.get('agent_id', 'unknown')
                
                if event_type == "routing":
                    logger.log_routing(
                        task_id=task_id,
                        agent=result if result else 'unknown',
                        context=fields.get('context', ''),
                        metadata=fields
                    )
                elif event_type == "utility":
                    logger.log_utility_eval(
                        task_id=task_id,
                        agent=agent_id,
                        utility_inputs=fields.get('inputs', []),
                        utility_output=fields.get('output', 0.0),
                        metadata=fields
                    )
                elif event_type == "governance":
                    logger.log_governance(
                        task_id=task_id,
                        agent=agent_id,
                        decision=fields.get('decision', 'unknown'),
                        metadata=fields
                    )
                elif event_type == "execution":
                    logger.log_execution(
                        action_id=task_id,
                        path=fields.get('path', [])
                    )
                    
            except Exception as e:
                # 不要因为 telemetry 而影响主流程
                pass
            
            return result
        return wrapper
    return decorator


class TelemetryContext:
    """Telemetry 上下文管理器"""
    
    def __init__(self, task_id: str, agent_id: str = None, metadata: Dict = None):
        self.task_id = task_id
        self.agent_id = agent_id
        self.metadata = metadata or {}
        self._previous_context = {}
    
    def __enter__(self):
        self._previous_context = _HOOK_CONTEXT.copy()
        set_hook_context(
            task_id=self.task_id,
            agent_id=self.agent_id,
            metadata=self.metadata
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _HOOK_CONTEXT
        _HOOK_CONTEXT = self._previous_context
        return False
    
    def update(self, **kwargs):
        _HOOK_CONTEXT.update(kwargs)


def attach_hooks(obj: Any, method_name: str, event_type: str):
    """
    将 telemetry hook 附加到对象的现有方法
    
    用法：
    attach_hooks(orchestrator, 'select_agent', 'routing')
    attach_hooks(orchestrator, 'evaluate_utility', 'utility')
    """
    original_method = getattr(obj, method_name)
    
    @wraps(original_method)
    def hooked(*args, **kwargs):
        context = get_hook_context()
        task_id = context.get('task_id', 'unknown')
        
        result = original_method(*args, **kwargs)
        
        try:
            from execution_logger import get_logger
            logger = get_logger()
            
            if event_type == "routing" and result:
                logger.log_routing(
                    task_id=task_id,
                    agent=result,
                    context=method_name,
                    metadata={'method': method_name}
                )
        except:
            pass
        
        return result
    
    setattr(obj, method_name, hooked)


class TruthMetricsCollector:
    """
    收集 Truth Metrics 所需的预测和结果数据
    
    用法：
    collector = TruthMetricsCollector()
    
    # 记录预测
    collector.record_prediction("task_001", "planner", 0.8, [0.7, 0.6])
    
    # 记录结果
    collector.record_outcome("task_001", "planner", 0.75, "success")
    
    # 生成报告
    validator = collector.get_validator()
    print(validator.generate_report())
    """
    
    def __init__(self):
        from truth_metrics import TruthValidator
        self.validator = TruthValidator()
    
    def record_prediction(self, task_id: str, agent_id: str,
                         expected_utility: float,
                         utility_inputs: List[float] = None,
                         context: Dict = None):
        self.validator.record_utility_prediction(
            task_id, agent_id, expected_utility, utility_inputs, context
        )
    
    def record_outcome(self, task_id: str, agent_id: str,
                      actual_outcome: float, outcome_type: str = "success"):
        self.validator.record_utility_outcome(
            task_id, agent_id, actual_outcome, outcome_type
        )
    
    def record_routing(self, task_id: str, chosen_agent: str,
                      context: str = "", available_agents: List[str] = None,
                      reasoning: str = ""):
        self.validator.record_routing(
            task_id, chosen_agent, context, available_agents, reasoning
        )
    
    def record_governance(self, task_id: str, proposed_action: str,
                         decision: str, constraints_checked: List[str],
                         reason: str, actual_outcome: str = None):
        self.validator.record_governance(
            task_id, proposed_action, decision, constraints_checked, reason, actual_outcome
        )
    
    def get_validator(self):
        return self.validator


# 全局 collector 实例
_collector: Optional[TruthMetricsCollector] = None


def get_collector() -> TruthMetricsCollector:
    global _collector
    if _collector is None:
        _collector = TruthMetricsCollector()
    return _collector


if __name__ == "__main__":
    print("=" * 60)
    print("Telemetry Hooks - Test")
    print("=" * 60)
    
    from execution_logger import get_logger
    
    # 测试 TelemetryContext
    print("\n[1] Testing TelemetryContext...")
    with TelemetryContext(task_id="test_001", agent_id="planner") as ctx:
        set_hook_context(task_id="test_001", agent_id="planner")
        print(f"    Context set: {get_hook_context()}")
        
        # 模拟 routing
        logger = get_logger()
        logger.log_routing("test_001", "planner", "test_context", {"test": True})
        print(f"    Logged routing event")
    
    # 测试 TruthMetricsCollector
    print("\n[2] Testing TruthMetricsCollector...")
    collector = get_collector()
    collector.record_prediction("task_001", "planner", 0.8, [0.7, 0.6])
    collector.record_outcome("task_001", "planner", 0.75, "success")
    collector.record_routing("task_001", "planner", "high_complexity", ["planner", "coder"])
    collector.record_governance("task_001", "build", "approved", [], "OK", "success")
    
    validator = collector.get_validator()
    print(validator.generate_report())
    
    print("\n" + "=" * 60)
    print("Telemetry hooks ready for integration")
    print("=" * 60)
