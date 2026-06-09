#!/usr/bin/env python3
"""
AI 开发生态系统 - 统一入口
18 层架构 + 11 Skills + 58 Agents + 智能路由
"""
import sys
import os

def main():
    print("=" * 60)
    print("  AI 开发生态系统 v4.0")
    print("  18 Layer + 11 Skills + 58 Agents + 智能路由")
    print("=" * 60)

    # Show 18 layers
    layers = [
        ("L1", "自主代理层", "Ralph / LangChain / CrewAI / Hermes"),
        ("L2", "多Agent协调", "gstack / CrewAI"),
        ("L3", "记忆/知识层", "agentmemory / Memori / Qdrant"),
        ("L4", "意图理解层", "IntentParser / TaskDecomposer"),
        ("L5", "规划推理层", "Beads / OpenSpec / RalphImport"),
        ("L6", "开发流程层", "ECC Superpowers / TDD"),
        ("L7", "智能开发层", "Tabby / Claude Code"),
        ("L8", "安全合规层", "ggshield / semgrep / Vault"),
        ("L9", "测试质量层", "Playwright / react-doctor"),
        ("L10", "监控可观测层", "Grafana / SigNoz / Uptime Kuma"),
        ("L11", "知识检索层", "Milvus / Quivr / dify"),
        ("L12", "基础设施层", "Docker / Kubernetes / Helm"),
        ("L13", "容器编排层", "Rancher / Nomad / ArgoCD"),
        ("L14", "部署自动化层", "ArgoCD / Flux / Jenkins"),
        ("L15", "前端生成层", "OpenUI / v0 / Bolt"),
        ("L16", "创意设计层", "Graphify / data-formulator"),
        ("L17", "数据工程层", "Airflow / Prefect / Kafka"),
        ("L18", "运维自动化层", "n8n / FastAPI / KEDA"),
    ]

    print("\n📊 18 层架构:")
    print("-" * 60)
    for layer, name, components in layers:
        print(f"  {layer:4} {name:12} | {components}")

    # Show 11 Skills
    print("\n🛠️  11 个 Skills:")
    print("-" * 60)
    skills = [
        ("brainstorming", "需求澄清"),
        ("writing_plans", "任务规划"),
        ("systematic_debugging", "问题定位"),
        ("tdd", "测试驱动"),
        ("code_review", "代码审查"),
        ("verification", "完成验证"),
        ("build", "增量实现"),
        ("e2e_test", "端到端测试"),
        ("memory", "持久记忆"),
        ("gateguard", "文件守护"),
        ("agent_loop", "持续循环"),
    ]
    for name, desc in skills:
        print(f"  {name:20} {desc}")

    # Show routing
    print("\n🎯 智能路由 (Skill + Agent + Layer):")
    print("-" * 60)
    print("  任务类型     → Skills                    → Agents")
    print("  ──────────────────────────────────────────────────────────")
    routes = [
        ("fix", "systematic_debugging, tdd", "build-error-resolver, tdd-guide"),
        ("create", "brainstorming, writing_plans, tdd", "planner, code-architect"),
        ("review", "code_review, verification", "code-reviewer, security-reviewer"),
        ("deploy", "build, verification, e2e_test", "architect"),
        ("security", "code_review", "security-reviewer"),
        ("performance", "verification, code_review", "performance-optimizer"),
    ]
    for task, skills_r, agents_r in routes:
        print(f"  {task:12} → {skills_r:35} → {agents_r}")

    print("\n🚀 启动 Ecosystem Orchestrator...")
    print()

    # Run orchestrator
    sys.path.insert(0, os.path.dirname(__file__))
    from ecosystem_orchestrator import EcosystemOrchestrator

    orch = EcosystemOrchestrator()
    orch.load_adapters()

    status = orch.get_status()
    print(f"\n📦 系统状态:")
    print(f"   Skills: {status['skills_count']} 个")
    print(f"   Agents: {status['agents_count']} 个")
    print(f"   Layers: {status['layers_count']} 个")

    # 测试自动路由
    print("\n" + "=" * 60)
    print("【自动路由测试】")
    task = "做个 AI 助手"
    result = orch.route_task(task)
    print(f"任务: {task}")
    print(f"  → 类型: {result['task_type']}")
    print(f"  → 置信度: {result['confidence']:.2f}")
    print(f"  → Skills: {result['recommended_skills']}")
    print(f"  → Agents: {result['recommended_agents']}")
    print(f"  → Layers: {result['recommended_layers']}")
    print(f"  → 完整管道: {result.get('full_pipeline', result['recommended_skills'] + result['recommended_agents'] + result['recommended_layers'])}")

    # 执行工作流
    print("\n" + "=" * 60)
    print("【自动模式执行】")
    result = orch.run_workflow(task, mode="auto")
    print(f"\n📋 执行结果:")
    print(f"   阶段完成: {result['stages_completed']}")
    print(f"   成功: {result['success_count']}")
    print()
    print("=" * 60)
    print("✅ 生态系统运行完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
