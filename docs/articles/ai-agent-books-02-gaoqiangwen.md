# 10个实战项目覆盖8大Agent框架：《大模型项目实战》技术路线解析

如果说黄佳的《动手做AI Agent》是一本"跟着做"的入门书，那么高强文的《大模型项目实战：Agent开发与应用》（机械工业出版社，2025年3月）更像是一本"自己选"的实战手册。

两本书都讲Agent实战，但路子完全不同。

黄佳的书是**线性路径**：从第1个项目做到第7个，一路下来就把Agent的主流技术学完了。

高强文的书是**分类选型**：先告诉你Agent有4大类型、8大框架，再给你10个项目场景自己挑——适合哪种场景就用哪种Agent。

## 这本书的核心价值：选型方法论

市面上讲Agent的书，大多从技术栈出发：先讲LangChain，再讲AutoGPT，再讲MetaGPT。但开发者真正面临的问题是：

**"我有个业务场景，该用哪种Agent？"**

这本书的回答是：先搞清楚Agent的类型，再选框架。

### Agent的四大类型

书中把Agent分为四类：

| 类型 | 特点 | 典型框架 | 适用场景 |
|------|------|----------|----------|
| **通用型** | 能完成多种任务，不限定领域 | AutoGPT、BabyAGI | 开放式任务、探索性工作 |
| **任务驱动型** | 目标明确，按步骤执行 | Devika、CodeFuse-ChatBot | 编程、数据分析、自动化流程 |
| **辅助开发型** | 帮助人类完成开发工作 | Camel、DB-GPT | 代码生成、SQL编写、系统设计 |
| **检索增强型** | 从知识库检索信息辅助回答 | QAnything、MemGPT | 企业知识库、智能客服、文档问答 |

这个分类的价值在于：**选型不再是瞎猜**。

比如你要做一个"自动写代码"的系统，就应该看任务驱动型或辅助开发型，而不是通用型。因为通用型Agent太"发散"，写代码这种目标明确的任务，需要的是"聚焦"。

### 八大Agent框架对比

书中详细介绍了8种Agent框架：

**1. AutoGPT**

最早的自主Agent之一。给定一个目标，它会自己拆解任务、自己执行、自己评估。

```
目标: "帮我研究AI Agent的最新进展"

AutoGPT的执行过程:
1. 搜索"AI Agent 2024 latest developments"
2. 阅读前10篇文章
3. 整理关键信息
4. 写一份总结报告
5. 保存到文件
```

**问题**：容易陷入无限循环，消耗大量Token。

**2. MemGPT**

把"记忆"作为核心能力的Agent。它模拟人类的记忆层次：

```
┌─────────────────────────────────┐
│         Core Memory            │  ← 核心记忆（人物设定、关键信息）
│    (System Prompt + Persona)   │
├─────────────────────────────────┤
│        Working Context         │  ← 工作记忆（当前对话上下文）
│     (Recent Conversation)      │
├─────────────────────────────────┤
│      Archival Memory           │  ← 档案记忆（长期存储）
│    (Vector Database)           │
└─────────────────────────────────┘
```

**优势**：能记住很久之前的对话，适合长期交互的场景。

**3. BabyAGI**

轻量级的任务驱动Agent。核心是任务队列管理：

```python
class BabyAGI:
    def run(self, objective):
        while True:
            # 1. 从队列取任务
            task = self.task_list.pop(0)

            # 2. 执行任务
            result = self.execute(task)

            # 3. 存储结果
            self.memory.add(task, result)

            # 4. 生成新任务
            new_tasks = self.plan(objective, result)
            self.task_list.extend(new_tasks)

            # 5. 排序
            self.prioritize()
```

**优势**：逻辑清晰，容易定制。

**4. Camel**

角色扮演式Agent。两个Agent对话完成任务：

```
User: "帮我设计一个电商推荐系统"

Camel启动两个Agent:
- AI User Agent（需求方）："我需要一个能处理百万用户的推荐系统..."
- AI Assistant Agent（实现方）："我建议使用协同过滤+深度学习的混合架构..."

两个Agent持续对话，最终输出完整方案。
```

**优势**：适合需求不明确的场景，通过对话逐步清晰化。

**5. Devika**

专注于软件开发的Agent。它的流程是：

```
需求 → 分析 → 设计 → 编码 → 测试 → 部署
```

每个环节都有对应的子Agent负责。

