#!/usr/bin/env python3
"""
Ecosystem Doctor - 健康检查
检查所有服务和依赖是否可用
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def check(name: str, fn) -> bool:
    """运行检查，返回 True 表示通过"""
    try:
        result = fn()
        if result.get("status") == "ok":
            print(f"  {GREEN}✓{RESET} {name}")
            if "message" in result:
                print(f"      {result['message']}")
            return True
        else:
            print(f"  {RED}✗{RESET} {name}")
            if "error" in result:
                print(f"      {RED}{result['error']}{RESET}")
            return False
    except Exception as e:
        print(f"  {RED}✗{RESET} {name}")
        print(f"      {RED}{type(e).__name__}: {str(e)[:60]}{RESET}")
        return False

def check_python_modules():
    """检查 Python 依赖"""
    print("\n[2] Python 依赖")
    modules = [
        ("hvac", "Vault"),
        ("docker", "Docker"),
        ("kubernetes", "Kubernetes"),
        ("qdrant_client", "Qdrant"),
        ("pydantic", "Pydantic"),
    ]
    results = []
    for module, name in modules:
        try:
            __import__(module)
            print(f"  {GREEN}✓{RESET} {name} ({module})")
            results.append(True)
        except ImportError:
            print(f"  {RED}✗{RESET} {name} ({module}) - 未安装")
            results.append(False)
    return all(results)

def check_docker():
    """检查 Docker"""
    print("\n[3] Docker")
    try:
        import docker
        client = docker.from_env()
        version = client.version()['Version']
        containers = len(client.containers.list())
        print(f"  {GREEN}✓{RESET} Docker v{version}")
        print(f"      运行容器: {containers} 个")
        return {"status": "ok", "message": f"v{version}, {containers} containers"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:60]}

def check_qdrant():
    """检查 Qdrant"""
    print("\n[4] Qdrant Vector DB")
    try:
        import qdrant_client
        client = qdrant_client.QdrantClient(host="localhost", port=6333)
        collections = client.get_collections()
        print(f"  {GREEN}✓{RESET} Qdrant 已连接")
        print(f"      Collections: {len(collections.collections)}")
        return {"status": "ok", "message": f"{len(collections.collections)} collections"}
    except Exception as e:
        return {"status": "error", "error": f"未连接: {str(e)[:40]}"}

def check_vault():
    """检查 Vault"""
    print("\n[5] HashiCorp Vault")
    try:
        import hvac
        client = hvac.Client(url="http://localhost:8200")
        if client.is_authenticated():
            return {"status": "ok", "message": "已认证"}
        else:
            return {"status": "error", "error": "未认证 (需要 Vault Token)"}
    except Exception as e:
        return {"status": "error", "error": f"未连接: {str(e)[:40]}"}

def check_skills():
    """检查 Skills"""
    print("\n[6] Skills (11个)")
    try:
        from src.skills import (
            BrainstormingSkill, WritingPlansSkill, SystematicDebuggingSkill,
            TDDGuideSkill, CodeReviewSkill, VerificationSkill, BuildSkill,
            E2ETestSkill, MemorySkill, GateGuardSkill, ContinuousAgentLoop
        )
        for s in [BrainstormingSkill, WritingPlansSkill, SystematicDebuggingSkill,
                  TDDGuideSkill, CodeReviewSkill, VerificationSkill, BuildSkill,
                  E2ETestSkill, MemorySkill, GateGuardSkill, ContinuousAgentLoop]:
            s()
        print(f"  {GREEN}✓{RESET} 11/11 Skills 可用")
        return {"status": "ok"}
    except Exception as e:
        print(f"  {RED}✗{RESET} Skills 加载失败: {e}")
        return {"status": "error", "error": str(e)[:60]}

def check_agents():
    """检查 Agents"""
    print("\n[7] Claude Code Agents")
    try:
        from src.skills import list_all_agents
        agents = list_all_agents()
        print(f"  {GREEN}✓{RESET} {len(agents)} Agents 已注册")
        return {"status": "ok", "message": f"{len(agents)} agents"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:60]}

def check_integrations():
    """检查 Integrations"""
    print("\n[8] Integrations (Layers)")
    try:
        from src.integrations import IntentUnderstandingAdapter, PlanningAdapter, DockerAdapter
        IntentUnderstandingAdapter().understand("test")
        PlanningAdapter().create_plan("t", "d", [])
        DockerAdapter().ps()
        print(f"  {GREEN}✓{RESET} L4/L5/L12 Integration 可用")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:60]}

def check_config():
    """检查配置"""
    print("\n[1] 配置文件")
    from pathlib import Path
    config_files = [
        ".env",
        ".env.example",
        "config/memory.yaml",
        "requirements.txt",
    ]
    all_exist = True
    for f in config_files:
        path = Path(f)
        if path.exists():
            print(f"  {GREEN}✓{RESET} {f}")
        else:
            print(f"  {RED}✗{RESET} {f} - 缺失")
            all_exist = False
    return {"status": "ok" if all_exist else "warning"}

def main():
    print("=" * 60)
    print("  AI 开发生态系统 - Doctor 健康检查")
    print("=" * 60)

    results = []

    # 1. Config files
    results.append(check("配置文件", check_config))

    # 2. Python modules
    results.append(check_python_modules())

    # 3. Docker
    results.append(check("Docker", check_docker))

    # 4. Qdrant
    results.append(check("Qdrant", check_qdrant))

    # 5. Vault
    results.append(check("Vault", check_vault))

    # 6. Skills
    results.append(check("Skills", check_skills))

    # 7. Agents
    results.append(check("Agents", check_agents))

    # 8. Integrations
    results.append(check("Integrations", check_integrations))

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"  检查结果: {passed}/{total} 项通过")
    
    if passed == total:
        print(f"  {GREEN}✓ 系统健康{RESET}")
    elif passed >= total * 0.7:
        print(f"  {YELLOW}⚠ 部分警告{RESET}")
    else:
        print(f"  {RED}✗ 系统异常{RESET}")

    print("=" * 60)
    return 0 if passed >= total * 0.7 else 1

if __name__ == "__main__":
    sys.exit(main())
