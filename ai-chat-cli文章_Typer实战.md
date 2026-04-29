# 用Typer从零搭一个AI命令行工具：我踩过的6个坑

2026年，Claude Code、Bolt、各路AI工具都在推命令行界面。

以前CLI是极客专属，现在成了每个AI工具的标配。开发者对CLI的期待变了——不能再是"能用就行"，得像一个正经产品。

最近我从头搭了一个AI对话CLI，用的是Typer框架，支持OpenAI和Anthropic双平台，跑了真实项目从零到发布全流程。

这篇文章不是安装教程，是踩坑实录。每一个你可能绕过去的地方，我都真实踩过了。

---

## 一、为什么选Typer

Python做CLI有三个主流选项：Click、argparse原生、Typer。

argparse太底层，写复杂命令要自己处理大量重复逻辑。Click成熟稳定，但语法偏传统。Typer的优势在于类型提示和自动文档生成——你写Python类型注解，它自动生成CLI参数。

```python
from typing import Optional
import typer

app = typer.Typer()

@app.command()
def greet(name: str, formal: bool = False):
    """问候命令"""
    if formal:
        print(f"Good day, {name}!")
    else:
        print(f"Hey, {name}!")
```

运行`python main.py greet --help`，自动得到完整帮助文档，不需要额外配置。

Typer 0.21稳定，生态完整，Rich输出支持好。这是选它的核心原因。

---

## 二、项目结构：从目录规划开始

CLI工具的项目结构和普通Python脚本完全不同。你的代码要被安装、被调用、被做shell补全，需要一个正经的Python包结构。

```
ai-chat-cli/
├── pyproject.toml          # 项目元数据+入口点定义
├── README.md
└── src/
    └── ai_chat_cli/
        ├── __init__.py
        ├── main.py          # CLI命令入口
        ├── config.py        # 配置管理
        ├── client.py        # LLM API客户端
        ├── history.py       # 对话历史管理
        └── tokenizer.py     # Token计数器
```

`pyproject.toml`里的`[project.scripts]`是整个安装流程的关键：

```toml
[project]
name = "ai-chat-cli"
version = "0.1.0"
description = "AI命令行对话工具"
requires-python = ">=3.10"
dependencies = [
    "typer>=0.21.0",
    "rich>=13.0.0",
    "openai>=1.0.0",
    "anthropic>=0.40.0",
    "tiktoken>=0.7.0",
    "python-dotenv>=1.0.0",
]

[project.scripts]
ai-chat = "ai_chat_cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

`ai-chat`就是用户安装后在终端里敲的命令名。`ai_chat_cli.main:app`指向`main.py`里的Typer实例。

安装命令很简单：

```bash
pip install -e .
```

`-e`表示editable模式，代码改了不需要重装。

---

## 三、配置管理：踩坑点1

配置是最容易出问题的模块。我的设计原则是：**命令行参数 > 环境变量 > 默认值**，优先级依次递减。

```python
import os
from pathlib import Path
from typing import Literal, Optional
import dotenv

dotenv.load_dotenv()

class Config:
    PROVIDER: Literal["openai", "anthropic"] = "openai"
    MODEL: str = "gpt-4o-mini"

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    MAX_TOKENS: int = 4096
    MAX_HISTORY_LENGTH: int = 50
    HISTORY_FILE: Path = Path.home() / ".ai_chat_history.json"
    STREAMING: bool = True
    VERBOSE: bool = False

    def __init__(self):
        # 从环境变量读取
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

        # 命令行参数可以覆盖环境变量
        if os.getenv("AI_PROVIDER"):
            self.PROVIDER = os.getenv("AI_PROVIDER")
        if os.getenv("AI_MODEL"):
            self.MODEL = os.getenv("AI_MODEL")

    def validate(self) -> bool:
        """验证API密钥是否配置"""
        if self.PROVIDER == "openai" and not self.OPENAI_API_KEY:
            print("错误：未设置 OPENAI_API_KEY")
            print("方法1：export OPENAI_API_KEY=sk-xxx")
            print("方法2：在当前目录创建 .env 文件，写入 OPENAI_API_KEY=sk-xxx")
            return False
        if self.PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            print("错误：未设置 ANTHROPIC_API_KEY")
            return False
        return True
