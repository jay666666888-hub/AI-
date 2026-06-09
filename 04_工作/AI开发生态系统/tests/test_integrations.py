"""
AI 开发生态系统 - 集成测试
测试已完成的适配器能否正常导入和基本运行
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAgentMemoryAdapter:
    """AgentMemory 适配器测试"""

    def test_import(self):
        from src.integrations.agentmemory_adapter import AgentMemoryAdapter
        assert AgentMemoryAdapter is not None

    def test_add_short_term(self):
        from src.integrations.agentmemory_adapter import AgentMemoryAdapter
        adapter = AgentMemoryAdapter()
        entry = adapter.add_short_term("测试记忆", {"source": "test"})
        assert entry.id.startswith("st_")
        assert entry.type == "short_term"

    def test_get_stats(self):
        from src.integrations.agentmemory_adapter import AgentMemoryAdapter
        adapter = AgentMemoryAdapter()
        adapter.add_short_term("测试1")
        adapter.add_short_term("测试2")
        stats = adapter.get_stats()
        assert stats["short_term"] == 2
        assert stats["total"] >= 2


class TestDifyAdapter:
    """Dify 适配器测试"""

    def test_import(self):
        from src.integrations.dify_adapter import DifyAdapter
        assert DifyAdapter is not None

    def test_init(self):
        from src.integrations.dify_adapter import DifyAdapter
        adapter = DifyAdapter()
        assert adapter.base_url == "http://localhost:8080"

    def test_generate_docker_compose(self):
        from src.integrations.dify_adapter import DifyAdapter
        adapter = DifyAdapter()
        compose = adapter.generate_docker_compose()
        assert "version" in compose
        assert "services" in compose
        assert "dify" in compose.lower()


class TestUptimeKumaAdapter:
    """Uptime Kuma 适配器测试"""

    def test_import(self):
        from src.integrations.uptime_kuma_adapter import UptimeKumaAdapter
        assert UptimeKumaAdapter is not None

    def test_init(self):
        from src.integrations.uptime_kuma_adapter import UptimeKumaAdapter
        adapter = UptimeKumaAdapter()
        assert adapter.base_url == "http://localhost:3001"

    def test_push_status(self):
        from src.integrations.uptime_kuma_adapter import UptimeKumaAdapter
        adapter = UptimeKumaAdapter()
        # 不实际发送，只验证方法存在
        assert hasattr(adapter, 'push_status')


class TestVaultAdapter:
    """Vault 适配器测试"""

    def test_import(self):
        from src.integrations.vault_adapter import VaultAdapter, SecretManager
        assert VaultAdapter is not None
        assert SecretManager is not None

    def test_init(self):
        from src.integrations.vault_adapter import SecretManager
        manager = SecretManager()
        assert manager is not None

    def test_set_and_get(self):
        from src.integrations.vault_adapter import SecretManager
        manager = SecretManager()
        result = manager.set("test_key", "test_value")
        assert result is True
        value = manager.get("test_key")
        assert value == "test_value"


class TestGitHubProjects:
    """GitHub 项目目录测试"""

    def test_import(self):
        from src.integrations.github_projects import GitHubIntegrator, GITHUB_PROJECTS
        assert GitHubIntegrator is not None
        assert GITHUB_PROJECTS is not None

    def test_list_projects(self):
        from src.integrations.github_projects import GitHubIntegrator
        integrator = GitHubIntegrator()
        projects = integrator.list_projects()
        assert len(projects) > 0
        assert "1_智能协作层" in projects

    def test_integrated_projects(self):
        from src.integrations.github_projects import GitHubIntegrator
        integrator = GitHubIntegrator()
        integrated = integrator.get_integrated_projects()
        assert "CrewAI/CrewAI" in integrated

    def test_pending_projects(self):
        from src.integrations.github_projects import GitHubIntegrator
        integrator = GitHubIntegrator()
        pending = integrator.get_pending_projects()
        assert len(pending) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
