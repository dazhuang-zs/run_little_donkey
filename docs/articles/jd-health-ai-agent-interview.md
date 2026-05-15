# 京东健康 AI Agent 开发工程师面试题库

> **岗位方向**：AI Agent / 大模型应用开发（Java 技术栈）  
> **适用场景**：一面（技术深度）→ 二面（系统设计）→ 三面（产品视野 + 团队领导力）  
> **核心领域**：智能分诊、健康管理、用药依从性、医学知识问答  
> **技术栈**：Java/Spring AI、LangChain4j、RAG、多模态、向量数据库

---

## 【一面】技术深度考察

### 1. 自我介绍

**回答要点**：
- 控制在 2 分钟内，聚焦 AI Agent 相关经验
- 结构：教育背景 + 核心技能 + 2-3 个代表性项目 + 当前关注方向
- 突出：用 Java 技术栈落地大模型应用的实战经验，以及医疗健康场景的领域知识

**示例框架**：
> 我叫 xxx，拥有 x 年 Java 开发经验，近两年专注于 AI Agent 在垂直领域的落地。
>
> 我主导设计并落地了两款 AI Agent 产品：一个是面向慢病管理的智能健康助手，支持多轮对话、用药提醒、健康报告解读；另一个是京东健康的智能分诊 Agent，日均处理 xxx 条问诊分流请求。
>
> 核心技术栈是 Spring AI + LangChain4j，负责过 RAG 知识库搭建、向量化检索、Function Calling 等核心模块的开发。在医疗场景下，我们特别关注幻觉控制、工具调用可靠性和对话状态管理。
>
> 最近在研究多 Agent 协同和持续学习方向，也在关注 OpenClaw 等新兴框架。

---

### 2. 请介绍一下你参与的项目，以及你在其中的角色和核心贡献

**回答要点**：
- 选 1-2 个最相关的项目，重点讲清楚：
  1. **业务背景**：解决了什么问题，为用户/业务带来什么价值
  2. **技术架构**：整体系统分层，关键模块
  3. **个人贡献**：你在其中的具体角色、最有技术含量的部分
  4. **量化成果**：上线效果、指标提升（用数据说话）

**推荐项目模板（以智能健康助手为例）**：

**项目背景**：
> 慢性病患者（高血压/糖尿病）需要持续监测和用药依从，但传统人工客服成本高、响应慢，我们设计了一个 AI Agent 来提供 7×24 小时的个性化健康管理服务。

**个人贡献**：
- 负责整体对话引擎设计，实现多轮对话状态管理（对话历史 + 用户画像 + 健康档案持久化）
- 实现 RAG 知识库Pipeline：医学指南 → 知识抽取 → 向量化 → Milvus 检索，召回率从 62% 提升至 89%
- 设计 Function Calling 扩展：挂号预约、药品查询、运动计话，接口调用成功率 > 99.5%
- 实现护栏机制（Guardrail）：用药剂量边界检查、高风险症状识别自动转人工

**量化成果**：
- 日均服务用户 5000+，对话轮次平均 8.3 轮
- 分诊准确率 91%，用户满意度 NPS +38
- 节省人工客服 40% 工作量

---

### 3. AI Agent 与传统的自动化脚本或 RPA 机器人最主要的区别是什么？你是如何理解"智能"这个维度的？

**回答要点**：从多个维度展开对比，核心体现对"智能"的理解深度

**核心区别**：

| 维度 | RPA/传统自动化脚本 | AI Agent |
|------|------------------|-----------|
| **决策方式** | 规则驱动，if-else 硬编码 | LLM 推理，理解自然语言意图 |
| **灵活性** | 固定流程，变更需改代码 | 自然语言描述即可执行新任务 |
| **泛化能力** | 仅处理预设场景，遇到新场景失效 | 零样本/少样本泛化，处理未见过的输入 |
| **交互方式** | 结构化输入（表单/API） | 自然语言，可多轮追问澄清 |
| **学习方式** | 静态，人工更新规则 | 可从交互中学习（RLHF/RL） |
| **工具使用** | 固定 API 集成，编码层面 | 自主判断并调用外部工具（Tool Use） |
| **容错能力** | 遇到异常直接失败 | 可通过推理补偿、尝试替代方案 |

**智能的理解**：

> "智能"不是"能对话"，而是三层能力的叠加：
>
> **第一层：理解（Perception）**——能准确理解用户模糊、碎片化、甚至有歧义的表达。比如用户说"我这两天头有点晕"，Agent 需要理解这不是"头晕"的字面意思，而是可能涉及血压、血糖、耳石症等多种健康问题。
>
> **第二层：推理（Reasoning & Planning）**——基于理解，自主拆解任务、规划步骤、调用工具。比如"头晕"→ 判断是否需要测量血压 → 查询用户健康档案 → 若血压异常则触发预警或建议挂号。
>
> **第三层：自适应（Learning）**——能从历史交互中提取模式，持续优化对单个用户的个性化服务质量。比如一个用户每次提到"没吃药"后面都跟负面情绪，Agent 学会在下次提醒时语气更温和。
>
> 传统 RPA 只能执行预定义好的固定路径，AI Agent 则能自主决策下一步该做什么——这才是"智能"的核心体现。

---

### 4. 在设计一个 AI Agent 时，你会从哪些方面考虑其系统架构？（可涉及模块划分、数据处理流程）

**回答要点**：给出清晰的架构分层，结合医疗场景具体说明

**推荐架构**：

```
┌─────────────────────────────────────────────────────────────┐
│                     用户交互层（UI / API）                    │
│  文字输入 → 语音识别 → 多模态融合                            │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agent 核心引擎                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 对话状态管理  │  │ 意图识别引擎  │  │  规划器(Planner)│     │
│  │ (Session+DB) │  │ (NLU/分类器)  │  │ (ReAct/CoT)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   护栏层     │  │   记忆层      │  │  工具调度器   │      │
│  │ (Guardrail)  │  │ (短期+长期)   │  │(Tool Router) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    知识与工具层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  RAG知识库   │  │  向量数据库   │  │  外部工具API │      │
│  │(医学指南/药品)│  │   (Milvus)   │  │(挂号/药品/检查)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      模型层                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  主推理模型   │  │  Embedding   │  │  多模态模型   │      │
│  │(通义/DeepSeek)│  │  (文本向量化) │  │(图像理解)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

**模块职责详解**：

| 模块 | 核心职责 | 技术选型 |
|------|---------|---------|
| **对话状态管理** | 维护多轮对话上下文、用户意图链、健康档案 | Redis + PostgreSQL |
| **意图识别引擎** | 将用户输入分类到具体 Intent（如"用药咨询"、"挂号预约"） | Spring AI Chat Model + Few-shot |
| **规划器（Planner）** | 将高层目标拆解为可执行步骤，决定调用哪些工具 | ReAct / CoT / ToolFormer |
| **护栏层（Guardrail）** | 内容安全审查、风险症状拦截、高风险操作二次确认 | 自建规则引擎 + LLM Safety Eval |
| **记忆层** | 短期记忆（当前对话）+ 长期记忆（用户健康画像） | Redis（短期）+ Milvus（长期） |
| **工具调度器** | 管理可用工具、路由请求、处理超时和降级 | LangChain4j Tool 接口 |
| **RAG 知识库** | 医学知识检索，为 Agent 提供准确的领域知识支撑 | LangChain4j + Milvus + 医学语料 |
| **多模态融合** | 处理图片（皮肤照片、体检报告）并结合文字理解 | 通义 VL / GPT-4V |

---

### 5. Agent 的核心循环通常包括感知、规划、执行、学习。在 Spring AI 或 LangChain 的框架实践中，你是如何对应实现这几个环节的？能结合一个具体场景（如用药提醒、报告解读）说明吗？

**回答要点**：结合具体框架和场景讲清楚每个环节的实现方式

**以"用药提醒"场景为例拆解四环**：

**① 感知（Perception）**：
```java
// Spring AI 方式：用户输入 → 结构化感知
UserMessage userMessage = UserMessage.builder()
    .text("我今天早上忘了吃降压药，现在能补吗？")
    .build();

ChatResponse response = chatModel.call(
    new Prompt(List.of(
        new SystemMessage("你是专业医学助手，从用户输入中提取关键实体：药品名称、剂量、用药时间、当前时间"),
        new UserMessage("我今天早上忘了吃降压药，现在能补吗？")
    ))
);
// 提取结果：{drug: "降压药", missed_time: "早上", current_action: "询问能否补服"}
```

**② 规划（Planning）**：
```java
// 使用 LangChain4j ReAct 模式
Agent agent = Agent.builder()
    .chatLanguageModel(chatModel)
    .tools(List.of(
        queryDrugInfoTool,    // 查询药品说明
        queryUserMedHistoryTool, // 查询用户历史用药
        sendReminderTool     // 发送提醒
    ))
    .chatMemory(MessageWindowChatMemory.withMaxMessages(20))
    .promptTemplate("""
        你是一个用药管理专家。使用以下格式推理：
        思考：分析用户问题...
        行动：调用[工具名]，参数{...}
        观察：从工具返回结果...
        最终回答：综合所有信息给出建议
    """)
    .build();

