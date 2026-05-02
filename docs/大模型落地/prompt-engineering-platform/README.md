# Prompt Engineering Platform

提示词工程化平台 —— 将提示词开发从"玄学调参"升级为可度量的工程化体系。

## 核心特性

- **模板管理**：变量化提示词模板，支持自动变量提取和渲染
- **版本控制**：Git 式版本管理，支持版本快照、历史追溯、回滚
- **自动评估**：准确率、一致性、延迟等多维指标自动化计算
- **A/B 测试**：统计显著性检验，数据驱动决策
- **生产监控**：调用日志、性能追踪、异常检测与告警

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行演示

```bash
# 初始化示例数据
python main.py init

# 列出所有提示词
python main.py list

# 查看版本历史
python main.py history <prompt_id>

# 运行评估
python main.py evaluate

# A/B 测试
python main.py abtest

# 监控检查
python main.py monitor

# 样本量计算
python main.py sample-size

# 完整工作流
python main.py workflow
```

## 项目结构

```
prompt-engineering-platform/
├── main.py                  # CLI 入口 & 演示集成
├── prompt_manager/          # 提示词管理核心
│   ├── models.py            # 数据模型（Template, Prompt, PromptVersion）
│   ├── repository.py        # SQLite 持久化
│   ├── template.py          # 模板渲染引擎
│   └── manager.py           # 高层业务 API
├── evaluator/               # 评估体系
│   ├── metrics.py           # 评估指标（准确率/一致性/延迟）
│   ├── ab_test.py           # A/B 测试框架
│   └── statistics.py        # 统计检验（t检验/McNemar/样本量计算）
├── monitor/                 # 生产监控
│   ├── tracker.py           # 调用日志追踪
│   └── alerting.py          # 异常检测与告警
├── requirements.txt
└── README.md
```

## 核心工作流

1. **编写模板** → 使用 `{{variable}}` 语法定义可复用的提示词模板
2. **创建提示词** → 关联模板，设置模型参数
3. **发布版本** → 每次修改创建版本快照，冻结模板内容
4. **评估验证** → 自动化批量评估，计算准确率和一致性
5. **A/B 测试** → 对比不同版本的效果，统计检验决策
6. **部署监控** → 跟踪生产调用，异常检测和告警

## 技术栈

- Python 3.10+
- Pydantic v2（数据建模与验证）
- SQLite（轻量持久化）
- Rich（终端 UI）
- NumPy / SciPy（统计计算）
- OpenAI SDK（LLM 调用，可选）


## 架构设计原则

1. **版本即快照**：每个版本冻结完整的模板内容和模型配置，保证可复现
2. **不可变历史**：只追加不删除，回滚通过创建新版本实现
3. **指标可量化**：所有效果评估有数字指标支撑
4. **数据驱动**：A/B 测试 + 统计检验，不做主观判断
5. **开箱即用**：SQLite 存储，零外部依赖即可运行

## 扩展指南

- **接入真实 LLM**：替换 `mock_llm_call` 为 `openai.ChatCompletion.create()`
- **自定义评估指标**：继承 `Evaluator` 类，重写评估逻辑
- **添加告警渠道**：向 `AnomalyDetector` 传入自定义 `alert_handler`
- **生产级存储**：将 SQLite 替换为 PostgreSQL（修改 `PromptRepository`）
