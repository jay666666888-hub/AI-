#!/usr/bin/env python3
"""
AST Export Generator - 只捕获模块中真正定义的 symbols
"""

import ast
import os
import re
from typing import List, Dict, Set


def extract_exports_from_file(file_path: str) -> List[str]:
    """
    只提取真正在本模块中定义的：
    - class（在 Module body 中，不是 import）
    - function（在 Module body 中，不是 import）
    - public constants（明确赋值的大写变量，非 import）
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content, filename=file_path)
    except SyntaxError:
        return []

    # 获取导入的 symbols（这些不是本模块定义的）
    imported_names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name.split('.')[0])
                if alias.asname:
                    imported_names.add(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_names.add(node.module.split('.')[0])
            for alias in node.names:
                if alias.asname:
                    imported_names.add(alias.asname)

    exports = []

    # 只看模块顶层定义的 class 和 function
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                exports.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith("_"):
                exports.append(node.name)
        # 只捕获明确赋值给大写变量的情况（不是 import）
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    # 只有不在 imported_names 中的才算
                    if not name.startswith("_") and name.isupper() and name not in imported_names:
                        exports.append(name)

    return sorted(set(exports))


def scan_infrastructure(infra_path: str) -> Dict[str, List[str]]:
    registry = {}
    for file in os.listdir(infra_path):
        if not file.endswith(".py"):
            continue
        if file.startswith("_") or file == "__init__.py":
            continue
        full_path = os.path.join(infra_path, file)
        module_name = file.replace(".py", "")
        exports = extract_exports_from_file(full_path)
        if exports:
            registry[module_name] = exports
            print(f"    {module_name}: {len(exports)} exports")
    return registry


def write_exports_to_module(file_path: str, exports: List[str]) -> bool:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    export_block = f"\n__exports__ = {repr(exports)}\n"

    if "__exports__" in content:
        content = re.sub(r"\n__exports__\s*=\s*\[.*?\]", export_block, content, flags=re.DOTALL)
    else:
        content += export_block

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def generate_all_exports(infra_path: str) -> Dict[str, List[str]]:
    print("=" * 60)
    print("AST Export Generator - Scanning (strict mode)...")
    print("=" * 60)
    registry = scan_infrastructure(infra_path)
    print(f"\n[FOUND] {len(registry)} modules with exports")
    print("\n[WRITING] Updating module files...")
    for module_name, exports in sorted(registry.items()):
        file_path = os.path.join(infra_path, f"{module_name}.py")
        write_exports_to_module(file_path, exports)
    return registry


if __name__ == "__main__":
    infra_path = "/mnt/e/黑曜石/04_工作/AI开发生态系统/src/infrastructure"
    registry = generate_all_exports(infra_path)
    print("\n" + "=" * 60)
    print(f"✓ GENERATED {len(registry)} module contracts")
    print("=" * 60)
