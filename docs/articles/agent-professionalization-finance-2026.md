# Agent 专业化的艺术：如何打造一个真正"懂投资"的理财Agent

> **阅读时间**：约25分钟 | **你将学到**：Agent专业化的四个层次、理财Agent的完整技术方案、多Agent协作架构设计、专业Prompt工程实战
>
> **核心观点**：让Agent变专业，不是堆工具，而是构建"知识-工具-流程-进化"的闭环。理财Agent尤其特殊，合规是底线，风险提示是灵魂。

---

## 一、为什么你的Agent总是不够"专业"

很多人做了理财Agent，喂了一堆基金知识、股票数据，但用户一问就露怯：

- "这个基金能买吗？" → 回复一堆数据，但不给明确建议
- "我亏了20%怎么办？" → 一通安慰，没有具体方案
- "推荐个理财产品" → 不问风险承受能力就直接推

问题出在哪？

```
不够专业的Agent：                      专业的Agent：
┌─────────────────────┐               ┌─────────────────────┐
│ 用户问什么答什么      │               │ 主动了解用户情况    │
│ 知识堆砌             │               │ 结合数据给建议      │
│ 不问风险偏好         │               │ 主动提示风险        │
│ 随时可以给出建议     │               │ 合规优先，不乱推    │
└─────────────────────┘               └─────────────────────┘
```

**专业化的本质**：不是知道多少，而是能否在正确的时间、用正确的方式、做正确的事。

---

## 二、Agent专业化的四个层次

### 2.1 第一层：知识注入 —— 让Agent"懂"

Agent的专业性，首先体现在"懂不懂"。

```python
# 理财领域知识库（RAG）
KNOWLEDGE_DOCS = [
    # 基金知识
    """
    ## 基金类型详解
    
    货币基金：
    - 风险等级：R1（最低）
    - 收益：2-3%年化
    - 特点：随时可取，实时到账
    - 适用：备用金、短期资金
    
    债券基金：
    - 风险等级：R2（较低）
    - 收益：4-6%年化
    - 特点：收益稳定，波动小
    - 适用：稳健增值、养老资金
    
    股票基金：
    - 风险等级：R3-R4（中高）
    - 收益：-20%~+40%年化
    - 特点：高波动，高收益
    - 适用：长期投资、能承受亏损
    
    混合基金：
    - 风险等级：R2-R4（可调）
    - 收益：取决于股债比例
    - 特点：灵活配置
    - 适用：平衡型投资者
    """,
    
    # 关键指标
    """
    ## 基金评估指标
    
    夏普比率 (Sharpe Ratio)：
    - 定义：每承担一单位风险获得的超额收益
    - 公式：(组合收益 - 无风险利率) / 组合标准差
    - 解读：越高越好，>1优秀，>2杰出
    
    最大回撤 (Max Drawdown)：
    - 定义：历史最高点到最低点的最大跌幅
    - 解读：越小越好，>30%需要警惕
    
    阿尔法系数 (Alpha)：
    - 定义：跑赢业绩基准的超额收益
    - 公式：实际收益 - 预期收益（β*基准收益）
    - 解读：正值表示跑赢基准
    
    贝塔系数 (Beta)：
    - 定义：组合相对市场的波动程度
    - 解读：=1与市场同步，>1波动大于市场，<1波动小于市场
    
    卡玛比率 (Calmar Ratio)：
    - 定义：年化收益 / 最大回撤
    - 解读：衡量"收益与风险的性价比"
    """,
    
    # 资产配置
    """
    ## 资产配置原则
    
    100减年龄法则：
    - 股票比例 = 100 - 年龄
    - 30岁：70%股票 + 30%债券
    - 50岁：50%股票 + 50%债券
    
    4321法则：
    - 40%：投资（股票、基金等）
    - 30%：生活（房贷、车贷等）
    - 20%：储蓄（应急资金）
    - 10%：保险（保障）
    
    核心-卫星策略：
    - 70%：核心资产（稳健ETF、债券基金）
    - 30%：卫星资产（成长型股票、行业基金）
    """,
    
    # 合规要求
    """
    ## 理财合规要求（重要！）
    
    适当性原则：
    - 不得向低风险客户推荐R3以上产品
    - 首次购买需进行风险测评
    - 销售时必须进行风险揭示
    
    禁止事项：
    - 禁止承诺保本保收益
    - 禁止预测具体点位
    - 禁止推荐未持牌产品
    
    信息披露：
    - 必须告知费率（管理费、托管费、销售服务费）
    - 必须揭示可能的最大亏损
    - 定期报告业绩（季报、半年报、年报）
    """
]
```

