"""Report generation - JSON output and rich console formatting."""

import json
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree
from rich import box
from rich.text import Text

from ai_code_reviewer.models import ReviewReport, Severity


# 严重级别对应的颜色和图标
SEVERITY_STYLES = {
    Severity.CRITICAL: {"color": "red", "icon": "🔴", "label": "CRITICAL"},
    Severity.HIGH:     {"color": "orange1", "icon": "🟠", "label": "HIGH"},
    Severity.MEDIUM:   {"color": "yellow", "icon": "🟡", "label": "MEDIUM"},
    Severity.LOW:      {"color": "cyan", "icon": "🔵", "label": "LOW"},
    Severity.INFO:     {"color": "white", "icon": "⚪", "label": "INFO"},
}


class ReportFormatter:
    """报告格式化输出"""

    def __init__(self, console: Console = None):
        self.console = console or Console()

    def print_report(self, report: ReviewReport):
        """打印完整审查报告到终端"""
        if report.total_findings == 0:
            self._print_empty_report(report)
            return

        self._print_header(report)
        self._print_summary_table(report)
        self._print_findings(report)
        self._print_metadata(report)

    def to_json(self, report: ReviewReport) -> str:
        """输出JSON格式报告"""
        return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)

    def save_report(self, report: ReviewReport, filepath: str):
        """保存报告到文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_json(report))

    def _print_header(self, report: ReviewReport):
        """打印报告头部"""
        header_text = Text()
        header_text.append(" AI 代码审查报告 ", style="bold white on blue")
        if report.commit_sha:
            header_text.append(f"  Commit: {report.commit_sha[:8]}", style="dim")
        if report.branch:
            header_text.append(f"  Branch: {report.branch}", style="dim")
        self.console.print()
        self.console.print(Panel(header_text, box=box.ROUNDED))
        self.console.print()

    def _print_empty_report(self, report: ReviewReport):
        """没有发现问题时的输出"""
        self.console.print()
        self.console.print(Panel(
            Text("✅ 未发现代码问题，审阅通过。", style="green bold"),
            box=box.ROUNDED,
        ))
        self.console.print(f"  审查文件数: {report.files_changed}")
        self.console.print()

    def _print_summary_table(self, report: ReviewReport):
        """打印汇总表格"""
        table = Table(title="审查汇总", box=box.SIMPLE)

        # 按维度
        dim_table = Table(box=box.SIMPLE, show_header=True)
        dim_table.add_column("审阅维度", style="bold")
        dim_table.add_column("发现问题数", justify="right")

        dim_labels = {
            "security": "安全漏洞",
            "performance": "性能问题",
            "style": "代码风格",
            "logic": "逻辑错误",
        }

        for dim_key, dim_label in dim_labels.items():
            count = report.summary.get("by_dimension", {}).get(dim_key, 0)
            dim_table.add_row(dim_label, str(count))

        self.console.print(dim_table)
        self.console.print()

        # 按严重级别
        sev_table = Table(box=box.SIMPLE, show_header=True)
        sev_table.add_column("严重级别", style="bold")
        sev_table.add_column("数量", justify="right")

        for sev in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]:
            style = SEVERITY_STYLES[sev]
            count = report.summary.get("by_severity", {}).get(sev.value, 0)
            if count or sev in [Severity.CRITICAL, Severity.HIGH]:
                sev_table.add_row(
                    f"{style['icon']} {style['label']}",
                    str(count),
                )

        self.console.print(sev_table)
        self.console.print()
        self.console.print(f"  发现问题总数: [bold]{report.total_findings}[/bold]")
        self.console.print()

    def _print_findings(self, report: ReviewReport):
        """逐条输出发现"""
        for i, finding in enumerate(report.findings, 1):
            sev_style = SEVERITY_STYLES[finding.severity]

            # 标题行
            title = Text()
            title.append(f" #{i} ", style="bold white on " + sev_style["color"])
            title.append(f" [{finding.dimension.value}] ", style="bold")
            title.append(finding.title, style="bold")

            # 文件位置
            location = f"{finding.file_path}:{finding.line_start}"
            if finding.line_end and finding.line_end != finding.line_start:
                location += f"-{finding.line_end}"

            # 创建发现面板
            content = Text()
            content.append(f"📁 {location}", style="dim")
            content.append("\n\n")
            content.append(finding.description)
            content.append("\n\n")
            content.append("💡 建议: ", style="bold green")
            content.append(finding.suggestion)
            if finding.is_hallucination_risk:
                content.append("\n\n")
                content.append("⚠️  低置信度提示: 此发现可能是AI误报，请人工确认", style="yellow italic")

            panel = Panel(
                content,
                title=title,
                title_align="left",
                border_style=sev_style["color"],
                box=box.ROUNDED,
            )
            self.console.print(panel)
            self.console.print()

    def _print_metadata(self, report: ReviewReport):
        """打印元数据"""
        meta = report.metadata
        if not meta:
            return

        table = Table(title="审查元数据", box=box.SIMPLE, show_header=False)
        table.add_column("项目", style="bold")
        table.add_column("值")

        table.add_row("审查模型", meta.get("model", "N/A"))
        table.add_row("耗时", f"{meta.get('elapsed_seconds', 0)}秒")
        table.add_row("API调用次数", str(meta.get("api_calls", 0)))
        table.add_row("输入Token", f"{meta.get('prompt_tokens', 0):,}")
        table.add_row("输出Token", f"{meta.get('completion_tokens', 0):,}")
        table.add_row("总计Token", f"{meta.get('total_tokens', 0):,}")
        table.add_row("预估成本", f"${meta.get('estimated_cost_usd', 0):.4f}")

        self.console.print(table)
        self.console.print()
