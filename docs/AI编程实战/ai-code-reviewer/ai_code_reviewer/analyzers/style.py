"""Code style analyzer."""

from ai_code_reviewer.models import ReviewDimension
from ai_code_reviewer.analyzers import BaseAnalyzer


class StyleAnalyzer(BaseAnalyzer):
    """代码风格分析器：检测可读性、可维护性、命名规范等"""

    def __init__(self, llm_client):
        super().__init__(ReviewDimension.STYLE, llm_client)

    def get_focus_prompt(self) -> str:
        return """请重点检查以下代码风格与可维护性问题：

1. **可读性**：
   - 命名不清晰（如a, b, tmp等无意义命名）
   - 过长的函数（超过50行应建议拆分为更小函数）
   - 复杂的嵌套（超过3层缩进应建议简化）
   - 魔法数字（直接使用字面量而不是命名常量）
   - 过长行（超过100字符）

2. **代码组织**：
   - 可以提取成函数/方法的重复代码块（DRY原则）
   - 职责过于集中的"上帝函数"
   - import组织混乱（未分组、未排序、通配符导入）

3. **类型安全**：
   - Python: 缺少类型提示，特别是公共API
   - TypeScript: 过度使用any类型

4. **错误处理**：
   - 空的except块（吞异常）
   - 过于宽泛的异常捕获（except Exception）
   - 没有恰当的日志记录

5. **注释与文档**：
   - 误导性或过时的注释
   - 复杂的业务逻辑缺少注释
   - TODO/FIXME残留

注意：风格建议应确保客观且符合主流规范。对于主观风格偏好，标记为info级别。"""