// 实际执行链：
// 思考：用户询问能否补服降压药 → 需要查询药品半衰期 + 用户用药历史
// 行动：queryDrugInfoTool({drug: "降压药", type: "half_life"})
// 观察：降压药半衰期约24小时，早晨漏服可于中午前补服，剂量减半
// 最终回答：给出补服建议 + 记录本次漏服事件
```

**③ 执行（Execution）**：
- 工具调用（Function Calling）：查询药品数据库、写入用药记录、更新健康档案
- 条件分支：若系统判断为高风险（如过量风险），触发人工复核流程
- 结果格式化：将结构化结果转为用户友好的自然语言回复

**④ 学习（Learning）**：
- **短期学习**：本次对话结果写入对话历史（用于本轮后续追问）
- **长期学习**：提取关键模式（如"漏服后用户通常问什么"）更新向量数据库
- **反馈闭环**：用户对回答满意度打分 → 更新意图分类器

---

### 6. 在 Java 技术栈中集成大模型能力，你通常会采用哪种方式？比较直接调用 API、使用 Spring AI 框架、或集成 LangChain4j 的优劣和适用场景。

**回答要点**：三种方案对比，突出场景匹配思维

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **直接调用 API** | 简单轻量、无额外依赖、易调试 | 缺少抽象、每次换模型需改代码、无工具链支持 | 简单单轮调用、快速 POC |
| **Spring AI** | 与 Spring 生态深度集成、模型抽象层好、配置化能力强、测试支持完善 | 发展早期，部分功能不如 LangChain 完善 | 企业级 Java 项目、需要与现有 Spring Boot 系统集成 |
| **LangChain4j** | 工具链完整（Chain/Agent/Tool/Memory）、RAG 支持好、社区活跃 | JVM 生态，Python 版功能更新快有时延，概念复杂 | 复杂多轮对话、需要丰富工具链、需要快速搭建 Agent 能力 |

**我的实践选择**：
> 对于京东健康这类项目，我推荐 **Spring AI + LangChain4j 组合**：
> - Spring AI 负责基础设施层（模型抽象、配置管理、安全）
> - LangChain4j 负责业务层（对话管理、工具编排、Chain 复用）
> - 两者可以很好共存：Spring AI 提供 `ChatModel`，LangChain4j 接收它作为 LLM 实例

**代码示例**：
```java
// Step 1: Spring AI 配置模型
@Configuration
public class AIConfig {
    @Bean
    public ChatModel qwenChatModel() {
        return new OpenAiChatModel(
            OpenAiChatModelOptions.builder()
                .apiKey(apiKey)
                .modelName("qwen-turbo")
                .temperature(0.7)
                .build()
        );
    }
}

// Step 2: LangChain4j 使用 Spring AI 的 ChatModel
AiServices.builder(MedicalAgentServices.class)
    .chatLanguageModel(qwenChatModel)  // 注入 Spring AI 模型
    .chatMemory(MessageWindowChatMemory.withMaxMessages(20))
    .tools(drugQueryTool, appointmentTool, healthRecordTool)
    .build();
```

---

### 7. AI Agent 在处理多轮对话时，如何有效管理和维护对话状态（Dialog State）与上下文（Context）？你在项目中是如何实现的？

**回答要点**：讲清楚三层架构 + 具体技术实现

**对话状态管理的三层架构**：

```
┌─────────────────────────────────────────────────────┐
│          Layer 1: 当前会话状态（短期）                  │
│  - 最近 N 轮对话内容                                  │
│  - 当前意图 + slot 填充状态                            │
│  - 本轮已调用的工具及结果                               │
│  技术：Redis（TTL 30 分钟）                          │
└────────────────────┬──────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────┐
│         Layer 2: 用户档案状态（中期）                   │
│  - 用户基本信息（年龄、病史、过敏源）                    │
│  - 当前疗程（药品、剂量、周期）                         │
│  - 健康目标与偏好                                      │
│  技术：PostgreSQL（持久化）                           │
└────────────────────┬──────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────┐
│         Layer 3: 长期记忆（历史交互沉淀）               │
│  - 用户历史问题模式、关注话题                           │
│  - 行为偏好（喜欢文字/语音、回复偏好）                  │
│  - 健康趋势（血压/血糖长期曲线）                        │
│  技术：Milvus 向量库（相似检索）                       │
└─────────────────────────────────────────────────────┘
```

**具体实现**：

```java
// 对话状态维护类
@Service
public class ConversationStateManager {
    
    // 短期记忆：Redis 存当前会话
    public void saveTurn(String sessionId, String userInput, String agentResponse) {
        String key = "session:" + sessionId;
        List<ChatMessage> history = getHistory(key);
        history.add(new UserMessage(userInput));
        history.add(new AiMessage(agentResponse));
        redisTemplate.opsForValue().set(key, history, 30, TimeUnit.MINUTES);
    }
    
    // 中期记忆：PostgreSQL 存用户档案
    public UserProfile getUserProfile(String userId) {
        return userProfileRepository.findByUserId(userId);
    }
    
    // 长期记忆：向量检索相似历史
    public List<String> retrieveLongTermMemory(String userId, String currentQuery) {
        EmbeddingModel embedding = new BgeSmallZhV15(); // 中文向量化模型
        float[] queryVector = embedding.embed(currentQuery);
        // 检索与该用户相关的历史相似问题
        return milvusClient.search(
            collectionName("user_memory"),
            queryVector,
            filter("user_id=" + userId),
            topK = 5
        );
    }
}
```

**关键设计原则**：
1. **状态分离**：短期（Redis）/中期（DB）/长期（向量库）各司其职
2. **分层注入**：每次推理前将三层状态拼装成 Prompt 上下文
3. **主动压缩**：对话超过 20 轮时用 LLM 总结历史，压缩 Token 消耗

---

### 8. 使用 Spring AI 时，如何对不同的模型提供商（如 OpenAI、通义千问、本地部署模型）进行抽象和统一管理，以实现灵活的模型切换和降级策略？

**回答要点**：讲清楚配置抽象 + 降级策略 + 代码示例

```java
// 1. 模型配置抽象（多模型注册中心）
@Configuration
public class ModelRegistry {
    
    @Bean
    public ChatModel openaiModel() {
        return OpenAiChatModel.builder()
            .apiKey(openaiKey)
            .modelName("gpt-4-turbo")
            .build();
    }
    
    @Bean
    public ChatModel qwenModel() {
        return new TongYiChatModel(
            TongYiChatModelOptions.builder()
                .apiKey(qwenKey)
                .modelName("qwen-turbo")
                .build()
        );
    }
    
    @Bean
    public ChatModel localModel() {
        return new OllamaChatModel(
            OllamaChatModelOptions.builder()
                .baseUrl("http://localhost:11434")
                .modelName("qwen2.5:7b")
                .build()
        );
    }
}

// 2. 模型选择器（场景路由）
@Component
public class ModelRouter {
    
    public ChatModel selectModel(String intent, boolean preferLocal) {
        if (preferLocal && hasLocalModel(intent)) {
            return modelRegistry.localModel(); // 降级到本地模型
        }
        // 根据意图路由到最适合的模型
        return switch (intent) {
            case "medical_diagnosis" -> modelRegistry.qwenModel(); // 中文医疗效果最好
            case "simple_qa" -> modelRegistry.localModel();         // 简单问答用本地省钱
            case "complex_reasoning" -> modelRegistry.openaiModel(); // 复杂推理用 GPT-4
            default -> modelRegistry.qwenModel();
        };
    }
    
    // 3. 降级策略：主模型失败自动切换备选
    public String chatWithFallback(String prompt) {
        try {
            return primaryModel.chat(prompt);
        } catch (Exception e) {
            log.warn("主模型调用失败，降级到通义千问: {}", e.getMessage());
            return qwenModel().chat(prompt);
        }
    }
}
```

**降级策略设计**：
1. **模型级降级**：OpenAI → 通义千问 → 本地 Ollama（三级跳）
2. **功能级降级**：Agent 模式失败降为简单 RAG 模式
3. **响应级降级**：流式输出失败降为普通同步返回

---

### 9. 场景题：假设要为京东健康设计一个"智能分诊"Agent，用户通过文字或语音描述症状，Agent 需要引导问询并初步判断可能的科室或紧急程度。请描述这个 Agent 的关键技术模块和核心处理流程。

**回答要点**：完整系统设计 + 核心模块详解 + 处理流程

**系统架构**：

```
用户（文字/语音）
     ↓
┌──────────────────────────────────────────────────────────────┐
│                    输入处理层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  语音识别   │  │  意图分类   │  │  紧急度评估  │          │
│  │ (ASR/Whisper)│ │ (初筛意图)  │  │ (风险分级)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    分诊推理引擎                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  症状收集   │  │  鉴别诊断   │  │  科室推荐   │          │
│  │(多轮追问)   │  │ (症状→可能疾病)│ │ (匹配科室)  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    安全护栏层                                 │
│  风险症状识别（胸痛/呼吸困难/意识障碍）→ 立即建议120           │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    输出层                                      │
│  科室推荐 + 紧急程度 + 挂号建议 + 健康科普                     │
└──────────────────────────────────────────────────────────────┘
```

**核心处理流程**：

```
Step 1: 症状接收
用户："我最近总是胸闷，爬楼梯的时候喘不上气"
  ↓
Step 2: 紧急度初筛（Guardrail）
  检查是否属于高风险症状（胸痛+呼吸困难 → 立即输出"请立即就医，建议拨打120"）
  若非高危 → 继续流程
  ↓
Step 3: 结构化症状提取
LLM 从自然语言提取：{symptom: "胸闷", trigger: "爬楼梯/运动", duration: "最近", severity: "中"}
  ↓
Step 4: 多轮追问（科室收敛）
"您胸闷时有没有伴随心悸（心跳不规律）或头晕？"
  → 收集补充信息，逐步缩小范围
  ↓
Step 5: 科室匹配
基于完整症状 → 查询科室知识库 → 推荐：心血管内科（优先）或呼吸内科（备选）
  ↓
Step 6: 分诊结果输出
"根据您的描述，建议您首先挂【心血管内科】，近期爬楼梯时胸闷可能与心脏供血相关，建议尽快就诊。是否需要我帮您预约明天的号？"
  ↓
Step 7: 预约挂号（Tool Call）
用户确认 → 调用挂号 API → 返回号源信息
```

**关键技术模块详解**：

| 模块 | 实现方式 | 关键点 |
|------|---------|-------|
| **语音识别** | Whisper API / 阿里云 ASR | 支持方言降级，支持嘈杂环境 |
| **紧急度评估** | 规则引擎 + LLM 双层过滤 | 规则兜底（胸痛/昏迷优先），LLM 做置信判断 |
| **症状提取** | Few-shot Prompt + 结构化输出 | 输出 JSON Schema 格式，便于后续处理 |
| **科室知识库** | RAG：医学指南 + 科室主诉 → Milvus 向量检索 | 定期更新（医学知识时效性） |
| **问询策略** | 决策树 + LLM 动态生成追问 | 按照"主诉 → 伴随症状 → 时间/频率 → 诱因"顺序收敛 |
| **Tool Calling** | 挂号 API + 科室查询 API + 健康科普 API | 幂等设计 + 超时降级 |

---

### 10. Agent 在调用外部工具（Tool Calling）或 API 时，如何保证调用的可靠性、处理异常与超时？

**回答要点**：从容错设计、降级策略、重试机制、隔离设计四个角度回答

**可靠性保障体系**：

**① 重试机制（指数退避）**：
```java
@Retryable(
    value = {HttpTimeoutException.class, HttpServerErrorException.class},
    maxAttempts = 3,
    backoff = @Backoff(delay = 1000, multiplier = 2)
)
public AppointmentResult bookAppointment(AppointmentRequest request) {
    return appointmentApi.book(request);
}
```

**② 超时控制**：
```java
RestTemplate template = new RestTemplate();
template.setConnectTimeout(Duration.ofSeconds(3));
template.setReadTimeout(Duration.ofSeconds(10));  // 读取超时 10s

