"""CLI entry point with click."""

import asyncio
import sys
from pathlib import Path

import click

from ai_code_reviewer.config import AppConfig
from ai_code_reviewer.reviewer import CodeReviewer
from ai_code_reviewer.report import ReportFormatter
from ai_code_reviewer import __version__


@click.group()
@click.version_option(__version__)
def main():
    """AI Code Reviewer - AI驱动的代码审查工具"""


@main.command()
@click.argument("target", default="HEAD")
@click.option("--staged", is_flag=True, help="审查已staged的变更")
@click.option("--config", "-c", help="配置文件路径", default=None)
@click.option("--output", "-o", help="输出JSON报告到文件", default=None)
@click.option("--dimensions", "-d", help="审阅维度，逗号分隔", default=None)
@click.option("--json", "json_output", is_flag=True, help="只输出JSON")
async def diff(target, staged, config, output, dimensions, json_output):
    """审查git diff

    TARGET: git ref，默认为HEAD（对比HEAD~1..HEAD）
    """
    cfg = AppConfig.load(config)

    if dimensions:
        cfg.review.dimensions = [d.strip() for d in dimensions.split(",")]

    reviewer = CodeReviewer(cfg)

    with click.progressbar(
        length=1,
        label="🔄 AI审阅中...",
        show_eta=False,
    ) as bar:
        report = await reviewer.review_git_diff(target, staged)
        bar.update(1)

    formatter = ReportFormatter()

    if json_output:
        click.echo(formatter.to_json(report))
    else:
        formatter.print_report(report)

    if output:
        formatter.save_report(report, output)
        click.echo(f"\n报告已保存至: {output}")

    # 如果有 CRITICAL 或 HIGH 级别的问题，非零退出
    from ai_code_reviewer.models import Severity
    critical_count = len(report.get_findings_by_severity(Severity.CRITICAL))
    high_count = len(report.get_findings_by_severity(Severity.HIGH))
    if critical_count > 0 or high_count > 0:
        sys.exit(1)


@main.command()
@click.argument("file_path")
@click.option("--config", "-c", help="配置文件路径", default=None)
@click.option("--output", "-o", help="输出JSON报告到文件", default=None)
async def file(file_path, config, output):
    """审查单个文件的代码"""
    cfg = AppConfig.load(config)
    reviewer = CodeReviewer(cfg)

    with click.progressbar(
        length=1,
        label="🔄 AI审阅中...",
        show_eta=False,
    ) as bar:
        report = await reviewer.review_file(file_path)
        bar.update(1)

    formatter = ReportFormatter()
    formatter.print_report(report)

    if output:
        formatter.save_report(report, output)
        click.echo(f"\n报告已保存至: {output}")


@main.command()
@click.option("--config", "-c", help="配置文件路径", default=None)
@click.option("--output", "-o", help="输出JSON报告到文件", default=None)
@click.option("--dimensions", "-d", help="审阅维度", default=None)
@click.option("--diff-text", help="直接传入diff文本（用于管道输入）", default=None)
async def review(config, output, dimensions, diff_text):
    """从标准输入或参数读取diff进行审查"""
    cfg = AppConfig.load(config)

    if dimensions:
        cfg.review.dimensions = [d.strip() for d in dimensions.split(",")]

    # 如果没有通过--diff-text传入，则从stdin读取
    if not diff_text:
        if not sys.stdin.isatty():
            diff_text = sys.stdin.read()

    if not diff_text:
        click.echo("错误: 请通过--diff-text参数或stdin管道传入diff内容", err=True)
        sys.exit(1)

    reviewer = CodeReviewer(cfg)

    with click.progressbar(
        length=1,
        label="🔄 AI审阅中...",
        show_eta=False,
    ) as bar:
        report = await reviewer.review_diff_text(diff_text)
        bar.update(1)

    formatter = ReportFormatter()
    formatter.print_report(report)

    if output:
        formatter.save_report(report, output)
        click.echo(f"\n报告已保存至: {output}")

    from ai_code_reviewer.models import Severity
    critical_count = len(report.get_findings_by_severity(Severity.CRITICAL))
    high_count = len(report.get_findings_by_severity(Severity.HIGH))
    if critical_count > 0 or high_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