**6. CodeFuse-ChatBot**

阿里开源的代码助手Agent。集成了：

- 代码理解（读代码）
- 代码生成（写代码）
- 代码解释（讲代码）
- 代码调试（改代码）

**7. DB-GPT**

数据库领域的Agent。能理解自然语言，转换为SQL：

```
用户: "查询过去一个月销售额超过10万的客户"

DB-GPT:
1. 理解意图
2. 分析数据库schema
3. 生成SQL: SELECT customer_id, SUM(amount) FROM orders WHERE date > DATE_SUB(NOW(), INTERVAL 1 MONTH) GROUP BY customer_id HAVING SUM(amount) > 100000
4. 执行查询
5. 返回结果
```

**8. QAnything**

检索增强型Agent。从任意文档中检索信息：

```
用户: "公司的报销流程是什么？"

QAnything:
1. 从知识库检索相关文档
2. 找到"员工手册.pdf"中的报销章节
3. 提取关键信息
4. 组织答案返回
```

## 10个实战项目：从场景到代码

书中第三篇（7-16章）提供了10个实战项目。我挑几个有代表性的分析。

### 项目1：智能客服Agent

**场景**：企业客服系统，回答产品咨询、处理投诉。

**架构**：

```
用户提问
    ↓
[意图识别] 分类问题类型
    ↓
[知识检索] RAG从知识库找答案
    ↓
[答案生成] LLM组织回复
    ↓
[情感分析] 判断是否需要人工介入
    ↓
返回答案 / 转人工
```

**关键代码**：

```python
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

class CustomerServiceAgent:
    def __init__(self, knowledge_base_path):
        # 加载知识库
        self.vectorstore = Chroma(
            persist_directory=knowledge_base_path,
            embedding_function=OpenAIEmbeddings()
        )
        self.llm = ChatOpenAI(model="gpt-4")

    def answer(self, question):
        # 1. 检索相关文档
        docs = self.vectorstore.similarity_search(question, k=3)

        # 2. 构建上下文
        context = "\n".join([doc.page_content for doc in docs])

        # 3. 生成答案
        prompt = f"""基于以下信息回答用户问题。

知识库内容：
{context}

用户问题：{question}

请给出准确的回答，如果知识库中没有相关信息，请诚实说明。"""

        response = self.llm.invoke(prompt)
        return response.content
```

**踩坑点**：
- 知识库更新后，需要重新构建向量索引
- 敏感问题（投诉、退款）要设置关键词触发人工

### 项目2：代码审查Agent

**场景**：自动审查PR代码，发现潜在问题。

**架构**：

```
Git PR事件
    ↓
[代码获取] 获取变更文件
    ↓
[静态分析] ESLint/SonarQube扫描
    ↓
[AI审查] LLM分析代码逻辑
    ↓
[报告生成] 汇总问题
    ↓
评论到PR
```

**关键代码**：

```python
def review_pr(repo, pr_number):
    # 获取PR的变更文件
    pr = repo.get_pull(pr_number)
    files = pr.get_files()

    issues = []

    for file in files:
        if file.filename.endswith('.py'):
            # 静态分析
            pylint_issues = run_pylint(file.patch)

            # AI审查
            ai_issues = ai_review(file.patch)

            issues.extend(pylint_issues)
            issues.extend(ai_issues)

    # 生成评论
    comment = format_review_report(issues)
    pr.create_issue_comment(comment)

    return issues

def ai_review(code_diff):
    prompt = f"""审查以下代码变更，找出潜在问题：

{code_diff}

请检查：
1. 是否有安全漏洞（SQL注入、XSS等）
2. 是否有性能问题
3. 是否有代码风格问题
4. 是否有逻辑错误"""

    response = llm.invoke(prompt)
    return parse_issues(response.content)
```

**踩坑点**：
- 大文件要分段审查，避免超出Token限制
- AI审查有误报，需要置信度过滤

### 项目3：数据分析Agent

**场景**：用户用自然语言提问，Agent自动分析数据、生成图表。

**架构**：

```
用户问题
    ↓
[问题理解] 提取分析意图
    ↓
[数据定位] 确定数据源
    ↓
[SQL生成] 生成查询语句
    ↓
[执行查询] 获取数据
    ↓
[可视化] 生成图表
    ↓
返回结果
```

**关键代码**：

