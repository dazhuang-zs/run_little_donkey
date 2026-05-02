"""
统计工具模块：提供提示词工程中常用的统计检验方法。
"""
from __future__ import annotations
import math
from typing import Sequence


class StatisticalTester:
    """
    统计检验工具集。

    在提示词工程中常用的统计方法:
    - 配对 t 检验：同一组测试用例在两个版本上的表现对比
    - 卡方检验：分类指标（如格式合规率）的对比
    - 效应量计算：量化版本间的实际差异大小
    """

    @staticmethod
    def paired_ttest(
        scores_a: Sequence[float],
        scores_b: Sequence[float],
    ) -> dict:
        """
        配对 t 检验：比较两个版本在同一组测试用例上的表现。

        参数:
            scores_a: 版本 A 的分数序列
            scores_b: 版本 B 的分数序列

        返回:
            包含 t 统计量、p 值、效应量 Cohen's d 的字典

        注意:
            配对 t 检验假设差值服从正态分布。
            在提示词评估中，通常 scores 是二值的（0 或 1），
            此时更推荐使用 McNemar 检验。
        """
        if len(scores_a) != len(scores_b):
            raise ValueError("两组分数长度必须相等")
        if len(scores_a) < 3:
            return {"t_stat": 0, "p_value": 1.0, "cohens_d": 0, "valid": False}

        n = len(scores_a)
        diffs = [b - a for a, b in zip(scores_a, scores_b)]
        mean_diff = sum(diffs) / n

        # 计算差值的标准差
        variance = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1)
        std_diff = math.sqrt(variance)

        if std_diff == 0:
            return {
                "t_stat": 0 if mean_diff == 0 else float("inf"),
                "p_value": 1.0 if mean_diff == 0 else 0.0,
                "cohens_d": 0,
                "mean_diff": mean_diff,
                "valid": True,
            }

        # t 统计量
        t_stat = mean_diff / (std_diff / math.sqrt(n))

        # 近似 p 值（使用正态近似，样本量 > 30 时有效）
        # 更精确的做法应查 t 分布表
        p_value = 2 * (1 - StatisticalTester._normal_cdf(abs(t_stat)))

        # Cohen's d 效应量
        cohens_d = mean_diff / std_diff

        return {
            "t_stat": round(t_stat, 4),
            "p_value": round(p_value, 4),
            "cohens_d": round(cohens_d, 4),
            "mean_diff": round(mean_diff, 4),
            "sample_size": n,
            "valid": True,
            "significant": p_value < 0.05,
        }

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """标准正态分布累积分布函数的近似计算"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    @staticmethod
    def mcnemar_test(
        n_00: int, n_01: int, n_10: int, n_11: int
    ) -> dict:
        """
        McNemar 检验：用于配对分类数据的差异显著性检验。

        在提示词评估中的典型应用:
        - n_01: A 正确但 B 错误的用例数
        - n_10: A 错误但 B 正确的用例数
        - n_00: 两者都正确的用例数
        - n_11: 两者都错误的用例数

        返回:
            {'chi2': 卡方统计量, 'p_value': 显著性, 'significant': 是否显著}
        """
        # McNemar 卡方统计量
        diff = abs(n_01 - n_10)
        denominator = n_01 + n_10

        if denominator == 0:
            return {"chi2": 0, "p_value": 1.0, "significant": False}

        # 连续性校正
        chi2 = (diff - 1) ** 2 / denominator

        # 卡方(1)分布近似 p 值
        p_value = 1 - StatisticalTester._chi2_cdf(chi2, 1)

        return {
            "chi2": round(chi2, 4),
            "p_value": round(p_value, 4),
            "significant": p_value < 0.05,
            "a_better": n_01 > n_10,  # A 正确更多的情况
            "b_better": n_10 > n_01,
        }

    @staticmethod
    def _chi2_cdf(x: float, df: int) -> float:
        """
        卡方分布 CDF 近似（仅用于 df=1）。
        使用标准正态分布转换：chi2(1) 的平方根服从标准正态分布。
        """
        if df == 1:
            z = math.sqrt(x) if x > 0 else 0
            return StatisticalTester._normal_cdf(z) * 2 - 1
        raise NotImplementedError("仅支持 df=1")

    @staticmethod
    def required_sample_size(
        baseline_accuracy: float,
        minimum_detectable_effect: float = 0.05,
        alpha: float = 0.05,
        power: float = 0.8,
    ) -> int:
        """
        计算 A/B 测试所需的最小样本量。

        参数:
            baseline_accuracy: 基准准确率（例如 0.85）
            minimum_detectable_effect: 最小可检测效果（例如 0.05 表示 5%）
            alpha: 显著性水平
            power: 统计功效

        返回:
            每组所需的最小样本量

        使用说明:
            如果测试用例少于计算值，A/B 测试的结果可能不可靠。
            这是提示词 A/B 测试中最容易被忽略的问题！
        """
        # 使用正态近似公式
        z_alpha = StatisticalTester._normal_ppf(1 - alpha / 2)
        z_beta = StatisticalTester._normal_ppf(power)

        p1 = baseline_accuracy
        p2 = baseline_accuracy + minimum_detectable_effect

        if p2 >= 1.0:
            p2 = 0.99  # 上限设为 0.99，避免计算异常

        # 标准样本量计算公式
        n = (
            (z_alpha * math.sqrt(2 * (p1 + p2) / 2 * (1 - (p1 + p2) / 2))
             + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))
        ) ** 2 / (p2 - p1) ** 2

        return math.ceil(n)

    @staticmethod
    def _normal_ppf(p: float) -> float:
        """标准正态分布分位函数的近似"""
        if p < 0.5:
            return -StatisticalTester._normal_ppf(1 - p)

        # 使用有理逼近
        a = [2.50662823884, -18.61500062529, 41.39119773534, -25.44106049637]
        b = [-8.47351093090, 23.08336743743, -21.06224101826, 3.13082909833]
        c = [0.3374754822726147, 0.9761690190917186, 0.1607979714918209,
             0.0276438810333863, 0.0038405729373609, 0.0003951896511919,
             0.0000321767881768, 0.0000002888167364, 0.0000003960315187]

        if p > 0.92:
            # 尾部区域
            r = math.sqrt(-2 * math.log(1 - p))
            return sum(c[i] * r ** i for i in range(len(c)))
        else:
            # 中心区域
            r = p - 0.5
            return (r * sum(a[i] * r ** (2 * i) for i in range(4))
                    / (1 + sum(b[i] * r ** (2 * i + 1) for i in range(4))))
