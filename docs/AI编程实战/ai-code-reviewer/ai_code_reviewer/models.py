"""Data models for review results."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(Enum):
    """问题严重级别"""
    CRITICAL = "critical"      # 安全漏洞、数据泄露等必须修复的问题
    HIGH = "high"              # 可能导致运行时错误的逻辑缺陷
    MEDIUM = "medium"          # 性能问题、代码异味
    LOW = "low"                # 风格建议、次要优化
    INFO = "info"              # 信息性提示


class ReviewDimension(Enum):
    """审阅维度"""
    SECURITY = "security"      # 安全漏洞
    PERFORMANCE = "performance"  # 性能问题
    STYLE = "style"            # 代码风格
    LOGIC = "logic"            # 逻辑错误


@dataclass
class ReviewFinding:
    """单条审阅发现"""
    dimension: ReviewDimension      # 所属维度
    severity: Severity              # 严重级别
    file_path: str                  # 文件路径
    line_start: int                 # 起始行号
    line_end: int                   # 结束行号
    title: str                      # 问题标题（简短）
    description: str                # 详细描述
    suggestion: str                 # 修复建议
    code_snippet: str               # 相关代码片段
    confidence: float               # 置信度 0.0-1.0
    is_hallucination_risk: bool = False  # 是否可能是AI幻觉

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_range": [self.line_start, self.line_end],
            "title": self.title,
            "description": self.description,
            "suggestion": self.suggestion,
            "code_snippet": self.code_snippet,
            "confidence": self.confidence,
            "is_hallucination_risk": self.is_hallucination_risk,
        }


@dataclass
class ReviewReport:
    """完整的审阅报告"""
    commit_sha: Optional[str]        # Git commit hash
    branch: Optional[str]            # 分支名
    files_changed: int               # 变更文件数
    total_findings: int              # 发现问题总数
    findings: list[ReviewFinding]    # 所有发现
    summary: dict = field(default_factory=dict)  # 按维度和严重级别的汇总
    metadata: dict = field(default_factory=dict)  # 元数据（耗时、token消耗等）
    raw_llm_responses: list[dict] = field(default_factory=list)  # LLM原始响应（调试用）

    def to_dict(self) -> dict:
        return {
            "commit_sha": self.commit_sha,
            "branch": self.branch,
            "files_changed": self.files_changed,
            "total_findings": self.total_findings,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings],
            "metadata": self.metadata,
        }

    def get_findings_by_severity(self, severity: Severity) -> list[ReviewFinding]:
        return [f for f in self.findings if f.severity == severity]

    def get_findings_by_dimension(self, dimension: ReviewDimension) -> list[ReviewFinding]:
        return [f for f in self.findings if f.dimension == dimension]
