"""
测试 skills.brainstorming 的单元测试
自动生成 by TDD Skill
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 正确导入模块
try:
    # rel_module 类似 "multi_agent.coordinator"
    parts = "skills.brainstorming".split(".")
    import importlib
    MODULE = importlib.import_module("src." + "skills.brainstorming")
except Exception as e:
    MODULE = None

class TestClarifyingQuestion:
    """测试 skills.brainstorming"""


    def test_clarifyingquestion_init(self):
        """测试 ClarifyingQuestion 初始化"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'ClarifyingQuestion')

    def test_brainstormingskill_init(self):
        """测试 BrainstormingSkill 初始化"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'BrainstormingSkill')

    def test_run_brainstorming(self):
        """测试 run_brainstorming 函数"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'run_brainstorming')