### 2.2 第二层：工具赋能 —— 让Agent"会"

光有知识不够，Agent还得"会干活"。

```python
# 理财Agent的专属工具箱
TOOLS = [
    {
        "name": "get_stock_price",
        "description": "获取A股/港股/美股实时股价和涨跌幅",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码，如 600519（茅台）、000001（平安）、AAPL（苹果）"
                },
                "market": {
                    "type": "string",
                    "enum": ["A股", "港股", "美股"],
                    "default": "A股"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_fund_info",
        "description": "获取基金基本信息，包括基金类型、规模、成立时间、基金经理等",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fund_code": {
                    "type": "string",
                    "description": "基金代码，如 161039（易方达消费）、110011（景顺长城新兴成长）"
                }
            },
            "required": ["fund_code"]
        }
    },
    {
        "name": "get_fund_performance",
        "description": "获取基金历史业绩，支持多时间段查询",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fund_code": {"type": "string"},
                "period": {
                    "type": "string",
                    "enum": ["1m", "3m", "6m", "1y", "2y", "3y", "5y", "成立以来"],
                    "description": "统计周期"
                }
            },
            "required": ["fund_code", "period"]
        }
    },
    {
        "name": "calculate_fund_return",
        "description": "计算基金投资收益，支持定投和一次性投入两种方式",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fund_code": {"type": "string"},
                "investment_type": {
                    "type": "string",
                    "enum": ["定投", "一次性"]
                },
                "amount": {
                    "type": "number",
                    "description": "总投入金额"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期 YYYY-MM-DD"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期 YYYY-MM-DD"
                },
                "frequency": {
                    "type": "string",
                    "enum": ["每周", "每月"],
                    "default": "每月",
                    "description": "定投频率"
                }
            },
            "required": ["fund_code", "investment_type", "amount", "start_date", "end_date"]
        }
    },
    {
        "name": "analyze_portfolio",
        "description": "分析投资组合的资产配置、风险暴露、收益率归因",
        "inputSchema": {
            "type": "object",
            "properties": {
                "positions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "asset": {"type": "string", "description": "资产名称/代码"},
                            "weight": {"type": "number", "description": "占比（0-1）"},
                            "return_1y": {"type": "number", "description": "近一年收益率"}
                        },
                        "required": ["asset", "weight"]
                    }
                }
            },
            "required": ["positions"]
        }
    },
    {
        "name": "risk_assessment",
        "description": "评估投资风险，给出风险等级和建议",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_risk_profile": {
                    "type": "string",
                    "enum": ["保守型", "稳健型", "平衡型", "进取型", "激进型"]
                },
                "investment_horizon": {
                    "type": "string",
                    "enum": ["短期(1年内)", "中期(1-3年)", "长期(3年以上)"]
                },
                "assets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "当前持仓（可选）"
                }
            },
            "required": ["user_risk_profile", "investment_horizon"]
        }
    },
    {
        "name": "get_financial_news",
        "description": "获取财经新闻，聚焦宏观、政策、行业动态",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "关键词，如 ['新能源', '半导体']"
                },
                "date": {
                    "type": "string",
                    "description": "日期 YYYY-MM-DD，默认当天"
                }
            }
        }
    },
    {
        "name": "compare_funds",
        "description": "对比多只基金的业绩、费率、风险指标",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fund_codes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "基金代码列表"
                },
                "period": {
                    "type": "string",
                    "enum": ["1y", "3y", "5y"],
                    "default": "1y"
                }
            },
            "required": ["fund_codes"]
        }
    },
]
```

### 2.3 第三层：流程规范 —— 让Agent"对"

专业最重要的一点：**合规**。

理财行业，合规是底线。

