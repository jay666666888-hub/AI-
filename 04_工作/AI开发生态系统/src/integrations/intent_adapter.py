#!/usr/bin/env python3
"""
Intent Adapter - 意图理解层集成 v2.1
L4 意图理解层 - 完整版：35 意图类型、多意图检测、实体识别、参数提取
"""

import re
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class IntentType(Enum):
    """意图类型 (35 种)"""
    # 基础操作类
    CREATE = "create"           # 创建新项目/功能
    MODIFY = "modify"          # 修改现有功能
    DELETE = "delete"          # 删除功能
    READ = "read"              # 读取/查看
    UPDATE = "update"          # 更新数据
    LIST = "list"              # 列出/列举
    
    # 开发流程类
    FIX = "fix"                # 修复 bug
    REFACTOR = "refactor"      # 重构
    OPTIMIZE = "optimize"      # 优化性能
    DEBUG = "debug"            # 调试
    
    # 代码质量类
    REVIEW = "review"          # 代码审查
    TEST = "test"              # 测试相关
    DOCUMENT = "document"      # 文档生成
    ANALYSIS = "analysis"      # 代码分析
    
    # 部署运维类
    DEPLOY = "deploy"          # 部署
    ROLLBACK = "rollback"      # 回滚
    MONITOR = "monitor"         # 监控
    BACKUP = "backup"          # 备份
    MIGRATE = "migrate"        # 迁移
    
    # 安全类
    SECURITY = "security"      # 安全扫描
    SCAN = "scan"              # 漏洞扫描
    AUTH = "auth"              # 认证授权
    
    # 数据类
    QUERY = "query"            # 查询/搜索
    EXPORT = "export"          # 导出数据
    IMPORT = "import"          # 导入数据
    SYNC = "sync"              # 同步数据
    
    # 配置类
    CONFIG = "config"          # 配置管理
    SETUP = "setup"            # 环境搭建
    INSTALL = "install"        # 安装依赖
    UPGRADE = "upgrade"        # 升级
    
    # 项目管理类
    PLAN = "plan"              # 规划
    ESTIMATE = "estimate"      # 估算工作量
    TRACK = "track"            # 跟踪进度
    
    # 协作类
    REVIEW_CODE = "review_code"    # PR审查
    MERGE = "merge"            # 合并代码
    BRANCH = "branch"          # 分支操作
    
    # 解释类
    EXPLAIN = "explain"        # 解释代码
    FIND = "find"              # 查找代码
    REPLACE = "replace"        # 查找替换
    
    # 日志类
    LOG = "log"               # 日志查看
    TRACE = "trace"           # 链路追踪
    
    # 未知
    UNKNOWN = "unknown"


class IntentPriority(Enum):
    """意图优先级"""
    CRITICAL = 1  # 紧急/阻塞
    HIGH = 2      # 高优先级
    MEDIUM = 3    # 中优先级
    LOW = 4       # 低优先级


@dataclass
class IntentEntity:
    """识别的实体"""
    name: str
    type: str  # file, function, class, module, api, url, path, variable
    value: str
    start_pos: int
    end_pos: int
    confidence: float = 1.0


@dataclass
class IntentParameter:
    """意图参数"""
    name: str
    type: str  # string, number, boolean, array, object
    value: Any
    required: bool = True
    default: Any = None


@dataclass
class ParsedIntent:
    """解析后的意图"""
    type: IntentType
    confidence: float
    entities: List[IntentEntity]
    action_verbs: List[str]
    target_objects: List[str]
    parameters: Dict[str, IntentParameter]
    raw_text: str
    priority: IntentPriority = IntentPriority.MEDIUM
    subtasks: List[str] = field(default_factory=list)
    estimated_effort: str = ""


@dataclass 
class MultiIntentResult:
    """多意图结果"""
    primary: ParsedIntent
    secondary: List[ParsedIntent]
    combined_confidence: float
    execution_order: List[str]


