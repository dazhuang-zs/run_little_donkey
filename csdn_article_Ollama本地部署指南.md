# 【AI工具】Ollama 本地部署大模型：零基础小白也能看懂的完整指南（2026年更新）

> **阅读提示**：本文面向零基础读者，每一步都有截图说明和命令验证。无论你用的是 Windows、macOS 还是 Linux，都能找到对应的操作步骤。文章最后还附赠了常见问题的解决方案。

---

## 一、为什么你需要本地部署大模型？

在说 Ollama 之前，先回答一个根本问题：**为什么要在自己电脑上跑大模型，而不是直接用 API？**

这里有一个经典的「AI 隐私三角」：

```
┌─────────────────────────────────────────┐
│              AI 隐私三角                 │
│                                         │
│         【成本可控】                     │
│           ↙       ↘                     │
│   【数据隐私】  ←→  【性能强劲】        │
│                                         │
│  公有 API: 便宜，但数据上传云端         │
│  本地部署: 数据不出本机，但硬件要求高   │
│  Ollama:   平民级本地部署，极低成本     │
└─────────────────────────────────────────┘
```

**本地部署大模型的三大理由：**

1. **隐私安全** —— 你的代码、文档、聊天记录不用上传到任何服务器。医疗、法律、金融等行业尤其敏感，本地运行是刚需。
2. **零成本** —— 买断制，不按 token 计费。跑多少问多少，永远不会有月底账单惊喜。
3. **离线可用** —— 没有网络也能跑。飞机上、地下室、在村里老家，都能正常使用。

**Ollama 的定位是什么？**

Ollama 是目前最流行的本地大模型运行工具，主打一个「一行命令跑模型」。它的目标是：**让任何人在任何电脑上，都能用一条命令把大模型跑起来。**

---

## 二、环境准备：你需要什么配置？

### 2.1 硬件配置对照表

硬件配置决定你能跑多大的模型。先对号入座：

| 配置档位 | 显存/内存 | 代表硬件 | 能跑的模型 | 速度参考 |
|:-------:|:--------:|---------|----------|---------|
| 入门级 | 核显 / 4GB 显存 | 老旧笔记本、GTX 970 | 1.5B~3B 参数 | 10~20 tokens/s |
| 主流级 | 6~8GB 显存 | RTX 3060/4060/4070 Mac M 系列 | 7B~14B 参数 | 20~60 tokens/s |
| 高性能 | 12~16GB 显存 | RTX 4080/4090 Mac M2 Pro/Max | 14B~32B 参数 | 40~100 tokens/s |
| 发烧级 | 24GB+ 显存 | RTX 4090 24G / A100 | 32B~70B 参数 | 60~150 tokens/s |

> **小知识**：日常办公用的轻薄本（8GB 内存，无独显）也能跑 3B 左右的小模型，只是速度慢一些。如果你只是想体验一下，1.5B~3B 的小模型完全够用。

### 2.2 显存需求速查（4-bit 量化版）

大模型的模型文件占用硬盘大小，以及运行时显存需求，参考下表：

| 模型 | 参数量 | 硬盘占用 | 最低显存（Q4量化） | 推荐场景 |
|-----|:-----:|--------:|:----------------:|---------|
| `phi4-mini` | 3.8B | ~2.5GB | 4GB | 工具调用、日常助手（⭐首选入门） |
| `qwen2.5:1.5b` | 1.5B | ~1.2GB | 2GB | 极低配置设备、文本文摘 |
| `llama3.2:3b` | 3B | ~2GB | 3GB | 中等配置、轻量对话 |
| `qwen2.5:7b` | 7B | ~5GB | 6GB | 主流推荐、性价比最高 |
| `llama3.1:8b` | 8B | ~5.5GB | 6GB | 代码能力强 |
| `mistral:7b` | 7B | ~4.5GB | 5GB | 指令遵循好 |
| `qwen2.5:14b` | 14B | ~9GB | 10GB | 中等性能需求 |
| `qwq:32b` | 32B | ~20GB | 20GB | 复杂推理、数学代码 |
| `llama3.3:70b` | 70B | ~40GB | 42GB | 专业场景、需要高端显卡 |

