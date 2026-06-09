"""
GitHub 热门项目集成
每个层面集成推荐的热门开源项目
"""

from typing import Dict, Any, List, Optional
import subprocess
import os


class GitHubProject:
    """GitHub 项目信息"""
    def __init__(self, name: str, url: str, stars: int, description: str, integration_status: str = "未集成"):
        self.name = name
        self.url = url
        self.stars = stars
        self.description = description
        self.integration_status = integration_status


# 各层面推荐的 GitHub 热门项目
GITHUB_PROJECTS = {
    "1_智能协作层": [
        GitHubProject("obra/superpowers", "https://github.com/obra/superpowers", 189000,
                      "Agentic skills framework, 完整开发方法论", "参考实现"),
        GitHubProject("garrytan/gstack", "https://github.com/garrytan/gstack", 95600,
                      "23个AI专家代理, slash commands, 多AI协调", "参考实现"),
        GitHubProject("mattpocock/skills", "https://github.com/garrytan/skills", 78700,
                      "工程技能集, TDD/调试/架构改善", "参考实现"),
        GitHubProject("CrewAI/CrewAI", "https://github.com/CrewAI/CrewAI", 28000,
                      "多AI代理编排框架 (已集成)", "已集成"),
    ],

    "2_记忆知识层": [
        GitHubProject("rohitg00/agentmemory", "https://github.com/rohitg00/agentmemory", 7400,
                      "AI编码代理持久化记忆", "待集成"),
        GitHubProject("langgenius/dify", "https://github.com/langgenius/dify", 141000,
                      "生产级Agent工作流开发平台", "待集成"),
        GitHubProject("Qdrant/Qdrant", "https://github.com/Qdrant/Qdrant", 22000,
                      "向量数据库 (已集成)", "已集成"),
        GitHubProject("Ollama/Ollama", "https://github.com/Ollama/Ollama", 98000,
                      "本地LLM运行 (已集成)", "已集成"),
    ],

    "3_开发流程层": [
        GitHubProject("oxc-project/oxc", "https://github.com/oxc-project/oxc", 21000,
                      "高性能JS工具链(解析器/linter/格式化)", "待集成"),
        GitHubProject("ansible/ansible", "https://github.com/ansible/ansible", 68000,
                      "IT自动化平台", "待集成"),
        GitHubProject("ReactDeveloper/react-doctor", "https://github.com/millionco/react-doctor", 9200,
                      "Agent写出烂React自动检测", "待集成"),
    ],

    "4_智能开发层": [
        GitHubProject("decolua/9router", "https://github.com/decolua/9router", 9800,
                      "无限AI编码, 多provider自动fallback", "待集成"),
        GitHubProject("CodebuffAI/codebuff", "https://github.com/CodebuffAI/codebuff", 5000,
                      "终端代码生成", "待集成"),
        GitHubProject("jarrodwatts/claude-hud", "https://github.com/jarrodwatts/claude-hud", 22000,
                      "Claude Code插件, 显示上下文/工具/进度", "待集成"),
    ],

    "5_安全合规层": [
        GitHubProject("hashicorp/vault", "https://github.com/hashicorp/vault", 35000,
                      "秘钥管理, 加密即服务", "待集成"),
        GitHubProject("zizmorcore/zizmor", "https://github.com/zizmorcore/zizmor", 4700,
                      "GitHub Actions静态分析", "待集成"),
        GitHubProject("imthenachoman/How-To-Secure-A-Linux-Server", "https://github.com/imthenachoman/How-To-Secure-A-Linux-Server", 27000,
                      "Linux服务器安全指南", "待集成"),
    ],

    "6_基础设施层": [
        GitHubProject("louislam/uptime-kuma", "https://github.com/louislam/uptime-kuma", 86000,
                      "自托管监控工具", "待集成"),
        GitHubProject("fatedier/frp", "https://github.com/fatedier/frp", 106000,
                      "快速反向代理", "待集成"),
        GitHubProject("firecracker-microvm/firecracker", "https://github.com/firecracker-microvm/firecracker", 34000,
                      "安全快速微VM", "待集成"),
    ],

    "7_创意设计层": [
        GitHubProject("microsoft/data-formulator", "https://github.com/microsoft/data-formulator", 15500,
                      "AI创建富可视化", "待集成"),
        GitHubProject("HeyPuter/puter", "https://github.com/HeyPuter/puter", 41000,
                      "互联网计算机, 开源自托管", "待集成"),
        GitHubProject("evidence-dev/evidence", "https://github.com/evidence-dev/evidence", 6300,
                      "商业智能 as code", "待集成"),
    ],
}


