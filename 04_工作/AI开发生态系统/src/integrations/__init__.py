"""
GitHub 热门项目集成适配器
将各层面推荐的热门开源项目集成到生态系统
18 层架构完整覆盖
"""

from .github_projects import GitHubIntegrator, show_all_projects, GITHUB_PROJECTS
from .agentmemory_adapter import AgentMemoryAdapter, integrate_with_hermes
from .dify_adapter import DifyAdapter, RAGPipeline
from .uptime_kuma_adapter import UptimeKumaAdapter, MonitorManager
from .vault_adapter import VaultAdapter, SecretManager
from .ralph_adapter import RalphAdapter, get_ralph_status
from .langchain_adapter import LangChainAdapter, CrewAIAdapter, HermesAgentAdapter
from .grafana_adapter import GrafanaAdapter, SigNozAdapter, OpenObserveAdapter
from .rag_adapter import QdrantRAGAdapter, RAGPipeline, L11KnowledgeRetrievalLayer
from .security_adapter import (
    GGShieldAdapter, SemgrepAdapter, TrivyAdapter,
    GitleaksAdapter
)
from .test_adapter import PlaywrightAdapter, ReactDoctorAdapter, JestAdapter, GoTestAdapter
from .container_adapter import (
    DockerAdapter, KubernetesAdapter, HelmAdapter,
    ArgoCDAdapter, NomadAdapter
)
from .frontend_adapter import (
    OpenUIAdapter, V0Adapter, BoltAdapter,
    DataFormulatorAdapter, GraphifyAdapter, EvidenceAdapter
)
from .data_adapter import AirflowAdapter, PrefectAdapter, KafkaAdapter, DBtAdapter
from .aiops_adapter import N8NAdapter, FastAPIAdapter, GrafanaAlertingAdapter, KEDAAdapter
from .intent_adapter import IntentUnderstandingAdapter, IntentParser, TaskDecomposer
from .planning_adapter import PlanningAdapter, BeadsAdapter, OpenSpecAdapter, RalphImportAdapter
from .dippy_adapter import DippyShellGuard, check_command_safety

__all__ = [
    # 基础
    "GitHubIntegrator",
    "show_all_projects",
    "GITHUB_PROJECTS",
    # L3 记忆/知识层
    "AgentMemoryAdapter",
    "integrate_with_hermes",
    # L11 知识检索层
    "DifyAdapter",
    "RAGPipeline",
    # L10 监控可观测层
    "UptimeKumaAdapter",
    "MonitorManager",
    # L8 安全合规层
    "VaultAdapter",
    "SecretManager",
    # L1 自主代理层
    "RalphAdapter",
    "get_ralph_status",
    "LangChainAdapter",
    "CrewAIAdapter",
    "HermesAgentAdapter",
    # L10 监控可观测层
    "GrafanaAdapter",
    "SigNozAdapter",
    "OpenObserveAdapter",
    # L11 知识检索层
    "QdrantRAGAdapter",
    "RAGPipeline",
    "L11KnowledgeRetrievalLayer",
    # L8 安全合规层
    "GGShieldAdapter",
    "SemgrepAdapter",
    "TrivyAdapter",
    "GitleaksAdapter",
    # L9 测试质量层
    "PlaywrightAdapter",
    "ReactDoctorAdapter",
    "JestAdapter",
    "GoTestAdapter",
    # L12-L14 容器化/部署层
    "DockerAdapter",
    "KubernetesAdapter",
    "HelmAdapter",
    "ArgoCDAdapter",
    "NomadAdapter",
    # L15-L16 前端/创意层
    "OpenUIAdapter",
    "V0Adapter",
    "BoltAdapter",
    "DataFormulatorAdapter",
    "GraphifyAdapter",
    "EvidenceAdapter",
    # L17 数据工程层
    "AirflowAdapter",
    "PrefectAdapter",
    "KafkaAdapter",
    "DBtAdapter",
    # L18 运维自动化层
    "N8NAdapter",
    "FastAPIAdapter",
    "GrafanaAlertingAdapter",
    "KEDAAdapter",
    # L4 意图理解层
    "IntentUnderstandingAdapter",
    "IntentParser",
    "TaskDecomposer",
    # L5 规划推理层
    "PlanningAdapter",
    "BeadsAdapter",
    "OpenSpecAdapter",
    "RalphImportAdapter",
    # L8 安全合规层 - Dippy Shell Guard
    "DippyShellGuard",
    "check_command_safety",
]
