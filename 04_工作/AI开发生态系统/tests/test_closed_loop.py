#!/usr/bin/env python3
"""闭环演示测试"""

import sys
import os

# 添加 src 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ecosystem_orchestrator import EcosystemOrchestrator


def test_intent_understanding():
    """测试意图理解层"""
    orch = EcosystemOrchestrator()
    orch.load_adapters()
    
    intent_adapter = orch.layers.get("L4_intent")
    assert intent_adapter is not None, "L4_intent should be loaded"
    
    result = intent_adapter.understand("做个AI助手")
    assert result["intent"]["type"] == "create"
    print("  ✅ Intent understanding works")


def test_planning():
    """测试规划层"""
    orch = EcosystemOrchestrator()
    orch.load_adapters()
    
    planning_adapter = orch.layers.get("L5_planning")
    assert planning_adapter is not None, "L5_planning should be loaded"
    
    result = planning_adapter.create_plan("test task", "description", [])
    assert result.id is not None
    print("  ✅ Planning works")


def test_memory_skill():
    """测试记忆技能"""
    orch = EcosystemOrchestrator()
    orch.load_adapters()
    
    memory_skill = orch.skills.get("memory")
    assert memory_skill is not None, "memory skill should be loaded"
    
    status = memory_skill.get_status()
    assert "total" in status
    print("  ✅ Memory skill works")


def test_skill_router():
    """测试智能路由"""
    orch = EcosystemOrchestrator()
    orch.load_adapters()
    
    result = orch.route_task("做个AI助手")
    assert result["task_type"] == "create"
    assert len(result["recommended_skills"]) > 0
    print("  ✅ Skill router works")


def test_full_pipeline():
    """测试完整管道"""
    orch = EcosystemOrchestrator()
    orch.load_adapters()
    
    assert len(orch.skills) == 11, f"Expected 11 skills, got {len(orch.skills)}"
    print("  ✅ 11 Skills initialized")
    
    assert len(orch.layers) == 13, f"Expected 13 layers, got {len(orch.layers)}"
    print("  ✅ 13 Layers initialized")


if __name__ == "__main__":
    print("运行闭环测试...")
    test_intent_understanding()
    test_planning()
    test_memory_skill()
    test_skill_router()
    test_full_pipeline()
    print("\n✅ 所有测试通过")
