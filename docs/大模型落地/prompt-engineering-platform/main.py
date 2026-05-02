"""
prompt-engineering-platform CLI 入口
==============================
集成演示：展示提示词工程化平台的核心工作流。

用法:
    python main.py init         初始化示例数据
    python main.py list         列出所有提示词和版本
    python main.py history <id> 查看版本历史
    python main.py evaluate     运行模拟评估
    python main.py abtest       运行 A/B 测试
    python main.py monitor      模拟监控检查
    python main.py sample-size  演示样本量计算
"""
import sys
import time
import json
import uuid
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.layout import Layout

from prompt_manager import PromptManager, TemplateRenderer
from evaluator import Evaluator, EvalResult, TestCase, ABTestFramework, StatisticalTester
from monitor import CallTracker, CallRecord, AnomalyDetector

console = Console()


# ============================================================
# 模拟 LLM 调用（不依赖真实 API，方便演示和测试）
# ============================================================

def mock_llm_call(prompt_text: str, config: dict) -> tuple[str, int]:
    """
    模拟 LLM 调用：根据关键词返回预设回复。
    真实场景中替换为 openai.ChatCompletion.create() 等。
    """
    time.sleep(0.05)  # 模拟网络延迟

    prompt_lower = prompt_text.lower()

    # 模拟不同场景的响应
    if "translate" in prompt_lower or "翻译" in prompt_lower:
        if "hello" in prompt_text:
            return "你好", 15
        elif "world" in prompt_text:
            return "世界", 12
        elif "apple" in prompt_text:
            return "苹果", 10
        else:
            return f"[翻译结果] {prompt_text[:50]}...", 25

    elif "classify" in prompt_lower or "分类" in prompt_lower:
        if "positive" in prompt_lower or "好" in prompt_lower:
            return "positive", 10
        elif "negative" in prompt_lower or "差" in prompt_lower:
            return "negative", 10
        else:
            return "neutral", 10

    elif "summarize" in prompt_lower or "总结" in prompt_lower:
        return "这是文章的简要总结...", 30

    else:
        return f"模拟回复: 已收到您的输入（长度={len(prompt_text)}字符）", 20


# ============================================================
# 初始化示例数据
# ============================================================

