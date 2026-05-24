# AI 开发进阶（第5篇）：多模态 Agent 实战——让 AI 能"看见"和"操作"

> 适合读者：已读完基础9篇 + 前④篇，想让 Agent 不仅能对话，还能看图、操作界面
> 预计阅读时间：40分钟
> 作者：AI小渔村

---

## 前言：文字不是一切

前四篇讨论的都是基于文本的 Agent。但现实世界中，**大量的信息是图片、表格、界面**：

- 用户发来一张截图，问"这个功能在哪"
- 收到一张发票图片，需要提取信息
- 想让 Agent 自动操作浏览器/桌面

**多模态 Agent**，让 AI 从"能说会道"进化到"能看会做"。

---

## 一、多模态 Agent 的三种类型

```
┌─────────────────────────────────────────────────────┐
│              多模态 Agent 能力矩阵                │
├─────────────────────────────────────────────────────┤
│  1. 看懂图片                                       │
│     → 视觉理解：截图、照片、图表 OCR             │
│                                                 │
│  2. 结合视觉+工具                                │
│     → 视觉 + Tool Use：自动化操作界面            │
│                                                 │
│  3. 主动感知 + 行动                            │
│     → 视觉 Agent：像人一样操作电脑              │
└─────────────────────────────────────────────────────┘
```

---

## 二、第一层：视觉理解（Vision Understanding）

### 2.1 基础：图片描述

```python
from openai import AsyncOpenAI
from pathlib import Path
import base64

class ImageDescriber:
    """图片描述器"""
    
    def __init__(self, client: AsyncOpenAI):
        self.client = client
    
    async def describe(self, image_path: str) -> str:
        """描述图片内容"""
        
        # 读取图片并转 base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": "请详细描述这张图片的内容"
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content


# 使用示例
client = AsyncOpenAI()
describer = ImageDescriber(client)

description = await describer.describe("invoice.jpg")
# 输出：这是一张发票图片，显示..."
```

### 2.2 进阶：OCR + 信息提取

```python
from dataclasses import dataclass
from typing import Optional, List
import re

@dataclass
class ExtractedField:
    name: str
    value: str
    confidence: float

class InvoiceExtractor:
    """发票信息提取器"""
    
    def __init__(self, client: AsyncOpenAI):
        self.client = client
    
    async def extract(self, image_path: str) -> List[ExtractedField]:
        """从发票图片提取信息"""
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # 设计 Schema 让输出更结构化
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """请从这张发票图片中提取以下信息，并以 JSON 格式返回：
{
  "invoice_no": "发票号码",
  "date": "开票日期",
  "seller": "销售方",
  "buyer": "购买方",
  "amount": "金额",
  "tax": "税额"
}
如果某项信息无法识别，请返回 "N/A"."""
                        }
                    ]
                }
            ],
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        
        import json
        data = json.loads(response.choices[0].message.content)
        
        return [
            ExtractedField(name=k, value=v, confidence=1.0)
            for k, v in data.items()
        ]


# 使用示例
extractor = InvoiceExtractor(client)
fields = await extractor.extract("invoice.jpg")

for field in fields:
    print(f"{field.name}: {field.value}")
# 输出：
# invoice_no: 0112023001
# date: 2026-05-24
# seller: XXX 公司
# buyer: YYY 公司
# amount: 1000.00
# tax: 130.00
```

### 2.3 应用场景

| 场景 | 技能 | 示例 |
|------|------|------|
| 发票处理 | OCR + 结构化 | 自动提发票信息 |
| 客服截图 | 界面理解 | 理解用户发的截图 |
| 数据图表 | 图表解读 | 从截图提取数据 |
| 手写文字 | OCR | 识别手写信件 |

---

## 三、第二层：视觉 + Tool Use

### 3.1 基础：看懂界面后操作

把视觉理解和工具调用结合起来：

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class UIAction(Enum):
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    WAIT = "wait"
    SELECT = "select"

@dataclass
class UIElement:
    type: str  # button, input, link, etc.
    text: Optional[str] = None
    selector: Optional[str] = None
    xpath: Optional[str] = None
    coordinates: Optional[tuple] = None  # (x, y)

@dataclass
class UIAutomationResult:
    action: UIAction
    element: UIElement
    success: bool
    output: Optional[str] = None