> **名词解释**：Q4 量化是一种模型压缩技术，把模型权重从高精度（FP32）压缩到 4-bit 表示。体积小 75%，显存占用也大幅降低，但模型能力会略有下降。对于普通用户来说，Q4 量化版本是最佳选择——性价比最高。

### 2.3 操作系统要求

| 操作系统 | 支持状态 | 备注 |
|---------|:-------:|------|
| Windows 10/11 | ✅ 官方支持 | 推荐 WSL2 模式，体验更好 |
| macOS | ✅ 官方支持 | Apple Silicon（M1/M2/M3/M4）原生支持，速度快 |
| Linux | ✅ 官方支持 | 推荐 Ubuntu 22.04+ |
| WSL2（Windows 子系统） | ✅ 推荐 | Linux 环境，兼容性最好 |

---

## 三、安装 Ollama（按系统分步操作）

### 3.1 Windows 安装（方法一：官网下载）

**第一步：下载安装包**

打开浏览器，访问 Ollama 官网下载页：

```
https://ollama.com/download
```

点击「Download for Windows」，下载 `OllamaSetup.exe` 文件（约几十 MB）。

**第二步：安装**

双击 `OllamaSetup.exe`，按照提示一路点「Next」即可完成安装。安装过程会自动配置环境变量。

**第三步：验证安装**

打开 PowerShell（按 `Win+X`，选择「终端」或「PowerShell」），输入：

```powershell
ollama --version
```

如果看到类似 `ollama version 0.5.x` 的版本号，说明安装成功。

> **常见问题**：安装后命令找不到？**重启电脑**，让环境变量生效。

---

### 3.2 Windows 安装（方法二：命令行安装，适合程序员）

如果你已经装了 WSL2，可以直接在 Linux 子系统里安装，体验更流畅：

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 curl（如果没有）
sudo apt install -y curl

# 一键安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 验证
ollama --version
```

---

### 3.3 macOS 安装（Apple Silicon 首选）

**方法一：官网下载（最简单）**

1. 访问 https://ollama.com/download
2. 下载 macOS 版本（.dmg 文件）
3. 双击打开，将 Ollama 拖入「应用程序」文件夹
4. 首次运行会在菜单栏出现 Ollama 图标

**方法二：Homebrew（程序员推荐）**

```bash
brew install ollama
```

**方法三：命令行安装**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**验证安装（macOS）**

```bash
ollama --version
```

> **Apple Silicon 用户注意**：Ollama 在 M1/M2/M3/M4 芯片上会自动调用 Neural Engine，CPU 推理速度比 Intel Mac 快 3~5 倍。如果你用的是 Apple Silicon，强烈推荐用原生版本。

---

### 3.4 Linux 安装（Ubuntu / Debian）

```bash
# 更新包管理器
sudo apt update
sudo apt upgrade -y

# 安装依赖
sudo apt install -y curl

# 一键安装（官方脚本）
curl -fsSL https://ollama.com/install.sh | sh

# 验证
ollama --version
```

> **国内服务器安装注意**：如果服务器在大陆，官方安装脚本可能下载缓慢。建议配置代理，或者手动下载二进制文件：
> ```bash
> # 手动下载（以 AMD64 为例）
> curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/local/bin/ollama
> chmod +x /usr/local/bin/ollama
> ```

---

## 四、运行你的第一个模型（5 分钟上手）

### 4.1 一条命令下载并运行模型

Ollama 的核心哲学就是「一行命令解决问题」。以最经典的 `qwen2.5:7b` 模型为例：

```bash
# 下载并直接运行模型（首次会自动下载）
ollama run qwen2.5:7b
```

这条命令会完成三件事：
1. 检查本地是否有 `qwen2.5:7b` 模型，没有则自动下载
2. 启动模型服务
3. 打开交互式对话界面

**运行效果（macOS 终端）：**

```
>>> 你好，请介绍一下你自己
我是通义千问，由阿里云开发的大型语言模型。我的目标是成为
人们的智能助手，帮助解答问题、提供信息和进行创意写作。
有什么我可以帮助你的吗？