```python
"""
风控Agent - 理财系统的"守门员"
每个建议都必须经过风控审核
"""

from typing import Optional
from pydantic import BaseModel
from enum import Enum


class RiskLevel(str, Enum):
    R1 = "R1"  # 保守型
    R2 = "R2"  # 稳健型
    R3 = "R3"  # 平衡型
    R4 = "R4"  # 进取型
    R5 = "R5"  # 激进型


class RiskChecker:
    """风控检查器"""
    
    # 风险等级映射
    risk_score = {
        "R1": 1,
        "R2": 2,
        "R3": 3,
        "R4": 4,
        "R5": 5,
    }
    
    def check(self, fund_risk_level: str, user_risk_level: str) -> dict:
        """
        检查基金风险是否匹配用户风险承受能力
        """
        fund_score = self.risk_score.get(fund_risk_level, 3)
        user_score = self.risk_score.get(user_risk_level, 3)
        
        # 规则：基金风险不能超过用户风险+1级
        if fund_score > user_score + 1:
            return {
                "passed": False,
                "reason": f"该基金风险等级({fund_risk_level})高于您的风险承受能力({user_risk_level})",
                "suggestion": f"建议选择{self._get_recommended_level(user_risk_level)}级别的产品",
            }
        
        return {"passed": True}
    
    def _get_recommended_level(self, user_level: str) -> str:
        """根据用户等级推荐产品"""
        level_map = {
            "R1": "R1",
            "R2": "R1-R2",
            "R3": "R1-R3",
            "R4": "R2-R4",
            "R5": "R2-R5",
        }
        return level_map.get(user_level, "R1-R3")
    
    def generate_warning(self, fund_data: dict, user_risk_level: str) -> str:
        """生成风险揭示"""
        warnings = []
        
        # 基础风险揭示
        warnings.append("基金过往业绩不代表未来表现")
        warnings.append("市场有风险，投资需谨慎")
        
        # 个性化风险揭示
        if fund_data.get("risk_level") in ["R4", "R5"]:
            warnings.append(f"该基金为高风险({fund_data['risk_level']})产品，可能遭受本金大幅亏损")
        
        if fund_data.get("leverage"):
            warnings.append("该基金为杠杆产品，亏损可能超过本金")
        
        if fund_data.get("concentration") > 0.5:
            warnings.append(f"该基金持仓集中度较高({fund_data['concentration']*100}%)，分散度不足")
        
        return "；".join(warnings)


class ComplianceChecker:
    """合规检查器"""
    
    def check_prompt(self, response: str) -> dict:
        """检查回复是否合规"""
        violations = []
        
        # 检查是否承诺保本
        forbidden_words = ["保本", "保证收益", "稳赚", "不会亏", "必涨"]
        for word in forbidden_words:
            if word in response:
                violations.append(f"包含承诺性词汇：{word}")
        
        # 检查是否预测点位
        prediction_words = ["会涨到", "会跌到", "突破", "跌破", "目标价"]
        for word in prediction_words:
            if word in response:
                violations.append(f"包含预测性内容：{word}")
        
        # 检查是否有风险提示
        if "风险" not in response and "风险" not in response.lower():
            violations.append("缺少风险提示")
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
        }
```

### 2.4 第四层：持续进化 —— 让Agent"更好"

```python
"""
Agent进化系统 - 从实践中学习
"""

class AgentEvolution:
    """Agent进化器"""
    
    def __init__(self):
        self.feedback_log = []  # 用户反馈
        self.bad_cases = []     # Bad case库
        self.improvements = []  # 改进记录
    
    def record_feedback(self, query: str, response: str, feedback: str):
        """记录用户反馈"""
        self.feedback_log.append({
            "query": query,
            "response": response,
            "feedback": feedback,
            "timestamp": datetime.now(),
        })
    
    def analyze_bad_cases(self):
        """分析Bad Cases"""
        # 统计被标记"不专业"、"不准确"的case
        bad = [f for f in self.feedback_log if f["feedback"] in ["不专业", "不准确", "没用"]]
        
        # 提取共性问题
        # 问题1：没问风险偏好就推荐
        # 问题2：推荐的基金规模太小
        # 问题3：没有给具体建议
        
        # 自动生成改进Prompt
        improvements = []
        if any("风险" in f["query"] and "推荐" in f["query"] for f in bad):
            improvements.append("推荐前必须先了解用户风险承受能力")
        
        return improvements
    
    def update_prompt(self, improvements: list):
        """更新Prompt"""
        # 每次微调或定期更新Prompt
        pass
```

---

## 三、多Agent协作架构

专业的事交给专业的Agent。

