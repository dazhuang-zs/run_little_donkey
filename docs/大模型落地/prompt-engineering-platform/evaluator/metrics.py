"""
评估指标层：定义提示词质量的量化评估体系。
包含准确率、一致性、延迟等多种指标的自动化计算。
"""
from __future__ import annotations
import time
import statistics
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class EvalResult:
    """单次评估结果"""
    accuracy: float = 0.0          # 准确率 (0~1)
    consistency: float = 0.0       # 一致性 (0~1)
    latency_ms: float = 0.0        # 平均延迟 (毫秒)
    total_tokens: int = 0          # 总消耗 token 数
    cost: float = 0.0              # 估算成本 (美元)
    details: list[dict] = field(default_factory=list)  # 每条样本的详细结果


@dataclass
class TestCase:
    """单条测试用例"""
    input: str                     # 输入
    expected: str                  # 期望输出
    variables: dict[str, Any] = field(default_factory=dict)  # 模板变量


class Evaluator:
    """
    评估器：支持批量测试和指标计算。

    典型用法:
        evaluator = Evaluator(llm_call_fn)
        result = evaluator.run(test_cases)
        print(f"准确率: {result.accuracy:.1%}")
    """

    def __init__(
        self,
        llm_call_fn: Callable,
        model_config: dict | None = None,
    ):
        """
        参数:
            llm_call_fn: LLM 调用函数，接受 (prompt_text, model_config) 参数，返回 (response_text, token_count)
            model_config: 调用参数，如 {"model": "gpt-4", "temperature": 0}
        """
        self.llm_call_fn = llm_call_fn
        self.model_config = model_config or {"model": "gpt-4", "temperature": 0}

    def run(
        self,
        test_cases: list[TestCase],
        similarity_fn: Callable[[str, str], float] | None = None,
    ) -> EvalResult:
        """
        批量运行测试用例并计算各项指标。

        指标说明:
        - accuracy: 基于相似度函数的匹配分数
        - consistency: 对同一样本多次运行时输出的稳定性
        - latency_ms: 端到端调用的延迟
        """
        if not test_cases:
            return EvalResult()

        latencies: list[float] = []
        total_tokens = 0
        scores: list[float] = []
        details: list[dict] = []

        # 默认相似度：精确字符串匹配
        if similarity_fn is None:
            similarity_fn = lambda a, b: 1.0 if a.strip() == b.strip() else 0.0

        for tc in test_cases:
            start = time.perf_counter()
            response, token_count = self.llm_call_fn(tc.input, self.model_config)
            elapsed = (time.perf_counter() - start) * 1000  # ms

            latencies.append(elapsed)
            total_tokens += token_count

            # 计算与期望输出的相似度
            score = similarity_fn(response, tc.expected)
            scores.append(score)

            details.append({
                "input": tc.input[:100],
                "expected": tc.expected[:100],
                "response": response[:200],
                "similarity": score,
                "latency_ms": round(elapsed, 1),
                "tokens": token_count,
            })

        # ------ 计算各项指标 ------
        # 准确率：所有样本的平均相似度
        accuracy = statistics.mean(scores) if scores else 0.0

        # 一致性：如果有多条相似输入，输出的标准差越低越好（高一致性）
        # 简化为：每条输出的长度变异系数的倒数
        if len(scores) > 1 and statistics.stdev(scores) > 0:
            consistency = 1.0 / (1.0 + statistics.stdev(scores))
        else:
            consistency = 1.0

        avg_latency = statistics.mean(latencies) if latencies else 0.0

        # 估算成本：以 GPT-4（输入 $0.03/1K tokens, 输出 $0.06/1K tokens）为例
        cost = (total_tokens / 1000) * 0.045

        return EvalResult(
            accuracy=round(accuracy, 4),
            consistency=round(consistency, 4),
            latency_ms=round(avg_latency, 1),
            total_tokens=total_tokens,
            cost=round(cost, 6),
            details=details,
        )

    def run_consistency_check(
        self,
        test_case: TestCase,
        n_runs: int = 5,
    ) -> dict:
        """
        对同一条输入重复运行 n 次，评估输出的稳定性。
        用于检测提示词是否对微小变化敏感（常见于 temperature > 0 的场景）。
        """
        responses: list[str] = []
        latencies: list[float] = []

        for _ in range(n_runs):
            start = time.perf_counter()
            response, _ = self.llm_call_fn(test_case.input, self.model_config)
            latencies.append((time.perf_counter() - start) * 1000)
            responses.append(response)

        # 输出长度稳定性
        lengths = [len(r) for r in responses]
        length_cv = statistics.stdev(lengths) / statistics.mean(lengths) if lengths else 0

        # 内容相似度（两两计算）
        pairwise_scores = []
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                pairwise_scores.append(
                    1.0 if responses[i].strip() == responses[j].strip() else 0.0
                )

        return {
            "total_runs": n_runs,
            "unique_outputs": len(set(responses)),
            "length_cv": round(length_cv, 4),          # 长度变异系数，越小越稳定
            "pairwise_consistency": round(
                statistics.mean(pairwise_scores) if pairwise_scores else 1.0, 4
            ),
            "avg_latency_ms": round(statistics.mean(latencies), 1),
            "latency_std_ms": round(statistics.stdev(latencies), 1) if len(latencies) > 1 else 0,
            "responses": responses,
        }
