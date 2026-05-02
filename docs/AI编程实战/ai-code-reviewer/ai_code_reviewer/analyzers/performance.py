"""Performance issue analyzer."""

from ai_code_reviewer.models import ReviewDimension
from ai_code_reviewer.analyzers import BaseAnalyzer


class PerformanceAnalyzer(BaseAnalyzer):
    """性能问题分析器：检测算法效率、资源管理、I/O模式等"""

    def __init__(self, llm_client):
        super().__init__(ReviewDimension.PERFORMANCE, llm_client)

    def get_focus_prompt(self) -> str:
        return """请重点检查以下性能问题（按优先级排序）：

1. **算法与数据结构**（高优先级）：
   - 循环内嵌O(n)操作导致整体O(n²)复杂度
   - 在循环中使用未索引的数据库查询
   - 不必要的数据复制或遍历
   - 使用低效的数据结构（如频繁查找却用list而不是set）

2. **资源管理**：
   - 未关闭的文件句柄/数据库连接/网络连接
   - 没有使用with语句进行资源管理
   - 内存泄漏风险（大对象长期持有引用）

3. **I/O模式**：
   - N+1查询问题（循环内逐条查数据库）
   - 批量操作优化机会（批量插入 vs 逐条插入）
   - 不必要的外部API同步调用

4. **并发与异步**：
   - 缺失锁或锁粒度过大
   - 可以并行却串行执行的任务
   - 线程池/连接池大小配置不当

5. **缓存与重复计算**：
   - 重复计算的表达式（可以提取为变量）
   - 可以加缓存却未加的场景
   - 同一函数多次调用且结果不变

对于没有性能问题的代码，返回空数组。不要为了凑数而报告虚假问题。对于微优化（如单个变量提取），标记为低优先级。"""