// Agent 调用时设置合理超时
CompletableFuture<AppointmentResult> future = 
    CompletableFuture.supplyAsync(() -> appointmentApi.book(request))
        .orTimeout(10, TimeUnit.SECONDS)  // 全局超时兜底
        .exceptionally(ex -> {
            log.error("挂号超时: {}", ex.getMessage());
            return AppointmentResult.timeout();
        });
```

**③ 降级策略**：
```java
public AppointmentResult getAppointmentWithFallback(Long deptId, LocalDate date) {
    try {
        // 主方案：实时查询号源
        return onlineAppointmentApi.query(deptId, date);
    } catch (Exception e) {
        log.warn("实时查询失败，降级到缓存数据: {}", e.getMessage());
        // 降级方案：返回当日号源缓存（每5分钟更新一次）
        return appointmentCache.getCached(deptId, date)
            .orElse(AppointmentResult.unavailable(deptId, date));
    }
}
```

**④ 服务隔离（舱壁模式）**：
- 不同工具调用使用独立线程池，避免单一工具阻塞影响整体 Agent
- 挂号 API 线程池（10 线程）、药品查询线程池（20 线程）、健康档案线程池（5 线程）

**⑤ 调用结果校验**：
```java
public AppointmentResult validateAndReturn(Object rawResult) {
    if (rawResult == null) return AppointmentResult.failure("接口返回空");
    if (rawResult.getCode() != 200) return AppointmentResult.failure(rawResult.getMessage());
    if (!validateSchema(rawResult)) return AppointmentResult.failure("返回结构不匹配");
    return (AppointmentResult) rawResult;
}
```

**⑥ 幂等设计**：
- 所有工具调用携带唯一 `requestId`，接口侧做幂等校验
- 防止 Agent 重试时重复挂号、重复创建记录

---

### 11. 在 Agent 的开发中，如何进行效果评估和持续优化？你关注哪些核心指标？

**回答要点**：区分技术指标和业务指标，建立完整的评估体系

**评估指标体系**：

| 类别 | 指标 | 含义 | 目标值 |
|------|------|------|--------|
| **准确性** | 意图识别准确率 | 分类器判断正确的比例 | > 95% |
| | 分诊准确率 | Agent 科室推荐与最终就诊科室一致 | > 90% |
| | RAG 召回率 | 知识库检索结果中包含正确答案的比例 | > 85% |
| **效率** | 首响延迟（P95） | 用户输入到首次响应时间 | < 3s |
| | 全链路延迟（P95） | 含工具调用的完整处理时间 | < 10s |
| | Token 消耗 | 每轮对话平均 Token 成本 | 持续优化 |
| **可靠性** | 工具调用成功率 | 外部 API 调用成功的比例 | > 99% |
| | 兜底率 | 需要转人工处理的比例 | < 5% |
| **体验** | 用户满意度（NPS） | 用户主动打分的均值 | > 40 |
| | 多轮对话维持率 | 对话超过 3 轮的比例 | > 60% |
| | 相似问题重复率 | 用户反复问同一问题的比例 | 监控趋势 |

**持续优化机制**：

1. **线上数据回流**：每次对话结束后记录 `input → output → user_feedback`
2. **Bad Case 分析**：每周 review 低分回答，归因分析（幻觉/工具错误/理解偏差）
3. **A/B 测试**：Prompt 改版先在 5% 流量验证，效果好再全量
4. **模型迭代**：基于 bad case 优化 Few-shot 示例，定期重训 Embedding 模型

---

### 12. 你如何看待 AI Agent 在医疗健康领域的应用边界与伦理风险？在技术实现上如何设置必要的"护栏"（Guardrail）？

**回答要点**：体现对医疗 AI 的敬畏之心，不能只谈技术，要谈边界意识

**应用边界**：

> AI Agent 在医疗健康领域的定位应该是**辅助决策**，而非替代医疗判断。我坚持三条红线：
>
> **红线 1：不能给出诊断结论**
> Agent 只能说"根据您描述的症状，建议您挂 XX 科室"，不能说"你得了 XX 病"。诊断必须由执业医师做出。
>
> **红线 2：不能开具处方**
> 所有用药建议必须引用公开药品说明，且明确标注"请遵医嘱用药"。
>
> **红线 3：不能处理急危重症**
> 胸痛、呼吸困难、意识丧失等症状，Agent 必须立即建议拨打 120，不能尝试"分析"。

**护栏实现**：

```java
// 三层护栏体系

// Layer 1: 规则护栏（兜底，零延迟）
public class RiskSymptomDetector {
    private static final Set<String> HIGH_RISK_KEYWORDS = 
        Set.of("胸痛", "呼吸困难", "意识模糊", "大量出血", "剧烈头痛");
    
    public RiskLevel evaluate(String userInput) {
        if (HIGH_RISK_KEYWORDS.stream().anyMatch(userInput::contains)) {
            return RiskLevel.CRITICAL; // 直接触发 120 建议
        }
        return RiskLevel.NORMAL;
    }
}

// Layer 2: LLM 护栏（语义层面）
public class ContentSafetyGuardrail {
    public boolean isSafe(String response) {
        // 检查回答中是否包含违规内容（诊断结论/处方/极端言论）
        return safetyClassifier.classify(response) == SafeLevel.SAFE;
    }
}

// Layer 3: 合规审查（事后）
public class ComplianceLogger {
    @PostConstruct
    public void logAllResponses() {
        // 所有 Agent 回复写入审计日志，供合规部门抽查
        // 记录：用户ID、输入、输出、时间戳、风险标记
    }
}
```

**伦理风险认识**：

1. **数据隐私**：用户健康数据极其敏感，需严格脱敏、加密存储、最小化使用
2. **公平性**：模型对不同地区、不同语言的用户服务质量要一致，防止算法歧视
3. **透明性**：用户需要知道他们在和 AI 对话（标识义务），AI 的能力边界要清晰告知
4. **可追责性**：所有决策链路要可审计，出了问题能找到责任人

---

## 【二面】系统设计与深度技术

### 1. 深入聊聊你做过的项目。遇到的最大技术挑战是什么？你是如何分析并解决的？

**回答要点**：选择一个有深度的挑战，讲清楚问题分析 → 方案设计 → 实施 → 结果的完整过程

**推荐挑战话题**：

**挑战：医学 RAG 知识库准确率不足（62% → 89%）**

**问题描述**：
> 健康管理 Agent 中，用户问"二甲双胍和格列美脲能一起吃吗"，检索到的文档片段经常答非所问——要么召回的是药品说明书全文（太长，LLM 无法聚焦），要么召回了过期版本的数据。

**分析过程**：
1. **根因定位**（5 Why 分析）：
   - 准确率低 → 检索结果相关性差 → 向量模型不适配医学术语（如"二甲双胍"在不同语境下检索出糖尿病和减肥两种内容）
   - 根本原因：中文医学领域词与通用中文 embedding 存在语义 gap

2. **数据层面**：
   - 医学文档结构混乱（PDF 解析后表格、段落混乱）
   - 药品说明书版本管理不规范，过期内容仍在知识库

3. **检索层面**：
   - 混合检索缺失（仅用向量检索，关键专业术语匹配不足）
   - 重排序（Rerank）环节缺失

**解决方案**：
1. **知识库重建**：医学指南 → 结构化知识图谱（Neo4j），药品信息单独建库，版本号标注
2. **Embedding 模型微调**：用医学问答对（CMRC2019 医学子集）微调 BGE 模型，让专业术语对齐
3. **Hybrid Retrieval**：向量检索（80%）+ BM25 关键词检索（20%）并行，取并集
4. **Rerank 模型**：用 bge-reranker-large 对 Top-20 结果重排序，取 Top-5

**结果**：召回率从 62% 提升至 89%，精确率从 41% 提升至 76%，用户满意度 NPS +28。

---

### 2. Agent 的规划（Planning）能力至关重要。在复杂的健康管理场景中（如慢性病管理涉及用药、运动、饮食、监测），Agent 如何进行任务分解和步骤规划？有没有研究或应用过 ReAct、ToT 等进阶框架思路？

**回答要点**：讲清楚规划的意义 + 具体框架的实践 + 医疗场景的适配

**为什么规划能力对慢病管理至关重要**：

> 慢病管理不是回答一个问题，而是一个**持续多天的行动计划**。比如一个糖尿病患者的目标是"3 个月将 HbA1c 从 8.5% 降到 7%"，Agent 需要把这个大目标分解为：每日用药提醒、每周运动计划（每周3次有氧，每次30分钟）、每餐饮食建议、每两周血糖监测记录回顾。这就是一个典型的任务规划问题。

**ReAct（Reasoning + Acting）框架实践**：

```java
// LangChain4j ReAct Agent 模式
Agent agent = AiServices.builder(DiabetesManagementAgent.class)
    .chatLanguageModel(qwenModel)
    .chatMemory(MessageWindowChatMemory.withMaxMessages(30))
    .tools(List.of(
        updateMedicationLogTool,    // 记录用药
        queryGlucoseHistoryTool,   // 查询血糖历史
        generateExercisePlanTool,   // 生成运动计划
        sendReminderTool,           // 发送提醒
        callNutritionApiTool        // 营养建议
    ))
    .promptTemplate("""
        你是一个糖尿病健康管理专家。用户目标：{goal}
        
        当前时间：{current_time}
        用户最新数据：
        - 血糖：{latest_glucose}
        - 用药：{medication_status}
        
        请按以下步骤推理并行动：
        Thought: 分析当前状态，判断下一步最重要的事
        Action: 调用工具[工具名]，参数{...}
        Observation: 工具返回结果
        Final: 给出个性化建议或执行具体操作
    """)
    .build();