```python
class DataAnalysisAgent:
    def __init__(self, db_connection, schema_info):
        self.db = db_connection
        self.schema = schema_info

    def analyze(self, question):
        # 1. 生成SQL
        sql = self.generate_sql(question)

        # 2. 执行查询
        data = self.execute_sql(sql)

        # 3. 生成图表
        chart = self.visualize(data, question)

        # 4. 生成解读
        insight = self.generate_insight(data, question)

        return {
            'sql': sql,
            'data': data,
            'chart': chart,
            'insight': insight
        }

    def generate_sql(self, question):
        prompt = f"""根据数据库schema，将用户问题转换为SQL。

数据库结构：
{self.schema}

用户问题：{question}

只返回SQL语句，不要其他解释。"""

        return self.llm.invoke(prompt).content
```

**踩坑点**：
- SQL生成要加入安全检查，防止删除/更新操作
- 复杂查询要分步执行，避免超时

### 项目4：知识库问答Agent

**场景**：企业内部知识库，员工提问，Agent从文档中找答案。

**架构**：

```
用户问题
    ↓
[问题向量化] Embedding
    ↓
[相似度检索] 从向量库找Top-K文档
    ↓
[重排序] 根据问题相关性重排
    ↓
[答案生成] LLM基于文档生成答案
    ↓
返回答案 + 引用来源
```

**关键点**：引用来源很重要。用户要知道答案从哪来，才能判断可信度。

```python
def answer_with_source(question, vectorstore):
    # 检索
    docs = vectorstore.similarity_search(question, k=5)

    # 重排序
    reranked_docs = rerank(question, docs)

    # 生成答案
    context = "\n\n".join([
        f"【来源{i+1}】{doc.metadata['source']}\n{doc.page_content}"
        for i, doc in enumerate(reranked_docs[:3])
    ])

    prompt = f"""基于以下资料回答问题，并在答案中标注引用来源。

资料：
{context}

问题：{question}

请给出答案，并用[来源X]标注引用的信息来源。"""

    answer = llm.invoke(prompt).content

    # 返回答案和来源
    sources = [doc.metadata['source'] for doc in reranked_docs[:3]]
    return {
        'answer': answer,
        'sources': sources
    }
```

**踩坑点**：
- 文档分块要保留语义完整性
- 引用来源要准确，不能"编造"出处

## 这本书的局限性与补充

**局限性1：技术更新快**

书中介绍的框架版本可能已经更新。比如AutoGPT现在有了新版本，API有变化。但核心思想不变，理解了原理就能适应变化。

**局限性2：代码不完整**

书中的代码是教学用的片段，缺少错误处理、日志、配置管理等生产级要素。实际部署需要补全。

**局限性3：缺少评测方法**

Agent的评测是个大问题。书中涉及较少。建议补充学习：
- AgentBench：Agent能力评测基准
- HumanEval：代码能力评测
- RAG评测：检索准确率、答案相关性

## 两本书怎么选？

| 对比维度 | 《动手做AI Agent》（黄佳） | 《大模型项目实战》（高强文） |
|---------|--------------------------|----------------------------|
| 目标读者 | 想系统学习Agent开发的入门者 | 有基础，需要选型指导的开发者 |
| 学习路径 | 线性，按章节推进 | 分类，按场景选择 |
| 项目数量 | 7个 | 10个（+8个框架介绍） |
| 框架覆盖 | LangChain、LlamaIndex、AutoGPT、MetaGPT | AutoGPT、MemGPT、BabyAGI、Camel、Devika、CodeFuse、DB-GPT、QAnything |
| 代码深度 | 较深，有完整实现 | 较浅，重在架构设计 |
| 适合场景 | 跟着做一遍，学会Agent开发 | 遇到具体问题，知道用什么Agent |

**我的建议**：

先读黄佳的书，把7个项目做一遍，建立Agent开发的"肌肉记忆"。

再读高强文的书，建立选型方法论，遇到业务场景能快速判断用哪种Agent。

两本书加起来，刚好覆盖"怎么做"和"怎么选"两个层面。

---

**书籍信息**
- 书名：《大模型项目实战：Agent开发与应用》
- 作者：高强文
- 出版社：机械工业出版社
- 出版时间：2025年3月
- 字数：10.3万字
- 电子书价格：53元（当当云阅读）
- 纸质书价格：64.10元（当当）

**相关书籍**
- 《大模型应用开发：动手做AI Agent》- 黄佳 - 人民邮电出版社 - 2024年5月