```
┌─────────────────────────────────────────────────────────────────┐
│                      理财Agent系统架构                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐                                              │
│   │   用户入口    │   小惠理财助手（对话入口，意图识别）           │
│   └──────┬───────┘                                              │
│          │                                                        │
│          ▼                                                        │
│   ┌─────────────────────────────────────────┐                    │
│   │           Agent Router（意图路由）        │                    │
│   │                                          │                    │
│   │   - 选基金 → 基金Agent                   │                    │
│   │   - 诊股票 → 股票Agent                  │                    │
│   │   - 组合建议 → 组合Agent                 │                    │
│   │   - 知识问答 → 问答Agent                 │                    │
│   │   - 投诉处理 → 人工客服                  │                    │
│   └─────────────────────┬───────────────────┘                    │
│                         │                                          │
│          ┌──────────────┼──────────────┐                         │
│          ▼              ▼              ▼                          │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│   │  基金Agent │ │  股票Agent │ │  组合Agent │               │
│   │            │ │            │ │            │               │
│   │ - 选基推荐 │ │ - 诊股分析 │ │ - 配置建议 │               │
│   │ - 收益计算 │ │ - 财报解读 │ │ - 再平衡   │               │
│   │ - 定投规划 │ │ - 估值判断 │ │ - 风控评估 │               │
│   │ - 基金对比 │ │ - 风险提示 │ │ - 收益归因 │               │
│   └─────┬──────┘ └─────┬──────┘ └─────┬──────┘               │
│         │               │               │                        │
│         └───────────────┼───────────────┘                        │
│                         ▼                                         │
│              ┌─────────────────────┐                              │
│              │   风控Agent（审核）   │  ← 关键！必须有            │
│              │                      │                              │
│              │ - 风险等级匹配       │                              │
│              │ - 合规检查           │                              │
│              │ - 风险提示生成       │                              │
│              │ - 适当性管理         │                              │
│              └──────────┬──────────┘                              │
│                         │                                          │
│                         ▼                                          │
│              ┌─────────────────────┐                              │
│              │   知识库Agent       │  ← RAG增强                  │
│              │   (背景知识查询)     │                              │
│              └──────────┬──────────┘                              │
│                         │                                          │
│                         ▼                                          │
│              ┌─────────────────────┐                              │
│              │   输出给用户         │                              │
│              │   - 建议            │                              │
│              │   - 数据支撑        │                              │
│              │   - 风险揭示        │                              │
│              │   - 后续行动        │                              │
│              └─────────────────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、专业Prompt怎么写

```python
FINANCIAL_AGENT_PROMPT = """
你是小惠，一位专业的理财顾问，具有基金从业资格和10年投资经验。

## 身份设定
- 你说话专业但易懂，不过度使用术语
- 你用数据说话，每条结论都有数据支撑
- 你主动提示风险，不回避负面信息

## 核心原则（按优先级）

### 适当性原则（最高优先级）
1. 首次推荐产品前，必须先了解用户风险承受能力
2. 只推荐与用户风险等级匹配的产品
3. 保守型用户绝对不能推荐R3以上产品

### 透明原则
1. 如实告知费率（管理费、托管费、销售服务费）
2. 如实告知可能的亏损
3. 明确区分"历史业绩"和"未来预期"

### 长期主义
1. 强调复利的力量
2. 反对追涨杀跌
3. 推荐长期持有

## 知识边界
- ✅ 你熟悉：公募基金、私募基金、A股、港股的基础知识
- ✅ 你了解：宏观经济、政策变化对市场的影响
- ✅ 你擅长：基金选择、组合配置、风险评估
- ❌ 你不预测：具体股价走势
- ❌ 你不推荐：未持牌产品
- ❌ 你不承诺：保本收益

## 对话流程

### 第一步：了解用户
用户来之后，先判断意图：
- 如果要推荐产品 → 先问风险偏好
- 如果要分析持仓 → 先获取持仓信息
- 如果要知识问答 → 直接回答

### 第二步：收集信息
- 风险承受能力（保守型/稳健型/平衡型/进取型/激进型）
- 投资期限（短期1年内/中期1-3年/长期3年以上）
- 投资金额
- 投资目标

### 第三步：给出建议
每条建议必须包含：
1. **建议内容**：明确告诉用户该怎么做
2. **数据支撑**：用数据支持你的结论
3. **风险揭示**：明确告知可能的风险
4. **后续行动**：告诉用户接下来该做什么

## 输出格式模板

```
【建议】{明确的动作}

【分析】{数据和分析}

【风险揭示】{可能的风险}

【下一步】{具体行动}
```

## 禁止事项（红线）
- ❌ 绝对不能承诺保本
- ❌ 绝对不能预测具体点位
- ❌ 绝对不能推荐高于用户风险承受能力的产品
- ❌ 绝对不能隐瞒费用
"""
```

---

## 五、实战：构建一个基金分析Agent

```python
"""
基金分析 Agent - 完整实现
"""

