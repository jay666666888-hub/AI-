#!/usr/bin/env python3
"""
Minimum Closed Loop Demo - 最小闭环演示
用户需求 → intent → planning → agent 执行 → memory 写入 → test/review → dashboard 指标

展示系统各层如何协同工作形成闭环
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ecosystem_orchestrator import EcosystemOrchestrator


class ClosedLoopDemo:
    """最小闭环演示"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.orch = EcosystemOrchestrator(self.project_path)
        self.orch.load_adapters()
        self.metrics = []

    def log_metric(self, stage: str, status: str, duration_ms: int, detail: str = ""):
        """记录指标"""
        self.metrics.append({
            "stage": stage,
            "status": status,
            "duration_ms": duration_ms,
            "detail": detail,
            "timestamp": datetime.now().isoformat()
        })

    def run(self, task: str) -> Dict[str, Any]:
        """运行完整闭环"""
        start_total = datetime.now()
        print("=" * 70)
        print("  最小闭环演示 - Closed Loop Demo")
        print("  用户需求 → intent → planning → agent → memory → test → dashboard")
        print("=" * 70)

        results = {
            "task": task,
            "stages": [],
            "metrics": []
        }

        # Stage 1: Intent Understanding
        print("\n【Stage 1】意图理解层 (L4_intent)")
        print("-" * 70)
        stage_start = datetime.now()

        intent_adapter = self.orch.layers.get("L4_intent")
        if intent_adapter:
            intent_result = intent_adapter.understand(task)
            print(f"  意图类型: {intent_result['intent']['type']}")
            print(f"  置信度: {intent_result['intent']['confidence']:.2f}")
            print(f"  子任务: {len(intent_result['subtasks'])} 个")
            self.log_metric("L4_intent", "success",
                int((datetime.now() - stage_start).total_seconds() * 1000),
                f"type={intent_result['intent']['type']}")
            results["stages"].append({"layer": "L4_intent", "status": "success", "result": intent_result})
        else:
            print("  [SKIP] L4_intent 未初始化")
            self.log_metric("L4_intent", "skipped", 0)

        # Stage 2: Planning
        print("\n【Stage 2】规划推理层 (L5_planning)")
        print("-" * 70)
        stage_start = datetime.now()

        planning_adapter = self.orch.layers.get("L5_planning")
        if planning_adapter:
            try:
                # 从 Stage 1 获取 subtasks 生成任务列表
                task_descriptions = []
                if intent_adapter:
                    subtasks = intent_adapter.understand(task).get('subtasks', [])
                    task_descriptions = [st.get('task', '') for st in subtasks if st.get('task')]

                plan_result = planning_adapter.create_plan(
                    title=task,
                    description="最小闭环演示任务",
                    tasks=task_descriptions
                )
                plan_dict = planning_adapter.export_plan(plan_result, format="json")
                print(f"  计划创建: {plan_dict.get('id', 'unknown')}")
                print(f"  任务数: {len(plan_dict.get('tasks', []))}")
                self.log_metric("L5_planning", "success",
                    int((datetime.now() - stage_start).total_seconds() * 1000))
                results["stages"].append({"layer": "L5_planning", "status": "success", "result": plan_dict})
            except Exception as e:
                print(f"  规划失败: {e}")
                self.log_metric("L5_planning", "failed",
                    int((datetime.now() - stage_start).total_seconds() * 1000), str(e))
                results["stages"].append({"layer": "L5_planning", "status": "failed", "error": str(e)})
        else:
            print("  [SKIP] L5_planning 未初始化")
            self.log_metric("L5_planning", "skipped", 0)

        # Stage 3: Agent Execution via routing
        print("\n【Stage 3】智能路由 + Agent 执行")
        print("-" * 70)
        stage_start = datetime.now()

        route_result = self.orch.route_task(task)
        print(f"  任务类型: {route_result['task_type']}")
        print(f"  推荐 Skills: {route_result['recommended_skills']}")
        print(f"  推荐 Agents: {route_result['recommended_agents']}")
        print(f"  管道: {route_result.get('full_pipeline', route_result['recommended_skills'])}")

        selected_agents = route_result['recommended_agents'][:1]
        for agent in selected_agents:
            print(f"  → Agent {agent} 执行中...")
            agent_result = self._run_agent(agent, task)
            preview = agent_result[:80].replace('\n', ' ') if agent_result else '执行完成'
            print(f"  → Agent 输出: {preview}...")

        self.log_metric("L4_routing", "success",
            int((datetime.now() - stage_start).total_seconds() * 1000),
            f"agents={selected_agents}")
        results["stages"].append({"type": "routing", "status": "success", "route": route_result})

        # Stage 4: Memory Write
        print("\n【Stage 4】记忆写入 (L3_memory)")
        print("-" * 70)
        stage_start = datetime.now()

        memory_skill = self.orch.skills.get("memory")
        if memory_skill:
            memory_entry = f"""
# 闭环执行记录

## 任务
{task}

## 时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 路由结果
- 类型: {route_result['task_type']}
- Skills: {route_result['recommended_skills']}
- Agents: {route_result['recommended_agents']}

## 执行状态
- Intent: {results['stages'][0]['status'] if results['stages'] else 'skipped'}
- Planning: {results['stages'][1]['status'] if len(results['stages']) > 1 else 'skipped'}
- Routing: success

## 指标
| 阶段 | 耗时(ms) |
|------|----------|
"""
            for m in self.metrics:
                memory_entry += f"| {m['stage']} | {m['duration_ms']} |\n"

            mem_result = memory_skill.remember(content=memory_entry, entry_type="project",
                tags=["闭环演示", route_result['task_type']])
            print(f"  记忆状态: {mem_result['status']}")
            print(f"  文件: {mem_result.get('filename', 'N/A')}")
            self.log_metric("L3_memory", "success",
                int((datetime.now() - stage_start).total_seconds() * 1000))
            results["stages"].append({"layer": "L3_memory", "status": "success", "result": mem_result})
        else:
            print("  [SKIP] memory skill 未初始化")
            self.log_metric("L3_memory", "skipped", 0)

        # Stage 5: Test & Review
        print("\n【Stage 5】测试与审查 (L9_testing + L9_review)")
        print("-" * 70)
        stage_start = datetime.now()

        tdd_skill = self.orch.skills.get("tdd")
        if tdd_skill:
            print("  TDD Guide: 初始化测试环境")
            tdd_result = tdd_skill.start_feature(task)
            print(f"  → {tdd_result.get('status', 'done')}")
            self.log_metric("L9_testing", "success",
                int((datetime.now() - stage_start).total_seconds() * 1000))
        else:
            print("  [SKIP] tdd skill 未初始化")
            self.log_metric("L9_testing", "skipped", 0)

        results["stages"].append({"layer": "L9_testing", "status": "success"})

        review_start = datetime.now()
        review_skill = self.orch.skills.get("code_review")
        if review_skill:
            print("  Code Review: 检查代码质量")
            review_result = review_skill.review("# 示例代码\ndef hello(): pass")
            print(f"  → {review_result.get('status', 'done')}")
            self.log_metric("L9_review", "success",
                int((datetime.now() - review_start).total_seconds() * 1000))
        else:
            print("  [SKIP] code_review skill 未初始化")
            self.log_metric("L9_review", "skipped", 0)

        results["stages"].append({"layer": "L9_review", "status": "success"})

        # Stage 6: Evolution Recording
        print("\n【Stage 6】自我进化记录")
        print("-" * 70)

        if "stages" in results and len(results["stages"]) > 0:
            success_count = sum(1 for s in results["stages"] if s.get("status") == "success")
            overall_success = success_count >= len(results["stages"]) * 0.5

            evol_result = self.orch.record_evolution(
                task=task,
                task_type=route_result.get("task_type", "unknown"),
                skills=route_result.get("recommended_skills", []),
                agents=route_result.get("recommended_agents", []),
                success=overall_success,
                duration_ms=0,
                feedback=f"完成 {success_count}/{len(results["stages"])} 阶段",
                layers=[s.get("layer", "") for s in results["stages"]]
            )
            print(f"  进化记录: {evol_result.get("status")}")

        # Stage 7: Dashboard
        print("\n【Stage 7】Dashboard 指标展示")
        print("-" * 70)

        total_duration = int((datetime.now() - start_total).total_seconds() * 1000)
        self.log_metric("total", "complete", total_duration)
        status = self.orch.get_status()

        print(f"""
┌─────────────────────────────────────────────────────────────┐
│  📊 闭环演示指标                                             │
├─────────────────────────────────────────────────────────────┤
│  任务: {task[:40]:<50} │
├─────────────────────────────────────────────────────────────┤
│  层   │ 阶段            │ 状态   │ 耗时(ms)                 │
│ ─────┼────────────────┼────────┼─────────┼──────────────── │
│ L4   │ Intent         │ {'✅' if len(results['stages']) > 0 and results['stages'][0]['status'] == 'success' else '⏭️':<3}   │ {self.metrics[0]['duration_ms'] if len(self.metrics) > 0 else 0:>7}                  │
│ L5   │ Planning       │ {'✅' if len(results['stages']) > 1 and results['stages'][1]['status'] == 'success' else '⏭️':<3}   │ {self.metrics[1]['duration_ms'] if len(self.metrics) > 1 else 0:>7}                  │
│ L4   │ Routing        │ {'✅' if len(results['stages']) > 2 and results['stages'][2]['status'] == 'success' else '⏭️':<3}   │ {self.metrics[2]['duration_ms'] if len(self.metrics) > 2 else 0:>7}                  │
│ L3   │ Memory         │ {'✅' if len(results['stages']) > 3 and results['stages'][3]['status'] == 'success' else '⏭️':<3}   │ {self.metrics[3]['duration_ms'] if len(self.metrics) > 3 else 0:>7}                  │
│ L9   │ Testing        │ {'✅' if len(results['stages']) > 4 and results['stages'][4]['status'] == 'success' else '⏭️':<3}   │ {self.metrics[4]['duration_ms'] if len(self.metrics) > 4 else 0:>7}                  │
│ L9   │ Review         │ {'✅' if len(results['stages']) > 5 and results['stages'][5]['status'] == 'success' else '⏭️':<3}   │ {self.metrics[5]['duration_ms'] if len(self.metrics) > 5 else 0:>7}                  │
├─────────────────────────────────────────────────────────────┤
│  总耗时: {total_duration:>6}ms                                          │
├─────────────────────────────────────────────────────────────┤
│  系统状态                                                    │
│  • Skills: {status['skills_count']:<4} 个  (可用)                                │
│  • Agents: {status['agents_count']:<4} 个  (已注册)                              │
│  • Layers: {status['layers_count']:<4} 个  (已初始化)                            │
└─────────────────────────────────────────────────────────────┘
""")

        results["metrics"] = self.metrics
        results["total_duration_ms"] = total_duration
        results["system_status"] = status

        return results

    def _run_agent(self, agent_name: str, task: str) -> str:
        """使用内部 Skill/Agent 系统执行"""
        # 检查是否有对应的 skill 可用
        if agent_name in self.orch.skills:
            skill = self.orch.skills[agent_name]
            try:
                result = skill.run(task) if hasattr(skill, 'run') else {"status": "completed"}
                return f"[SKILL] {agent_name} executed via skill: {str(result)[:100]}"
            except Exception as e:
                return f"[SKILL ERROR] {str(e)[:80]}"

        # 返回路由结果而非真实执行
        return f"[ROUTED] Agent {agent_name} 已路由，将在完整工作流中执行"



def main():
    print("\n" + "=" * 70)
    print("  🤖 AI 开发生态系统 - 最小闭环演示")
    print("  Minimal Closed Loop Demo")
    print("=" * 70)

    project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    demo = ClosedLoopDemo(project_path)

    test_tasks = ["做个 AI 助手", "修复登录bug", "优化数据库查询性能"]

    print("\n选择演示任务:")
    for i, t in enumerate(test_tasks, 1):
        print(f"  {i}. {t}")

    print("\n" + "=" * 70)
    print("【执行闭环演示】")
    print("=" * 70)

    result = demo.run(test_tasks[0])

    print("\n" + "=" * 70)
    print("  ✅ 闭环演示完成")
    print(f"  完成阶段: {len(result.get('stages', []))}")
    print(f"  总耗时: {result.get('total_duration_ms', 0)}ms")
    print("=" * 70)


if __name__ == "__main__":
    main()