```

**踩坑1：Typer的`config`命令名被内部占用**

定义了一个命令叫`config_cmd`，注册命令时用的是`@app.command()`。跑起来才发现Typer的全局选项里有`--config`，自定义命令`config`会冲突报错：

```
Error: No such command 'config'. Did you mean 'config-cmd'?
```

解决：换成`setup`或其他未占用名称，或者显式用`@app.command(name="cfg")`指定别名。

---

## 四、LLM客户端：踩坑点2和3

这是最复杂的模块，也是踩坑最多的地方。

### OpenAI和Anthropic的消息格式差异

两个平台的消息格式不一样。OpenAI用的是`{"role": "user", "content": "..."}`，Anthropic的`system`消息是独立字段，不是`role: system`。

```python
# OpenAI格式
messages = [
    {"role": "system", "content": "你是助手"},
    {"role": "user", "content": "你好"}
]

# Anthropic格式（system是独立参数）
response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    system="你是助手",          # 独立的system参数
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=4096
)
```

我的解决思路：统一用OpenAI格式存储历史，调用Anthropic时做一次格式转换。

```python
def _to_anthropic_format(self, messages):
    """将统一格式转换为Anthropic格式"""
    system_prompt = ""
    anthropic_messages = []

    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        else:
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

    return system_prompt, anthropic_messages
```

### 踩坑2：流式输出的降级处理

流式输出体验好，但不稳定。网络抖动、超时、API服务端问题都可能导致流式中断。

我用了降级策略：流式失败时自动切换到非流式，不报错，用户无感知。

```python
def _stream_openai(self, messages):
    try:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=config.MAX_TOKENS,
            stream=True,
        )

        full_response = []
        print()  # 换行，开始流式输出

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response.append(content)

        print()  # 流式结束，换行
        return "".join(full_response)

    except Exception as e:
        print(f"\n[流式输出失败: {e}]，切换非流式...")
        # 降级到非流式
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=config.MAX_TOKENS,
            stream=False,
        )
        return response.choices[0].message.content or ""
```

### 踩坑3：Anthropic的流式API完全不同

Anthropic的流式API和OpenAI是两套完全不同的实现。OpenAI用`stream=True`参数，Anthropic用上下文管理器。

```python
def _stream_anthropic(self, system, messages):
    try:
        with self._client.messages.stream(
            model=self.model,
            system=system,
            messages=messages,
            max_tokens=config.MAX_TOKENS,
        ) as stream:
            full_response = []
            print()

            for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.text:
                        print(event.delta.text, end="", flush=True)
                        full_response.append(event.delta.text)

            print()
            return "".join(full_response)

    except Exception as e:
        print(f"\n[Anthropic流式失败: {e}]")
        return ""  # 降级处理
```

这两个流式API的差异是文档里没有明确说清楚的，必须实际踩过才知道。

---

## 五、Token计数：踩坑点4

Token计数有两个用途：估算费用、控制上下文长度。

主流方案是用`tiktoken`库，它是OpenAI开源的精确tokenizer，比按字符数估算准很多。

```python
try:
    import tiktoken
    _HAS_TIKTOKEN = True
except ImportError:
    _HAS_TIKTOKEN = False

def num_tokens_from_messages(messages, model="gpt-4o-mini"):
    if _HAS_TIKTOKEN:
        encoding = tiktoken.encoding_for_model(model)
    else:
        # 备用：粗估
        total_chars = sum(len(str(v)) for m in messages for v in m.values())
        chinese = sum(1 for m in messages for c in str(m.get("content","")) if '\u4e00' <= c <= '\u9fff')
        return int(chinese + (total_chars - chinese) / 4)
```

### 踩坑4：tokenizer版本不兼容

`tiktoken`对模型名称有要求，`gpt-4o`可能不在tiktoken的模型列表里，需要做fallback：

```python
def num_tokens_from_messages(messages, model="gpt-4o-mini"):
    if _HAS_TIKTOKEN:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # 模型不在列表里，用默认编码器
            encoding = tiktoken.get_encoding("cl100k_base")
