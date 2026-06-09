#!/usr/bin/env bash
#
# Superpowers/ECC 工作流强制执行 Hook
# 智能检测需要 brainstorming 的任务
#

INPUT_FILE="$1"
[ -f "$INPUT_FILE" ] || INPUT_FILE="/dev/stdin"

CONTENT=$(cat "$INPUT_FILE" 2>/dev/null || echo "{}")
MESSAGE=$(echo "$CONTENT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('message',{}).get('content',''))" 2>/dev/null || echo "")

# ===== 排除模式（查询类、询问类）=====
EXCLUDE_PATTERNS="查一下|查查|看看这个|看看是|帮我查|帮我看看|帮我查查|什么问题|怎么回事|为什么|怎么解决|怎么修|报错|错误|问一下|问一下|有什么"

# 如果匹配排除模式，直接放行
if echo "$MESSAGE" | grep -qiE "$EXCLUDE_PATTERNS"; then
    echo "{}"
    exit 0
fi

# ===== 需要 blocking 的模式 =====

# 模式1: 执行类请求
PATTERN_EXEC="做个|实现|开发|搭建|构建|创建|写个|做个.*功能|实现.*系统|开发.*系统|做个.*项目|开发.*应用"

# 模式2: 技术操作+创建意图
PATTERN_TECH_CREATE="集成.*|接入.*|部署.*|配置.*|安装.*|搭建.*|构建.*"

# 模式3: 复杂任务（6+ 个领域关键词）
DOMAIN_KEYWORDS="用户|项目|功能|模块|系统|服务|数据库|API|界面|组件|工具|集成|部署|测试|安全|性能|认证|权限|日志|监控"
COUNT=$(echo "$MESSAGE" | grep -oiE "$DOMAIN_KEYWORDS" | sort -u | wc -l)

# ===== 判断 =====
SHOULD_BLOCK=0

if echo "$MESSAGE" | grep -qiE "$PATTERN_EXEC"; then
    SHOULD_BLOCK=1
elif echo "$MESSAGE" | grep -qiE "$PATTERN_TECH_CREATE"; then
    SHOULD_BLOCK=1
elif [ "$COUNT" -ge 6 ]; then
    SHOULD_BLOCK=1
fi

# ===== 输出 =====
if [ "$SHOULD_BLOCK" -eq 1 ]; then
    echo "{\"blocked\":true,\"reason\":\"superpowers_required\",\"message\":\"❌ Superpowers 检查：\n\n在开始之前，你必须：\n1. 先 brainstorming - 了解真正需求和约束\n2. 提出方案及权衡\n3. 获得用户批准\n4. 才能开始实现\n\n请输入 \\\"brainstorming\\\" 开始。\",\"required_action\":\"brainstorming\"}"
    exit 1
fi

echo "{}"
exit 0
