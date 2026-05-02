"""Base analyzer class and prompt templates."""

from abc import ABC, abstractmethod
from typing import Any

from ai_code_reviewer.models import ReviewDimension, ReviewFinding


# 系统提示词模板：定义了AI审阅者的角色和基本原则
SYSTEM_PROMPT = """你是一位资深的代码审查专家，在以下领域有深厚经验：
- 安全编码（OWASP Top 10、CWE）
- 性能优化（算法复杂度、资源管理）
- 代码设计（SOLID原则、设计模式、可维护性）
- 逻辑正确性（边界条件、并发安全、错误处理）

审查原则：
1. 只关注diff中的变更，不要审查未改动的代码
2. 每个发现必须提供：问题描述、风险等级、修复建议、相关代码行号
3. 如果你不确定某个问题是否存在，请降低置信度分数
4. 不要提出模糊的"建议改进"而没有具体理由
5. 对于明显安全漏洞或逻辑错误，标记为高严重性
6. 对于风格偏好，标记为低严重性或信息性
7. 输出必须是严格的JSON格式，不要包含markdown代码块标记

置信度评分标准：
- 1.0：确定是问题（如SQL注入、空指针解引用）
- 0.7-0.9：非常有把握
- 0.4-0.6：有一定把握，但需要人工确认
- 0.1-0.3：猜测，可能是代码误读

回复格式必须是以下JSON（不要包含任何其他内容）：
{
  "findings": [
    {{
      "title": "短标题",
      "severity": "critical|high|medium|low|info",
      "line_start": 行号,
      "line_end": 行号,
      "description": "问题详细描述",
      "suggestion": "具体的修复建议",
      "confidence": 0.0-1.0
    }}
  ]
}
"""


class BaseAnalyzer(ABC):
    """审阅分析器基类"""

    def __init__(self, dimension: ReviewDimension, llm_client: Any):
        self.dimension = dimension
        self.dimension_name = dimension.value
        self.llm_client = llm_client

    @abstractmethod
    def get_focus_prompt(self) -> str:
        """获取该维度审阅的重点提示词"""
        ...

    async def analyze(self, code_context: dict) -> list[ReviewFinding]:
        """分析代码变更"""
        results = []
        # 每个dimension分析一次，减少API调用
        # 如果代码量很大，可以分批处理
        for chunk in self._chunk_context(code_context):
            raw_response = await self._call_llm(chunk)
            parsed = self._parse_response(raw_response, chunk)
            results.extend(parsed)
        return results

    def _chunk_context(self, context: dict, max_tokens: int = 3500) -> list[dict]:
        """如果上下文太大，按文件分片"""
        chunks = []
        for file_diff in context.get("files", []):
            chunks.append({
                "file": file_diff,
                "context": context,
            })
        return chunks if chunks else [context]

    async def _call_llm(self, chunk: dict) -> dict:
        """调用LLM进行分析"""
        messages = self._build_messages(chunk)
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.llm_client._model,
                messages=messages,
                temperature=0.1,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            return {"raw": content, "usage": dict(response.usage)}
        except Exception as e:
            return {"raw": f'{{"findings": []}}', "error": str(e), "usage": {}}

    def _build_messages(self, chunk: dict) -> list[dict]:
        """构建LLM消息"""
        # 构建代码上下文
        code_context = ""
        files = chunk.get("files", [chunk]) if isinstance(chunk, dict) else []

        # 从chunk中提取file信息
        file_diff = chunk.get("file", {})
        if file_diff:
            code_context = self._format_file_diff(file_diff)
        else:
            for f in chunk.get("context", {}).get("files", []):
                code_context += self._format_file_diff(f)

        user_prompt = f"""## 审阅维度：{self.dimension_name}
{self.get_focus_prompt()}

## 代码变更（diff）
{code_context}

请只关注{dimension_labels.get(self.dimension_name, self.dimension_name)}相关的问题。"""

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    def _format_file_diff(self, file_diff) -> str:
        """格式化单个文件的diff用于LLM输入"""
        lines = [f"### 文件: {file_diff.file_path} (状态: {file_diff.status})"]
        for hunk in file_diff.hunks:
            lines.append(hunk.header)
            # 只包含有变更的行（去掉纯上下文行太长），但保留前后几行上下文
            for line in hunk.lines:
                if line.startswith("+") or line.startswith("-") or line.startswith("@@"):
                    lines.append(line)
        return "\n".join(lines)

    def _parse_response(self, raw: dict, chunk: dict) -> list[ReviewFinding]:
        """解析LLM响应为结构化发现"""
        import json
        findings = []

        try:
            content = raw.get("raw", "{}")
            data = json.loads(content)
        except json.JSONDecodeError:
            return findings

        # 获取当前文件路径
        file_path = ""
        file_diff = chunk.get("file", {})
        if file_diff:
            file_path = file_diff.file_path if hasattr(file_diff, "file_path") else ""

        for item in data.get("findings", []):
            # 过滤低置信度发现
            confidence = item.get("confidence", 0.5)
            if confidence < 0.3:
                continue

            finding = ReviewFinding(
                dimension=self.dimension,
                severity=self._parse_severity(item.get("severity", "medium")),
                file_path=file_path,
                line_start=item.get("line_start", 0),
                line_end=item.get("line_end", 0),
                title=item.get("title", "未命名发现"),
                description=item.get("description", ""),
                suggestion=item.get("suggestion", ""),
                code_snippet="",
                confidence=confidence,
                is_hallucination_risk=confidence < 0.5,
            )
            findings.append(finding)

        return findings

    def _parse_severity(self, value: str):
        from ai_code_reviewer.models import Severity
        try:
            return Severity(value.lower())
        except ValueError:
            return Severity.MEDIUM


# 维度中文标签
dimension_labels = {
    "security": "安全漏洞",
    "performance": "性能问题",
    "style": "代码风格与可维护性",
    "logic": "逻辑错误与边界条件",
}