def cmd_init():
    """初始化示例数据：创建模板、提示词和版本历史"""

    pm = PromptManager()

    # ---- 1. 创建模板 ----
    console.print(Panel("[bold]初始化提示词工程化平台示例数据[/bold]"))

    # 翻译模板
    trans_template = pm.create_template(
        name="translation_template",
        content=(
            "你是一个专业的翻译助手。请将以下文本从 {{source_lang}} 翻译成 {{target_lang}}。\n\n"
            "翻译要求：\n"
            "1. 保持原意的准确性\n"
            "2. 符合目标语言表达习惯\n"
            "3. 专业术语需准确\n\n"
            "待翻译文本：\n"
            "{{text}}\n\n"
            "翻译结果："
        ),
        description="通用翻译模板，支持源语言和目标语言变量",
    )

    # 分类模板
    classify_template = pm.create_template(
        name="sentiment_template",
        content=(
            "你对以下文本进行情感分类。\n\n"
            "文本：{{text}}\n\n"
            "请从以下类别中选择一个：\n"
            "- positive（正面）\n"
            "- negative（负面）\n"
            "- neutral（中性）\n\n"
            "仅输出分类结果，不要输出其他内容。"
        ),
        description="情感分类模板",
    )

    # 客服模板
    support_template = pm.create_template(
        name="customer_support_template",
        content=(
            "你是一个专业的客服助手，你的名字是 {{agent_name}}。\n\n"
            "客户信息：\n"
            "- 用户名：{{user_name}}\n"
            "- 会员等级：{{membership_level}}\n\n"
            "客户问题：{{user_question}}\n\n"
            "回复要求：\n"
            "1. 语气友好专业\n"
            "2. 先确认问题，再提供解决方案\n"
            "3. 如果无法解决，提供替代方案\n\n"
            "回复："
        ),
        description="客户服务模板，含角色扮演和个性化变量",
    )

    console.print(f"  [green]✓[/] 创建模板: {trans_template.name}")
    console.print(f"  [green]✓[/] 创建模板: {classify_template.name}")
    console.print(f"  [green]✓[/] 创建模板: {support_template.name}")

    # ---- 2. 创建提示词并发布版本 ----
    console.print("")

    # 翻译提示词
    trans_prompt = pm.create_prompt(
        name="translation_service",
        description="通用翻译服务",
        tags=["nlp", "translation", "production"],
    )

    pm.create_version(
        prompt_id=trans_prompt.prompt_id,
        template_id="translation_template",
        llm_config={"model": "gpt-4", "temperature": 0.1},
        commit_message="初始版本：基础翻译能力",
        author="alice",
        bump="minor",
    )

    # 发布 v0.2.0 版本（优化）
    pm.create_version(
        prompt_id=trans_prompt.prompt_id,
        template_id="translation_template",
        llm_config={"model": "gpt-4", "temperature": 0.05},
        commit_message="降低 temperature 提高翻译一致性",
        author="alice",
        bump="patch",
    )

    # 发布 v0.3.0 版本（重大更新）
    pm.create_version(
        prompt_id=trans_prompt.prompt_id,
        template_id="translation_template",
        llm_config={"model": "gpt-4", "temperature": 0.05},
        commit_message="增加专业术语要求，优化翻译质量",
        author="bob",
        bump="minor",
    )

    # 情感分析提示词
    sentiment_prompt = pm.create_prompt(
        name="sentiment_analysis",
        description="文本情感分类",
        tags=["nlp", "classification"],
    )

    pm.create_version(
        prompt_id=sentiment_prompt.prompt_id,
        template_id="sentiment_template",
        llm_config={"model": "gpt-3.5-turbo", "temperature": 0},
        commit_message="初始版本：三分类情感分析",
        author="alice",
        bump="minor",
    )

    # 客服提示词
    support_prompt = pm.create_prompt(
        name="customer_support",
        description="自动化客服回复",
        tags=["service", "production"],
    )

    pm.create_version(
        prompt_id=support_prompt.prompt_id,
        template_id="customer_support_template",
        llm_config={"model": "gpt-4", "temperature": 0.3},
        commit_message="初始版本：基础客服回复能力",
        author="bob",
        bump="minor",
    )

    console.print(f"  [green]✓[/] 创建提示词: {trans_prompt.name} (ID={trans_prompt.prompt_id})")
    console.print(f"  [green]✓[/] 创建提示词: {sentiment_prompt.name} (ID={sentiment_prompt.prompt_id})")
    console.print(f"  [green]✓[/] 创建提示词: {support_prompt.name} (ID={support_prompt.prompt_id})")
    console.print(f"\n[green]初始化完成！共 3 个模板、3 个提示词、6 个版本。[/]")

    # 保存 ID 供后续命令使用
    return {
        "translation_id": trans_prompt.prompt_id,
        "sentiment_id": sentiment_prompt.prompt_id,
        "support_id": support_prompt.prompt_id,
    }


# ============================================================
# 列出提示词和版本
# ============================================================

def cmd_list():
    """列出所有提示词及其版本信息"""
    pm = PromptManager()
    prompts = pm.list_prompts()

    if not prompts:
        console.print("[yellow]暂无提示词，请先运行 python main.py init[/]")
        return

    for p in prompts:
        console.print(Panel(f"[bold]{p.name}[/] (ID: {p.prompt_id})"))
        console.print(f"  描述: {p.description}")
        console.print(f"  当前版本: {p.current_version}")
        console.print(f"  状态: {p.status}")
        console.print(f"  标签: {', '.join(p.tags) if p.tags else '无'}")

        versions = pm.list_versions(p.prompt_id)
        if versions:
            table = Table(title=f"版本历史 - {p.name}")
            table.add_column("版本", style="cyan")
            table.add_column("模板", style="green")
            table.add_column("提交信息", style="white")
            table.add_column("作者", style="yellow")
            table.add_column("日期", style="dim")

            for v in versions:
                table.add_row(
                    v.version_id,
                    v.template_id,
                    v.commit_message[:40],
                    v.author,
                    v.created_at.strftime("%m-%d %H:%M"),
                )
            console.print(table)
        console.print("")


# ============================================================
# 版本历史查看
# ============================================================

