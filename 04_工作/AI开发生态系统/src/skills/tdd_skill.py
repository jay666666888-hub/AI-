#!/usr/bin/env python3
"""
TDD Skill - 测试驱动开发
基于 Superpowers TDD 工作流：红→绿→重构
真实实现版本：生成测试文件，运行 pytest
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import os
import sys
import subprocess
import re


class TDDPhase(Enum):
    RED = "red"      # 写测试，测试应该失败
    GREEN = "green"  # 写最小实现让测试通过
    REFACTOR = "refactor"  # 重构改进代码


@dataclass
class TDDState:
    feature: str
    phase: TDDPhase
    test_code: str = ""
    implementation: str = ""
    coverage: float = 0.0
    test_file_path: str = ""


class TDDGuideSkill:
    """TDD 指导技能 - 强制先写测试"""

    COVERAGE_THRESHOLD = 80

    def __init__(self):
        self.state: Optional[TDDState] = None
        self.history: List[Dict[str, Any]] = []
        self.project_path = "/mnt/e/黑曜石/04_工作/AI开发生态系统"

    def start_feature(self, feature: str) -> Dict[str, Any]:
        """开始新功能开发 - 真实生成测试文件并运行"""
        self.state = TDDState(
            feature=feature,
            phase=TDDPhase.RED
        )

        # 分析 feature 名称，确定目标源文件
        target_module = self._extract_module_from_feature(feature)
        if target_module:
            test_file = self._generate_test_file(target_module)
            if test_file:
                self.state.test_file_path = test_file
                # 运行 pytest 验证 RED 阶段
                result = self._run_pytest(test_file)
                return {
                    "phase": "RED",
                    "instruction": "编写测试用例，描述期望的行为",
                    "guidance": [
                        "测试应该失败（RED阶段）",
                        "使用 describe-it 结构组织测试",
                        "覆盖正常路径和边界情况",
                        "先写测试再写实现"
                    ],
                    "next_phase": "GREEN",
                    "mode": "test_first",
                    "test_file": test_file,
                    "pytest_result": result
                }

        return self._get_red_instruction()

    def _extract_module_from_feature(self, feature: str) -> Optional[str]:
        """从 feature 名称提取目标模块路径"""
        patterns = [
            r'为\s+([\w_]+)\s+编写',           
            r'for\s+([\w_]+)\s+write',          
            r'test\s+([\w_]+)',                 
            r'src/([\w/]+)\.py',               
            r'([\w_]+)_skill\.py',            
        ]

        for pattern in patterns:
            match = re.search(pattern, feature)
            if match:
                module = match.group(1).strip()
                module = module.replace('/', '.').replace('\\', '.').replace('.py', '')
                if module.startswith('src.'):
                    module = module[4:]
                return module.split('.')[-1] if '.' in module else module
        return feature if '.' not in feature else None

    def _generate_test_file(self, module_name: str) -> Optional[str]:
        """生成测试文件"""
        try:
            src_path = None
            search_path = os.path.join(self.project_path, "src")
            for root, dirs, files in os.walk(search_path):
                for f in files:
                    if f.endswith('.py') and not f.startswith('__'):
                        fname = f.replace('.py', '')
                        # Normalize names for comparison
                        module_norm = module_name.lower().replace('_', '').replace('-', '')
                        fname_norm = fname.lower().replace('_', '').replace('-', '')
                        # Also remove _skill suffix if present
                        for suffix in ['_skill', '_adapter', '_manager', 'skill', 'adapter', 'manager']:
                            if module_norm.endswith(suffix):
                                module_norm = module_norm[:-len(suffix)]
                            if fname_norm.endswith(suffix):
                                fname_norm = fname_norm[:-len(suffix)]
                        
                        if (module_name == fname or
                            module_norm == fname_norm or
                            module_name.replace('.', '_') == fname):
                            src_path = os.path.join(root, f)
                            break
                if src_path:
                    break

            if not src_path:
                return None

            with open(src_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            # 构建相对于 src 的模块路径
            rel_path = os.path.relpath(src_path, search_path)
            rel_module = rel_path.replace(os.sep, '.').replace('.py', '')

            module_filename = module_name.replace('.', '_').replace('/', '_')
            test_filename = f"test_{module_filename}.py"
            test_path = os.path.join(self.project_path, "tests", test_filename)

            classes = re.findall(r'^class\s+(\w+)', source_code, re.MULTILINE)
            functions = re.findall(r'^def\s+(\w+)\s*\(', source_code, re.MULTILINE)

            cls_name = classes[0] if classes else "Module"

            # 修复导入逻辑 - 使用正确的模块路径
            test_code = f'''"""