// 示例执行链：
// Thought: 用户 HbA1c 为 8.5%（偏高），用药规律，但近3天血糖波动大（餐后12.8 mmol/L）
//          需要分析原因。查看最近饮食记录和运动情况。
// Action: queryGlucoseHistoryTool({days: 7})
// Observation: 发现餐后血糖在 11-14 mmol/L 波动，午餐后特别高
// Action: queryUserDietLog({meals: "lunch", days: 3})
// Observation: 午餐碳水摄入偏高（米饭约250g）
// Action: generateExercisePlanTool({goal: "降低餐后血糖", constraint: "30分钟有氧"})
// Final: "根据您近3天数据，午餐后血糖偏高，建议将米饭量减少至150g，餐后30分钟散步20分钟，预计可将餐后血糖降低 15-20%。"
```

**ToT（Tree of Thoughts）进阶实践**：

> 对于需要复杂推理的场景（如判断是否需要调整降糖药剂量），我使用 ToT 框架：让 LLM 生成多个可能的方案树，然后评估每个分支的优劣，选择最优路径。

```java
// ToT 规划示例：糖尿病药物调整规划
public class ToTPlanner {
    
    public MedicationPlan planMedicationAdjustment(UserState state) {
        // Step 1: 生成多个可能方案（并行采样）
        List<String> options = llm.batchGenerate("""
            用户情况：HbA1c=8.5%, 近7天空腹血糖波动在 7-9 mmol/L,
            餐后血糖 11-14 mmol/L, 当前用药：二甲双胍 500mg BID。
            请给出3种不同的药物调整方案，每种包含：调整策略、预期效果、风险评估。
        """, n = 3);
        
        // Step 2: 评估每个方案
        List<PlanScore> scoredPlans = options.stream().map(opt -> {
            double effectScore = evaluateEffect(opt, state);    // 预期效果
            double riskScore = evaluateRisk(opt, state);        // 风险
            double costScore = evaluateCost(opt);               // 用药成本
            return new PlanScore(opt, effectScore, riskScore, costScore);
        }).toList();
        
        // Step 3: 选择最优方案（综合评分最高）
        return scoredPlans.stream()
            .max(Comparator.comparingDouble(PlanScore::totalScore))
            .map(PlanScore::getPlan)
            .orElse(defaultPlan);
    }
}
```

**医疗场景的规划约束**：
1. 所有规划方案必须经过**安全校验**（剂量边界、禁忌检查）才能执行
2. 高风险调整（如增加胰岛素剂量）需要**医生确认**才能执行
3. 规划结果要给用户明确说明**依据和不确定性**，不能过于笃定

---

### 3. RAG 是增强 Agent 知识准确性的关键。在健康领域，如何构建高质量的医学知识库（数据来源、清洗、结构化）？在检索阶段，如何提升查询与文档的匹配精度，并处理可能的冲突或过期信息？

**回答要点**：医学知识库的特殊性 + 全流程方案

**数据来源分级**：

| 优先级 | 数据来源 | 权威性 | 更新频率 |
|--------|---------|--------|---------|
| **S级** | 药品说明书（NMPA）、临床指南（中华医学会）、诊疗规范 | ⭐⭐⭐⭐⭐ | 季度更新 |
| **A级** | 医学教科书（8年制内科学）、UpToDate 摘要 | ⭐⭐⭐⭐ | 年度更新 |
| **B级** | CSDN/丁香园/医学论坛高质量问答（需人工审核） | ⭐⭐⭐ | 按需更新 |
| **C级** | 用户生成内容（UGC）健康管理记录 | ⭐⭐ | 实时更新 |

**知识库构建流程**：

```
原始医学文档（PDF/HTML）
    ↓
【解析层】
  PDF 解析（pdfbox）→ 文本提取
  表格识别（table extraction）→ 结构化 JSON
  命名实体识别（BERT-NER）→ 药品/症状/检查指标实体提取
    ↓
【结构化层】
  知识图谱构建（Neo4j）：药品-适应症-禁忌-相互作用
  药品知识库（独立库）：名称/规格/用法/不良反应/相互作用
  症状-科室映射库：主诉 → 可能科室（收敛版）
    ↓
【向量化层】
  分块策略：按语义段落（300-500 tokens/块）+ 保留上下文标题
  Embedding：医学领域微调模型（bge-medical-zh）
  元数据标注：来源、发布时间、版本号、适用范围
    ↓
【质量控制层】
  准确性：医学专家抽检（5% 覆盖率）
  时效性：版本号追踪，过期内容标记为 deprecated
  一致性：相同药品不同来源的冲突检测
```

**检索精度提升**：

1. **混合检索**：
   ```java
   public List<Document> hybridSearch(String query) {
       // 向量检索（语义相似）
       List<Document> semanticResults = milvusClient.search(query, topK=20);
       
       // BM25 关键词检索（术语精确匹配）
       List<Document> keywordResults = bm25Search(query, topK=20);
       
       // 加权合并 + Rerank
       List<Document> merged = mergeResults(semanticResults, keywordResults, weights=[0.7, 0.3]);
       return reranker.rerank(merged, topK=5);  // bge-reranker-large
   }
   ```

2. **查询扩展（Query Expansion）**：
   - 用户输入"头疼" → 扩展为"头痛、头部不适、偏头痛"
   - 使用同义词库（中医药学领域同义词表）进行查询改写

3. **上下文重排（Contextual Rerank）**：
   - 将用户健康档案（病史、用药）作为上下文传入 Rerank 模型
   - 优先召回与用户具体情况最相关的医学知识（如糖尿病用户优先召回糖尿病相关内容）

**冲突与过期处理**：

```java
public class KnowledgeQualityController {
    
    // 过期检测：文档版本号与当前知识库版本对比
    public boolean isOutdated(Document doc) {
        return doc.getVersion() < currentKnowledgeVersion;
    }
    
    // 冲突检测：同一药品不同来源说法矛盾时，优先权威来源
    public Document resolveConflict(List<Document> docs) {
        // 优先级：NMPA > 临床指南 > 教科书 > 论坛
        return docs.stream()
            .sorted(Comparator.comparing(Document::getSourcePriority).reversed())
            .findFirst()
            .orElseThrow(() -> new ConflictException("无法解决文档冲突"));
    }
    
    // 标记不确定性：来源为 C 级时，答案后附"此信息来自社区分享，建议咨询医生"
    public String addDisclaimer(Document doc, String answer) {
        if (doc.getSourcePriority() <= 2) {
            return answer + "\n\n⚠️ 以上信息仅供参考，来自[来源名称]，建议咨询专业医生确认。";
        }
        return answer;
    }
}
```

---

### 4. 多模态能力整合：如果 Agent 需要处理用户的皮肤照片、体检报告图片等，并结合文字描述进行判断，在架构上如何设计？涉及哪些关键组件和技术选型？

**回答要点**：多模态架构设计 + 具体组件选型

**架构设计**：

```
┌─────────────────────────────────────────────────────────────┐
│                    多模态输入处理层                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ 皮肤照片    │  │ 体检报告图  │  │  文字描述   │           │
│  │(手机拍摄)   │  │(PDF/扫描)  │  │  (症状描述) │           │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘           │
│         │              │              │                   │
│  ┌──────▼─────┐  ┌──────▼─────┐  ┌──────▼─────┐          │
│  │  图像预处理  │  │  OCR识别   │  │   NLU     │          │
│  │(去噪/旋转)  │  │(提取表格)   │  │(意图/实体) │          │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘          │
└─────────┼───────────────┼───────────────┼──────────────────┘
          │               │               │
          └───────────────┼───────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    多模态融合层                              │
│  ┌─────────────────────────────────────────────────┐       │
│  │  多模态理解模型（皮肤图像 + 体检报告 + 文字）         │       │
│  │  通义 VL 2.0 / GPT-4V / Gemini Pro Vision         │       │
│  └─────────────────────────────────────────────────┘       │
│  输出：结构化医学解读（症状描述 + 图片发现 + 综合判断）       │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    多模态 Agent 决策层                       │
│  - 皮肤图片发现 → 是否需要皮肤科转诊                         │
│  - 体检报告异常指标 → 结合文字症状综合判断                    │
│  - 高风险发现 → 触发医生介入通知                             │
└─────────────────────────────────────────────────────────────┘
```

**关键组件选型**：

| 功能 | 技术选型 | 选型理由 |
|------|---------|---------|
| **图像编码** | 通义 VL 2.0（阿里）/ GPT-4V（OpenAI） | 中文理解好，支持长上下文（体检报告多页） |
| **OCR 识别** | PaddleOCR（自部署）或 阿里云 OCR | 支持表格结构化提取，医学术语识别准确 |
| **皮肤图像分析** | 专用皮肤病分类模型（如 SkinGPT 架构）+ 通义 VL | 通用模型对皮肤病识别效果一般，需要垂类模型补充 |
| **多模态融合** | Qwen-VL-Chat（免费）+ RAG 知识库 | 开源中文多模态，部署成本低 |
| **报告结构化** | 表格检测模型 + 正则解析 | 体检报告格式相对固定（表格+数值），可规则+模型结合 |

**具体实现流程**：

```java
public class MultimodalAnalysisResult analyzeSkinCondition(String imageUrl, String description) {
    // Step 1: 图片理解
    String imageAnalysis = qwenVL.analyzeImage(imageUrl, """
        请详细描述这张皮肤照片：
        1. 病灶位置、大小、形状、颜色
        2. 是否有红肿、渗液、脱屑
        3. 您的初步判断（请注明置信度）
    """);
    
    // Step 2: 结合症状描述综合判断
    String combinedAnalysis = chatModel.call("""
        图片分析结果：{imageAnalysis}
        用户自述：{description}
        请综合图片和文字信息：
        1. 判断可能疾病类型（并给出置信度和依据）
        2. 是否需要立即就医
        3. 建议就诊科室
    """);
    
    // Step 3: 安全护栏
    if (detectedHighRiskCondition(combinedAnalysis)) {
        // 高风险情况自动通知医生
        doctorNotificationService.notify(imageAnalysis, combinedAnalysis);
    }
    