>>> /bye
```

> **下载时间说明**：首次下载模型需要一些时间，取决于网络速度。7B 模型大约 4~5GB，14B 模型约 9GB，32B 模型约 20GB。建议在网络好的环境下操作。

### 4.2 常用命令一览

进入 Ollama 交互界面后，这些命令最常用：

| 命令 | 说明 |
|-----|------|
| `/bye` 或 `/exit` | 退出对话 |
| `/show info` | 查看当前模型信息（参数量、量化版本等） |
| `/set parameter temperature 0.7` | 设置温度参数（0=确定性强，1=创意强） |
| `/set num_ctx 4096` | 设置上下文窗口大小 |
| `/clear` | 清屏 |
| `/models` | 查看已下载的模型列表 |
| `/?` | 查看帮助 |

### 4.3 查看本地已安装的模型

```bash
ollama list
```

输出示例：

```
NAME                ID           SIZE      MODIFIED
qwen2.5:7b          a3c1e2d3...  4.9GB     2 hours ago
llama3.2:3b         b4d2f3e4...  2.0GB     3 days ago
phi4-mini:3.8b      c5e3g4h5...  2.4GB     1 week ago
```

---

## 五、模型配置详解：如何选对模型？

### 5.1 模型从哪里来？

Ollama 的模型托管在 [ollama.com/library](https://ollama.com/library)，里面有几千个模型，涵盖了主流的开源大模型。

**搜索想要的模型：**

```bash
ollama search qwen
```

输出示例：

```
NAME                    DESCRIPTION                     SIZE
qwen2.5:72b             Qwen 2.5 72B                  43GB
qwen2.5:32b             Qwen 2.5 32B                  20GB
qwen2.5:14b             Qwen 2.5 14B                  9.0GB
qwen2.5:7b              Qwen 2.5 7B                   4.9GB
qwen2.5:1.5b            Qwen 2.5 1.5B                 1.1GB
qwen2.5-coder:32b       Qwen 2.5 Coder 32B             20GB
qwen2.5-coder:14b       Qwen 2.5 Coder 14B            9.0GB
```

### 5.2 主流模型推荐

根据不同使用场景，推荐以下模型：

| 场景 | 推荐模型 | 说明 |
|-----|---------|------|
| **日常聊天 / 写作助手** | `qwen2.5:7b` ⭐ | 性价比最高，中文能力强 |
| **代码生成** | `qwen2.5-coder:14b` ⭐ | 阿里专门为代码场景微调 |
| **极低配置设备** | `phi4-mini:3.8b` | 微软出品，支持工具调用，4GB 显存即可 |
| **复杂推理 / 数学** | `qwq:32b` | 具备思维链能力，适合数学证明 |
| **英文为主的任务** | `llama3.1:8b` | Meta 原生，英文能力最强 |
| **多语言翻译** | `mistral:7b` | 指令遵循能力强，多语言表现均衡 |

### 5.3 拉取特定版本的模型

Ollama 支持拉取指定量化版本的模型，满足不同配置需求：

```bash
# 完整版（精度最高，显存占用大）
ollama pull qwen2.5:7b

# Q4 量化版（推荐，平衡精度和性能）
ollama pull qwen2.5:7b-q4_0

# Q8 量化版（更高精度，体积更大）
ollama pull qwen2.5:7b-q8_0