def cmd_history(prompt_id: str):
    """查看指定提示词的完整版本历史"""
    pm = PromptManager()
    prompt = pm.get_prompt(prompt_id)

    if not prompt:
        console.print(f"[red]提示词 {prompt_id} 不存在[/]")
        return

    console.print(Panel(f"[bold]版本历史: {prompt.name}[/] (当前: {prompt.current_version})"))

    history = pm.get_version_history(prompt_id)

    # 以 Git 风格的树状结构展示
    for entry in history:
        prefix = "→ " if entry["version"] == prompt.current_version else "  "
        parent_info = f" ← {entry['parent']}" if entry["parent"] else " (初始)"
        console.print(f"  {prefix}[cyan]{entry['version']}[/] {entry['message']} "
                      f"[dim]({entry['author']}, {entry['created_at'][:19]}){parent_info}[/]")


# ============================================================
# 评估演示
# ============================================================

def cmd_evaluate():
    """运行模拟评估，展示指标计算"""
    console.print(Panel("[bold]提示词评估演示[/]"))

    # 准备测试用例
    test_cases = [
        TestCase(
            input="Translate to Chinese: Hello, world!",
            expected="你好，世界！",
            variables={"source_lang": "English", "target_lang": "Chinese", "text": "Hello, world!"},
        ),
        TestCase(
            input="Translate to Chinese: Apple is a fruit.",
            expected="苹果是一种水果。",
            variables={"source_lang": "English", "target_lang": "Chinese", "text": "Apple is a fruit."},
        ),
        TestCase(
            input="Classify sentiment: I love this product!",
            expected="positive",
            variables={"text": "I love this product!"},
        ),
        TestCase(
            input="Classify sentiment: This is terrible.",
            expected="negative",
            variables={"text": "This is terrible."},
        ),
    ]

    # 模拟渲染模板
    def eval_llm_call(prompt_text: str, config: dict) -> tuple[str, int]:
        time.sleep(0.03)
        prompt_lower = prompt_text.lower()
        if "hello" in prompt_text and "translate" in prompt_lower:
            return "你好，世界！", 15
        elif "apple" in prompt_text and "translate" in prompt_lower:
            return "苹果是一种水果。", 12
        elif "love" in prompt_text:
            return "positive", 8
        elif "terrible" in prompt_text:
            return "negative", 8
        return "模拟回复", 10

    evaluator = Evaluator(llm_call_fn=eval_llm_call)

    # 将 TestCase 转为纯文本输入
    text_cases = [tc.input for tc in test_cases]

    # 运行评估
    console.print("[yellow]正在运行评估...[/]")

    # 手动计算
    scores = []
    latencies = []
    total_tokens = 0
    for tc in test_cases:
        start = time.time()
        resp, tokens = eval_llm_call(tc.input, {})
        elapsed = (time.time() - start) * 1000
        score = 1.0 if resp.strip() == tc.expected.strip() else 0.0
        scores.append(score)
        latencies.append(elapsed)
        total_tokens += tokens

    accuracy = sum(scores) / len(scores)
    avg_latency = sum(latencies) / len(latencies)

    # 展示结果表格
    table = Table(title="评估结果")
    table.add_column("输入", style="cyan")
    table.add_column("期望", style="green")
    table.add_column("实际", style="white")
    table.add_column("匹配", style="yellow")

    for i, tc in enumerate(test_cases):
        resp, _ = eval_llm_call(tc.input, {})
        match = "✓" if resp.strip() == tc.expected.strip() else "✗"
        table.add_row(
            tc.input[:40],
            tc.expected,
            resp[:30],
            match,
        )

    console.print(table)

    # 指标汇总
    console.print(Panel(
        f"[bold]指标汇总[/]\n"
        f"  准确率 (Accuracy):    {accuracy:.1%}\n"
        f"  平均延迟:             {avg_latency:.1f} ms\n"
        f"  总 Token 消耗:        {total_tokens}\n"
        f"  估算成本:             ${(total_tokens / 1000) * 0.045:.6f}\n"
    ))


# ============================================================
# A/B 测试演示
# ============================================================