    return MultimodalAnalysisResult.builder()
        .imageDescription(imageAnalysis)
        .combinedDiagnosis(combinedAnalysis)
        .departmentRecommendation(determineDepartment(imageAnalysis))
        .riskLevel(determineRiskLevel(imageAnalysis))
        .build();
}
```

---

### 5. Agent 的"记忆"机制。如何设计长期记忆和短期记忆，以支持对用户个性化健康习惯的学习和持续服务？在实现上，如何与向量数据库、传统数据库结合？

**回答要点**：记忆架构设计 + 三层实现 + 医疗场景的特殊处理

**三层记忆架构**：

| 层级 | 内容 | 技术选型 | TTL/更新频率 |
|------|------|---------|------------|
| **感官记忆** | 当前轮对话的原始输入输出 | LLM 内部隐状态 | 本轮对话内 |
| **工作记忆** | 最近 20 轮对话摘要 + 当前任务上下文 | Redis（进程内） | 30 分钟 |
| **长期记忆** | 用户健康画像、行为模式、偏好 | PostgreSQL + Milvus | 持久化 + 按需更新 |

**短期记忆（工作记忆）实现**：

```java
@Service
public class WorkingMemoryManager {
    
    // 滑动窗口：保留最近 N 轮完整对话 + 压缩摘要
    public ConversationContext buildWorkingContext(String sessionId) {
        List<ChatMessage> recentMessages = redisTemplate.opsForList()
            .range("chat:" + sessionId, -20, -1);
        
        if (recentMessages.size() >= 15) {
            // 超过 15 轮时压缩历史（节省 Token）
            String summary = llm.summarize压缩对话(
                "将以下对话压缩为 3 句话摘要，保留关键信息：\n" +
                joinMessages(recentMessages.subList(0, recentMessages.size() - 1))
            );
            return new ConversationContext(summary, recentMessages.getLast());
        }
        return new ConversationContext(recentMessages);
    }
}
```

**长期记忆（用户健康画像）实现**：

```java
@Entity
@Table(name = "user_health_profile")
public class UserHealthProfile {
    private String userId;
    private Map<String, Object> healthBaseline;    // 基线数据：血压/血糖正常范围
    private List<String> chronicConditions;         // 慢病列表
    private List<String> allergies;                 // 过敏源
    private List<String> medicationCurrent;         // 当前用药
    
    // 通过向量库存储用户行为模式
    // 例如："用户每次提到'没吃药'后情绪低落" → 存入 Milvus
}

@Service
public class LongTermMemoryManager {
    
    // 存入长期记忆（用户行为模式）
    public void storeBehaviorPattern(String userId, String pattern, float confidence) {
        EmbeddingModel embedding = new BgeZh15();
        float[] vector = embedding.embed("用户行为：" + pattern);
        milvusClient.insert(
            Collection.of("user_memory"),
            vector,
            Metadata.of(
                "user_id", userId,
                "pattern", pattern,
                "confidence", confidence,
                "timestamp", Instant.now().toString()
            )
        );
    }
    
    // 检索相似历史模式
    public List<String> retrieveSimilarPatterns(String userId, String currentSituation) {
        float[] queryVector = embedding.embed(currentSituation);
        return milvusClient.search(
            Collection.of("user_memory"),
            queryVector,
            Filter.eq("user_id", userId),
            topK=5
        ).stream().map(r -> r.getString("pattern")).toList();
    }
}
```

**记忆与知识库的融合**：

```java
public class MemoryAugmentedRAG {
    
    public String answerWithMemory(String userId, String question) {
        // 1. 检索用户长期记忆（个性化上下文）
        List<String> userPatterns = memoryManager.retrieveSimilarPatterns(userId, question);
        
        // 2. 检索通用医学知识
        List<Document> medicalKnowledge = ragPipeline.retrieve(question, topK=5);
        
        // 3. 拼装增强 Prompt
        String enhancedPrompt = """
            用户画像：{getUserProfile(userId)}
            历史模式：{userPatterns}
            相关医学知识：
            {medicalKnowledge}
            
            当前问题：{question}
            请结合用户个性化情况给出回答。
        """;
        
        // 4. 生成答案
        return chatModel.call(enhancedPrompt);
    }
}
```

**医疗场景的特殊设计**：
- **敏感信息保护**：健康档案中的敏感字段（诊断结果、用药记录）需要加密存储，Agent 访问时做脱敏处理
- **记忆时效性**：慢病管理中，健康基线（血压、血糖目标值）需要定期复核更新
- **遗忘机制**：用户主动要求删除记忆的能力（GDPR 合规）

---

### 6. 场景题：设计一个"智能用药依从性管理 Agent"。它需要提醒用户服药，并能回答用户关于"忘吃了怎么办"、"有副作用如何处理"等复杂咨询。请详细阐述其系统设计、核心交互逻辑以及可能用到的 AI 模型工具。

**回答要点**：完整系统设计，覆盖所有功能模块

**系统架构**：

```
┌─────────────────────────────────────────────────────────────┐
│                        用户触达渠道                           │
│  App 推送 / 微信小程序 / 电话外呼 / 短信                       │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    核心 Agent 模块                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ 用药提醒引擎 │  │ 咨询问答引擎 │  │ 依从性分析引擎 │           │
│  │(定时任务)   │  │(RAG+LLM)   │  │(数据统计)   │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    知识与数据层                               │
│  药品说明书库 / 用药知识库 / 用户档案 / 依从性记录              │
└─────────────────────────────────────────────────────────────┘
```

**核心功能模块设计**：

**① 用药提醒引擎**：
- 基于处方信息生成定时提醒任务（晨起/餐后/睡前）
- 提醒策略：首次提醒 → 15分钟后未确认 → 第二次提醒 → 1小时后仍未确认 → 通知家属
- 智能调整：根据用户反馈（"太早了起不来"）动态调整提醒时间

**② 漏服处理咨询**：
```java
// 漏服处理 RAG 问答
public String handleMissedDose(String userId, String drugName, String missedTime) {
    // 1. 查询药品漏服处理规则
    DrugPolicy policy = drugKnowledgeBase.getMissedDosePolicy(drugName);
    
    // 2. 查询用户用药历史
    List<MedicationLog> history = medicationLogRepository.findRecent(userId, drugName, days=7);
    
    // 3. 构造个性化回答
    String response = llm.generate("""
        药品漏服政策：{policy}
        用户历史：{history}
        用户问题：我{drugName}漏吃了，时间是{missedTime}，现在怎么办？
        请给出：① 是否需要补服（附具体规则）② 补服注意事项 ③ 下次正常服药时间调整
        注意：涉及胰岛素等高风险药品时，必须提示"请咨询医生后再决定"
    """);
    
    return addSafetyDisclaimer(response, drugName);
}
```

**③ 副作用咨询**：
```java
// 副作用处理 RAG 问答
public String handleSideEffect(String userId, String drugName, String symptom) {
    // 1. 查询药品已知副作用列表
    List<SideEffect> knownEffects = drugKnowledgeBase.getKnownSideEffects(drugName);
    
    // 2. 判断症状严重程度
    SeverityLevel severity = sideEffectClassifier.classify(symptom, knownEffects);
    
    // 3. 根据严重程度差异化处理
    return switch (severity) {
        case MILD -> normalSideEffectAdvice(drugName, symptom, knownEffects);
        case MODERATE -> moderateSideEffectAdvice(drugName, symptom, knownEffects);
        case SEVERE -> severeSideEffectAdvice(drugName, symptom, knownEffects);
        // SEVERE 情况：立即建议就医，不通过 AI 自主处理
    };
}
```

**核心交互逻辑**：

```
用户："降压药忘吃了，现在下午3点了"
  ↓
Agent 问询澄清：「您吃的是哪种降压药？早上几点应该吃？」
  ↓
用户：「络活喜，晨起吃的」
  ↓
Agent 查询：络活喜（氨氯地平）半衰期 35-50 小时
  ↓
判断：漏服时间在 6 小时内 → 可以补服，建议下午 4 点前补服半片
  ↓
执行：记录本次漏服事件，更新依从性统计
  ↓
输出：「络活喜漏服 6 小时内可补服。建议现在吃半片（2.5mg），明天恢复正常晨起服用。注意监测血压，若有头晕等不适立即休息并就医。」
  ↓
护栏检查：「若血压高于 160/100 mmHg 或有胸痛，立即拨打 120」
```

**AI 模型工具组合**：

| 能力 | 模型/工具 | 说明 |
|------|---------|------|
| 对话理解 | 通义千问（Qwen-Turbo） | 中文理解好，响应快 |
| 药品知识 RAG | LangChain4j + Milvus | 知识检索 |
| 用药安全判断 | 规则引擎 + LLM 双层 | 规则兜底，LLM 增强 |
| 数据统计 | PostgreSQL + Grafana | 依从性报表 |
| 提醒触达 | 极光推送 / 阿里云 SMS | 消息推送 |

---

### 7. Spring AI 的 Function Calling 支持是怎样的？在项目中，你是如何定义和管理这些可供 Agent 调用的函数的？如何保证函数调用的安全性和权限控制？

**回答要点**：Spring AI Function Calling 机制 + 安全设计

**Spring AI Function Calling 支持**：

```java
// 定义一个可用工具（Function）
public class AppointmentBookingFunction implements Tool {
    
    @Bean
    public Tool appointmentTool() {
        return Tool.builder()
            .name("book_appointment")
            .description("预约挂号。用户说「帮我挂心血管内科明天的号」时使用。")
            .inputSchema("""
                {
                  "type": "object",
                  "properties": {
                    "department": {"type": "string", "description": "科室名称"},
                    "date": {"type": "string", "description": "预约日期，格式 YYYY-MM-DD"},
                    "patientName": {"type": "string", "description": "患者姓名"}
                  },
                  "required": ["department", "date"]
                }
            """)
            .action(this::bookAppointment)  // 执行逻辑
            .build();
    }
    
    public AppointmentResult bookAppointment(Map<String, Object> params) {
        String department = (String) params.get("department");
        String date = (String) params.get("date");
        String patientName = (String) params.get("patientName");
        // 调用真实挂号 API
        return appointmentApi.book(department, date, patientName);
    }
}
```

**工具注册与管理**：

```java
@Configuration
public class ToolRegistry {
    
    @Autowired private Tool appointmentTool;
    @Autowired private Tool drugQueryTool;
    @Autowired private Tool healthRecordTool;
    @Autowired private Tool reminderTool;
    
