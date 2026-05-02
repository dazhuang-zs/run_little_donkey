"""
A/B 测试框架：支持两版提示词的对比实验。
"""
from __future__ import annotations
import random
import statistics
from dataclasses import dataclass, field
from typing import Callable
from .metrics import TestCase


@dataclass
class ABTestResult:
    """A/B 测试结果"""
    version_a_name: str
    version_b_name: str
    a_accuracy: float
    b_accuracy: float
    a_avg_latency: float
    b_avg_latency: float
    a_avg_cost: float
    b_avg_cost: float
    p_value: float = 1.0          # 统计显著性 p 值
    significant: bool = False     # 是否显著
    sample_size: int = 0
    lift: float = 0.0             # B 相对于 A 的提升百分比
    winner: str = "tie"


class ABTestFramework:
    """
    A/B 测试框架：使用随机分配将测试用例分到 A/B 两组，
    分别用不同版本的提示词调用 LLM，然后比较效果。

    典型场景:
    - 对比 prompt 版本 v1.2 和 v1.3 的效果
    - 对比不同 temperature 设置的效果
    - 对比不同模型（GPT-4 vs Claude）的效果
    """

    def __init__(
        self,
        llm_call_fn_a: Callable,
        llm_call_fn_b: Callable,
        config_a: dict | None = None,
        config_b: dict | None = None,
    ):
        self.llm_call_fn_a = llm_call_fn_a
        self.llm_call_fn_b = llm_call_fn_b
        self.config_a = config_a or {}
        self.config_b = config_b or {}

    def run(
        self,
        test_cases: list[TestCase],
        split_ratio: float = 0.5,
        seed: int = 42,
    ) -> ABTestResult:
        """
        运行 A/B 测试。

        参数:
            test_cases: 测试用例列表
            split_ratio: 分配给 A 组的比例
            seed: 随机种子，保证可复现

        返回:
            ABTestResult: 包含对比结果和统计显著性
        """
        if not test_cases:
            raise ValueError("测试用例不能为空")

        random.seed(seed)
        random.shuffle(test_cases)

        split_point = max(1, int(len(test_cases) * split_ratio))
        group_a = test_cases[:split_point]
        group_b = test_cases[split_point:]

        # 分别评估两组
        scores_a, latencies_a, tokens_a = self._evaluate_group(
            group_a, self.llm_call_fn_a, self.config_a
        )
        scores_b, latencies_b, tokens_b = self._evaluate_group(
            group_b, self.llm_call_fn_b, self.config_b
        )

        # 计算指标
        a_accuracy = statistics.mean(scores_a) if scores_a else 0
        b_accuracy = statistics.mean(scores_b) if scores_b else 0
        a_latency = statistics.mean(latencies_a) if latencies_a else 0
        b_latency = statistics.mean(latencies_b) if latencies_b else 0
        a_cost = (sum(tokens_a) / 1000) * 0.045
        b_cost = (sum(tokens_b) / 1000) * 0.045

        # 计算提升
        if a_accuracy > 0:
            lift = (b_accuracy - a_accuracy) / a_accuracy * 100
        else:
            lift = 0.0

        # 确定胜者
        if b_accuracy > a_accuracy:
            winner = "B"
        elif a_accuracy > b_accuracy:
            winner = "A"
        else:
            winner = "tie"

        # 使用 scipy 进行 t 检验
        p_value = self._calculate_p_value(scores_a, scores_b)
        significant = p_value < 0.05

        return ABTestResult(
            version_a_name="A",
            version_b_name="B",
            a_accuracy=round(a_accuracy, 4),
            b_accuracy=round(b_accuracy, 4),
            a_avg_latency=round(a_latency, 1),
            b_avg_latency=round(b_latency, 1),
            a_avg_cost=round(a_cost, 6),
            b_avg_cost=round(b_cost, 6),
            p_value=round(p_value, 4),
            significant=significant,
            sample_size=len(test_cases),
            lift=round(lift, 2),
            winner=winner,
        )

    def _evaluate_group(
        self,
        cases: list[TestCase],
        llm_fn: Callable,
        config: dict,
    ) -> tuple[list[float], list[float], list[int]]:
        """评估一组测试用例，返回（相似度分数列表, 延迟列表, token数列表）"""
        scores: list[float] = []
        latencies: list[float] = []
        tokens_list: list[int] = []

        import time
        for tc in cases:
            start = time.perf_counter()
            response, token_count = llm_fn(tc.input, config)
            elapsed = (time.perf_counter() - start) * 1000

            # 简单匹配
            score = 1.0 if response.strip() == tc.expected.strip() else 0.0

            scores.append(score)
            latencies.append(elapsed)
            tokens_list.append(token_count)

        return scores, latencies, tokens_list

    @staticmethod
    def _calculate_p_value(scores_a: list[float], scores_b: list[float]) -> float:
        """
        使用独立样本 t 检验计算 p 值。
        如果 scipy 不可用，回退到近似计算。
        """
        try:
            from scipy import stats
            _, p_value = stats.ttest_ind(scores_a, scores_b, equal_var=False)
            return p_value
        except ImportError:
            # 手动近似：基于均值和样本量
            if len(scores_a) < 2 or len(scores_b) < 2:
                return 1.0
            mean_a = statistics.mean(scores_a)
            mean_b = statistics.mean(scores_b)
            var_a = statistics.variance(scores_a)
            var_b = statistics.variance(scores_b)

            # Welch's t-test 近似
            se = (var_a / len(scores_a) + var_b / len(scores_b)) ** 0.5
            if se == 0:
                return 1.0
            t_stat = (mean_a - mean_b) / se

            # 粗略 p 值（正常应该查 t 分布表，这里做简化）
            # |t| > 2 通常表示在 95% 置信水平下显著
            if abs(t_stat) > 2.58:
                return 0.01
            elif abs(t_stat) > 1.96:
                return 0.05
            elif abs(t_stat) > 1.64:
                return 0.10
            return 0.50
