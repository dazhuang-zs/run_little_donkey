"""Core review engine - orchestrates the review process."""

import asyncio
import time
from typing import Optional

from ai_code_reviewer.config import AppConfig
from ai_code_reviewer.models import (
    ReviewDimension,
    ReviewFinding,
    ReviewReport,
    Severity,
)
from ai_code_reviewer.diff_parser import DiffParser
from ai_code_reviewer.llm_client import LLMClient
from ai_code_reviewer.analyzers.security import SecurityAnalyzer
from ai_code_reviewer.analyzers.performance import PerformanceAnalyzer
from ai_code_reviewer.analyzers.style import StyleAnalyzer
from ai_code_reviewer.analyzers.logic import LogicAnalyzer


# analyzer维度映射
ANALYZER_MAP = {
    "security": SecurityAnalyzer,
    "performance": PerformanceAnalyzer,
    "style": StyleAnalyzer,
    "logic": LogicAnalyzer,
}


class CodeReviewer:
    """AI代码审查引擎"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.llm_client = LLMClient(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            model=config.llm.model,
            max_tokens=config.llm.max_tokens,
            temperature=config.llm.temperature,
            timeout=config.llm.request_timeout,
        )
        self.diff_parser = DiffParser()

    def _init_analyzers(self) -> list:
        """根据配置初始化分析器"""
        analyzers = []
        for dim_name in self.config.review.dimensions:
            analyzer_cls = ANALYZER_MAP.get(dim_name)
            if analyzer_cls:
                analyzers.append(analyzer_cls(self.llm_client))
        return analyzers

    async def review_diff_text(self, diff_text: str) -> ReviewReport:
        """审查diff文本内容"""
        files = self.diff_parser.parse(diff_text)
        return await self._run_review(files)

    async def review_git_diff(self, target: str = "HEAD", staged: bool = False) -> ReviewReport:
        """审查git diff"""
        diff_text = DiffParser.get_git_diff(target, staged)
        if not diff_text:
            return ReviewReport(
                commit_sha="",
                branch="",
                files_changed=0,
                total_findings=0,
                findings=[],
            )
        files = self.diff_parser.parse(diff_text)
        return await self._run_review(files)

    async def review_file(self, file_path: str) -> ReviewReport:
        """审查单个文件的变更内容（非git场景）"""
        from pathlib import Path

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        content = path.read_text()
        # 构造一个简单的diff（全部是新增行）
        lines = content.split("\n")
        from ai_code_reviewer.diff_parser import FileDiff, DiffHunk

        added_lines = [(i + 1, line) for i, line in enumerate(lines)]
        hunk = DiffHunk(
            old_start=0, old_count=0,
            new_start=1, new_count=len(lines),
            header="@@ -0,0 +1,{} @@".format(len(lines)),
            lines=[f"+{line}" for line in lines],
            added_lines=added_lines,
            removed_lines=[],
        )
        file_diff = FileDiff(
            old_path="/dev/null",
            new_path=file_path,
            status="added",
            hunks=[hunk],
        )

        return await self._run_review([file_diff])

    async def _run_review(self, files: list) -> ReviewReport:
        """核心审查逻辑：运行所有分析器，汇总结果"""
        start_time = time.time()
        analyzers = self._init_analyzers()
        all_findings: list[ReviewFinding] = []

        if not files:
            return ReviewReport(
                files_changed=0,
                total_findings=0,
                findings=[],
                metadata={"error": "没有检测到代码变更"},
            )

        # 构建共享上下文（所有分析器共享相同代码）
        code_context = {
            "files": files,
            "total_files": len(files),
            "total_hunks": sum(len(f.hunks) for f in files),
        }

        # 并发运行所有维度的分析
        tasks = []
        for analyzer in analyzers:
            tasks.append(self._run_analyzer_safe(analyzer, code_context))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集所有发现
        raw_responses = []
        for result in results:
            if isinstance(result, Exception):
                continue
            if isinstance(result, tuple):
                findings, raw = result
                all_findings.extend(findings)
                raw_responses.extend(raw)

        # 去重：相同文件、相同行、相似描述的发现只保留一个
        all_findings = self._deduplicate(all_findings)

        # 过滤低置信度
        min_conf = self.config.review.min_confidence
        all_findings = [f for f in all_findings if f.confidence >= min_conf]

        # 按严重级别排序
        severity_order = {
            Severity.CRITICAL: 0, Severity.HIGH: 1,
            Severity.MEDIUM: 2, Severity.LOW: 3, Severity.INFO: 4,
        }
        all_findings.sort(key=lambda f: severity_order.get(f.severity, 99))

        # 生成汇总
        summary = self._build_summary(all_findings)

        elapsed = time.time() - start_time

        report = ReviewReport(
            files_changed=len(files),
            total_findings=len(all_findings),
            findings=all_findings,
            summary=summary,
            metadata={
                "elapsed_seconds": round(elapsed, 2),
                "analyzers_used": len(analyzers),
                "model": self.llm_client.model_name,
            },
            raw_llm_responses=raw_responses,
        )
        # 合并LLM使用统计
        report.metadata.update(self.llm_client.get_usage_summary())

        return report

    async def _run_analyzer_safe(self, analyzer, code_context) -> tuple:
        """安全地运行单个分析器"""
        try:
            findings = await analyzer.analyze(code_context)
            return findings, []
        except Exception as e:
            return [], [{"error": str(e), "analyzer": analyzer.dimension_name}]

    def _deduplicate(self, findings: list[ReviewFinding]) -> list[ReviewFinding]:
        """去重：同一文件、相近行、相似标题的问题只保留一个"""
        seen = set()
        unique = []
        for f in findings:
            # 用(文件, 行号范围, 问题维度)作为去重key
            key = (f.file_path, f.line_start // 10, f.dimension.value)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _build_summary(self, findings: list[ReviewFinding]) -> dict:
        """按维度和严重级别汇总"""
        summary = {
            "by_dimension": {},
            "by_severity": {},
            "total": len(findings),
        }

        for f in findings:
            dim = f.dimension.value
            sev = f.severity.value
            summary["by_dimension"][dim] = summary["by_dimension"].get(dim, 0) + 1
            summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1

        return summary