class IntentPatterns:
    """意图模式库"""

    PATTERNS = {
        IntentType.CREATE: [
            "创建", "新建", "做个", "实现", "开发", "添加", "增加", "写一个",
            "create", "new", "implement", "add", "generate", "build", "编写"
        ],
        IntentType.MODIFY: [
            "修改", "改动", "调整", "更新", "改", "改变",
            "modify", "change", "update", "alter", "edit", "tweak"
        ],
        IntentType.DELETE: [
            "删除", "移除", "清除", "去掉",
            "delete", "remove", "clear", "drop", "uninstall"
        ],
        IntentType.READ: [
            "查看", "看看", "显示", "打开", "读取",
            "view", "show", "display", "open", "read", "get"
        ],
        IntentType.UPDATE: [
            "更新", "刷新", "同步",
            "update", "refresh", "sync"
        ],
        IntentType.LIST: [
            "列出", "列表", "展示所有", "查看所有",
            "list", "show all", "display all", "enumerate"
        ],
        IntentType.FIX: [
            "修复", "修", "fix", "bug", "错误", "问题", "解决", "报错", "登不进去", "不能用",
            "repair", "correct", "solve"
        ],
        IntentType.REFACTOR: [
            "重构", "重写", "整理",
            "refactor", "rewrite", "restructure", "reorganize"
        ],
        IntentType.OPTIMIZE: [
            "优化", "提升性能", "加快", "性能", "太慢",
            "optimize", "improve", "performance", "speed up", "enhance"
        ],
        IntentType.DEBUG: [
            "调试", "排错", "排除故障", "断点",
            "debug", "troubleshoot", "breakpoint"
        ],
        IntentType.REVIEW: [
            "审查", "检查", "review", "audit", "检视",
            "inspect", "examine"
        ],
        IntentType.TEST: [
            "测试", "单元测试", "e2e", "集成测试", "压力测试", "写单元测试",
            "test", "testing", "unit test", "e2e", "integration"
        ],
        IntentType.DOCUMENT: [
            "文档", "注释", "说明", "写文档",
            "document", "docs", "comment", "spec", "readme"
        ],
        IntentType.ANALYSIS: [
            "分析", "统计", "报告", "复杂度",
            "analyze", "analysis", "statistics", "report"
        ],
        IntentType.DEPLOY: [
            "部署", "上线", "发布", "发布上线",
            "deploy", "release", "publish", "push to prod"
        ],
        IntentType.ROLLBACK: [
            "回滚", "撤销", "恢复",
            "rollback", "revert", "undo", "restore"
        ],
        IntentType.MONITOR: [
            "监控", "观测", "指标", "仪表盘",
            "monitor", "observe", "metrics", "dashboard"
        ],
        IntentType.BACKUP: [
            "备份", "导出配置",
            "backup", "export config"
        ],
        IntentType.MIGRATE: [
            "迁移", "转移", "导入导出",
            "migrate", "transfer", "move data"
        ],
        IntentType.SECURITY: [
            "安全", "漏洞", "密码", "加密",
            "security", "vulnerability", "secret", "encrypt"
        ],
        IntentType.SCAN: [
            "扫描", "检测", "体检", "安全漏洞",
            "scan", "detect", "check"
        ],
        IntentType.AUTH: [
            "认证", "授权", "登录", "权限", "添加认证",
            "auth", "login", "permission", "credential"
        ],
        IntentType.QUERY: [
            "查询", "搜索", "找", "搜索代码",
            "query", "search", "find", "lookup"
        ],
        IntentType.EXPORT: [
            "导出", "导出数据", "下载",
            "export", "download", "extract"
        ],
        IntentType.IMPORT: [
            "导入", "导入数据", "上传",
            "import", "upload", "ingest"
        ],
        IntentType.SYNC: [
            "同步", "数据同步",
            "sync", "synchronize"
        ],
        IntentType.CONFIG: [
            "配置", "设置", "环境变量",
            "config", "configure", "setting", "env"
        ],
        IntentType.SETUP: [
            "搭建", "初始化", "安装", "配置环境",
            "setup", "initialize", "install", "environment"
        ],
        IntentType.INSTALL: [
            "安装依赖", "装包", "npm install", "pip install",
            "install", "npm i", "pip install", "package"
        ],
        IntentType.UPGRADE: [
            "升级", "更新依赖", "版本升级",
            "upgrade", "update package", "version bump"
        ],
        IntentType.PLAN: [
            "规划", "计划", "方案",
            "plan", "planning", "roadmap"
        ],
        IntentType.ESTIMATE: [
            "估算", "工作量评估",
            "estimate", "effort", "man hours"
        ],
        IntentType.TRACK: [
            "跟踪", "进度", "状态",
            "track", "progress", "status", "sprint"
        ],
        IntentType.REVIEW_CODE: [
            "review", "pr审查", "pull request", "代码审查", "mr",
            "merge request"
        ],
        IntentType.MERGE: [
            "合并", "merge", "合并分支",
            "squash", "rebase"
        ],
        IntentType.BRANCH: [
            "分支", "创建分支", "切换分支",
            "branch", "checkout", "git branch"
        ],
        IntentType.EXPLAIN: [
            "解释", "说明", "什么是", "为什么", "怎么用",
            "explain", "what", "why", "how", "what is"
        ],
        IntentType.FIND: [
            "查找", "定位", "找到",
            "find", "locate", "grep", "search"
        ],
        IntentType.REPLACE: [
            "替换", "查找替换", "批量替换",
            "replace", "find and replace", "sed"
        ],
        IntentType.LOG: [
            "日志", "log", "查看日志",
            "查看最近的"
        ],
        IntentType.TRACE: [
            "链路", "trace", "调用链",
            "请求链路"
        ],
    }

    ACTION_VERBS = [
        "创建", "生成", "添加", "删除", "更新", "修改", "修复",
        "实现", "调用", "执行", "查询", "处理", "验证", "检查",
        "分析", "优化", "重构", "部署", "回滚", "监控", "备份",
        "迁移", "扫描", "认证", "授权", "导出", "导入", "同步",
        "配置", "搭建", "安装", "升级", "规划", "跟踪", "合并"
    ]

    URGENCY_KEYWORDS = {
        IntentPriority.CRITICAL: ["紧急", "立刻", "马上", "critical", "urgent", "asap", "blocking", "阻塞", "挂了", "crash", "down"],
        IntentPriority.HIGH: ["重要", "高优", "尽快", "important", "high priority", "soon"],
        IntentPriority.MEDIUM: ["普通", "正常", "一般", "normal", "medium"],
        IntentPriority.LOW: ["以后", "有空", "低优", "later", "low priority", "eventually"]
    }

    EFFORT_PATTERNS = [
        (r"快速|简单|容易|easy|quick|simple", "10m"),
        (r"中等|半小时|medium", "30m"),
        (r"复杂|困难|hard|complex|一天|1d", "1d"),
        (r"简单功能|小功能|几分钟", "5m"),
    ]

    ENTITY_PATTERNS = [
        ("file", r'[\w\-/]+\.(py|js|ts|tsx|jsx|go|java|cpp|c|rs|rb|php|html|css|json|yaml|yml|md|txt)'),
        ("function", r'(?:def|function|class|const|let|var)\s+(\w+)'),
        ("api", r'(?:GET|POST|PUT|DELETE|PATCH)\s+/?[\w\-/]+'),
        ("url", r'https?://[^\s<>"{}|\\^`\[\]]+'),
        ("path", r'(?:^|[\s])(/[^\s]+)'),
        ("variable", r'\$?\w+\s*=\s*["\']?[^"\',\s]+["\']?'),
        ("module", r'(?:import|require)\s+["\']([^"\']+)["\']'),
        ("number", r'\d+(?:\.\d+)?'),
    ]