# Q2 量化版（体积最小，精度损失较多）
ollama pull qwen2.5:7b-q2_K
```

> **量化版本说明**：Q2_K ≈ 60% 精度，Q4_K_M ≈ 80% 精度（推荐），Q5_K_M ≈ 90% 精度，Q8_0 ≈ 接近原版。日常使用 Q4_K_M 是最佳选择。

### 5.4 同时管理多个模型

Ollama 支持同时安装多个模型，需要切换时直接 `run` 另一个即可：

```bash
# 安装第二个模型
ollama pull llama3.2:3b

# 切换使用
ollama run qwen2.5:7b      # 用千问
ollama run llama3.2:3b     # 用 Llama
ollama run phi4-mini:3.8b   # 用 Phi
```

---

## 六、GPU 加速配置：如何让模型跑得更快？

### 6.1 NVIDIA 显卡配置

**第一步：安装 NVIDIA 驱动**

确保你的 NVIDIA 显卡驱动是最新的。在 Windows 上，去 NVIDIA 官网下载对应驱动；在 Linux 上：

```bash
# Ubuntu/Debian
sudo apt install nvidia-driver-535

# 验证驱动
nvidia-smi
```

输出类似：

```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 550.54.15  Driver Version: 550.54.15  CUDA Version: 12.4       |
|-------------------------------+----------------------+----------------------+
| GPU  Name        TCC/WDDM  |  Bus-Id  Disp.A  |  Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|      Memory-Usage  | GPU-Util  Compute M. |
|                             |                    |               MIG M.  |
|   0  NVIDIA GeForce ...  WDDM |  00000000:01:00.0 On |                  N/A |
+-------------------------------+----------------------+----------------------+
```

**第二步：安装 CUDA Toolkit**

Ollama 自动使用 NVIDIA 显卡进行加速。如果你的显存足够（6GB+），模型会自动分配到 GPU 上运行。

> **显存不够怎么办？** 如果显存只有 4GB，但模型需要 6GB，Ollama 会自动回退到 CPU 运行。速度会变慢，但不会报错。如果你想强制用 CPU 运行：
> ```bash
> OLLAMA_HOST=0.0.0.0 OLLAMA_NUM_PARALLEL=1 ollama run qwen2.5:7b
> ```

### 6.2 Apple Silicon（Mac M 系列）配置

Mac 用户无需任何额外配置，Ollama 在 Apple Silicon 上开箱即用，且自动利用 Neural Engine 加速。

查看 Ollama 使用的设备：

```bash
# 查看日志中的 GPU 使用情况
tail -f ~/.ollama/logs/server.log
```

> **Mac 用户优化建议**：
> - 保持足够的内存可用（Ollama 会占用约 8GB 内存用于加载模型）
> - MacBook 建议接电源使用，避免电池消耗过快
> - 如果遇到内存不足，Mac 会自动使用磁盘交换，速度会明显下降

### 6.3 AMD 显卡配置（Linux）

AMD 显卡在 Linux 上通过 ROCm 支持：

```bash
# 安装 ROCm（Ubuntu）
sudo apt install rocm-hip-sdk rocm-libs

# 验证
rocminfo | grep "Agent"
```

> **注意**：AMD 显卡支持相对 NVIDIA 来说还不够完善，部分模型可能出现兼容性问题。如果遇到报错，建议查阅 Ollama 官方文档的 [AMD GPU 指南](https://github.com/ollama/ollama/blob/main/docs/amd.md)。

---

## 七、API 调用：让程序也能用大模型

### 7.1 REST API 基础调用

Ollama 启动后会默认在 `http://localhost:11434` 提供 REST API。不需要任何 API Key，直接调用。

**对话补全（Chat Completions）示例：**

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "qwen2.5:7b",
  "messages": [
    { "role": "user", "content": "用 Python 写一个快速排序" }
  ],
  "stream": false
}'
```

**响应示例：**

```json
{
  "model": "qwen2.5:7b",
  "created_at": "2026-04-19T10:30:00.000000Z",
  "message": {
    "role": "assistant",
    "content": "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)\n\nprint(quicksort([3, 6, 8, 10, 1, 2, 1]))"
  },
  "done": true
}
```

### 7.2 生成接口（/api/generate）

用于单轮生成场景，不需要对话历史：

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "解释一下什么是微服务架构",
  "stream": false
}'
```

