#!/usr/bin/env python3
"""
Ralph 循环任务 - AI 开发生态系统自我完善
基于 EcosystemOrchestrator 的自主循环开发系统
消耗 ralph_tasks.json 中的任务队列
"""

import sys
import os
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 添加项目路径
PROJECT_PATH = "/mnt/e/黑曜石/04_工作/AI开发生态系统"
TASKS_FILE = os.path.join(PROJECT_PATH, "ralph_tasks.json")
sys.path.insert(0, os.path.join(PROJECT_PATH, "src"))

from ecosystem_orchestrator import EcosystemOrchestrator
from skills.agent_loop import ContinuousAgentLoop, LoopMode

class RalphLoopTask:
    """Ralph 风格的循环任务执行器 - 消费任务队列"""

    def __init__(self, project_path: str = PROJECT_PATH):
        self.project_path = project_path
        self.tasks_file = TASKS_FILE
        self.orchestrator = None
        self.loop = None
        self.iteration = 0
        self.max_iterations = 999999  # 近无限
        self.results_history = []
        self.task_queue = []
        self.current_task = None

    def load_tasks(self) -> list:
        """从 JSON 文件加载任务队列"""
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.task_queue = data.get('task_queue', [])
                print(f"📋 加载任务队列: {len(self.task_queue)} 个任务")
                for task in data.get('tasks', []):
                    status = "⏳ 待处理" if task['id'] in self.task_queue else "✅ 已完成"
                    print(f"   {task['id']} [{task['priority']}] {task['title']} - {status}")
                return self.task_queue
        except Exception as e:
            print(f"⚠️  无法加载任务文件: {e}")
            return []

    def initialize(self):
        """初始化生态系统编排器"""
        print("=" * 70)
        print("  Ralph Loop Task - AI 开发生态系统自我完善")
        print("=" * 70)
        print(f"\n初始化时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"项目路径: {self.project_path}")

        self.orchestrator = EcosystemOrchestrator(self.project_path)
        self.orchestrator.load_adapters()

        status = self.orchestrator.get_status()
        print(f"\n📦 系统状态:")
        print(f"   Skills: {status['skills_count']} 个")
        print(f"   Agents: {status['agents_count']} 个")
        print(f"   Layers: {status['layers_count']} 个")

        self.loop = ContinuousAgentLoop(mode="sequential")
        print("\n✅ 初始化完成")

        # 加载任务队列
        print("\n" + "-" * 50)
        self.load_tasks()

        return status

    def get_next_task(self) -> dict:
        """获取下一个任务"""
        if not self.task_queue:
            return None
        task_id = self.task_queue[0]
        # 找到任务详情
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for task in data.get('tasks', []):
                    if task['id'] == task_id:
                        return task
        except:
            pass
        return {"id": task_id, "title": task_id, "description": ""}

    def run_closed_loop(self, goal: str = None):
        """
        运行闭环测试循环 - 无限循环消费任务队列

        循环流程:
        1. 获取下一个任务（队列空则自动生成）
        2. brainstorming - 理解任务目标
        3. tdd - 编写测试
        4. build - 实现功能
        5. code_review - 代码审查
        6. verification - 验证
        7. e2e_test - 端到端测试
        8. pytest 验证
        """

        print("\n" + "=" * 70)
        print(f"  🎯 Ralph 自主循环 - 无限执行模式")
        print("=" * 70)

        iteration = 0
        while True:  # 无限循环
            iteration += 1
            self.iteration = iteration
            ts = datetime.now().strftime('%H:%M:%S')

            # 获取下一个任务（队列空则生成新任务）
            if not self.task_queue:
                print("\n📋 任务队列已空，正在生成新任务...")
                self._generate_next_tasks()
                if not self.task_queue:
                    print("\n⚠️  无法生成新任务，循环终止")
                    break

            task = self.get_next_task()
            if not task:
                break

            self.current_task = task
            task_id = task['id']
            task_title = task['title']

            print(f"\n{'='*70}")
            print(f"  【迭代 #{iteration}】任务: {task_id} - {task_title}")
            print(f"  时间: {ts}")
            print(f"  剩余任务: {len(self.task_queue)}")
            print(f"{'='*70}")

            # 检查循环状态
            if self.loop.state.status == "frozen":
                print(f"\n⚠️  循环已冻结! 运行审计...")
                audit_result = self.loop.audit()
                print(f"   状态: {audit_result['status']}")
                print(f"   问题数: {len(audit_result['issues'])}")
                print(f"   建议: {audit_result['recommendation']}")

                if "freeze" in audit_result['recommendation'].lower():
                    print("\n🔒 达到冻结条件，循环终止")
                    break
                else:
                    print("\n🔄 尝试恢复循环...")
                    self.loop.recover()

            # Stage 1: Brainstorming - 理解任务
            print(f"\n[Stage 1/6] 🔥 brainstorming...")
            result = self._run_skill_stage("brainstorming", task['description'])
            self._record_result(task_id, "brainstorming", result)

            # Stage 2: TDD - 编写测试
            print(f"\n[Stage 2/6] 🧪 tdd (RED 阶段)...")
            result = self._run_skill_stage("tdd", {"feature": task_title})
            self._record_result(task_id, "tdd", result)

            # Stage 3: Build - 实现
            print(f"\n[Stage 3/6] 🔨 build (实现功能)...")
            result = self._run_skill_stage("build", {"goal": task_title, "tasks": []})
            self._record_result(task_id, "build", result)

            # Stage 4: Code Review
            print(f"\n[Stage 4/6] 👀 code_review (GREEN→REFACTOR)...")
            result = self._run_skill_stage("code_review", {"code": task_title})
            self._record_result(task_id, "code_review", result)

            # Stage 5: Verification
            print(f"\n[Stage 5/6] ✅ verification...")
            result = self._run_skill_stage("verification", task_title)
            self._record_result(task_id, "verification", result)

            # Stage 6: E2E Test
            print(f"\n[Stage 6/6] 🧪 e2e_test (端到端测试)...")
            result = self._run_skill_stage("e2e_test", {"suite": task_id})
            self._record_result(task_id, "e2e_test", result)

            # 循环迭代检查点
            self.loop.checkpoint(f"Task {task_id} iteration {iteration}")
            self.loop.run_iteration(task_title)

            # 从队列移除已完成任务
            self.task_queue.pop(0)
            print(f"\n✅ 任务 {task_id} 本轮完成")

            # 运行测试验证
            print(f"\n{'='*70}")
            print(f"  📋 迭代 #{iteration} 完成 - 运行测试验证")
            print(f"{'='*70}")

            test_result = self._run_tests()
            print(f"\n🧪 pytest 结果: {test_result['summary']}")

            # 检查是否需要冻结
            if test_result['failed'] > 0 and iteration > 3:
                self.loop.freeze(f"测试失败: {test_result['failed_count']} 个")

            time.sleep(0.5)

        # 最终报告
        self._print_final_report()

    def _generate_next_tasks(self):
        """当任务队列空时，基于当前状态生成新任务"""
        # 基于测试覆盖率和系统状态生成新任务
        test_result = self._run_tests()
        passed = test_result.get('passed', 0)

        new_tasks = []

        # 如果测试覆盖率低，生成覆盖率提升任务
        if passed < 30:
            new_tasks.append({
                "id": f"ECO-COVERAGE-{self.iteration}",
                "priority": "HIGH",
                "title": "提升测试覆盖率",
                "description": "当前测试数量不足，需要编写更多单元测试"
            })

        # 基于 Skills 状态生成完善任务
        skills_to_improve = []
        for name, skill in self.orchestrator.skills.items():
            status = getattr(skill, 'state', None)
            if status and hasattr(status, 'status'):
                if status.status in ['unknown', None]:
                    skills_to_improve.append(name)

        for skill_name in skills_to_improve[:3]:
            new_tasks.append({
                "id": f"ECO-SKILL-{skill_name.upper()}-{self.iteration}",
                "priority": "MEDIUM",
                "title": f"完善 {skill_name} skill",
                "description": f"需要完善 {skill_name} skill 的实现，连接真实服务"
            })

        # 添加到队列
        for task in new_tasks:
            self.task_queue.append(task['id'])
            # 更新任务文件
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['tasks'].append(task)
                data['task_queue'] = self.task_queue
                with open(self.tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except:
                pass

        if new_tasks:
            print(f"📝 生成了 {len(new_tasks)} 个新任务:")
            for t in new_tasks:
                print(f"   {t['id']} [{t['priority']}] {t['title']}")

    def _run_skill_stage(self, skill_name: str, input_data) -> dict:
        """运行单个技能阶段 - 使用 SkillExecutor 实现真正执行"""
        try:
            from skills.skill_executor import SkillExecutor
            executor = SkillExecutor(self.project_path)

            # 先调用原始 skill 获取 instruction
            if skill_name == "brainstorming":
                instruction = self.orchestrator.skills[skill_name].run(input_data)
            elif skill_name == "systematic_debugging":
                instruction = self.orchestrator.skills[skill_name].run(input_data)
            elif skill_name == "tdd":
                feature = input_data.get("feature", "") if isinstance(input_data, dict) else input_data
                instruction = self.orchestrator.skills[skill_name].start_feature(feature)
            elif skill_name == "build":
                goal = input_data.get("goal", "") if isinstance(input_data, dict) else input_data
                instruction = self.orchestrator.skills[skill_name].create_plan(goal, [])
            elif skill_name == "code_review":
                code = input_data.get("code", "") if isinstance(input_data, dict) else input_data
                instruction = self.orchestrator.skills[skill_name].review(code)
            elif skill_name == "verification":
                code = input_data if isinstance(input_data, str) else str(input_data)
                instruction = self.orchestrator.skills[skill_name].verify(code)
            elif skill_name == "e2e_test":
                suite = input_data.get("suite", "default") if isinstance(input_data, dict) else "default"
                instruction = self.orchestrator.skills[skill_name].run_suite(suite)
            else:
                return {"status": "unknown_skill"}

            # 使用 SkillExecutor 执行 instruction
            exec_result = executor.execute(skill_name, instruction)

            status = "success" if exec_result.get("status") not in ["failed", "error"] else "failed"
            print(f"   → {status}")

            return {"status": status, "result": exec_result, "executed": True}
        except Exception as e:
            print(f"   → failed: {str(e)[:50]}")
            return {"status": "failed", "error": str(e)}

    def _run_tests(self) -> dict:
        """运行测试套件"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/test_ecosystem.py", "-v", "--tb=line"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            output = result.stdout + result.stderr

            # 解析测试结果
            passed = output.count("PASSED")
            failed = output.count("FAILED")

            return {
                "summary": f"{passed} passed, {failed} failed",
                "passed": passed,
                "failed": failed,
                "failed_count": failed
            }
        except Exception as e:
            return {"summary": f"Error: {str(e)}", "passed": 0, "failed": 0, "failed_count": 0}

    def _record_result(self, task_id: str, stage: str, result: dict):
        """记录阶段结果"""
        self.results_history.append({
            "iteration": self.iteration,
            "task_id": task_id,
            "stage": stage,
            "status": result.get("status", "unknown"),
            "timestamp": datetime.now().isoformat()
        })

    def _print_final_report(self):
        """打印最终报告"""
        print("\n" + "=" * 70)
        print("  📊 Ralph 循环任务 - 最终报告")
        print("=" * 70)

        total = len(self.results_history)
        success = sum(1 for r in self.results_history if r["status"] == "success")
        failed = total - success

        print(f"\n总迭代次数: {self.iteration}")
        print(f"总阶段数: {total}")
        print(f"成功: {success}")
        print(f"失败: {failed}")
        print(f"成功率: {success/total*100:.1f}%" if total > 0 else "N/A")

        # 最后一次测试运行
        print("\n" + "-" * 50)
        print("最后测试运行:")
        test_result = self._run_tests()
        print(f"结果: {test_result['summary']}")

        print("\n循环状态:")
        audit = self.loop.audit()
        print(f"  状态: {audit['status']}")
        print(f"  迭代: {audit['iterations']}")
        print(f"  检查点: {audit['checkpoints']}")
        print(f"  问题: {audit['issues']}")
        print(f"  建议: {audit['recommendation']}")


def main():
    """主入口"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║     █████╗ ██╗   ██╗██╗██╗╗██╗  ██╗███████╗██████╗  ██████╗ ██████╗ ██╗   ║
║    ██╔══██╗██║   ██║██║██║╚██╗██╔╝██╔════╝██╔══██╗██╔═══██╗██╔══██╗╚██╗  ║
║    ███████║██║   ██║██║██║ ╚███╔╝ █████╗  ██████╔╝██║   ██║██████╔╝ ╚██╗ ║
║    ██╔══██║╚██╗ ██╔╝██║██║ ██╔██╗ ██╔══╝  ██╔══██╗██║   ██║██╔══██╗ ██║ ║
║    ██║  ██║ ╚████╔╝ ██║██║██╔╝ ██╗███████╗██║  ██║╚██████╔╝██║  ██║██║ ║
║    ╚═╝  ╚═╝  ╚═══╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝ ║
║                                                                           ║
║              自主循环任务 - AI 开发生态系统自我完善                          ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    task = RalphLoopTask()
    task.initialize()

    # 运行闭环测试 - 消费任务队列
    task.run_closed_loop()


if __name__ == "__main__":
    main()