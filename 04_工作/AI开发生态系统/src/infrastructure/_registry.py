#!/usr/bin/env python3
"""
Infrastructure Registry - SSOT (Single Source of Truth)
六层结构：
1. Module Layer
2. Module Contract (__exports__)
3. Registry (SSOT) - auto-generated from contracts
4. Import Builder + Validator
5. __init__.py (pure assembler)
6. Import Guard (防 AI 乱补)

入口：validate_registry() / build_init() / load_registry()
"""

import importlib
import pkgutil
import hashlib
import os
import sys
from typing import Dict, List

# 确保 infrastructure 包可被导入
_src_path = "/mnt/e/黑曜石/04_工作/AI开发生态系统/src"
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# ==============================================================================
# Layer 3: Registry (SSOT) - 自动从模块 contract 生成
# ==============================================================================

MODULE_REGISTRY: Dict[str, List[str]] = {}
FINGERPRINTS: Dict[str, str] = {}


def _compute_fingerprint(exports: List[str]) -> str:
    """Contract Fingerprint - 检测 API 漂移"""
    return hashlib.md5(",".join(sorted(exports)).encode()).hexdigest()[:12]


def load_registry() -> Dict[str, List[str]]:
    """
    自动扫描所有模块的 __exports__ contract
    Layer 3: Registry 生成器
    """
    global MODULE_REGISTRY, FINGERPRINTS

    # 使用硬编码的绝对路径避免 __file__ 问题
    infra_path = "/mnt/e/黑曜石/04_工作/AI开发生态系统/src/infrastructure"
    MODULE_REGISTRY = {}
    FINGERPRINTS = {}

    # 遍历所有 .py 文件（排除私有模块）
    for py_file in os.listdir(infra_path):
        if not py_file.endswith(".py") or py_file.startswith("_"):
            continue

        module_name = py_file[:-3]  # 去掉 .py

        # 跳过非模块文件
        if module_name in ("__init__",):
            continue

        try:
            module = importlib.import_module(f"infrastructure.{module_name}")
        except ImportError:
            continue

        exports = getattr(module, "__exports__", None)

        if exports is None:
            raise ImportError(
                f"[BROKEN CONTRACT] {module_name} is missing __exports__ declaration. "
                f"Every module MUST declare: __exports__ = ['Symbol1', 'Symbol2', ...]"
            )

        if not isinstance(exports, list):
            raise ImportError(
                f"[BROKEN CONTRACT] {module_name}.__exports__ must be a list, got {type(exports)}"
            )

        MODULE_REGISTRY[module_name] = exports
        FINGERPRINTS[module_name] = _compute_fingerprint(exports)

    return MODULE_REGISTRY


# ==============================================================================
# Layer 4: Validator - 强制校验（关键防炸点）
# ==============================================================================

def validate_registry() -> Dict[str, List[str]]:
    """
    验证所有模块 contract 是否与实际 exports 匹配
    Layer 4: 强制校验器
    Returns: {"valid": bool, "errors": [], "warnings": []}
    """
    import importlib

    result = {"valid": True, "errors": [], "warnings": [], "missing_in_module": [], "missing_in_contract": []}

    if not MODULE_REGISTRY:
        load_registry()

    for module_name, contract_exports in MODULE_REGISTRY.items():
        try:
            module = importlib.import_module(f"infrastructure.{module_name}")
        except ImportError as e:
            result["valid"] = False
            result["errors"].append(f"[IMPORT FAIL] {module_name}: {e}")
            continue

        module_symbols = {s for s in dir(module) if not s.startswith("_")}

        # 检查 contract 中声明的 symbol 是否真的在模块里
        for symbol in contract_exports:
            if not hasattr(module, symbol):
                result["valid"] = False
                result["missing_in_module"].append(f"    {module_name}.{symbol}")

        # 检查模块里是否有 contract 没声明的（警告，非错误）
        actual_public = [s for s in module_symbols
                        if not s.startswith("_")
                        and s not in ("Any", "Dict", "List", "Optional", "Callable",
                                     "dataclass", "Enum", "field", "datetime",
                                     "os", "sys", "json", "time", "uuid")]
        undeclared = set(actual_public) - set(contract_exports)
        if undeclared:
            result["missing_in_contract"].append(f"    {module_name}: {sorted(undeclared)}")

    if result["missing_in_module"]:
        result["errors"].append("[BROKEN CONTRACT] Symbols declared in __exports__ but not found in module:")
        result["errors"].extend(result["missing_in_module"])

    if result["missing_in_contract"]:
        result["warnings"].append("[UNDECLARED] Public symbols found in module but not in __exports__:")
        result["warnings"].extend(result["missing_in_contract"])

    return result


# ==============================================================================
# Layer 5: Import Guard - 防止 AI 乱补
# ==============================================================================