### 7.3 流式输出（streaming）

把 `"stream": true` 改成流式输出，模型会一个字一个字地返回，适合前端实时展示：

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "qwen2.5:7b",
  "messages": [
    { "role": "user", "content": "讲一个关于程序员的笑话" }
  ],
  "stream": true
}'
```

### 7.4 Python SDK 调用

Ollama 提供了官方 Python SDK，安装方式：

```bash
pip install ollama
```

**Python 代码示例：**

```python
import ollama

# 同步调用
response = ollama.chat(
    model='qwen2.5:7b',
    messages=[
        {'role': 'user', 'content': '解释一下 REST API 是什么'}
    ]
)
print(response['message']['content'])

# 流式调用
stream = ollama.chat(
    model='qwen2.5:7b',
    messages=[
        {'role': 'user', 'content': '用列表说明 Python 的优点'}
    ],
    stream=True
)
for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)
```

**完整 Python 示例（带错误处理）：**

```python
import ollama

def ask_ollama(prompt, model='qwen2.5:7b'):
    """向本地 Ollama 模型提问，带错误处理"""
    try:
        response = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            options={
                'temperature': 0.7,    # 创造性（0~1）
                'num_predict': 512,     # 最大 token 数
                'top_p': 0.9,           # 采样策略
            }
        )
        return response['message']['content']
    except ollama.ResponseError as e:
        print(f'错误: {e.error}')
        return None

# 测试
result = ask_ollama('AI 和机器学习有什么区别？')
if result:
    print(result)
```

### 7.5 JavaScript / TypeScript 调用

```bash
npm install ollama
```

```typescript
import ollama from 'ollama'

const response = await ollama.chat({
  model: 'qwen2.5:7b',
  messages: [
    { role: 'user', content: '什么是函数式编程？' }
  ]
})

console.log(response.message.content)
```

---

## 八、自定义模型：Modelfile 高级玩法

### 8.1 什么是 Modelfile？

Modelfile 是 Ollama 的自定义模型配置文件。你可以通过它：
- 给模型设定系统提示词（相当于设定「人格」）
- 调整模型参数
- 定制默认行为

### 8.2 创建一个「代码助手」模型

创建一个专门用于代码审查的模型：

```dockerfile
# Modelfile（保存为 Modelfile，无后缀）

# 基于 qwen2.5-coder:14b
FROM qwen2.5-coder:14b

# 设置系统提示词
SYSTEM """
你是一位资深软件架构师，精通代码审查。
审查时需要指出：
1. 代码逻辑问题
2. 潜在的性能瓶颈
3. 安全漏洞
4. 可维护性问题
每次审查请给出改进建议和参考代码。
"""

# 参数调优
PARAMETER temperature 0.3
PARAMETER num_ctx 8192
PARAMETER top_p 0.95
```

然后执行：

```bash
# 根据 Modelfile 创建自定义模型
ollama create code-reviewer -f Modelfile