class IntentParser:
    """意图解析器 v2.1"""

    def __init__(self):
        self.patterns = IntentPatterns()
        self.custom_parsers: List[Callable] = []

    def add_parser(self, parser: Callable[[str], ParsedIntent]) -> None:
        self.custom_parsers.append(parser)

    def parse(self, text: str) -> ParsedIntent:
        """解析单个意图"""
        text_lower = text.lower()

        # 1. 检测意图类型
        intent_type, confidence, matched_keywords = self._detect_intent(text_lower)

        # 2. 提取动作动词
        action_verbs = [v for v in self.patterns.ACTION_VERBS if v in text_lower]

        # 3. 提取实体（只匹配真正的代码实体）
        entities = self._extract_code_entities(text)

        # 4. 提取目标对象（从引号和代码实体中）
        target_objects = self._extract_targets(text, entities)

        # 5. 提取参数
        parameters = self._extract_parameters(text)

        # 6. 检测优先级
        priority = self._detect_priority(text_lower)

        # 7. 估算工作量
        effort = self._estimate_effort(text)

        # 8. 生成子任务
        main_target = target_objects[0] if target_objects else "目标"
        subtasks = self._generate_subtasks(intent_type, main_target)

        return ParsedIntent(
            type=intent_type,
            confidence=confidence,
            entities=entities,
            action_verbs=action_verbs,
            target_objects=target_objects,
            parameters=parameters,
            raw_text=text,
            priority=priority,
            subtasks=subtasks,
            estimated_effort=effort
        )

    def _detect_intent(self, text_lower: str) -> Tuple[IntentType, float, List[str]]:
        """检测意图类型 - 使用贝叶斯置信度公式"""
        best_type = IntentType.UNKNOWN
        max_matches = 0
        matched_keywords = []

        for intent_type, keywords in self.patterns.PATTERNS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > max_matches:
                max_matches = matches
                best_type = intent_type
                matched_keywords = [kw for kw in keywords if kw in text_lower]

        # === 新的贝叶斯置信度公式 ===
        # 基础分：关键词命中数
        base_score = max_matches * 0.25 if max_matches > 0 else 0.25

        # 从 Calibration 系统获取历史成功率
        try:
            from infrastructure.tools.unified_calibration import UnifiedCalibrationSystem
            calibration = UnifiedCalibrationSystem()
            task_type_str = best_type.value

            # 获取该类型的统计数据
            stats = calibration.get_history_stats(task_type_str)
            history_success_rate = stats.get("avg_actual", 0.5)
            sample_count = stats.get("count", 0)
            ece = stats.get("ece", 0.0)
        except:
            history_success_rate = 0.5
            sample_count = 0
            ece = 0.0

        # 贝叶斯权重：sample_count / (sample_count + 50)
        # 14条 → weight = 14/64 ≈ 0.22，更保守
        weight = sample_count / (sample_count + 50) if sample_count > 0 else 0

        # 历史成功率作为先验
        if weight > 0:
            confidence = base_score * (1 - weight) + history_success_rate * weight
        else:
            confidence = base_score

        # 温和的 ECE 折扣（ECE=0.28 → 折扣14%）
        if ece > 0:
            calibration_discount = ece * 0.5  # 温和折扣
            confidence = confidence * (1 - calibration_discount)

        # 确保在合理范围内
        confidence = max(0.1, min(0.95, confidence))

        return best_type, confidence, matched_keywords

    def _extract_code_entities(self, text: str) -> List[IntentEntity]:
        """提取代码实体"""
        entities = []

        for entity_type, pattern in self.patterns.ENTITY_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value = match.group(0)
                if value and len(value) > 1:
                    entities.append(IntentEntity(
                        name=value,
                        type=entity_type,
                        value=value,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=1.0
                    ))

        return entities

    def _extract_targets(self, text: str, entities: List[IntentEntity]) -> List[str]:
        """提取目标对象"""
        targets = []

        # 从代码实体中提取有意义的
        for entity in entities:
            if entity.type in ["file", "function", "class", "module", "api"]:
                targets.append(entity.value)

        # 从引号中提取（排除单字）
        quoted = re.findall(r'["\']([^"\']{2,})["\']', text)
        targets.extend(quoted)

        # 去重
        return list(dict.fromkeys(targets))

    def _extract_parameters(self, text: str) -> Dict[str, IntentParameter]:
        """提取参数"""
        params = {}

        # --flag 格式
        flags = re.findall(r'--(\w+)', text)
        for flag in flags:
            params[flag] = IntentParameter(name=flag, type="boolean", value=True, required=False)

        # key=value 格式
        kv_pairs = re.findall(r'(\w+)=([^\s]+)', text)
        for key, value in kv_pairs:
            params[key] = IntentParameter(name=key, type="string", value=value, required=False)

        # 数字参数
        numbers = re.findall(r'(\d+)(?:\s+(?:个|条|次|分钟|小时|天))?', text)
        if numbers:
            params["count"] = IntentParameter(name="count", type="number", value=int(numbers[0]), required=False)

        return params

    def _detect_priority(self, text_lower: str) -> IntentPriority:
        """检测优先级"""
        for priority, keywords in self.patterns.URGENCY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return priority
        return IntentPriority.MEDIUM

    def _estimate_effort(self, text: str) -> str:
        """估算工作量"""
        for pattern, effort in self.patterns.EFFORT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return effort
        return ""

    def _generate_subtasks(self, intent_type: IntentType, target: str) -> List[str]:
        """生成子任务"""
        templates = {
            IntentType.CREATE: [f"调研 {target} 需求", f"设计 {target} 架构", f"实现 {target} 代码", f"为 {target} 编写测试", f"审查 {target} 代码"],
            IntentType.FIX: [f"收集 {target} 问题症状", f"定位 {target} 根因", f"修复 {target} 问题", f"验证 {target} 修复"],
            IntentType.REFACTOR: [f"分析 {target} 当前实现", f"设计 {target} 重构方案", f"执行 {target} 重构", f"测试 {target} 重构后功能"],
            IntentType.TEST: [f"确定 {target} 测试范围", f"编写 {target} 测试用例", f"运行 {target} 测试", f"生成 {target} 测试报告"],
            IntentType.DEPLOY: [f"构建 {target} 产物", f"准备部署环境", f"执行 {target} 部署", f"验证 {target} 部署结果"],
            IntentType.REVIEW: [f"获取 {target} 代码", f"检查 {target} 安全性", f"检查 {target} 性能", f"检查 {target} 可维护性", f"输出 {target} 审查报告"],
            IntentType.SECURITY: [f"扫描 {target} 漏洞", f"分析 {target} 安全风险", f"生成 {target} 安全报告"],
            IntentType.OPTIMIZE: [f"分析 {target} 性能瓶颈", f"识别 {target} 优化点", f"实施 {target} 优化", f"验证 {target} 性能提升"],
            IntentType.ANALYSIS: [f"收集 {target} 数据", f"分析 {target} 结果", f"生成 {target} 分析报告"],
            IntentType.QUERY: [f"构建 {target} 查询条件", f"执行 {target} 查询", f"返回 {target} 结果"],
            IntentType.MONITOR: [f"配置 {target} 监控指标", f"设置 {target} 告警规则", f"验证 {target} 监控生效"],
            IntentType.LOG: [f"确定 {target} 日志范围", f"提取 {target} 日志", f"分析 {target} 日志内容"],
            IntentType.AUTH: [f"分析 {target} 认证需求", f"设计 {target} 认证方案", f"实现 {target} 认证", f"测试 {target} 认证流程"],
        }

        return templates.get(intent_type, [f"处理 {target}"])


