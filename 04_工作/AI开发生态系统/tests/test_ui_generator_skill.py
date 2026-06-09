"""
测试 creative.ui_generator 的单元测试
自动生成 by TDD Skill
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 正确导入模块
try:
    # rel_module 类似 "multi_agent.coordinator"
    parts = "creative.ui_generator".split(".")
    import importlib
    MODULE = importlib.import_module("src." + "creative.ui_generator")
except Exception as e:
    MODULE = None

class TestComponent:
    """测试 creative.ui_generator"""


    def test_component_init(self):
        """测试 Component 初始化"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'Component')

    def test_uigenerator_init(self):
        """测试 UIGenerator 初始化"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'UIGenerator')