# 使用自定义模型
ollama run code-reviewer
```

现在 `code-reviewer` 就成了一个专属的代码审查助手，比直接用通用模型效果更好。

### 8.3 更多 Modelfile 模板

**模板一：中文作文助手**

```dockerfile
FROM qwen2.5:7b
SYSTEM """
你是一位资深语文老师，擅长指导学生写作文。
你会帮助学生：
1. 梳理文章结构
2. 优化语言表达
3. 提供写作思路建议
"""
PARAMETER temperature 0.8
```

**模板二：翻译助手**

```dockerfile
FROM llama3.1:8b
SYSTEM """
你是一位专业翻译，擅长中英互译和多种语言翻译。
翻译时保持：
1. 原文意思准确
2. 目标语言自然流畅
3. 专业术语准确
"""
PARAMETER temperature 0.2
PARAMETER num_ctx 4096
```

---

## 九、Ollama 常用配置与优化

### 9.1 配置文件位置

Ollama 的配置文件在各平台上：

| 操作系统 | 配置路径 |
|---------|---------|
| macOS / Linux | `~/.ollama/` |
| Windows | `C:\Users\<用户名>\.ollama\` |

**重要子目录：**

```
~/.ollama/
├── models/           # 模型文件存放位置
├── logs/             # 运行日志
└── config.json       # 全局配置
```

### 9.2 修改模型存放路径（解决 C 盘空间不足）

默认情况下，模型会存放在系统盘。如果你的系统盘空间不足，可以迁移到其他盘：

**macOS / Linux：**

```bash
# 方式一：创建软链接
mkdir -p /path/to/large/disk/ollama-models
# 把 ~/.ollama/models 整个迁移过去，然后：
ln -s /path/to/large/disk/ollama-models ~/.ollama/models

# 方式二：设置环境变量（推荐）
export OLLAMA_MODELS=/path/to/large/disk/ollama-models
```

**Windows（PowerShell）：**

```powershell
# 设置用户级环境变量
[Environment]::SetEnvironmentVariable(
    "OLLAMA_MODELS",
    "D:\ollama-models",
    "User"
)
# 重启 Ollama 服务后生效
```

### 9.3 设置默认模型参数

在 `~/.ollama/Modelfile` 中设置全局默认参数：

```
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
```

### 9.4 GPU 内存优化

如果显存不够但还想跑大模型，可以：

```bash
# 强制使用更小的上下文窗口，减少显存占用
OLLAMA_NUM_CTX=2048 ollama run qwen2.5:14b

# 限制并发数量
OLLAMA_NUM_PARALLEL=1 ollama run qwen2.5:14b
```

### 9.5 作为后台服务运行

Ollama 默认在后台运行一个服务进程。如果你想让它开机自启：

**macOS（LaunchD）：**

```bash
brew services start ollama
```

**Linux（systemd）：**

```bash
sudo systemctl enable ollama
sudo systemctl start ollama
```

---

## 十、进阶应用：Ollama + 主流 AI 工具

### 10.1 接入 Cursor AI 编程

Cursor 可以配置使用本地 Ollama 模型：

1. 打开 Cursor Settings → Models
2. 选择「Add OpenAI compatible model」
3. Base URL 填写：`http://localhost:11434/v1`
4. Model 填写：`qwen2.5-coder:14b`
5. API Key 填写：`ollama`（Ollama 不需要真正的 Key，随便填）

### 10.2 接入 Chatbox（桌面客户端）