from typing import Optional, List
from pydantic import BaseModel
from dataclasses import dataclass
from enum import Enum


class RiskProfile(str, Enum):
    CONSERVATIVE = "保守型"     # R1
    PRUDENT = "稳健型"         # R2
    BALANCED = "平衡型"         # R3
    AGGRESSIVE = "进取型"      # R4
    VERY_AGGRESSIVE = "激进型" # R5


class InvestmentHorizon(str, Enum):
    SHORT = "短期(1年内)"
    MEDIUM = "中期(1-3年)"
    LONG = "长期(3年以上)"


@dataclass
class FundData:
    """基金数据"""
    code: str
    name: str
    risk_level: str
    type: str
    manager: str
    aum: float  # 规模
    return_1y: float
    return_3y: float
    sharpe_ratio: float
    max_drawdown: float
    fees: dict


class FundAnalysisAgent:
    """基金分析Agent"""
    
    def __init__(self):
        self.tools = FundTools()      # 基金工具
        self.knowledge = FundKnowledge()  # 知识库
        self.risk_checker = RiskChecker()    # 风控
        self.compliance = ComplianceChecker() # 合规
    
    async def analyze(self, fund_code: str, user_profile: dict) -> dict:
        """分析基金并给出建议"""
        
        # 1. 获取基金数据
        fund_data = await self.tools.get_fund_info(fund_code)
        performance = await self.tools.get_fund_performance(fund_code, "3y")
        
        # 2. 风控检查（关键！）
        risk_result = self.risk_checker.check(
            fund_risk_level=fund_data.risk_level,
            user_risk_level=user_profile["risk_profile"],
        )
        
        # 3. 如果风控不通过，直接返回不建议
        if not risk_result["passed"]:
            return {
                "recommendation": "不建议购买",
                "reason": risk_result["reason"],
                "alternative": risk_result.get("suggestion"),
                "warning": self.risk_checker.generate_warning(
                    {"risk_level": fund_data.risk_level},
                    user_profile["risk_profile"]
                ),
            }
        
        # 4. 生成分析
        analysis = self._generate_analysis(fund_data, performance, user_profile)
        
        # 5. 合规检查
        compliance_result = self.compliance.check_prompt(analysis["response"])
        if not compliance_result["passed"]:
            analysis["response"] = self._fix_compliance(
                analysis["response"], 
                compliance_result["violations"]
            )
        
        return analysis
    
    def _generate_analysis(self, fund: FundData, perf: dict, user: dict) -> dict:
        """生成分析报告"""
        
        # 计算各项得分
        score = 0
        reasons = []
        
        # 规模得分
        if fund.aum > 50:  # 50亿以上
            score += 20
            reasons.append(f"规模{fund.aum}亿，运作稳健")
        elif fund.aum < 2:  # 2亿以下
            score -= 10
            reasons.append(f"规模较小({fund.aum}亿)，有清盘风险")
        
        # 业绩得分
        if perf["return_3y"] > 50:
            score += 30
            reasons.append(f"近3年收益{perf['return_3y']}%，表现优秀")
        elif perf["return_3y"] < 0:
            score -= 20
            reasons.append(f"近3年收益{perf['return_3y']}%，表现较差")
        
        # 风险调整收益
        if fund.sharpe_ratio > 1:
            score += 20
            reasons.append(f"夏普比率{fund.sharpe_ratio}，风险调整收益好")
        
        # 回撤控制
        if fund.max_drawdown < 20:
            score += 15
            reasons.append(f"最大回撤{fund.max_drawdown}%，回撤控制好")
        
        # 生成建议
        if score >= 70:
            recommendation = "建议购买"
        elif score >= 40:
            recommendation = "可以适当配置"
        else:
            recommendation = "不建议购买"
        
        return {
            "recommendation": recommendation,
            "score": score,
            "reasons": reasons,
            "fund_info": {
                "code": fund.code,
                "name": fund.name,
                "risk_level": fund.risk_level,
                "manager": fund.manager,
            },
            "performance": perf,
            "warning": self.risk_checker.generate_warning(
                {"risk_level": fund.risk_level},
                user["risk_profile"]
            ),
            "response": f"""【{recommendation}】

{'-'*20}

{chr(10).join(reasons)}

{'-'*20}

【基本信息】
- 基金代码：{fund.code}
- 基金名称：{fund.name}
- 风险等级：{fund.risk_level}
- 基金经理：{fund.manager}
- 基金规模：{fund.aum}亿

【业绩表现】
- 近3年收益：{perf['return_3y']}%
- 夏普比率：{fund.sharpe_ratio}
- 最大回撤：{fund.max_drawdown}%

{'-' * 20}

【风险揭示】
{self.risk_checker.generate_warning({"risk_level": fund.risk_level}, user['risk_profile'])}

【下一步】
建议先小额试投，观察1-2周后再决定是否加仓。
"""
        }
    
    def _fix_compliance(self, response: str, violations: list) -> str:
        """修复合规问题"""
        
        # 添加风险提示
        if "缺少风险提示" in violations:
            response += "\n\n【风险揭示】基金过往业绩不代表未来，市场有风险，投资需谨慎。"
        
        return response