class ImportGuard:
    """
    Layer 6: Import Guard（防 AI 在 auto mode 下"猜导出"）

    用法：
    from infrastructure._registry import ImportGuard, MODULE_REGISTRY

    # 在任何 import 前调用
    ImportGuard.check(symbol="must_hold", module="invariant_engine")
    """

    _checked_contracts: Dict[str, set] = {}

    @classmethod
    def check(cls, symbol: str, module: str) -> None:
        """
        检查 symbol 是否在 module 的 __exports__ contract 中
        不在则抛出异常，阻止 speculation
        """
        if not MODULE_REGISTRY:
            load_registry()

        if module not in MODULE_REGISTRY:
            raise RuntimeError(
                f"[IMPORT VIOLATION] Module '{module}' not found in registry"
            )

        contract = MODULE_REGISTRY[module]

        if symbol not in contract:
            raise RuntimeError(
                f"[IMPORT VIOLATION] '{symbol}' not declared in {module}.__exports__\n"
                f"    Declared exports: {contract}\n"
                f"    To fix: add '{symbol}' to {module}.__exports__ or use a declared symbol"
            )

    @classmethod
    def validate_all(cls) -> None:
        """验证所有模块 contract"""
        result = validate_registry()
        if not result["valid"]:
            raise RuntimeError(
                "[CONTRACT VIOLATION] Cannot proceed with invalid contracts:\n" +
                "\n".join(result["errors"])
            )


# ==============================================================================
# Layer 5: __init__.py Generator - 纯 assembler
# ==============================================================================

def build_init_content() -> str:
    """
    基于 registry 生成 __init__.py 内容
    Layer 5: __init__.py 生成器（纯 assembler，无逻辑）
    """
    if not MODULE_REGISTRY:
        load_registry()

    infra_path = "/mnt/e/黑曜石/04_工作/AI开发生态系统/src/infrastructure"

    lines = [
        '#!/usr/bin/env python3',
        '"""',
        'Infrastructure Layer - Auto-generated from registry',
        'DO NOT EDIT MANUALLY - This file is generated by _registry.py',
        '"""',
        '',
        '# WARNING: This file is auto-generated',
        '# Any manual edits will be overwritten',
        '# To modify exports: edit the module\'s __exports__ list',
        '',
        '',
    ]

    all_exports = []

    for module_name in sorted(MODULE_REGISTRY.keys()):
        exports = MODULE_REGISTRY[module_name]
        if not exports:
            continue

        lines.append(f'# ===== {module_name} =====')
        lines.append(f'from .{module_name} import (')
        for exp in exports:
            lines.append(f'    {exp},')
            all_exports.append(exp)
        lines.append(')')
        lines.append('')

    lines.append('# ===== __all__ =====')
    lines.append('__all__ = [')
    for exp in sorted(all_exports):
        lines.append(f'    "{exp}",')
    lines.append(']')

    return '\n'.join(lines)


def generate_init_file() -> None:
    """生成 __init__.py 文件"""
    content = build_init_content()
    init_path = "/mnt/e/黑曜石/04_工作/AI开发生态系统/src/infrastructure/__init__.py"

    with open(init_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("[REGISTRY] Generated __init__.py")


# ==============================================================================
# CLI Entry Point
# ==============================================================================

if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("SSOT Module Registry - Infrastructure Contract System")
    print("=" * 70)

    # Step 1: Load registry
    print("\n[1] Loading registry from module contracts...")
    try:
        load_registry()
        print(f"    Loaded {len(MODULE_REGISTRY)} modules")
        for mod, exports in sorted(MODULE_REGISTRY.items()):
            fp = FINGERPRINTS.get(mod, "?")
            print(f"    {mod}: [{fp}] {len(exports)} exports")
    except ImportError as e:
        print(f"    ERROR: {e}")
        sys.exit(1)

    # Step 2: Validate
    print("\n[2] Validating contracts...")
    result = validate_registry()

    if result["valid"]:
        print("    ✓ ALL CONTRACTS VALID")
    else:
        print("    ✗ CONTRACT VIOLATIONS FOUND:")
        for err in result["errors"]:
            print(f"        {err}")
        print("\n[FATAL] Fix broken contracts before generating __init__.py")
        sys.exit(1)

    # Step 3: Warnings (non-blocking)
    if result["warnings"]:
        print("\n[3] Warnings (non-blocking):")
        for warn in result["warnings"]:
            print(f"        {warn}")

    # Step 4: Generate fingerprint report
    print("\n[4] Contract Fingerprints:")
    for mod, fp in sorted(FINGERPRINTS.items()):
        print(f"    {mod}: {fp}")

    # Step 5: Generate __init__.py
    print("\n[5] Generating __init__.py...")
    generate_init_file()

    # Step 6: Lock registry (freeze structure)
    print("\n[6] Locking registry...")
    from tools.registry_lock import RegistryLock, RegistryGuard

    lock = RegistryLock()
    lock.lock(MODULE_REGISTRY)
    RegistryGuard.enable_lock()

    print("\n" + "=" * 70)
    print("✓ REGISTRY SYSTEM READY + LOCKED")
    print("=" * 70)
    print("\nSystem is now in STRUCTURAL FREEZE mode")
    print("Registry fingerprint:", lock._fingerprint[:16] + "...")
    print("\nUsage:")
    print("  from infrastructure._registry import validate_registry, ImportGuard")
    print("  from infrastructure._registry import load_registry, MODULE_REGISTRY")
    print("  from infrastructure._registry import MODULE_REGISTRY, FINGERPRINTS")