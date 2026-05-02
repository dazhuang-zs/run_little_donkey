"""Security vulnerability analyzer."""

from ai_code_reviewer.models import ReviewDimension
from ai_code_reviewer.analyzers import BaseAnalyzer


class SecurityAnalyzer(BaseAnalyzer):
    """安全漏洞分析器：检测SQL注入、XSS、命令注入、敏感信息泄露等"""

    def __init__(self, llm_client):
        super().__init__(ReviewDimension.SECURITY, llm_client)

    def get_focus_prompt(self) -> str:
        return """请重点检查以下安全风险（按优先级排序）：

1. **注入攻击**（高优先级）：
   - SQL注入：直接拼接SQL字符串、使用eval()执行查询
   - 命令注入：os.system()、subprocess(shell=True)、exec()使用未净化输入
   - NoSQL注入：MongoDB $where注入等

2. **认证与授权**：
   - 硬编码密钥/密码/token
   - 缺失权限检查
   - JWT验证绕过

3. **敏感数据泄露**：
   - 日志中打印密码/密钥/个人信息
   - 未加密传输敏感数据
   - 不安全的会话管理

4. **文件操作安全**：
   - 路径遍历（Path Traversal）
   - 任意文件读取/写入
   - 不安全的反序列化（pickle.loads等）

5. **配置安全**：
   - DEBUG模式在生产环境开启
   - CORS配置过于宽松
   - 缺少安全头

6. **依赖安全**：
   - 使用已知有漏洞的API或模式

对于没有安全问题的代码，返回空数组即可。不要为了凑数而报告虚假安全问题。"""