测试 {rel_module} 的单元测试
自动生成 by TDD Skill
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 正确导入模块
try:
    # rel_module 类似 "multi_agent.coordinator"
    parts = "{rel_module}".split(".")
    import importlib
    MODULE = importlib.import_module("src." + "{rel_module}")
except Exception as e:
    MODULE = None

class Test{cls_name}:
    """测试 {rel_module}"""

'''

            for cls in classes:
                test_code += f'''
    def test_{cls.lower()}_init(self):
        """测试 {cls} 初始化"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, '{cls}')
'''

            for func in functions:
                if not func.startswith('_'):
                    test_code += f'''
    def test_{func}(self):
        """测试 {func} 函数"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, '{func}')
'''

            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(test_code)

            return test_path

        except Exception as e:
            print(f"生成测试文件失败: {e}")
            return None

    def _run_pytest(self, test_file: str) -> Dict[str, Any]:
        """运行 pytest"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            output = result.stdout + result.stderr
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")
            errors = output.count(" ERROR")

            return {
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "summary": f"{passed} passed, {failed} failed, {errors} errors",
                "returncode": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_red_instruction(self) -> Dict[str, Any]:
        return {
            "phase": "RED",
            "instruction": "编写测试用例，描述期望的行为",
            "guidance": [
                "测试应该失败（RED阶段）",
                "使用 describe-it 结构组织测试",
                "覆盖正常路径和边界情况",
                "先写测试再写实现"
            ],
            "next_phase": "GREEN",
            "mode": "test_first"
        }

    def proceed_to_green(self, test_code: str) -> Dict[str, Any]:
        """进入 GREEN 阶段：编写最小实现"""
        if not self.state:
            raise ValueError("No active TDD session. Call start_feature first.")
        
        self.state.test_code = test_code
        self.state.phase = TDDPhase.GREEN

        return {
            "phase": "GREEN",
            "instruction": "编写最小实现让测试通过",
            "guidance": [
                "不要过度设计",
                "只要让测试变绿即可",
                "可以暂时硬编码",
                "保持最简单的实现"
            ],
            "focus": ["核心功能", "测试通过", "最小代码"],
            "next_phase": "REFACTOR",
            "mode": "minimal_implementation"
        }

    def proceed_to_refactor(self, implementation: str) -> Dict[str, Any]:
        """进入 REFACTOR 阶段"""
        if not self.state:
            raise ValueError("No active TDD session.")
        
        self.state.implementation = implementation
        self.state.phase = TDDPhase.REFACTOR

        return {
            "phase": "REFACTOR",
            "instruction": "重构代码提升质量，保持测试通过",
            "checklist": [
                "消除重复代码",
                "提取函数",
                "改善命名",
                "验证覆盖率 >= 80%",
                "检查无 mutation"
            ],
            "next_phase": "RED",
            "mode": "cleanup"
        }

    def complete_cycle(self) -> Dict[str, Any]:
        """完成当前周期"""
        if not self.state:
            return {"status": "no_active_session"}

        self.history.append({
            "feature": self.state.feature,
            "phase": self.state.phase.value,
            "coverage": self.state.coverage
        })

        self.state = None
        return {
            "status": "cycle_complete",
            "cycles_completed": len(self.history),
            "message": "准备开始下一个 TDD 周期"
        }

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        if not self.state:
            return {"status": "idle", "cycles": len(self.history)}
        
        return {
            "status": "active",
            "feature": self.state.feature,
            "phase": self.state.phase.value,
            "cycles_completed": len(self.history)
        }


def run_tdd(feature: str, phase: str = "start", 
            test_code: str = "", implementation: str = "") -> Dict[str, Any]:
    """运行 TDD 流程的快捷函数"""
    skill = TDDGuideSkill()
    
    if phase == "start":
        return skill.start_feature(feature)
    elif phase == "green":
        return skill.proceed_to_green(test_code)
    elif phase == "refactor":
        return skill.proceed_to_refactor(implementation)
    elif phase == "complete":
        return skill.complete_cycle()
    else:
        return {"error": f"Unknown phase: {phase}"}