class MultiIntentDetector:
    """多意图检测器"""

    def __init__(self, parser: IntentParser):
        self.parser = parser

    def detect(self, text: str) -> MultiIntentResult:
        """检测多意图"""
        primary_intent = self.parser.parse(text)
        secondary_intents = []
        text_lower = text.lower()

        for intent_type, keywords in IntentPatterns.PATTERNS.items():
            if intent_type == primary_intent.type:
                continue
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                si = self.parser.parse(text)
                si.type = intent_type
                si.confidence = min(len(matches) * 0.2, 0.7)
                secondary_intents.append(si)

        execution_order = [primary_intent.type.value]
        for si in secondary_intents:
            if si.type.value not in execution_order:
                execution_order.append(si.type.value)

        combined = primary_intent.confidence
        if secondary_intents:
            combined = min(primary_intent.confidence + sum(s.confidence for s in secondary_intents) * 0.5, 1.0)

        return MultiIntentResult(
            primary=primary_intent,
            secondary=secondary_intents,
            combined_confidence=combined,
            execution_order=execution_order
        )


class TaskDecomposer:
    """任务分解器 v2.1"""

    def __init__(self, intent_parser: IntentParser = None):
        self.intent_parser = intent_parser or IntentParser()
        self.multi_detector = MultiIntentDetector(self.intent_parser)

    def decompose(self, text: str, multi_intent: bool = True) -> List[Dict[str, Any]]:
        """分解任务"""
        if multi_intent:
            multi_result = self.multi_detector.detect(text)
            tasks = []

            for i, subtask in enumerate(multi_result.primary.subtasks):
                tasks.append({
                    "task": subtask,
                    "type": multi_result.primary.type.value,
                    "priority": multi_result.primary.priority.name,
                    "order": i + 1,
                    "intent_type": multi_result.primary.type.value
                })

            for si in multi_result.secondary:
                for i, subtask in enumerate(si.subtasks):
                    tasks.append({
                        "task": subtask,
                        "type": si.type.value,
                        "priority": si.priority.name,
                        "order": len(tasks) + 1,
                        "intent_type": si.type.value,
                        "is_secondary": True
                    })

            return tasks

        intent = self.intent_parser.parse(text)
        return [{
            "task": subtask,
            "type": intent.type.value,
            "priority": intent.priority.name,
            "order": i + 1,
            "intent_type": intent.type.value
        } for i, subtask in enumerate(intent.subtasks)]