    @Bean
    public List<Tool> allTools() {
        return List.of(
            appointmentTool,
            drugQueryTool,
            healthRecordTool,
            reminderTool
        );
    }
    
    // 工具分组（根据用户权限）
    public List<Tool> toolsForUser(UserRole role) {
        return switch (role) {
            case PATIENT -> List.of(drugQueryTool, healthRecordTool, reminderTool);  // 无挂号权限
            case DOCTOR -> allTools();  // 医生可用全部
            case ADMIN -> allTools();
        };
    }
}
```

**安全性保障**：

| 安全维度 | 实现方式 |
|---------|---------|
| **权限控制** | 工具注册时绑定角色，患者角色无法调用"修改处方"类高危工具 |
| **参数校验** | JSON Schema 校验输入，拒绝不合规参数（如负数剂量、未来日期） |
| **调用限流** | 每用户每分钟同一工具最多调用 10 次，防止滥用 |
| **审计日志** | 所有工具调用记录日志（用户/工具/参数/结果/时间），支持事后追溯 |
| **超时控制** | 单次工具调用超时 10s，超时自动返回错误 |
| **灰度验证** | 高风险工具（如"开具处方"）需要医生二次确认，不做自动化执行 |

---

### 8. 在微服务架构下，如何将 AI Agent 能力以服务的形式提供？如何设计 API 接口、如何处理高并发下的 Agent 实例管理与资源隔离？

**回答要点**：微服务暴露 AI 能力 + 高并发设计

**服务拆分设计**：

```
┌──────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│  /ai-agent/chat  →  对话服务（长连接，流式输出）              │
│  /ai-agent/rag   →  知识检索服务（同步，短响应）              │
│  /ai-agent/tools →  工具注册管理                              │
└──────────────────────────────────────────────────────────────┘
          │                      │                    │
          ▼                      ▼                    ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Chat Service   │   │   RAG Service   │   │  Tool Service   │
│  (Spring WebFlux)│   │  (同步调用)     │   │  (注册/发现)    │
│  - 流式响应     │   │  - 向量检索     │   │  - 权限管理     │
└────────┬────────┘   └────────┬────────┘   └─────────────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐   ┌─────────────────┐
│ Agent Cluster   │   │  Milvus Cluster │
│ (多实例+负载均衡) │   │  (知识库服务)   │
└─────────────────┘   └─────────────────┘
```

**API 接口设计**：

```java
// 对话 API（流式响应）
@RestController
@RequestMapping("/ai-agent")
public class AgentController {
    
    @PostMapping("/chat")
    public Flux<String> chat(@RequestBody ChatRequest request,
                              @RequestHeader("X-User-Id") String userId) {
        // 验证 Token + 权限
        // 限流：每用户 10 次/分钟
        return agentService.streamChat(request, userId)
            .take(Duration.ofSeconds(60))  // 最大响应时间 60s
            .onErrorResume(e -> Flux.just("抱歉，服务暂时不可用，请稍后再试。"));
    }
    
    // 同步知识检索（轻量）
    @PostMapping("/rag/query")
    public RAGResult query(@RequestBody RAGRequest request) {
        return ragService.query(request.getQuestion());
    }
}
```

**高并发下的实例管理**：

1. **Agent 实例池化**：
   - 使用 Spring WebFlux（非阻塞）+ Reactor 实现高并发（单实例支持 1000+ 并发）
   - Kubernetes HPA 基于 CPU + 队列长度自动扩缩容
   - 冷启动优化：Agent 实例预热（提前加载模型到内存）

2. **Token 消耗隔离**：
   - 按用户维度隔离 Token 配额，避免单个用户耗尽全局 Token
   - 使用 Redis 计数实现 Token 配额管理

3. **资源隔离**：
   - 不同优先级的请求走不同队列：紧急（医生端）优先，低优先级（用户端）正常队列
   - GPU 资源池：LLM 推理使用 GPU 池，共享调度

```yaml
# Kubernetes HPA 配置
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-service
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: agent_queue_length
      target:
        type: AverageValue
        averageValue: "10"
```

---

### 9. 谈谈你对 LangChain（或 LangChain4j）中 Chain、Agent、Tool 这些核心抽象的理解。它的设计哲学对你构建 Agent 系统时有什么启发或影响？

**回答要点**：理解核心抽象的设计意图 + 对实际系统设计的启发

**核心抽象理解**：

**Chain（链）**：
> Chain 是将多个操作**有序串联**的执行单元。最经典的 `LLMChain` = Prompt + LLM + OutputParser。它的设计哲学是**确定性**：给定相同的输入，经过 Chain 的每一步都是可预测的。
>
> 类比：在健康管理场景中，"用药提醒流程"就是一个 Chain：触发提醒 → 查询药品信息 → 构造提醒内容 → 发送通知。每一步都是固定的，不依赖 LLM 自主决策。

**Agent（智能体）**：
> Agent 是**带自主决策能力**的 Chain。它不只是执行固定步骤，而是根据当前状态判断"下一步该做什么"。核心循环：感知 → 推理（ReAct/CoT）→ 选择工具 → 执行 → 观察结果 → 继续循环。
>
> 类比：智能分诊就是一个 Agent。用户说"胸闷"，Agent 自主决定：先问"有没有伴随心悸"（工具：追问）→ 查询科室知识库（工具：RAG）→ 推荐科室（工具：科室推荐API）。

**Tool（工具）**：
> Tool 是 Agent 可以调用的外部能力。LangChain 提供了标准化接口，任何外部 API、本地函数、数据库查询都可以封装为 Tool。
>
> 关键点：工具本身是**被动**的，只有被 Agent 调用时才生效。工具的定义包含：名称、描述（供 LLM 理解何时使用）、输入 schema、执行逻辑。

**设计哲学的启发**：

| LangChain 设计理念 | 对我的系统设计启发 |
|------------------|------------------|
| **可组合性**：Chain 可以嵌套 Chain | 将复杂流程拆解为可复用的小 Chain（如"问诊 Chain"、"挂号 Chain"） |
| **工具抽象**：所有外部能力统一 Tool 接口 | 统一封装挂号/药品/健康档案等 API，降低 Agent 与外部系统的耦合 |
| **记忆分离**：Memory 独立于 Agent | 短期/长期记忆分层设计，避免对话膨胀 |
| **Prompt 模板化**：Chain 的每一步可插拔 Prompt | 将医疗场景的专家知识固化为 Prompt 模板，降低 LLM 的幻觉风险 |
| **评估驱动**：内置 evaluation 工具 | 建立 Bad Case 库，每次更新前先跑评估集，确保质量不下降 |

**LangChain4j 的局限性（实战总结）**：
- **调试困难**：Agent 内部决策黑盒，出问题时难以追踪是 Prompt 问题还是工具问题
- **生产监控缺失**：需要自建 Tracing（我使用 OpenTelemetry + Jaeger）
- **Java 生态更新滞后**：Python 版本功能领先 3-6 个月，需要定期迁移

---

### 10. 如何对 AI Agent 系统进行监控和可观测性建设？除了常规的 QPS、耗时，你会特别关注哪些与 AI 相关的指标（如 Token 消耗、推理速率、工具调用成功率等）？

**回答要点**：完整的可观测性体系 + AI 特有指标

**可观测性三支柱**：

```
Metrics（指标）     Logs（日志）          Traces（链路追踪）
     │                  │                    │
 QPS/延迟/错误率    结构化日志          请求全链路追踪
 + AI 特有指标       + Prompt 日志        + Agent 决策路径
 + Token 消耗        + Tool 调用记录       + RAG 检索过程
```

**AI 特有监控指标体系**：

| 维度 | 指标 | 说明 | 告警阈值 |
|------|------|------|---------|
| **Token 消耗** | 每小时 Token 总消耗 | 成本控制 | 超过日均 200% |
| | 每用户 Token 消耗 | 异常用户检测 | 单用户 > 日均 5 倍 |
| | Token 使用效率 | 有效 Token / 总 Token | < 60%（可能存在 Prompt 膨胀） |
| **推理质量** | 工具调用成功率 | 工具返回有效结果的比例 | < 95% |
| | RAG 召回率 | 检索结果包含正确答案的比例 | < 80% |
| | 幻觉率 | 回答中出现事实错误的比例 | < 2% |
| | 兜底率 | 需要转人工处理的比例 | > 5% |
| **推理性能** | LLM 首 token 延迟 | 模型开始响应时间 | P95 < 2s |
| | LLM 推理速率 | tokens/秒 | < 20 tokens/s（模型可能过热） |
| | 向量检索延迟 | Milvus 查询时间 | P95 < 100ms |
| **用户反馈** | 满意度评分分布 | 1-5 分打分 | 平均分 < 3.5 |
| | 回复有用率 | 用户标记"有用"的比例 | < 70% |

**Prometheus + Grafana 监控大盘**：

```yaml
# Prometheus 指标定义（示例）
agent_tokens_total{category="rag", model="qwen-turbo"} 1234567
agent_tool_calls_total{tool="drug_query", status="success"} 98234
agent_tool_calls_total{tool="drug_query", status="failed"} 123
agent_rag_recall_rate{source="medical_knowledge"} 0.89
agent_hallucination_rate{} 0.015
```

**链路追踪（OpenTelemetry）**：

```java
// 为每个 Agent 决策步骤添加 Span
Span span = tracer.spanBuilder("agent.react.step")
    .setAttribute("step", "action")
    .setAttribute("tool", selectedTool)
    .setAttribute("tool_input", toolParams)
    .startSpan();

try {
    Object result = toolExecutor.execute(selectedTool, toolParams);
    span.setAttribute("tool_result", "success");
    span.setAttribute("tool_result_size", result.toString().length());
} catch (Exception e) {
    span.setAttribute("tool_result", "error");
    span.recordException(e);
} finally {
    span.end();
}
```

**日志规范（结构化 JSON）**：

```json
{
  "timestamp": "2026-05-15T08:00:00Z",
  "level": "INFO",
  "type": "agent_tool_call",
  "session_id": "abc123",
  "user_id": "user456",
  "intent": "drug_side_effect",
  "tool": "drug_side_effect_query",
  "tool_params": {"drug": "二甲双胍", "symptom": "恶心"},
  "tool_result": "MILD",
  "latency_ms": 342,
  "token_used": 1234,
  "feedback": null
}
```

**告警规则示例**：
```yaml
# Prometheus Alert Rule
- alert: AgentToolCallFailureRate
  expr: |
    sum(rate(agent_tool_calls_total{status="failed"}[5m])) 
    / sum(rate(agent_tool_calls_total[5m])) > 0.05
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Agent 工具调用失败率超过 5%"
    description: "过去 5 分钟失败率为 {{ $value | humanizePercentage }}"