```

---

## 六、对话历史管理

历史管理需要处理三个场景：加载、保存、自动修剪。

```python
class HistoryManager:
    def __init__(self, history_file=None):
        self.history_file = history_file or config.HISTORY_FILE
        self._history: List[Dict] = []

    def load(self):
        if not self.history_file.exists():
            return []
        with open(self.history_file, "r", encoding="utf-8") as f:
            self._history = json.load(f)
        return self._history

    def save(self):
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self._history, f, ensure_ascii=False, indent=2)

    def prune(self):
        """上下文太长时自动删最早的对话"""
        if not self._history:
            return
        # 简单策略：保留最近的消息对
        if len(self._history) > config.MAX_HISTORY_LENGTH:
            self._history = self._history[-config.MAX_HISTORY_LENGTH:]
```

---

## 七、主命令入口

Typer的全局选项在`@app.callback()`里定义，子命令用`@app.command()`。

```python
app = typer.Typer(
    name="ai-chat",
    help="AI命令行对话工具",
)

@app.callback()
def callback(
    ctx: typer.Context,
    provider: str = typer.Option(None, "-p", "--provider"),
    model: str = typer.Option(None, "-m", "--model"),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
):
    if provider:
        config.PROVIDER = provider
    if model:
        config.MODEL = model
    config.VERBOSE = verbose

@app.command()
def chat(message: Optional[str] = None):
    if message:
        _single_chat(message)
    else:
        _interactive_chat()

@app.command("ask")
def ask(message: str = typer.Argument(..., help="要提问的内容")):
    """快捷单次提问"""
    _single_chat(message)
```

运行效果：

```
$ ai-chat --help
╭─ Options ─────────────────────────────────────╮
│ --provider   -p      TEXT  AI提供商          │
│ --model      -m      TEXT  模型名称           │
│ --verbose    -v            详细输出           │
╰───────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────╮
│ chat     与AI对话                             │
│ ask      快速单次提问                         │
│ setup    查看和修改配置                       │
│ history  管理对话历史                         │
╰───────────────────────────────────────────────╯

$ ai-chat setup --list
Provider: openai
Model: gpt-4o-mini
OpenAI Key: 已设置
Anthropic Key: 未设置
```

---

## 八、完整踩坑清单

搭这个工具踩了6个坑，汇总一下：

| 序号 | 坑 | 严重程度 | 解决方案 |
|------|----|---------|---------|
| 1 | Typer的`config`命令名被内部占用 | 高 | 换用`setup`等其他名称 |
| 2 | OpenAI和Anthropic消息格式不兼容 | 高 | 统一存储OpenAI格式，调用时转换 |
| 3 | Anthropic流式API和OpenAI完全不同 | 高 | 分别实现，不共用代码 |
| 4 | tiktoken模型名不匹配导致KeyError | 中 | try/except加fallback到cl100k_base |
| 5 | 流式输出网络失败没有降级 | 中 | 异常时自动切换非流式 |
| 6 | pyproject.toml缺少README导致安装失败 | 低 | 加上`readme = "README.md"` |

---

## 九、进阶扩展方向

这个基础版本可以往几个方向扩展：

**1. Shell补全**

Typer内置Shell补全支持，但需要额外安装：

```bash
# Bash
ai-chat --install-completion bash >> ~/.bashrc

# Zsh
ai-chat --install-completion zsh >> ~/.zshrc

# Fish
ai-chat --install-completion fish
```

补全安装后，输入`ai-chat ask "`<Tab>`能自动补全选项。

**2. 多轮Agent模式**

加上工具调用能力，让AI能执行shell命令、读文件、搜索网络。这是Claude Code的核心能力。

**3. 发布到PyPI**

```bash
pip install build twine
python -m build
twine upload dist/*
```

发布后全世界都能`pip install ai-chat-cli`安装你的工具。

---

## 总结

用Typer搭AI CLI比想象中更简单，也比想象中更容易踩坑。

核心经验三条：

**1. 选对框架省大量时间。** Typer的类型推断+自动文档，比argparse少写一半代码。

**2. API兼容层要早做。** OpenAI和Anthropic的差异从第一天就想清楚怎么处理，别等产品做完了再重构。

**3. 流式输出必须有降级。** 网络不稳定是常态，没有降级方案的工具在生产环境会频繁挂掉。

完整项目代码在workspace的`ai-chat-cli/`目录下，可以直接`pip install -e .`安装运行。
