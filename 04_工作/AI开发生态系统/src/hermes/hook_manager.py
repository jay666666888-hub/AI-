"""
Hook Manager - Hermes Hook 管理器
管理 AI 协作系统的 hooks 和事件
"""

from typing import Callable, Dict, List, Any, Optional
from enum import Enum


class HookType(Enum):
    """Hook 类型枚举"""
    PRE_AGENT = "pre_agent"       # Agent执行前
    POST_AGENT = "post_agent"     # Agent执行后
    PRE_TASK = "pre_task"         # 任务执行前
    POST_TASK = "post_task"       # 任务执行后
    ON_ERROR = "on_error"         # 错误发生
    ON_SUCCESS = "on_success"     # 成功完成


class HookManager:
    """Hook 管理器，管理和触发各种 hooks"""

    def __init__(self):
        self.hooks: Dict[HookType, List[Callable]] = {
            HookType.PRE_AGENT: [],
            HookType.POST_AGENT: [],
            HookType.PRE_TASK: [],
            HookType.POST_TASK: [],
            HookType.ON_ERROR: [],
            HookType.ON_SUCCESS: []
        }
        self.event_history: List[Dict[str, Any]] = []

    def register(self, hook_type: str, callback: Callable) -> bool:
        """
        注册一个 hook

        Args:
            hook_type: hook类型字符串 (pre_agent, post_agent, etc.)
            callback: 回调函数

        Returns:
            注册是否成功
        """
        try:
            hook_enum = HookType(hook_type)
            self.hooks[hook_enum].append(callback)
            return True
        except ValueError:
            return False

    def unregister(self, hook_type: str, callback: Callable) -> bool:
        """取消注册一个 hook"""
        try:
            hook_enum = HookType(hook_type)
            if callback in self.hooks[hook_enum]:
                self.hooks[hook_enum].remove(callback)
                return True
            return False
        except ValueError:
            return False

    def trigger(self, hook_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        触发所有注册的 hooks

        Args:
            hook_type: hook类型
            context: 上下文数据

        Returns:
            触发结果
        """
        try:
            hook_enum = HookType(hook_type)
        except ValueError:
            return {"error": f"Unknown hook type: {hook_type}"}

        results = []
        for callback in self.hooks[hook_enum]:
            try:
                result = callback(context)
                results.append({"hook": callback.__name__, "result": result, "status": "success"})
            except Exception as e:
                results.append({"hook": callback.__name__, "error": str(e), "status": "failed"})

        # 记录事件历史
        self.event_history.append({
            "hook_type": hook_type,
            "context": context,
            "results": results,
            "timestamp": self._get_timestamp()
        })

        return {
            "hook_type": hook_type,
            "results": results,
            "total": len(results)
        }

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取事件历史"""
        return self.event_history[-limit:]

    def clear_history(self):
        """清空事件历史"""
        self.event_history = []

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# 示例 hooks
def pre_agent_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """Agent执行前的hook示例"""
    print(f"Agent {context.get('agent_name')} 即将执行")
    return {"status": "allowed"}


def post_agent_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """Agent执行后的hook示例"""
    print(f"Agent {context.get('agent_name')} 执行完成")
    return {"status": "recorded"}


if __name__ == "__main__":
    # 示例用法
    manager = HookManager()

    # 注册 hooks
    manager.register("pre_agent", pre_agent_hook)
    manager.register("post_agent", post_agent_hook)

    # 触发 hook
    result = manager.trigger("pre_agent", {"agent_name": "researcher", "task": "分析项目"})
    print(result)

    # 查看历史
    history = manager.get_history()
    print(history)