def cmd_abtest():
    """A/B 测试演示"""
    console.print(Panel("[bold]A/B 测试演示[/]"))

    # 模拟两个版本的 LLM
    def version_a(prompt: str, config: dict) -> tuple[str, int]:
        time.sleep(0.05)
        return "positive" if "love" in prompt.lower() else "neutral", 15

    def version_b(prompt: str, config: dict) -> tuple[str, int]:
        time.sleep(0.03)
        return "positive" if "love" in prompt.lower() else "negative", 12

    test_cases = [
        TestCase(input="I love this!", expected="positive"),
        TestCase(input="This is great!", expected="positive"),
        TestCase(input="Terrible experience", expected="negative"),
        TestCase(input="Not bad", expected="positive"),
        TestCase(input="Could be better", expected="negative"),
        TestCase(input="Absolutely wonderful", expected="positive"),
        TestCase(input="Waste of money", expected="negative"),
        TestCase(input="Pretty good actually", expected="positive"),
        TestCase(input="Disappointed", expected="negative"),
        TestCase(input=" exceeded expectations ", expected="positive"),
    ]

    # 统计功效分析
    required_n = StatisticalTester.required_sample_size(
        baseline_accuracy=0.7,
        minimum_detectable_effect=0.2,
    )
    console.print(f"[dim]统计功效分析：在 80% 功效下检测 20% 提升需要每组 n≥{required_n}[/]")
    console.print(f"[dim]当前测试用例数: {len(test_cases)}[/]\n")

    ab = ABTestFramework(
        llm_call_fn_a=version_a,
        llm_call_fn_b=version_b,
    )

    result = ab.run(test_cases, split_ratio=0.5)

    table = Table(title="A/B 测试结果对比")
    table.add_column("指标", style="cyan")
    table.add_column("版本 A", style="yellow")
    table.add_column("版本 B", style="green")

    table.add_row("准确率", f"{result.a_accuracy:.1%}", f"{result.b_accuracy:.1%}")
    table.add_row("平均延迟", f"{result.a_avg_latency:.1f} ms", f"{result.b_avg_latency:.1f} ms")
    table.add_row("估算成本", f"${result.a_avg_cost:.6f}", f"${result.b_avg_cost:.6f}")

    console.print(table)

    console.print(Panel(
        f"[bold]结论[/]\n"
        f"  提升 (Lift): {result.lift:+.2f}%\n"
        f"  p 值:       {result.p_value}\n"
        f"  统计显著:   {'[green]是[/]' if result.significant else '[red]否[/]'}\n"
        f"  胜者:       [bold]{'版本 B' if result.winner == 'B' else '版本 A' if result.winner == 'A' else '平局'}[/]"
    ))


# ============================================================
# 监控演示
# ============================================================

def cmd_monitor():
    """模拟监控检查"""
    console.print(Panel("[bold]生产环境监控检查[/]"))

    tracker = CallTracker()
    detector = AnomalyDetector(tracker)

    prompt_id = "prompt_demo_monitor"
    version_id = "v1.0.0"

    # 模拟正常调用
    console.print("[yellow]模拟正常调用...[/]")
    for i in range(20):
        record = CallRecord(
            call_id=f"call_{uuid.uuid4().hex[:8]}",
            prompt_id=prompt_id,
            version_id=version_id,
            template_name="translation_template",
            model="gpt-4",
            prompt_text="Translate to Chinese: Hello!",
            response_text="你好！",
            latency_ms=200 + (i * 5),  # 正常延迟
            token_count=50,
            status="success",
            created_at=datetime.now().isoformat(),
        )
        tracker.record(record)

    # 模拟异常调用（高延迟）
    console.print("[yellow]模拟异常调用（高延迟）...[/]")
    for i in range(5):
        record = CallRecord(
            call_id=f"call_{uuid.uuid4().hex[:8]}",
            prompt_id=prompt_id,
            version_id=version_id,
            template_name="translation_template",
            model="gpt-4",
            prompt_text="Translate to Chinese: Hello!",
            response_text="你好！",
            latency_ms=8000 + (i * 500),  # 异常延迟 > 5s
            token_count=50,
            status="success",
            created_at=datetime.now().isoformat(),
        )
        tracker.record(record)

    # 模拟错误调用
    console.print("[yellow]模拟错误调用...[/]")
    for i in range(3):
        record = CallRecord(
            call_id=f"call_{uuid.uuid4().hex[:8]}",
            prompt_id=prompt_id,
            version_id=version_id,
            template_name="translation_template",
            model="gpt-4",
            prompt_text="Translate to Chinese: Hello!",
            response_text="",
            latency_ms=1000,
            token_count=0,
            status="error",
            error_message="API rate limit exceeded",
            created_at=datetime.now().isoformat(),
        )
        tracker.record(record)

    # 运行检查
    console.print("[yellow]运行监控检查...[/]")

    latency_events = detector.check_latency_anomaly(prompt_id, threshold_ms=5000)
    error_events = detector.check_error_rate(prompt_id, threshold_percent=5.0)

    all_events = latency_events + error_events

    # 性能摘要
    summary = tracker.get_performance_summary(prompt_id)
    console.print(Panel(
        f"[bold]性能摘要[/]\n"
        f"  总调用次数: {summary['total_calls']}\n"
        f"  平均延迟:   {summary['avg_latency_ms']} ms\n"
        f"  P95 延迟:   {summary['p95_latency_ms']} ms\n"
        f"  错误率:     {summary['error_rate']}%\n"
    ))

    if all_events:
        table = Table(title="触发告警")
        table.add_column("规则", style="red")
        table.add_column("指标", style="cyan")
        table.add_column("实际值", style="yellow")
        table.add_column("阈值", style="dim")
        table.add_column("严重程度", style="magenta")

        for e in all_events:
            table.add_row(
                e.rule_name,
                e.metric,
                str(e.actual_value),
                str(e.threshold),
                e.severity,
            )
        console.print(table)
    else:
        console.print("[green]✓ 所有检查通过，未触发告警[/]")