class IntentUnderstandingAdapter:
    """意图理解适配器 v2.1"""

    def __init__(self):
        self.parser = IntentParser()
        self.decomposer = TaskDecomposer(self.parser)
        self.multi_detector = MultiIntentDetector(self.parser)

    def understand(self, text: str, multi_intent: bool = True) -> Dict[str, Any]:
        """理解意图"""
        multi_result = self.multi_detector.detect(text)
        tasks = self.decomposer.decompose(text, multi_intent=True)

        return {
            "intent": {
                "type": multi_result.primary.type.value,
                "confidence": multi_result.combined_confidence,
                "entities": [{"name": e.name, "type": e.type, "value": e.value} for e in multi_result.primary.entities[:5]],
                "action_verbs": multi_result.primary.action_verbs,
                "parameters": {k: {"type": v.type, "value": v.value} for k, v in multi_result.primary.parameters.items()},
                "priority": multi_result.primary.priority.name,
                "estimated_effort": multi_result.primary.estimated_effort
            },
            "multi_intent": {
                "detected": len(multi_result.secondary) > 0,
                "secondary_count": len(multi_result.secondary),
                "execution_order": multi_result.execution_order,
                "secondary_types": [s.type.value for s in multi_result.secondary]
            },
            "subtasks": tasks,
            "original_text": text,
            "timestamp": datetime.now().isoformat()
        }

    def batch_understand(self, texts: List[str]) -> List[Dict[str, Any]]:
        """批量理解"""
        return [self.understand(text) for text in texts]


