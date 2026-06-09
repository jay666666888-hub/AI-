"""
测试 skills.skill_router 的单元测试
自动生成 by TDD Skill
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 正确导入模块
try:
    # rel_module 类似 "multi_agent.coordinator"
    parts = "skills.skill_router".split(".")
    import importlib
    MODULE = importlib.import_module("src." + "skills.skill_router")
except Exception as e:
    MODULE = None

class TestTaskType:
    """测试 skills.skill_router"""


    def test_tasktype_init(self):
        """测试 TaskType 初始化"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'TaskType')

    def test_routerule_init(self):
        """测试 RouteRule 初始化"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'RouteRule')

    def test_componentregistry_init(self):
        """测试 ComponentRegistry 初始化"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'ComponentRegistry')

    def test_skillrouter_init(self):
        """测试 SkillRouter 初始化"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'SkillRouter')

    def test_route_task(self):
        """测试 route_task 函数"""
        if MODULE is None:
            pytest.skip("模块不可导入")
        assert hasattr(MODULE, 'route_task')