class GitHubIntegrator:
    """GitHub 项目集成管理器"""

    def __init__(self):
        self.projects = GITHUB_PROJECTS

    def list_projects(self) -> Dict[str, List[Dict]]:
        """列出所有项目"""
        result = {}
        for layer, projects in self.projects.items():
            result[layer] = [
                {
                    "name": p.name,
                    "stars": p.stars,
                    "description": p.description,
                    "status": p.integration_status
                }
                for p in projects
            ]
        return result

    def get_integrated_projects(self) -> List[str]:
        """获取已集成的项目"""
        integrated = []
        for layer, projects in self.projects.items():
            for p in projects:
                if "已集成" in p.integration_status:
                    integrated.append(p.name)
        return integrated

    def get_pending_projects(self) -> Dict[str, List[str]]:
        """获取待集成的项目"""
        pending = {}
        for layer, projects in self.projects.items():
            pending_projects = [p.name for p in projects if "待集成" in p.integration_status]
            if pending_projects:
                pending[layer] = pending_projects
        return pending

    def clone_project(self, project_url: str, target_dir: Optional[str] = None) -> Dict[str, Any]:
        """克隆 GitHub 项目"""
        if target_dir is None:
            target_dir = os.path.join(os.path.dirname(__file__), "integrations")

        # 安全检查：只允许 HTTPS GitHub URL
        if not project_url.startswith("https://github.com/"):
            return {"success": False, "error": "仅支持 github.com HTTPS URL"}

        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", project_url, target_dir],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                return {"success": True, "path": target_dir}
            return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def install_dependency(self, project_name: str, method: str = "pip") -> Dict[str, Any]:
        """安装项目依赖"""
        install_commands = {
            "pip": ["pip", "install", project_name],
            "npm": ["npm", "install", "-g", project_name],
            "cargo": ["cargo", "install", project_name],
        }

        if method not in install_commands:
            return {"success": False, "error": f"不支持的安装方法: {method}"}

        try:
            result = subprocess.run(
                install_commands[method],
                capture_output=True,
                text=True,
                timeout=300
            )
            return {"success": result.returncode == 0, "output": result.stdout}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_integration_guide(self, layer: str) -> str:
        """生成指定层面的集成指南"""
        if layer not in self.projects:
            return f"未知层面: {layer}"

        projects = self.projects[layer]
        guide = f"# {layer} 集成指南\n\n"

        for p in projects:
            guide += f"""## {p.name}
- Stars: {p.stars:,}
- URL: {p.url}
- 描述: {p.description}
- 状态: {p.integration_status}

### 集成步骤
1. 访问: {p.url}
2. 查看 README 了解安装方式
3. 集成到本生态系统

---
"""

        return guide


def show_all_projects():
    """显示所有 GitHub 热门项目"""
    integrator = GitHubIntegrator()

    print("=" * 70)
    print("AI 开发生态系统 - GitHub 热门项目一览")
    print("=" * 70)

    for layer, projects in integrator.list_projects().items():
        print(f"\n{layer}")
        print("-" * 50)
        for p in projects:
            status = "✓" if "已集成" in p["status"] else "○"
            print(f"  {status} {p['name']:40} ⭐ {p['stars']:>7,}")
            print(f"      {p['description'][:50]}...")

    print("\n" + "=" * 70)
    print(f"已集成: {len(integrator.get_integrated_projects())}")
    print(f"待集成: {sum(len(v) for v in integrator.get_pending_projects().values())}")
    print("=" * 70)


if __name__ == "__main__":
    show_all_projects()