# ============================================================
# 样本量计算演示
# ============================================================

def cmd_sample_size():
    """演示 A/B 测试样本量计算"""
    console.print(Panel("[bold]A/B 测试样本量计算器[/]"))

    table = Table(title="不同场景所需最小样本量（每组）")
    table.add_column("基准准确率", style="cyan")
    table.add_column("检测 5% 提升", style="yellow")
    table.add_column("检测 10% 提升", style="green")
    table.add_column("检测 20% 提升", style="blue")

    for baseline in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]:
        n5 = StatisticalTester.required_sample_size(baseline, 0.05)
        n10 = StatisticalTester.required_sample_size(baseline, 0.10)
        n20 = StatisticalTester.required_sample_size(baseline, 0.20)
        table.add_row(
            f"{baseline:.0%}",
            str(n5),
            str(n10),
            str(n20),
        )

    console.print(table)

    console.print(Panel(
        "[bold]解读[/]\n"
        "• 基准准确率越高，所需样本量越大\n"
        "• 想检测更小的提升，需要更多样本\n"
        "• 提示词评估中常见错误：只用 20 条测试用例就说 'B 版本更好'\n"
        "• 对于 90% 的基准准确率，检测 5% 提升需要每组 400+ 样本"
    ))


# ============================================================
# 模板渲染演示
# ============================================================

def cmd_render():
    """演示模板变量渲染"""
    console.print(Panel("[bold]模板渲染演示[/]"))

    template_str = (
        "你是一个专业的翻译助手。请将以下文本从 {{source_lang}} 翻译成 {{target_lang}}。\n\n"
        "待翻译文本：\n"
        "{{text}}\n\n"
        "翻译结果："
    )

    variables = {
        "source_lang": "English",
        "target_lang": "中文",
        "text": "Hello, welcome to prompt engineering!",
    }

    console.print("[yellow]模板内容:[/]")
    console.print(Syntax(template_str, "text"))

    rendered = TemplateRenderer.render_string(template_str, variables)

    console.print("\n[yellow]渲染结果:[/]")
    console.print(Panel(rendered))

    console.print(f"\n[yellow]提取变量:[/] {TemplateRenderer.extract_variables(template_str)}")


# ============================================================
# 完整工作流演示
# ============================================================