if __name__ == "__main__":
    adapter = IntentUnderstandingAdapter()

    test_cases = [
        "做个 AI 助手",
        "修复登录bug，用户反馈输入正确密码也登不进去",
        "优化数据库查询性能，查询太慢了",
        "部署到生产环境，然后监控指标",
        "扫描代码中的安全漏洞",
        "创建一个用户管理模块，然后写单元测试",
        "紧急！服务挂了，立刻修复",
        "分析这个函数的复杂度",
        "给这个API添加认证",
        "查看最近的50条日志",
        "快速搭建一个测试环境",
        "给这个函数添加注释",
    ]

    print("=== 意图理解 v2.1 测试 ===\n")

    for text in test_cases:
        result = adapter.understand(text)
        intent = result["intent"]

        print(f"📝 输入: {text}")
        print(f"   类型: {intent['type']} | 置信度: {intent['confidence']:.2f} | 优先级: {intent['priority']}")
        
        if intent['entities']:
            print(f"   实体: {[e['value'] for e in intent['entities'][:3]]}")
        
        if result["multi_intent"]["detected"]:
            print(f"   多意图: ✓ → {' → '.join(result['multi_intent']['execution_order'])}")
        
        print(f"   子任务: {len(result['subtasks'])}")
        for task in result["subtasks"][:2]:
            print(f"      {task['order']}. {task['task']}")
        print()
