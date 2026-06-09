#!/usr/bin/env python3
"""
Registry Lock - 冻结 module exports 结构
防止 runtime / AI / init.py 再修改系统结构
"""

import hashlib
import json
from typing import Dict, List, Optional


class RegistryLock:
    """
    冻结整个 module exports 结构
    """

    def __init__(self):
        self._fingerprint: Optional[str] = None
        self._locked_registry: Optional[Dict[str, List[str]]] = None

    def build_fingerprint(self, registry: Dict[str, List[str]]) -> str:
        """对 registry 做结构 hash"""
        normalized = json.dumps(registry, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def lock(self, registry: Dict[str, List[str]]) -> None:
        """锁定当前 registry 状态"""
        self._locked_registry = registry
        self._fingerprint = self.build_fingerprint(registry)
        print(f"[LOCK] Registry locked with fingerprint: {self._fingerprint[:16]}...")

    def verify(self, registry: Dict[str, List[str]]) -> bool:
        """校验是否被修改"""
        current_fp = self.build_fingerprint(registry)
        return current_fp == self._fingerprint

    def get_locked(self) -> Optional[Dict[str, List[str]]]:
        return self._locked_registry

    def is_locked(self) -> bool:
        return self._locked_registry is not None


class RegistryGuard:
    """
    防止运行时修改 exports
    """

    _locked: bool = False

    @classmethod
    def forbid_mutation(cls, operation: str = "mutation") -> None:
        if cls._locked:
            raise RuntimeError(
                f"[REGISTRY LOCKED] {operation} is forbidden at runtime. "
                "Registry structure is frozen after initial lock."
            )

    @classmethod
    def enable_lock(cls) -> None:
        cls._locked = True
        print("[GUARD] Registry mutation guard ENABLED")

    @classmethod
    def disable_lock(cls) -> None:
        cls._locked = False
        print("[GUARD] Registry mutation guard DISABLED (dev only)")


def verify_on_boot(registry: Dict[str, List[str]], lock: RegistryLock) -> None:
    """启动时校验"""
    if not lock.is_locked():
        print("[WARNING] Registry not locked yet")
        return

    if not lock.verify(registry):
        raise RuntimeError(
            "[FATAL] Registry drift detected - system structure has changed!"
        )
    print("[VERIFY] Registry structure verified - OK")