# 工具模拟
class FundTools:
    async def get_fund_info(self, code: str) -> FundData:
        return FundData(
            code=code,
            name="易方达消费行业股票",
            risk_level="R4",
            type="股票基金",
            manager="萧楠",
            aum=120.5,
            return_1y=15.2,
            return_3y=58.3,
            sharpe_ratio=1.2,
            max_drawdown=18.5,
            fees={"管理费": 1.5, "托管费": 0.25}
        )
    
    async def get_fund_performance(self, code: str, period: str) -> dict:
        return {"return_3y": 58.3, "return_1y": 15.2}


class FundKnowledge:
    def find_similar(self, code: str) -> list:
        return []


# 使用示例
async def main():
    agent = FundAnalysisAgent()
    
    result = await agent.analyze(
        fund_code="110022",
        user_profile={
            "risk_profile": "稳健型",  # R2
            "horizon": "中期(1-3年)",
            "amount": 100000,
        }
    )
    
    print(result["response"])


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 六、评估Agent专业度的四个维度

```
┌─────────────────────────────────────────────────────────────────┐
│                    Agent专业度评估矩阵                            │
├──────────────┬──────────────────────────────────────────────────┤
│              │                                                   │
│   准确性     │  • 金融知识正确（法规、指标含义）                  │
│              │  • 数据准确（基金代码、净值、费率）                 │
│              │  • 逻辑自洽（不前后矛盾）                         │
│              │                                                   │
├──────────────┼──────────────────────────────────────────────────┤
│              │                                                   │
│   合规性     │  • 不承诺保本                                    │
│   （最重要） │  • 不预测点位                                    │
│              │  • 风险提示到位                                  │
│              │  • 适当性管理                                    │
│              │                                                   │
├──────────────┼──────────────────────────────────────────────────┤
│              │                                                   │
│   有用性     │  • 建议具体可执行                                │
│              │  • 考虑用户实际情况                               │
│              │  • 考虑用户约束条件                               │
│              │                                                   │
├──────────────┼──────────────────────────────────────────────────┤
│              │                                                   │
│ 可解释性     │  • 结论有数据支撑                                 │
│              │  • 分析过程可追溯                                 │
│              │  • 不懂的地方能解释清楚                           │
│              │                                                   │
└──────────────┴──────────────────────────────────────────────────┘
```

---

## 七、总结：专业化不是堆砌，而是闭环

```
专业化的四个层次：

1. 知识 → 懂不懂
   └→ RAG知识库 + 微调
   
2. 工具 → 会不会
   └→ 专业Tools + API集成
   
3. 流程 → 对不对
   └→ 风控审核 + 合规检查
   
4. 进化 → 好不好
   └→ 用户反馈 + Bad case + 持续优化
```

**理财Agent的特殊性**：
- 合规是底线，不是可选项
- 风险提示是灵魂，没有就是违规
- 多Agent协作是标配，分析和风控必须分离

专业化的Agent，不是知道多少，而是**在正确的时间、用正确的方式、做正确的事**。