class VisualAutomationAgent:
    """基于视觉的自动化 Agent"""
    
    def __init__(self, vision_client, automation_tools):
        self.client = vision_client
        self.tools = automation_tools  # Playwright/Selenium 等
    
    async def understand_and_act(self, task: str, screenshot_path: str) -> str:
        """理解截图，执行任务"""
        
        # 1. 理解当前界面
        interface_desc = await self._describe_interface(screenshot_path)
        
        # 2. 结合任务，决定下一步
        action_plan = await self._plan_action(task, interface_desc)
        
        # 3. 执行
        result = await self._execute_actions(action_plan)
        
        return result
    
    async def _describe_interface(self, screenshot_path: str) -> str:
        """描述界面元素"""
        
        with open(screenshot_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """请描述这个界面包含的元素：
1. 有哪些按钮？请说出按钮上的文字
2. 有哪些输入框？
3. 当前页面显示了什么内容？
4. 哪里可能有我要找的内容？"""
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    async def _plan_action(self, task: str, interface_desc: str) -> dict:
        """决定下一步动作"""
        
        prompt = f"""当前界面描述：
{interface_desc}

用户任务：{task}

请决定需要做什么操作？返回 JSON：
{{
  "action": "click/type/scroll/wait",
  "target_element": "元素的文字或描述",
  "value": "如果是输入，要输入什么"
}}"""
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    
    async def _execute_actions(self, action_plan: dict) -> str:
        """执行动作"""
        
        action = action_plan["action"]
        
        if action == "click":
            # 点击元素
            await self.tools.click(action_plan["target_element"])
        elif action == "type":
            # 输入文本
            await self.tools.type(action_plan["target_element"], action_plan["value"])
        elif action == "scroll":
            await self.tools.scroll(action_plan.get("direction", "down"))
        
        # 等待页面加载
        await self.tools.wait(1)
        
        return "操作完成"
```

### 3.2 进阶：自动遍历查找

```python
class VisualFinder:
    """视觉元素查找器"""
    
    def __init__(self, automation_agent: VisualAutomationAgent):
        self.agent = automation_agent
    
    async def find_and_click(self, target_text: str, max_scrolls: int = 10) -> bool:
        """滚动查找并点击目标"""
        
        for i in range(max_scrolls):
            # 截取当前界面
            screenshot = await self.agent.tools.screenshot()
            
            # 让模型判断有没有目标
            found = await self._check_if_found(target_text, screenshot)
            
            if found:
                # 点击
                await self.agent.tools.click(target_text)
                return True
            
            # 没找到，向下滚动
            await self.agent.tools.scroll("down")
            await self.agent.tools.wait(0.5)
        
        return False
    
    async def _check_if_found(self, target: str, screenshot_path: str) -> bool:
        """检查目标是否在当前界面"""
        
        with open(screenshot_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        response = await self.agent.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": f"""请判断这个界面是否包含 "{target}" 这个内容？
只回答 YES 或 NO。"""
                        }
                    ]
                }
            ]
        )
        
        return "YES" in response.choices[0].message.content.upper()
```

---

## 四、第三层：Desktop Agent（macOS/Windows）

### 4.1 基础：屏幕读取 + 控制

```python
class DesktopAgent:
    """桌面 Agent"""
    
    def __init__(self):
        self.screenshot_tool = None  # pyautogui / pygetwindow
        self.control_tool = None
    
    async def execute_task(self, task: str) -> str:
        """执行桌面任务"""
        
        # 1. 截取屏幕
        screenshot = self._capture_screen()
        
        # 2. 理解当前状态
        state = await self._understand_state(screenshot)
        
        # 3. 规划动作
        actions = await self._plan_actions(task, state)
        
        # 4. 执行
        for action in actions:
            await self._execute(action)
        
        return "任务完成"
    
    def _capture_screen(self) -> bytes:
        """截取屏幕"""
        import pyautogui
        return pyautogui.screenshot()
    
    async def _understand_state(self, screenshot) -> str:
        """理解屏幕状态（调用视觉模型）"""
        # 同前文的界面描述
        pass
    
    async def _plan_actions(self, task: str, state: str) -> list:
        """规划动作"""
        pass
    
    async def _execute(self, action: dict):
        """执行动作"""
        import pyautogui
        
        action_type = action["type"]
        
        if action_type == "click":
            pyautogui.click(action["x"], action["y"])
        elif action_type == "type":
            pyautogui.typewrite(action["text"])
        elif action_type == "hotkey":
            pyautogui.hotkey(*action["keys"])
        elif action_type == "scroll":
            pyautogui.scroll(action["amount"])
```

### 4.2 高级：根据描述操作

```python
class NaturalDesktopControl:
    """自然语言桌面控制"""
    
    def __init__(self, llm, desktop_agent: DesktopAgent):
        self.llm = llm
        self.agent = desktop_agent
    
    async def natural_control(self, instruction: str) -> str:
        """自然语言控制桌面"""
        
        # 1. 截取当前屏幕
        screenshot = self.agent._capture_screen()
        
        # 2. 用 LLM 理解指令 + 当前界面
        actions = await self._interpret_instruction(instruction, screenshot)
        
        # 3. 执行
        for action in actions:
            await self.agent._execute(action)
        
        return f"已执行：{instruction}"
    
    async def _interpret_instruction(self, instruction: str, screenshot) -> list:
        """解析自然语言指令"""
        
        prompt = f"""你需要根据用户的自然语言指令，控制电脑完成操作。

当前屏幕：（见附件图片）

用户指令：{instruction}

请确定需要做什么操作？返回 JSON 数组：
[
  {{"type": "click", "x": 100, "y": 200}},
  {{"type": "type", "text": "hello"}},
  {{"type": "hotkey", "keys": ["cmd", "c"]}}
]

可能的动作类型：
- click: 点击 (x, y) 坐标
- type: 输入文本
- hotkey: 快捷键
- scroll: 滚动
- wait: 等待

请只返回 JSON，不要其他内容。"""
        
        response = await self.llm.chat([
            {"role": "user", "content": prompt}
        ], image=screenshot)
        
        import json
        return json.loads(response.content)
```

### 4.3 实用场景

| 场景 | 应用 |
|------|------|
| 自动化测试 | 自动操作 GUI 应用 |
| 数据录入 | 读图片/表格，自动填表单 |
| 批量处理 | 批量处理文件 |
| 会议纪要 | 自动截屏 + OCR 记录 |

---

## 五、实战：GPT-4o/Gemini 视觉模型对比

### 5.1 支持的模型

| 模型 | 视觉输入 | 支持场景 | 价格 |
|-----|---------|--------|------|
| GPT-4o | ✅ 128k | 截图、图表、照片 | $5/1M inp |
| Gemini 2.0 Flash | ✅ 10M | 视频理解 | 免费 |
| Claude 3 | ✅ 200k | 超长图像分析 | $3/1M inp |
| 通义千眼 | ⏳ | 国内 | 待定 |

### 5.2 代码对比

```python
# GPT-4o 视觉
response = await openai.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "https://..."}},
            {"type": "text", "text": "描述这个图片"}
        ]
    }]
)

# Gemini 2.0 Flash 视觉
response = await genai.chat.completions.create(
    model="gemini-2.0-flash-exp",
    contents=[
        {"role": "user", "parts": [
            {"inline_data": {"mime_type": "image/jpeg", "data": ...}},
            {"text": "描述这个图片"}
        ]}
    ]
)
```

### 5.3 选择建议

- **快速原型**：GPT-4o（稳定、效果好）
- **超高分辨率**：Claude 3（支持最大）
- **免费/视频**：Gemini 2.0 Flash
- **国内场景**：等通义千眼

---

## 六、总结：多模态 Agent 发展路线

```
阶段1：视觉理解（现在）
  ↓   学会"看"图片，理解内容
阶段2：视觉 + 工具（本月）
  ↓   看到 → 分析 → 操作
阶段3：桌面 Agent（下个月）
  ↓   像人一样操作电脑
阶段4：持续感知（3个月后）
  ← 主动感知环境变化，做出反应
```

**核心思想**：多模态是 Agent 从"对话"到"行动"的关键一步。

文字 Agent 再强，不会看图、不会操作界面，应用场景就受限。
多模态 Agent 让 AI 从"能说会道"变成"能看会做"。

---

## 踩坑经验汇总

1. **图片质量很重要**——模糊的图片严重影响识别效果
2. **坐标需要校准**——不同分辨率下坐标不一样
3. **视觉理解有延迟**——处理图片需要额外 1-3 秒
4. **模型幻觉**——图片识别偶尔会"脑补"，需要验证
5. **权限问题**——桌面控制需要无障碍权限授权

---

**本篇代码**：https://github.com/dazhuang-zs/run_little_donkey/blob/master/docs/articles/ai-dev-advanced-05-multimodal-agent.md

**AI 开发进阶系列（10篇）全文完**

---

## 系列回顾与下一步

**已完成的 10 篇：**

| 序号 | 标题 | 状态 |
|------|------|------|
| 基础 1-9 | API、KV Cache、Agent Loop、Tool Use、Reasoning、MCP、Memory/RAG、Multi-Agent、Prompt/ContextEngineering | ✅ |
| 进阶 ① | 生产级 Agent 评估体系 | ✅ |
| 进阶 ② | AI 系统可观测性 | ✅ |
| 进阶 ③ | 推理加速与成本控制 | ✅ |
| 进阶 ④ | Context Engineering 深入 | ✅ |
| 进阶 ⑤ | 多模态 Agent 实战 | ✅ |

**进阶方向推荐：**

1. **项目驱动**：挑一个小项目，用这 10 篇的内容做一个完整 Agent
2. **垂直领域**：选择一个领域（客服、代码、数据），深入研究该领域的 Agent 设计
3. **面试准备**：这 10 篇内容足够覆盖大多数 AI 开发工程师的面试题

祝你在 AI 开发的路上越走越远 🚀

---

**作者**：AI小渔村  
**许可**：署名-非商业性使用-相同方式共享