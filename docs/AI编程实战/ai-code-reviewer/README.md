# AI Code Reviewer

AI驱动的代码审查工具，支持多维度代码分析：安全漏洞、性能问题、代码风格、逻辑错误。

## 功能特性

- **四维审查**：安全（Security）、性能（Performance）、风格（Style）、逻辑（Logic）
- **结构化报告**：JSON格式输出，支持CI/CD集成
- **Git集成**：自动解析git diff，支持staged变更审查
- **Pre-commit Hook**：提交前自动审查
- **多模型支持**：兼容所有OpenAI接口的服务（GPT-4o、Claude API、vLLM、Ollama等）
- **Token感知**：大diff自动分片，避免上下文窗口溢出
- **去重与过滤**：相似发现自动去重，低置信度自动过滤
- **置信度评分**：每个发现附带置信度，标注可能的AI误报

## 安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置环境变量
export LLM_API_KEY=sk-your-api-key
export LLM_BASE_URL=https://api.openai.com/v1  # 可选，默认值
export LLM_MODEL=gpt-4o                        # 可选，默认值
```

## 使用方法

### 审查最新commit的diff

```bash
ai-review diff
```

### 审查staged的变更

```bash
ai-review diff --staged
```

### 审查指定commit

```bash
ai-review diff HEAD~3
```

### 审查单个文件

```bash
ai-review file path/to/file.py
```

### 通过stdin管道传入diff

```bash
git diff HEAD~1 | ai-review review
```

### 仅输出JSON（便于CI集成）

```bash
ai-review diff --json > review-report.json
```

### 指定审阅维度

```bash
ai-review diff --dimensions "security,logic"
```

### 输出报告到文件

```bash
ai-review diff -o report.json
```

### 使用配置文件

```yaml
# review-config.yml
llm:
  api_key: sk-xxx
  base_url: https://api.openai.com/v1
  model: gpt-4o
review:
  dimensions:
    - security
    - performance
    - style
    - logic
  min_confidence: 0.3
```

```bash
ai-review diff -c review-config.yml
```

## 作为Pre-commit Hook使用

```bash
# 安装hook
cp examples/pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# 设置环境变量（建议写入~/.bashrc或项目.env）
export LLM_API_KEY=sk-your-key
```

## 返回码

- 0: 审查完成，未发现严重问题
- 1: 发现 CRITICAL 或 HIGH 级别的问题

## 项目结构

```
ai-code-reviewer/
├── ai_code_reviewer/
│   ├── __init__.py       # 包入口
│   ├── __main__.py       # python -m 支持
│   ├── cli.py            # 命令行接口
│   ├── config.py         # 配置管理
│   ├── models.py         # 数据模型
│   ├── diff_parser.py    # Git diff解析
│   ├── llm_client.py     # LLM API客户端
│   ├── reviewer.py       # 审查引擎
│   ├── report.py         # 报告输出
│   └── analyzers/
│       ├── __init__.py   # 基类与提示词
│       ├── security.py   # 安全分析器
│       ├── performance.py# 性能分析器
│       ├── style.py      # 风格分析器
│       └── logic.py      # 逻辑分析器
├── tests/
│   ├── test_diff_parser.py
│   └── test_models.py
├── examples/
│   ├── pre-commit-hook.sh
│   └── sample_review.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

## License

MIT