def cmd_workflow():
    """完整工作流演示：从创建到监控的端到端流程"""
    console.print(Panel("[bold]提示词工程化完整工作流演示[/]", style="bold green"))

    # Step 1: 创建模板
    console.print("\n[bold step=1]Step 1/6: 创建模板[/]")
    pm = PromptManager()
    template = pm.create_template(
        name="review_classifier",
        content=(
            "你是一个评论分析助手。请对以下用户评论进行分类。\n\n"
            "评论内容：{{review_text}}\n\n"
            "请从以下维度分析：\n"
            "1. 情感倾向：{{sentiment_options}}\n"
            "2. 提及功能：{{feature_options}}\n"
            "3. 紧急程度：高/中/低\n\n"
            "以 JSON 格式输出。"
        ),
        description="评论分析模板",
    )
    console.print(f"  [green]✓[/] 模板创建成功: {template.name} (变量: {template.variables})")

    # Step 2: 创建提示词
    console.print("\n[bold step=1]Step 2/6: 创建提示词[/]")
    prompt = pm.create_prompt(
        name="review_analyzer",
        description="用户评论自动分类与分析",
        tags=["nlp", "review", "production"],
    )
    console.print(f"  [green]✓[/] 提示词创建成功: {prompt.name} (ID: {prompt.prompt_id})")

    # Step 3: 发布版本
    console.print("\n[bold step=1]Step 3/6: 发布版本[/]")
    v1 = pm.create_version(
        prompt_id=prompt.prompt_id,
        template_id="review_classifier",
        llm_config={"model": "gpt-4", "temperature": 0.1},
        commit_message="初始版本",
        author="alice",
        bump="minor",
    )
    v2 = pm.create_version(
        prompt_id=prompt.prompt_id,
        template_id="review_classifier",
        llm_config={"model": "gpt-4", "temperature": 0.05},
        commit_message="降低 temperature 以提高一致性",
        author="alice",
        bump="patch",
    )
    console.print(f"  [green]✓[/] 版本 v1: {v1.commit_message}")
    console.print(f"  [green]✓[/] 版本 v2: {v2.commit_message}")

    # Step 4: 回滚演示
    console.print("\n[bold step=1]Step 4/6: 回滚操作[/]")
    rollback_v = pm.rollback(prompt.prompt_id, v1.version_id)
    console.print(f"  [green]✓[/] 回滚到 {v1.version_id}，创建回滚快照 {rollback_v.version_id}")

    # Step 5: 渲染与调用
    console.print("\n[bold step=1]Step 5/6: 模板渲染与调用[/]")
    rendered = TemplateRenderer.render_string(
        template.content,
        {
            "review_text": "这个产品太棒了，功能强大但价格偏高",
            "sentiment_options": "正面/负面/中性",
            "feature_options": "价格/功能/用户体验/售后服务",
        },
    )
    console.print(f"  渲染后的提示词 ({len(rendered)} 字符):")
    console.print(Panel(rendered[:200] + "...", style="dim"))

    # 模拟调用并记录
    response, tokens = mock_llm_call(rendered, {})
    tracker = CallTracker()
    record = CallRecord(
        call_id=f"call_{uuid.uuid4().hex[:8]}",
        prompt_id=prompt.prompt_id,
        version_id=rollback_v.version_id,
        template_name="review_classifier",
        model="gpt-4",
        prompt_text=rendered,
        response_text=response,
        latency_ms=150,
        token_count=tokens,
        status="success",
        created_at=datetime.now().isoformat(),
    )
    tracker.record(record)
    console.print(f"  [green]✓[/] LLM 调用完成: {response}")
    console.print(f"  [green]✓[/] 调用记录已持久化")

    # Step 6: 监控检查
    console.print("\n[bold step=1]Step 6/6: 监控检查[/]")
    detector = AnomalyDetector(tracker)
    events = detector.run_all_checks(prompt.prompt_id)
    if events:
        console.print(f"  [yellow]⚠ 触发 {len(events)} 条告警[/]")
    else:
        console.print(f"  [green]✓[/] 所有检查通过")

    console.print("\n[bold green]完整工作流演示完成！[/]")


# ============================================================
# CLI 路由
# ============================================================

def print_help():
    """打印帮助信息"""
    help_text = """
[bold]prompt-engineering-platform CLI[/]

用法:
    python main.py <command> [args]

命令:
    init        初始化示例数据（模板、提示词、版本）
    list        列出所有提示词和版本历史
    history     <prompt_id> 查看版本历史
    evaluate    运行模拟评估（准确率/延迟/成本）
    abtest      运行 A/B 测试对比
    monitor     模拟生产环境监控
    sample-size 样本量计算演示
    render      模板渲染演示
    workflow    完整工作流演示
    help        显示本帮助
"""
    console.print(Panel(help_text))


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    if command == "init":
        cmd_init()
    elif command == "list":
        cmd_list()
    elif command == "history":
        if len(sys.argv) < 3:
            console.print("[red]请指定 prompt_id: python main.py history <prompt_id>[/]")
        else:
            cmd_history(sys.argv[2])
    elif command == "evaluate":
        cmd_evaluate()
    elif command == "abtest":
        cmd_abtest()
    elif command == "monitor":
        cmd_monitor()
    elif command == "sample-size":
        cmd_sample_size()
    elif command == "render":
        cmd_render()
    elif command == "workflow":
        cmd_workflow()
    elif command == "help":
        print_help()
    else:
        console.print(f"[red]未知命令: {command}[/]")
        print_help()


if __name__ == "__main__":
    main()
