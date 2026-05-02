#!/usr/bin/env python3
"""使用AI Code Reviewer的示例代码"""

import asyncio
import os

from ai_code_reviewer.config import AppConfig
from ai_code_reviewer.reviewer import CodeReviewer


SAMPLE_CODE = """
# 待审查的示例代码（包含多个典型问题）

import os
import sqlite3
import subprocess


def get_user_data(user_id, db_path):
    \"\"\"获取用户数据 - 存在SQL注入漏洞\"\"\"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # BUG: SQL注入 - 直接拼接用户输入
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchall()


def run_command(cmd):
    \"\"\"执行系统命令 - 存在命令注入风险\"\"\"
    # BUG: 命令注入 - 使用shell=True
    result = subprocess.run(cmd, shell=True, capture_output=True)
    return result.stdout


def process_items(items):
    \"\"\"处理列表 - 存在性能问题\"\"\"
    result = []
    for i in range(len(items)):  # 风格: 应直接遍历items
        item = items[i]
        # 性能: 每次循环都执行一次find操作
        if item in result:  # result是list, in操作是O(n)
            continue
        result.append(item)
    return result


def divide_numbers(a, b):
    \"\"\"除法 - 缺少除零检查\"\"\"
    # BUG: 没有检查b==0
    return a / b


class ConfigManager:
    \"\"\"配置管理器 - 硬编码密钥\"\"\"
    # 安全: 硬编码密钥
    SECRET_KEY = "sk-1234567890abcdef"
    API_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"

    def __init__(self, debug=False):
        self.debug = debug
        # 安全: 生产环境开启DEBUG
        if debug:
            print("DEBUG mode enabled")


async def main():
    config = AppConfig.load()
    reviewer = CodeReviewer(config)

    print("=" * 60)
    print("示例: 审查文件代码")
    print("=" * 60)

    report = await reviewer.review_file("sample_code.py")

    print(f"\n发现 {report.total_findings} 个问题:")
    for i, finding in enumerate(report.findings, 1):
        print(f"  {i}. [{finding.severity.value}] {finding.title}")
        print(f"     {finding.file_path}:{finding.line_start}")
        print(f"     {finding.description[:80]}...")
        print(f"     置信度: {finding.confidence}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
"""