[Chatbox](https://chatboxai.app) 是一个支持 Ollama 的本地 AI 客户端，支持多会话管理和数据导出。

**配置步骤：**
1. 下载 Chatbox
2. 设置 → 模型设置 → 选择「Ollama API」
3. API Host：`http://localhost:11434`
4. 模型：`qwen2.5:7b`

### 10.3 接入 AnythingLLM（本地知识库）

[AnythingLLM](https://useanything.com) 可以让你基于本地文档构建 RAG 知识库，接入 Ollama 后完全离线运行：

1. 安装 AnythingLLM
2. 选择 Embedding 模型：`nomic-embed-text`
3. 选择 LLM：`qwen2.5:7b`
4. 上传 PDF、Markdown 等文档，即可实现本地文档问答

### 10.4 接入 OpenWebUI（Web 界面）

如果你想要一个类似 ChatGPT 的 Web 界面，可以部署 OpenWebUI：

```bash
# Docker 方式（推荐）
docker run -d \
  -p 3000:8080 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

安装后，打开 http://localhost:3000 即可看到一个美观的 Web 界面。

---

## 十一、常见问题解答（FAQ）

### Q1: 提示「command not found: ollama」，怎么办？

**原因**：安装后没有重启终端，或者环境变量没有生效。

**解决**：
1. 完全关闭并重新打开终端
2. 如果是 Windows，重启电脑
3. Linux/macOS 可以手动刷新环境变量：`source ~/.zshrc` 或 `source ~/.bashrc`

---

### Q2: 模型下载很慢，总是中断怎么办？

**原因**：官方服务器在国外，下载速度受网络影响。

**解决**：
1. 配置科学上网代理：
   ```bash
   # Linux/macOS
   export https_proxy=http://127.0.0.1:7890
   export http_proxy=http://127.0.0.1:7890
   ollama pull qwen2.5:7b
   ```
2. 使用国内镜像源（如果有的话）
3. 分段下载：`ollama pull` 支持断点续传，中断了重新执行即可

---

### Q3: 显存不足（Out of Memory）报错？

**原因**：模型太大，显存装不下。

**解决**：
1. 换成更小的模型（如从 14B 换成 7B）
2. 使用更激进的量化版本（如从 Q4 换成 Q2）
3. 减少上下文窗口大小：`OLLAMA_NUM_CTX=2048 ollama run xxx`
4. 关闭其他占用显存的程序（游戏、Chrome 等）

---

### Q4: macOS 跑模型很热，风扇狂转？

**这是正常现象**，大模型推理是高计算密集型任务。优化建议：
1. 降低并发数：`OLLAMA_NUM_PARALLEL=1`
2. 使用更小的模型（7B 比 14B 发热量小很多）
3. MacBook 建议接电源并关闭不必要的后台应用

---

### Q5: 如何更新 Ollama 到最新版本？

```bash
# macOS (Homebrew)
brew upgrade ollama

# Linux/macOS (官方脚本)
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# 直接重新下载安装包安装，会自动更新
```

> 更新 Ollama 后，已下载的模型文件会保留，无需重新下载。

---

### Q6: 模型回答质量很差，是怎么回事？

可能的原因：
1. **温度参数太高**：试试 `--parameter temperature 0.3`
2. **模型太小**：7B 模型的能力有限，复杂任务需要 14B+
3. **提示词不清晰**：大模型对提示词很敏感，试试更明确的指令
4. **上下文太长**：清空对话重新开始：`/clear`

---

### Q7: Ollama 占用的内存/显存不释放？

Ollama 默认会保留已加载的模型在内存中。要手动释放：

```bash
# 查看当前加载的模型
ollama ps

# 卸载指定模型
ollama stop qwen2.5:7b

# 卸载所有模型
ollama stop all
```

---

## 十二、总结与下一步

### 一张图总结 Ollama 使用流程：

```
第一步：安装 Ollama（3种系统，一条命令）
         ↓
第二步：ollama run qwen2.5:7b（5分钟跑通第一个模型）
         ↓
第三步：ollama list（管理你的模型库）
         ↓
第四步：接入 API / Python SDK / 第三方工具
         ↓
第五步：用 Modelfile 自定义你的专属 AI 助手
```

### 给不同需求的你：

| 你的情况 | 建议 |
|--------|------|
| 第一次接触 AI | 先跑通 `ollama run phi4-mini:3.8b`，体验一下再说 |
| 想本地跑 AI 编程 | 用 `ollama run qwen2.5-coder:14b` + Cursor |
| 有隐私需求的工作流 | 用 Ollama + OpenWebUI + AnythingLLM 搭建完全离线的知识库 |
| 想体验最强开源模型 | `ollama run qwq:32b`（需要 24GB+ 显存）|

---

**相关资源：**

- Ollama 官网：https://ollama.com
- 模型库：https://ollama.com/library
- GitHub：https://github.com/ollama/ollama
- 官方文档：https://github.com/ollama/ollama/blob/main/docs/README.md

---

*本文会持续更新。如果你在安装过程中遇到问题，欢迎在评论区留言，我会尽力解答。*