```

---

## 【三面】产品愿景与团队领导力

### 1. 抛开具体技术，从产品和技术愿景角度，你认为一个理想的"京东健康 AI 健康助手"应该具备哪些核心能力和特征？它与目前常见的客服机器人或知识库搜索有何本质不同？

**回答要点**：产品愿景表达 + 差异化认知

**理想 AI 健康助手的核心能力**：

1. **持续性陪伴，而非一次性问答**
   > 传统客服是"问答式"的，用户问完即走。理想的健康助手应该像"私人健康顾问"一样，持续跟踪用户的健康状态，主动发现问题而非被动响应。比如用户说"最近睡眠不好"，传统机器人会回答睡眠建议然后结束对话；理想助手则会记住这个信号，3天后主动问"睡眠有改善吗？"，7天后问"需要我帮你预约睡眠门诊吗？"

2. **个性化，而非通用回答**
   > 每个人的身体状况、用药历史、生活习惯都不同，理想的助手给出的建议应该是"为你量身定做"的，而非从通用知识库里检索出来的标准答案。

3. **主动性干预，而非被动回答**
   > 不是等用户来问，而是主动发现问题：血糖仪数据异常了，主动联系用户；用户连续 3 天没有运动，主动提醒并调整计划；体检报告出结果了，主动解读并建议下一步。

4. **跨模态理解，不只是文字**
   > 能看懂体检报告图片、皮肤照片、处方照片，能理解语音描述的症状（老人不会打字），能处理多种输入形式的混合（语音+图片+文字）。

5. **可信可控，安全第一**
   > 在医疗领域，用户对 AI 的信任建立在"AI 知道自己不知道什么"的基础上。理想助手会主动说"这个建议需要咨询医生"，而不确定时不会瞎猜。

**本质差异**：

| 维度 | 传统客服机器人 | 知识库搜索 | 理想 AI 健康助手 |
|------|-------------|---------|---------------|
| **交互模式** | 单轮问答 | 搜索-匹配 | 多轮持续跟踪 |
| **个性化** | 无（所有人同一回答）| 弱（基于搜索结果）| 强（基于健康档案）|
| **主动性** | 被动 | 被动 | 主动干预 |
| **记忆能力** | 无 | 无 | 长期记忆用户 |
| **风险意识** | 无 | 无 | 有边界，知道何时该转人工 |
| **核心价值** | 解答问题 | 检索知识 | 管理健康、预防风险 |

---

### 2. 在技术决策层面，当面对一个全新的快速演进的 AI Agent 技术栈（如不断更新的 LangChain、各种新框架）和一个你们团队已经熟悉但可能并非最优的旧方案时，你会如何做技术选型？决策过程中会重点评估哪些维度？

**回答要点**：技术决策框架 + 具体评估维度

**技术选型决策框架**：

```
┌─────────────────────────────────────────────────────┐
│              技术选型三维评估模型                     │
│                                                    │
│   ┌───────────────┐                                │
│   │  业务契合度   │  ← 能否解决真实业务问题？        │
│   │  (Must Have) │    优先级最高                   │
│   └───────────────┘                                │
│          │                                         │
│   ┌───────────────┐   ┌───────────────┐           │
│   │   团队能力    │ + │   生态成熟度   │           │
│   │  (Can Learn) │   │  (Will Survive)│           │
│   └───────────────┘   └───────────────┘           │
│          │                  │                     │
│          ▼                  ▼                     │
│   ┌─────────────────────────────────────────┐     │
│   │          综合决策：做 / 不做 / 观察      │     │
│   └─────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

**评估维度详解**：

| 维度 | 评估问题 | 评估方法 |
|------|---------|---------|
| **业务契合度** | 这个技术能解决我们业务中的哪个具体问题？解决得比现有方案好多少？ | 痛点优先：先列出业务痛点，再找技术方案 |
| **技术成熟度** | 有多少生产环境案例？有没有大厂背书？文档完善吗？ | 参考 LangChain vs Spring AI 的实际落地案例数 |
| **团队学习成本** | 团队现有技能与新技术的 gap 有多大？需要多久能掌握？ | 估算学习曲线 vs 收益，优先选团队能快速掌握的 |
| **可替代性** | 如果这个框架 2 年后停止维护，我们的系统能平滑迁移吗？ | 选择核心逻辑不绑定特定框架的架构（我负责接口抽象层） |
| **性能与成本** | 推理延迟是否满足业务需求？Token 成本是否可接受？ | 压测 + 成本建模 |
| **风险控制** | 新技术引入对现有系统的稳定性有多大影响？ | 采用"渐进式引入"：先在非核心模块试点，验证稳定后再推广 |

**我的选型原则**：
> 核心业务逻辑用团队可控的技术（不依赖最新框架），边缘能力可以用新技术尝试。
>
> 具体来说：对话引擎（RAG、状态管理）用我们自己设计的架构，对齐 LangChain 的理念但不完全依赖其实现；工具层按需接入各家 SDK。这样即使 LangChain 停止更新，我们的核心逻辑不受影响。

---

### 3. 如何带领或协调一个团队从 0 到 1 开发一个 AI Agent 项目？在人员能力构建、开发流程、协同方式上，你认为有哪些需要特别注意的地方？

**回答要点**：团队领导力 + 方法论 + 具体实践

**从 0 到 1 开发 AI Agent 项目的关键要点**：

**① 人员能力构建**：
- **分方向培养**：团队内分为"AI 算法"和"工程实现"两条线，算法方向同学深入 LLM/RAG，工程方向深入 Spring AI/微服务，两条线都要懂 Agent 全流程
- **建立知识共享机制**：每周技术分享会，轮流讲一个 AI Agent 主题（Prompt 工程、RAG 调优、Guardrail 设计等）
- **引入外部培训**：对 LangChain4j、Spring AI 等新框架，安排外训或线上课程

**② 开发流程设计**：
```
Week 1-2: 需求澄清 + 技术方案设计（架构师 + 高级开发）
Week 3-4: MVP 开发（核心对话引擎 + 1-2 个工具）
Week 5:   内部测试 + Bad Case 分析
Week 6-8: 迭代优化（基于 Bad Case 持续改进）
Week 9+:  上线灰度 + 监控体系建设
```

**③ 协同方式**：
- **AI 技术特殊性**：AI Agent 的输出不像传统代码那样确定性，同样 Prompt 可能每次结果不同，所以需要建立"Prompt 版本管理"（像管理代码一样管理 Prompt），所有 Prompt 变更走 Code Review
- **数据驱动开发**：建立 Eval 数据集，每个功能的迭代基于 Eval 效果评估，而非主观感觉
- **跨职能协作**：AI Agent 涉及产品（需求定义）、算法（模型调优）、工程（系统集成）、医学（知识准确性）多方协作，需要明确各方的 Definition of Done

**特别注意的地方**：

1. **不要急于上 AI**：先明确业务场景，用规则/传统方法能解决的就不要用 LLM，降低复杂度
2. **Prompt 即代码**：所有 Prompt 要版本化管理，通过测试后才能上线
3. **效果评估前置**：在开发之初就建立 Eval 集，不要等产品做完了才发现无法评估效果
4. **容错心态**：AI Agent 有不确定性，团队需要有"拥抱不完美"的心态，同时建立快速回滚机制

---

### 4. AI Agent 的幻觉问题是落地中的一大挑战。在健康这种高严谨性领域，你们在项目中采用了哪些工程和技术手段来尽量缓解和控制幻觉？效果如何？

**回答要点**：完整的幻觉控制体系 + 实战效果

**幻觉控制四层体系**：

**Layer 1：输入层——减少触发概率**
```java
// 用户输入校验：检测并拒绝模糊/危险问题
public class InputValidator {
    public ValidationResult validate(String userInput) {
        // 模糊检测：问题太宽泛时，引导用户明确
        if (ambiguityScore(userInput) > 0.7) {
            return ValidationResult.ambiguous("您的问题比较宽泛，能否具体描述一下您的症状？");
        }
        // 超出知识边界的问题直接拒答
        if (outOfScope(userInput)) {
            return ValidationResult.decline("这个问题超出了我的能力范围，建议您咨询专业医生。");
        }
        return ValidationResult.valid();
    }
}
```

**Layer 2：检索层——确保知识来源准确**
- RAG 知识库建设（见上文"知识库构建"），减少 LLM 必须"凭记忆回答"的情况
- 强制要求 LLM 在回答时引用检索到的文档片段（没有引用则提示"我无法确定"）

**Layer 3：推理层——约束 LLM 输出**
```java
// 输出结构化 + 强制引用
public String generateWithCitations(String question, List<Document> context) {
    String prompt = """
        基于以下检索到的文档片段回答问题。如果文档中没有支持某个说法，明确说"我无法确定"。
        文档：{context}
        问题：{question}
        
        要求：
        1. 每个事实性陈述后面标注[来源：文档标题]
        2. 不确定的内容说"我无法确定"
        3. 不编造药品名称、剂量、治疗方法
    """;
    return llm.generate(prompt);
}
```

**Layer 4：验证层——双重检查高风险内容**
```java
// 高风险内容（药品剂量、诊断建议）二次验证
public class MedicalFactChecker {
    
    public FactCheckResult check(String answer, String question) {
        // 提取答案中的医学事实声明
        List<MedicalClaim> claims = extractMedicalClaims(answer);
        
        // 逐一与知识库核实
        for (MedicalClaim claim : claims) {
            if (claim.getType() == ClaimType.DOSAGE) {
                // 药品剂量声明：必须与药品数据库完全一致
                DrugPolicy policy = drugDb.getPolicy(claim.getDrug());
                if (!policy.getDosage().equals(claim.getDosage())) {
                    return FactCheckResult.fails("剂量不匹配：回答中为" + claim.getDosage() 
                        + "，实际应为" + policy.getDosage());
                }
            }
        }
        return FactCheckResult.passed();
    }
}
```

