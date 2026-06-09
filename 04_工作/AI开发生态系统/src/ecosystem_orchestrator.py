#!/usr/bin/env python3
"""
Ralph Ecosystem Orchestrator - 完整生态系统编排器
整合: 11 Skills + 58 Agents + 13 Layers + 智能路由
"""

import os, json
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from skills.evolution_skill import get_evolution_skill
from infrastructure.tools.unified_calibration import UnifiedCalibrationSystem
from infrastructure.tools.human_override_recorder import HumanOverrideRecorder, OverrideType, OverrideReason
from infrastructure.tools.delayed_outcome_tracker import DelayedOutcomeTracker, DelayedCheckpoints
from infrastructure.policy_update_engine import PolicyUpdateEngine
from integrations.security_adapter import SecurityAdapter

@dataclass
class LayerResult:
    layer: str
    status: str
    output: str
    error: str
    duration_ms: int
    timestamp: str

class EcosystemOrchestrator:
    """生态系统编排器 - 整合所有组件"""

    def __init__(self, project_path=None):
        self.project_path = project_path or os.getcwd()
        self.layers = {}
        self.skills = {}
        self.agents = {}
        self.skill_router = None
        self.ready = False

    def load_adapters(self):
        """加载所有 adapters、skills 和 agents"""
        import sys
        sys.path.insert(0, os.path.join(self.project_path, "src"))

        # 加载 Integrations (Layers)
        from integrations import (
            IntentUnderstandingAdapter, PlanningAdapter,
            GrafanaAdapter, ArgoCDAdapter, DockerAdapter, KubernetesAdapter,
            UptimeKumaAdapter, VaultAdapter, GitHubIntegrator,
            L11KnowledgeRetrievalLayer
        )

        # 加载 Skills (11个)
        from skills import (
            BrainstormingSkill, WritingPlansSkill, SystematicDebuggingSkill,
            TDDGuideSkill, CodeReviewSkill, VerificationSkill, BuildSkill,
            GateGuardSkill, ContinuousAgentLoop, E2ETestSkill, MemorySkill
        )

        # 加载 Agent Registry
        from skills import AgentRegistry, list_all_agents, SkillRouter

        # 初始化 Layers
        self.layers = {
            "L4_intent": IntentUnderstandingAdapter(),
            "L5_planning": PlanningAdapter(self.project_path),
            "L9_testing": TDDGuideSkill(),
            "L9_review": CodeReviewSkill(),
            "L9_e2e": E2ETestSkill(),
            "L10_monitoring": GrafanaAdapter(),
            "L10_uptime": UptimeKumaAdapter(),
            "L12_container": DockerAdapter(),
            "L14_deploy": DockerAdapter(),  # Docker 部署替代 ArgoCD
            "L14_k8s": KubernetesAdapter(),
            "L8_security": VaultAdapter(),
            "L1_github": GitHubIntegrator(),
            "L3_memory": MemorySkill(),
            "L11_rag": L11KnowledgeRetrievalLayer(self.project_path),
        }

        # 初始化 Skills
        self.skills = {
            "brainstorming": BrainstormingSkill(),
            "writing_plans": WritingPlansSkill(),
            "systematic_debugging": SystematicDebuggingSkill(),
            "tdd": TDDGuideSkill(),
            "code_review": CodeReviewSkill(),
            "verification": VerificationSkill(),
            "build": BuildSkill(),
            "e2e_test": E2ETestSkill(),
            "memory": MemorySkill(),
            "gateguard": GateGuardSkill(),
            "agent_loop": ContinuousAgentLoop(),
        }

        # 初始化 Agents (58个)
        self.agents = {name: {"name": name} for name in list_all_agents()}

        # 初始化路由
        self.skill_router = SkillRouter(self.skills)

        # 初始化进化系统
        self.evolution = get_evolution_skill()

        # 初始化 Reality Alignment 系统
        self.calibration = UnifiedCalibrationSystem()
        self.human_overrides = HumanOverrideRecorder()
        self.delayed_tracker = DelayedOutcomeTracker()
        self.policy_engine = PolicyUpdateEngine()
        self.security_adapter = SecurityAdapter(self.project_path)

        self.ready = True

    def route_task(self, task: str) -> Dict[str, Any]:
        """路由任务 - 返回技能、Agent 和工具推荐"""
        if not self.ready:
            self.load_adapters()
        return self.skill_router.route(task)

    def run_workflow(self, task: str, mode: str = "full") -> Dict[str, Any]:
        """运行工作流"""
        if not self.ready:
            self.load_adapters()

        print("=" * 60)
        print("  Ralph Ecosystem Orchestrator v4.0")
        print("  11 Skills + 58 Agents + 13 Layers + 智能路由")
        print("=" * 60)

        # 自动路由
        route_result = self.route_task(task)
        task_type = route_result['task_type']
        predicted_confidence = route_result['confidence']

        print(f"\n🎯 路由结果:")
        print(f"   任务类型: {task_type}")
        print(f"   置信度: {predicted_confidence:.2f}")
        print(f"   Skills: {route_result['recommended_skills']}")
        print(f"   Agents: {route_result['recommended_agents']}")
        print(f"   Layers: {route_result['recommended_layers']}")

        results = []
        execution_start = datetime.now()

        if mode == "auto":
            # 自动模式 - 根据路由结果执行
            pipeline = route_result.get('full_pipeline', route_result['recommended_skills'] + route_result['recommended_agents'] + route_result['recommended_layers'])
            print(f"\n📋 执行管道: {pipeline}")
            
            for i, item in enumerate(pipeline, 1):
                print(f"\n[{i}/{len(pipeline)}] {item}...")
                r = self._run_pipeline_item(item, task)
                results.append(r)
                print(f"   → {r.get('status', 'unknown')}")

        elif mode == "full":
            # 完整模式
            stages = [
                ("brainstorming", task),
                ("writing_plans", task),
                ("tdd", {"feature": task}),
                ("build", {"goal": task}),
                ("code_review", {"code": task}),
                ("verification", task),
                ("e2e_test", {"suite": "main"}),
            ]

            for i, (skill_name, input_data) in enumerate(stages, 1):
                print(f"\n[{i}/7] {skill_name}...")
                r = self._run_skill(skill_name, input_data)
                results.append(r)

        # 汇总
        success = sum(1 for r in results if r.get("status") == "success")
        duration_ms = int((datetime.now() - execution_start).total_seconds() * 1000)

        print("\n" + "=" * 60)
        print(f"  完成: {success}/{len(results)} 阶段成功")
        print("=" * 60)

        # ===== 安全扫描（L8） =====
        security_result = None
        if mode == "full":
            print("\n🔒 执行安全扫描...")
            try:
                security_result = self.security_adapter.scan_all(self.project_path)
                if security_result.get("skipped"):
                    print(f"  ⏭️ 安全扫描跳过: {security_result.get('skipped_reason', 'unknown')}")
                elif security_result.get("total_findings", 0) > 0:
                    print(f"  ⚠️ 发现 {security_result['total_findings']} 个安全问题")
                    for finding in security_result.get("findings", [])[:3]:
                        print(f"     [{finding.severity}] {finding.title} @ {finding.file}:{finding.line}")
                    # 阻断：如果有严重问题
                    if self.security_adapter.block_if_critical(security_result):
                        print("  🚨 安全阻断：发现严重问题，终止执行")
                        return {
                            "task": task,
                            "route": route_result,
                            "stages_completed": len(results),
                            "success_count": 0,
                            "blocked": True,
                            "block_reason": "security",
                            "security_result": security_result
                        }
                else:
                    print("  ✅ 无安全问题")
            except Exception as e:
                print(f"  ⚠️ 安全扫描失败: {e}")

        # ===== 反馈回路：记录执行结果到 Reality Alignment 系统 =====
        outcome_success = success == len(results) if results else False

        # 提取实际质量分数（从各 skill 结果中）
        quality_scores = []
        for r in results:
            if r.get('result'):
                # 检查是否有质量分数
                res = r.get('result', {})
                if isinstance(res, dict):
                    if 'score' in res:
                        quality_scores.append(res['score'])
                    elif 'coverage' in res:
                        quality_scores.append(res['coverage'])
                    elif 'quality' in res:
                        quality_scores.append(res['quality'])

        # 计算平均质量分数（连续值）
        actual_score = sum(quality_scores) / len(quality_scores) if quality_scores else (1.0 if outcome_success else 0.0)

        # 1. 记录到 Unified Calibration System（用于 ECE 计算）
        self.calibration.record_outcome(task_type, predicted_confidence, actual_score)
        ece = self.calibration.calibrator.get_ece(task_type)

        # 2. 记录到 Delayed Outcome Tracker（T+1h/6h/24h 重新评估）
        task_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.delayed_tracker.track(task_id, task_type, actual_score, outcome_success)
        # 调度延迟检查点
        self.delayed_tracker.register_checkpoint_handler(DelayedCheckpoints.T_PLUS_1H, lambda: self._recheck_delayed_outcome)
        self.delayed_tracker.register_checkpoint_handler(DelayedCheckpoints.T_PLUS_6H, lambda: self._recheck_delayed_outcome)
        self.delayed_tracker.register_checkpoint_handler(DelayedCheckpoints.T_PLUS_24H, lambda: self._recheck_delayed_outcome)

        # 3. 记录到 Evolution Skill（用于自适应路由）
        self.evolution.record_execution(
            task=task,
            task_type=task_type,
            skills=route_result['recommended_skills'],
            agents=route_result['recommended_agents'],
            success=outcome_success,
            duration_ms=duration_ms,
            feedback=f"quality={actual_score:.2f}, ece={ece:.3f}",
            layers=route_result['recommended_layers']
        )

        # 4. 记录到 Policy Update Engine（策略学习）
        expected_utility = predicted_confidence
        actual_utility = actual_score
        outcome_type = "success" if outcome_success else "failure"
        self.policy_engine.process_experience(
            execution_id=task_id,
            context={"task_type": task_type, "mode": mode},
            action=f"skill:{route_result['recommended_skills'][0]}" if route_result['recommended_skills'] else "unknown",
            expected_utility=expected_utility,
            actual_utility=actual_utility,
            outcome_type=outcome_type,
            duration_ms=duration_ms
        )

        print(f"\n📊 Reality Alignment 反馈已记录:")
        print(f"   Task Type: {task_type}")
        print(f"   Predicted: {predicted_confidence:.2f} | Actual: {actual_score:.2f}")
        print(f"   ECE: {ece:.3f}")
        print(f"   Policy Update: {'Applied' if outcome_success else 'Failed'}")

        return {
            "task": task,
            "route": route_result,
            "stages_completed": len(results),
            "success_count": success,
            "quality_score": actual_score,
            "ece": ece,
            "results": results
        }

    def _run_pipeline_item(self, item: str, task: str) -> Dict[str, Any]:
        """执行管道中的单个项目"""
        start = datetime.now()

        # 优先检查是否是 skill
        if item in self.skills:
            return self._run_skill(item, task)
        
        # 然后检查是否是 agent
        if item in self.agents:
            return {
                "type": "agent",
                "name": item,
                "status": "routed",
                "duration_ms": int((datetime.now() - start).total_seconds() * 1000),
                "note": f"Agent {item} 已路由，请使用 Agent 调用执行"
            }

        # 最后检查是否是 layer
        if item in self.layers:
            return self._run_layer(item, task)

        return {"item": item, "status": "unknown_type"}

    def _run_skill(self, skill_name: str, input_data: Any) -> Dict[str, Any]:
        """运行单个 skill"""
        if skill_name not in self.skills:
            return {"skill": skill_name, "status": "not_found"}

        skill = self.skills[skill_name]
        start = datetime.now()

        try:
            if skill_name == "brainstorming":
                result = skill.run(input_data)
            elif skill_name == "writing_plans":
                result = skill.run(input_data)
            elif skill_name == "tdd":
                if isinstance(input_data, dict):
                    result = skill.start_feature(input_data.get("feature", ""))
                else:
                    result = skill.start_feature(str(input_data))
            elif skill_name == "code_review":
                code = input_data.get("code", "") if isinstance(input_data, dict) else str(input_data)
                result = skill.review(code)
            elif skill_name == "verification":
                code = input_data if isinstance(input_data, str) else str(input_data)
                result = skill.verify(code)
            elif skill_name == "build":
                if isinstance(input_data, dict):
                    result = skill.create_plan(input_data.get("goal", ""), input_data.get("tasks", []))
                else:
                    result = skill.create_plan(str(input_data), [])
            elif skill_name == "e2e_test":
                if isinstance(input_data, dict):
                    suite_name = input_data.get("suite", "default")
                    test_name = input_data.get("test")
                    skill.create_suite(suite_name)
                    if test_name:
                        skill.add_test(test_name, "")
                        result = skill.run_test(test_name, suite_name)
                    else:
                        result = skill.run_suite(suite_name)
                else:
                    result = {"status": "need_dict_input"}
            elif skill_name == "memory":
                result = skill.get_status()
            else:
                result = {"status": "completed"}

            return {
                "type": "skill",
                "name": skill_name,
                "status": "success",
                "duration_ms": int((datetime.now() - start).total_seconds() * 1000),
                "result": result
            }
        except Exception as e:
            return {
                "type": "skill",
                "name": skill_name,
                "status": "failed",
                "error": str(e)
            }

    def _run_layer(self, layer_name: str, task: Dict) -> Dict[str, Any]:
        """运行单个 layer"""
        if layer_name not in self.layers:
            return {"layer": layer_name, "status": "not_found"}

        layer = self.layers[layer_name]
        start = datetime.now()

        try:
            if hasattr(layer, "understand"):
                task_input = task.get("input", str(task)) if isinstance(task, dict) else task
                result = layer.understand(task_input)
            elif hasattr(layer, "create_plan"):
                result = layer.create_plan("Task", "", [])
            elif hasattr(layer, "sync"):
                # sync 需要 app 参数，ArgoCD
                try:
                    result = layer.sync(app=task.get("app", "default-app"))
                except TypeError:
                    result = layer.sync()
            elif hasattr(layer, "get_status"):
                result = layer.get_status()
            else:
                result = {"status": "unknown_method"}

            return {
                "type": "layer",
                "name": layer_name,
                "status": "success",
                "duration_ms": int((datetime.now() - start).total_seconds() * 1000),
                "result": result
            }
        except Exception as e:
            return {
                "type": "layer",
                "name": layer_name,
                "status": "failed",
                "error": str(e)
            }

    def record_evolution(self, task: str, task_type: str, skills: List[str],
                        agents: List[str], success: bool, duration_ms: int,
                        feedback: str = "", layers: List[str] = None) -> Dict[str, Any]:
        """记录执行结果用于进化学习"""
        return self.evolution.record_execution(task, task_type, skills, agents,
                                            success, duration_ms, feedback, layers)

    def get_evolution_status(self) -> Dict[str, Any]:
        """获取进化系统状态"""
        return self.evolution.get_status()

    def get_reality_alignment_status(self) -> Dict[str, Any]:
        """获取 Reality Alignment 系统整体状态"""
        # ECE 统计
        ece_by_type = {}
        for tt in ['build', 'deploy', 'delete', 'research', 'fix', 'review', 'create', 'test', 'review', 'unknown']:
            ece = self.calibration.calibrator.get_ece(tt)
            if ece > 0:
                ece_by_type[tt] = round(ece, 4)

        # 延迟追踪统计
        delayed_summary = self.delayed_tracker.get_summary()

        # Policy 学习状态
        policy_status = self.policy_engine.get_learning_status()

        # Evolution 状态
        evolution_status = self.evolution.get_status()

        return {
            "calibration": {
                "ece_by_task_type": ece_by_type,
                "overall_ece": round(sum(ece_by_type.values()) / len(ece_by_type), 4) if ece_by_type else 0
            },
            "delayed_outcomes": delayed_summary,
            "policy_learning": policy_status,
            "evolution": evolution_status
        }

    def import_evolution_history_to_calibration(self):
        """
        将 EvolutionSkill 的历史执行数据导入 UnifiedCalibrationSystem
        补历史欠账，让新公式有数据可用
        """
        try:
            evolution_dir = os.path.expanduser("~/.claude/projects/-mnt-c-Users-Admin/evolution")
            history_file = os.path.join(evolution_dir, 'execution_history.json')

            if not os.path.exists(history_file):
                return {"imported": 0, "status": "no_file"}

            with open(history_file, 'r', encoding='utf-8') as f:
                records = json.load(f)

            imported = 0
            for record in records:
                task_type = record.get('task_type', 'unknown')
                feedback = record.get('feedback', '')
                quality = 1.0 if record.get('success', False) else 0.0
                if 'quality=' in feedback:
                    try:
                        quality = float(feedback.split('quality=')[1].split(',')[0])
                    except:
                        pass

                predicted = 0.7  # 旧数据没有置信度，默认 0.7
                self.calibration.record_outcome(task_type, predicted, quality)
                imported += 1

            return {"imported": imported, "status": "success"}
        except Exception as e:
            return {"imported": 0, "status": "error", "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "skills_count": len(self.skills),
            "agents_count": len(self.agents),
            "layers_count": len(self.layers),
            "ready": self.ready
        }

    def run_ralph_cycle(self, task: str, use_skills: bool = True) -> Dict[str, Any]:
        """兼容旧接口"""
        return self.run_workflow(task, mode="auto" if use_skills else "planning")


if __name__ == "__main__":
    orch = EcosystemOrchestrator()
    orch.load_adapters()

    status = orch.get_status()
    print(f"\n📦 系统状态:")
    print(f"   Skills: {status['skills_count']} 个")
    print(f"   Agents: {status['agents_count']} 个")
    print(f"   Layers: {status['layers_count']} 个")

    print("\n" + "=" * 60)
    print("【自动路由 + 执行测试】")
    
    task = "做个 AI 助手"
    result = orch.route_task(task)
    print(f"\n任务: {task}")
    print(f"类型: {result['task_type']}")
    print(f"管道: {result.get('full_pipeline', result['recommended_skills'] + result['recommended_agents'] + result['recommended_layers'])}")

    print("\n" + "=" * 60)
    print("【执行工作流】")
    result = orch.run_workflow(task, mode="auto")
    print(f"\n结果: {result['success_count']}/{result['stages_completed']} 成功")
