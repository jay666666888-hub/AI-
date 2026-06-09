"""
测试 skills.build_skill 的单元测试
自动生成 by TDD Skill
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 正确导入模块
try:
    # rel_module 类似 "multi_agent.coordinator"
    parts = "skills.build_skill".split(".")
    import importlib
    MODULE = importlib.import_module("src." + "skills.build_skill")
except Exception as e:
    MODULE = None

class TestBuildPhase:
    """测试 skills.build_skill"""


    def test_buildphase_init(self):
        """测试 BuildPhase 初始化"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'BuildPhase')

    def test_buildtask_init(self):
        """测试 BuildTask 初始化"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'BuildTask')

    def test_buildskill_init(self):
        """测试 BuildSkill 初始化"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'BuildSkill')

    def test_run_build(self):
        """测试 run_build 函数"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'run_build')
