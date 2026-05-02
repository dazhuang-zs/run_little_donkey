"""Logic error analyzer."""

from ai_code_reviewer.models import ReviewDimension
from ai_code_reviewer.analyzers import BaseAnalyzer


class LogicAnalyzer(BaseAnalyzer):
    """逻辑错误分析器：检测边界条件、竞态条件、错误处理缺陷等"""

    def __init__(self, llm_client):
        super().__init__(ReviewDimension.LOGIC, llm_client)

    def get_focus_prompt(self) -> str:
        return """请重点检查以下逻辑错误（按优先级排序，这是最重要也是最容易被漏检的维度）：

1. **边界条件**（高优先级）：
   - 数组越界：off-by-one错误
   - 空值/None处理：未判空就直接调用方法
   - 除零错误：未检查除数是否为零
   - 空集合/空字符串的处理

2. **条件逻辑**：
   - 条件判断错误（如 >= 误写为 >）
   - 布尔逻辑错误（and/or混淆）
   - switch/match缺少default分支
   - 不完整的if-else链（分支遗漏）

3. **并发与竞态**：
   - 检查-使用竞态条件（TOCTOU）
   - 非原子操作序列
   - 异步代码中的回调地狱或遗漏await

4. **事务与一致性**：
   - 数据库操作缺少事务
   - 部分失败导致数据不一致
   - 分布式场景下缺少幂等性考虑

5. **数值与类型**：
   - 整数溢出/精度损失
   - 类型不匹配或隐式类型转换问题
   - 时区处理不当

6. **业务逻辑**：
   - 状态转换不合法
   - 权限校验遗漏
   - 回调/事件处理流程缺陷

逻辑错误是最容易被AI漏检的维度，请特别仔细。如果你发现很隐蔽的逻辑问题，可以提高置信度分数。"""
