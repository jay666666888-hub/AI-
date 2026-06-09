#!/usr/bin/env python3
"""
Dippy Shell Guard Adapter - Shell 命令安全层
L8 安全合规层

基于 dippy_guard.sh 的 Python 封装
- 危险命令拦截: rm -rf, fork, eval, exec
- 安全命令自动批准: ls, cd, pwd, echo, cat, grep 等
"""

import os
import re
from typing import Dict, Any


class DippyShellGuard:
    """Shell 命令安全门禁"""

    DANGEROUS_PATTERNS = [
        r"rm\s+-rf", r"fork\s*\(", r"eval\s*\(", r"exec\s*\(",
        r"\|\s*bash", r";\s*rm\s+", r"&&\s*rm\s+",
    ]

    SAFE_COMMANDS = [
        "read", "glob", "grep", "ls", "cd", "pwd", "echo", "cat",
        "head", "tail", "which", "file", "stat", "find", "awk",
        "sed", "sort", "uniq", "wc", "tr", "cut", "join",
        "paste", "bc", "expr", "test", "git", "hub", "python",
        "python3",
    ]

    def __init__(self, guard_script: str = None):
        self.guard_script = guard_script
        if not self.guard_script:
            paths = [
                os.path.expanduser("~/.claude/hooks/dippy_guard.sh"),
                os.path.join(os.getcwd(), ".claude/hooks/dippy_guard.sh"),
            ]
            for path in paths:
                if os.path.exists(path):
                    self.guard_script = path
                    break

    def is_available(self) -> bool:
        return self.guard_script and os.path.exists(self.guard_script)

    def check_command(self, command: str) -> Dict[str, Any]:
        if not command:
            return {"allowed": True, "reason": "empty", "dangerous": False}

        command = command.strip()

        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return {"allowed": False, "reason": f"危险命令: {pattern}", "dangerous": True}

        command_lower = command.lower()
        for safe_cmd in self.SAFE_COMMANDS:
            if command_lower.startswith(safe_cmd.lower()):
                return {"allowed": True, "reason": f"安全命令: {safe_cmd}", "dangerous": False}

        if command_lower.startswith("git ") or command_lower.startswith("hub "):
            return {"allowed": True, "reason": "git 操作", "dangerous": False}

        return {"allowed": True, "reason": "命令已放行", "dangerous": False, "requires_approval": True}

    def get_status(self) -> Dict[str, Any]:
        return {
            "available": self.is_available(),
            "guard_script": self.guard_script,
            "dangerous_patterns": len(self.DANGEROUS_PATTERNS),
            "safe_commands": len(self.SAFE_COMMANDS)
        }


def check_command_safety(command: str) -> Dict[str, Any]:
    guard = DippyShellGuard()
    return guard.check_command(command)


if __name__ == "__main__":
    guard = DippyShellGuard()
    print(f"Dippy 可用: {guard.is_available()}")
    print(f"状态: {guard.get_status()}")
    print()

    test_commands = ["ls -la", "rm -rf /tmp/test", "git status", "echo hello", "python src/ecosystem.py"]

    for cmd in test_commands:
        result = guard.check_command(cmd)
        status = "❌" if not result["allowed"] else "✅"
        print(f"{status} {cmd} - {result['reason']}")