**效果数据**：
- 幻觉率从上线初期 8%（人工抽检）降至 1.5%（持续监控）
- 高风险医学事实错误从 3% 降至 0.2%
- 同时保留了 LLM 的灵活性和自然语言交互体验

---

### 5. 从系统架构角度看，你认为构建一个企业级、可运维、可迭代的 AI Agent 平台，需要哪些核心的中间件或平台组件支持？（可以谈模型管理、评估平台、AB测试、数据回流等）

**回答要点**：平台化思维 + 组件全景图

**企业级 AI Agent 平台组件全景**：

```
┌──────────────────────────────────────────────────────────────┐
│                     用户层                                    │
│           Web / App / 第三方系统                              │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    平台能力层                                  │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  流量管理   │  │  A/B 测试    │  │  Prompt 管理 │         │
│  │  (Gateway)  │  │  (Feature Flag)│ │ (版本化/回滚)│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  评估平台   │  │  监控告警   │  │  数据回流   │           │
│  │  (Eval Hub) │  │ (Prometheus)│  │(用户反馈→训练)│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    模型服务层                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  模型网关   │  │  模型注册   │  │  模型监控   │           │
│  │(统一接入/路由)│  │(版本/回滚)  │  │(延迟/错误率)│          │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    Agent 运行时                               │
│        对话引擎 / RAG Pipeline / 工具调度 / 记忆管理          │
└──────────────────────────────────────────────────────────────┘
```

**核心组件详解**：

| 组件 | 职责 | 关键技术 |
|------|------|---------|
| **模型网关** | 统一接入多个模型（OpenAI / 通义 / 本地），智能路由 | Envoy / 自建 API 网关 |
| **Prompt 管理平台** | Prompt 版本化、灰度发布、AB 测试、回滚 | Git-like 版本控制 |
| **评估平台（Eval Hub）** | 管理 Eval 数据集、自动化评估、A/B 对比 | 构建 Baseline，对比新旧版本 |
| **流量管理** | 根据用户特征（新老/高活/高风险）分配不同 Agent 版本 | Feature Flag / Canary Release |
| **数据回流管道** | 收集用户反馈（点赞/点踩/转人工）→ 清洗 → 入评估集 | Kafka + 实时处理 |
| **可观测性平台** | 全面监控（见上文第 10 题） | Prometheus + Grafana + Jaeger |

---

### 6. Agent 的持续学习（Continual Learning）能力。如何设计系统，使得 Agent 能够从与用户的真实交互中安全地学习并优化自身行为，而不需要频繁的全量重训？

**回答要点**：安全学习机制 + 不重训的增量优化思路

**持续学习设计原则**：

> 核心观点：在不重训基础模型的前提下，通过**Prompt 优化、Few-shot 更新、知识库更新**三种方式实现持续学习。

**① 安全反馈闭环**：

```
用户交互 → 反馈收集 → 自动标注 → 人工审核 → 知识库更新
                            ↓
                      Prompt 模板优化
```

```java
// 反馈自动标注流程
@Service
public class FeedbackProcessor {
    
    public void processFeedback(String sessionId, String question, 
                                 String answer, Integer rating) {
        // 1. 自动收集（用户点赞/点踩 / 抄送给医生）
        if (rating != null && rating <= 2) {
            // 低分回答自动进入 Bad Case 库
            badCaseRepository.save(new BadCase(question, answer, rating, 
                LocalDateTime.now(), sessionId));
        }
        
        // 2. 定期人工审核（每天 20 条）
        // 3. 审核通过的 Bad Case → 更新 Few-shot 示例
        // 4. 审核通过的高质量回答 → 加入知识库
        if (isHighQualityNewPattern(question, answer)) {
            knowledgeBase.addDocument(
                new Document(question, answer, source="user_feedback")
            );
        }
    }
}
```

**② 三层增量优化（无需重训）**：

| 优化层 | 方式 | 更新频率 | 效果 |
|--------|------|---------|------|
| **Prompt 层** | 更新 Few-shot 示例、新增指导规则 | 按周 | 针对特定类型问题效果显著 |
| **知识库层** | 新增文档、更新过期内容 | 按天 | 扩展能力边界，不重训 |
| **工具层** | 新增工具、优化工具描述 | 按月 | 扩展 Agent 能做的事 |

**③ 约束条件**：
- **安全边界**：学习过程需要人工审核，不能自动更新到生产环境
- **可回滚**：每次学习更新都有版本，支持一键回滚到上一版本
- **渐进验证**：更新先在 5% 流量验证，效果好再全量

---

### 7. 谈谈你对"多 Agent 协同"在复杂健康场景（例如，一个负责解读报告，一个负责生成膳食建议，一个负责协调日程）中应用前景的看法。这会带来哪些新的技术挑战？

**回答要点**：多 Agent 协同的价值 + 挑战 + 个人理解

**多 Agent 协同的价值**：

> 医疗健康场景天然适合多 Agent 协同，因为健康问题从来不是单一维度的。体检报告解读需要医学知识，膳食建议需要营养学知识，日程协调需要了解用户的生活节奏——这些能力集中在单一 Agent 里会导致模型"什么都懂一点，但什么都不精"。多 Agent 协同允许每个 Agent 专注自己的领域，通过协作完成复杂任务。

**典型协作场景示例**：

```
用户：上传了体检报告
  ↓
[报告解读 Agent] → 识别异常指标（血脂偏高、尿酸偏高）
  ↓ (传递结构化结果)
[膳食建议 Agent] → 根据异常指标生成个性化饮食方案（低嘌呤+低脂）
  ↓ (传递饮食计划)
[日程协调 Agent] → 结合用户工作安排，建议运动时间/医院复查时间
  ↓ (传递给用户)
用户：收到综合健康方案
```

**新的技术挑战**：

| 挑战 | 描述 | 应对思路 |
|------|------|---------|
| **Agent 间通信协议** | 多个 Agent 如何高效传递信息？结构化数据还是自然语言？ | 设计标准化的 Agent 消息协议（如 JSON Schema），避免纯自然语言传递导致信息损耗 |
| **状态一致性** | 多个 Agent 操作同一用户数据时，如何避免冲突（如报告 Agent 说血糖高，膳食 Agent 说吃甜食）？ | 引入"健康状态中心"，统一管理用户当前健康状态，所有 Agent 读写前先查状态 |
| **协调调度** | 多个 Agent 的执行顺序如何确定？串行还是并行？出错时如何回滚？ | 设计 Orchestrator（编排器）统一调度，使用状态机管理协作流程 |
| **可解释性** | 当最终建议有问题时，如何追溯是哪个 Agent 出错了？ | 每个 Agent 的输入/输出/决策都要完整记录（链路追踪），支持逐层排查 |
| **资源消耗** | 多个 Agent 串联意味着 Token 消耗成倍增长 | 优化 Agent 间信息传递（传递摘要而非全文），设置最大调用深度限制 |
| **隐私合规** | 健康数据在多个 Agent 间流转，安全边界如何保障？ | 每个 Agent 只能访问其职责所需的最少数据（最小权限原则） |

---

### 8. 你个人如何保持对 LLM、AI Agent 领域快速发展的技术敏感度和学习节奏？最近半年，最让你感到兴奋或认为有颠覆性潜力的相关技术、论文或开源项目是什么？

**回答要点**：学习方法和视野 + 具体技术举例

**我的技术敏感度保持方法**：

1. **信息源精选**：
   - 每日：Hugging Face Daily Papers、ArXiv cs.CL 最新论文摘要
   - 每周：Lex Fridman Podcast（AI 方向）、The Batch（吴恩达）
   - 每月：深入读 1-2 篇核心技术论文（而非只看摘要）

2. **动手实践**：
   - 任何新技术我都会在周末跑一个 Mini POC（30 分钟的小实验）
   - 将实验结果写成笔记（Obsidian 知识库）而非只存在脑子里

3. **社区参与**：
   - 参与 LangChain4j、Spring AI 的 GitHub Issue 讨论（提问题 + 看别人怎么解决问题）
   - 在 CSDN 写技术文章（写的过程是最好的学习）

**最近最让我兴奋的技术方向**：

1. **OpenClaw（龙虾）**：
   > Peter Steinberger 的开源项目，2 天 10 万 Star 的记录背后是真正的工程创新——Gateway + WebSocket 架构让 AI Agent 的部署门槛大幅降低，Canvas 可视化和飞书/微信原生支持让 AI 从"极客玩具"变成"普通人的生产力工具"。我认为这类"让 AI Agent 普惠化"的工具会是 2026 年的重要趋势。

2. **MiMo（大模型）**：
   > 小米的开源大模型，在中文场景下的性价比极高，配合百万亿 Token 激励计划，为开发者提供了极低成本的 AI 应用开发基础。我认为 AI Agent + 垂直领域的结合（医疗/法律/教育）会诞生大量机会。

3. **RAG + Knowledge Graph 融合**：
   > 传统向量 RAG 的局限在于"语义相似但事实可能矛盾"，结合知识图谱的精确关系推理可以大幅提升准确性。这在医疗场景特别有价值，因为医学知识的精确性要求远比一般问答场景高。

4. **Function Calling 标准化**：
   > Anthropic、OpenAI、阿里都推出了 Function Calling 规范，标准化后会让多工具协同的 Agent 开发成本大幅降低，不同模型之间可以无缝切换。

---

## 附录：面试准备资源

### 核心参考文档
- Spring AI 官方文档：https://docs.spring.io/spring-ai/reference/
- LangChain4j 官方文档：https://docs.langchain4j.com/
- 京东健康 Agent 技术实践（内部 Wiki）

### 推荐阅读论文
- "ReAct: Synergizing Reasoning and Acting in Language Models"（SyLVester et al., 2023）
- "Tree of Thoughts: Deliberate Problem Solving with Large Language Models"（Yao et al., 2023）
- "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"（Lewis et al., 2020）
- "Guardrails for Safe AI in Healthcare"（Anthropic Safety Guide）

### 推荐实践项目
- 构建一个健康管理 Agent（覆盖 RAG、多轮对话、Tool Calling）
- 参与开源社区（LangChain4j / Spring AI 贡献）
- 在 CSDN 写 AI Agent 实战文章（教学相长）

---

**文档版本**：v1.0  
**维护者**：xiaoyuer  
**更新日期**：2026-05-15