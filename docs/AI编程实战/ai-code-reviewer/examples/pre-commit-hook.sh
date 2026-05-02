#!/bin/bash
# pre-commit hook: 在git commit前自动运行AI代码审查
# 安装方法:
#   ln -sf ../../examples/pre-commit-hook.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit

echo "🔍 Running AI Code Review..."

# 配置：如果不存在则使用默认值
API_KEY="${LLM_API_KEY:-}"
BASE_URL="${LLM_BASE_URL:-https://api.openai.com/v1}"
MODEL="${LLM_MODEL:-gpt-4o}"

if [ -z "$API_KEY" ]; then
    echo "⚠️  未设置 LLM_API_KEY 环境变量，跳过AI审阅"
    exit 0
fi

# 获取staged的diff
STAGED_DIFF=$(git diff --cached)

if [ -z "$STAGED_DIFF" ]; then
    echo "没有检测到staged变更"
    exit 0
fi

# 调用AI审阅工具（通过stdin传diff）
echo "$STAGED_DIFF" | ai-review review \
    --dimensions "security,logic" \
    --json 2>/dev/null

# 捕获退出码
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ AI审查发现了严重问题！"
    echo "   如果要强制提交，请使用: git commit --no-verify"
    echo "   警告: 跳过审查可能引入安全隐患或逻辑缺陷"
fi

exit $EXIT_CODE
