# Sora之死：OpenAI关停视频生成产品背后的算力陷阱与商业逻辑

2026年4月，OpenAI毫无预兆地关停了Sora。没有过渡期，没有灰度方案，应用下架、API关闭、ChatGPT内置视频功能一并撤走。迪士尼10亿美元合作当场告吹。

从2024年2月惊艳全球，到2026年4月仓促谢幕，Sora只活了25个月。

这不是一个技术失败的故事。Sora的视频质量至今仍是行业顶级。这是一个**算力经济学**的故事：当生成一段视频的GPU成本是生成一段文本的数千倍，当每日运营成本是收入的1000倍，当60天用户留存率归零，再好的技术也撑不住商业的底。

更值得关注的是：Sora倒下了，国产的可灵AI和即梦AI却活得好好的。同一赛道，冰火两重天。为什么？

---

## 一、Sora的死亡账单：每一组数字都是致命的

### 1.1 算力黑洞：日烧1500万美元

先看最核心的经济账。

Sora上线一年，累计消费者收入约140万美元（Appfigures数据），日均运营成本1500万美元。年化成本约54亿美元，投入产出比接近2500:1。

这意味着什么？**Sora一年的收入，不够它烧15分钟。**

算力为什么这么贵？因为视频生成是AI领域最吃算力的任务，没有之一。

一段60秒1080p视频，DiT（Diffusion Transformer）模型需要执行数百步去噪推理，每一步都要处理数万个token的空间-时间注意力计算。相比文本生成（自回归、逐token输出），视频生成的计算量是文本的**数千倍**，是图片生成的**50倍以上**。

更致命的是重复渲染。用户生成1条满意视频，平均需要尝试5-10次。Sora的可用率（生成出满意结果的概率）仅为5%-10%。每次失败都意味着GPU算力的纯浪费，形成"越用越亏、越亏越限用"的恶性循环。

OpenAI不得不把免费额度从30条/月砍到6条/月，结果用户流失更严重。

### 1.2 留存率归零：尝鲜即走

数据更残酷：

- 2025年12月，Sora下载量环比下降32%
- 2026年1月，继续暴跌45%
- 30天留存率：1%
- 60天留存率：0%

60天留存归零意味着：**没有任何一个用户在两个月后还在使用Sora。**

北京航空航天大学胡堃研究员指出了双端失守的问题：普通用户只为娱乐体验，没有持续付费意愿；专业创作者对Sora的可用率和控制力不满意，无法满足更高技术要求。

### 1.3 迪士尼10亿美元合作泡汤

2025年12月，迪士尼与OpenAI达成重磅合作：200+角色授权，三年10亿美元+10亿美元股权投资。这是AI行业最大内容授权合作。

Sora关停，这笔钱一分没到账。

### 1.4 核心负责人出走

2026年4月18日，Sora核心负责人比尔·皮布尔斯（Bill Peebles）宣布离开OpenAI。技术灵魂人物离职，等于给这个项目盖棺定论。

---

## 二、Sora为什么非死不可：三重致命伤

### 2.1 致命伤一：选错了赛道定位

Sora想做"通用视频生成工具"，面向所有用户、所有场景。这是最致命的定位错误。

通用意味着无法对任何场景做深度优化。影视制作需要精确的运镜控制和角色一致性，广告需要品牌色的精准还原，短视频需要快速出片和低成本。Sora一个都满足不了。

更关键的是，通用定位意味着用C端消费级定价覆盖不了B端专业需求，用B端专业定价吓跑了C端尝鲜用户。两头不讨好。

### 2.2 致命伤二：算力经济学崩溃

OpenAI当时正在筹备IPO，需要在财务报表上交出漂亮数字。一个年烧54亿美元、收入仅140万的项目，是财报上的巨大拖累。

更紧迫的是，OpenAI急需算力资源支持下一代模型"Spud"（GPT-6）。华尔街日报报道，OpenAI关停Sora的核心原因就是**释放算力资源**，全力投入Spud和企业级AI产品开发。

Sora每生成一段视频消耗的GPU算力，可以支撑数千次ChatGPT对话。在算力极度紧缺的2026年，这是一个无法接受的资源错配。

### 2.3 致命伤三：竞争格局恶化

Sora发布时是行业唯一的"电影级"视频生成工具。但到2026年，格局已变：

- **Runway Gen-4**：4K/60秒，$12-76/月，专业影视创作定位
- **可灵AI（快手）**：1080p/3分钟续写，ARR超3亿美元
- **即梦AI（字节）**：1080p/60秒，抖音生态打通
- **HappyHorse（阿里）**：开源Apache 2.0，Video Arena盲测登顶
- **Google Veo**：4K/60秒+空间音频，即将开放

Sora不再独特，却仍然最贵。

---

## 三、为什么国产活得下去：三条活路

Sora死了，但可灵AI和即梦AI活得很好。同一赛道，为什么冰火两重天？

### 3.1 可灵AI：精准定位+生态协同

可灵AI 2025年Q4营收3.4亿元，2026年1月ARR超3亿美元（约20.4亿元），预计全年翻倍。

**活路一：不碰C端娱乐，锚定B端专业创作。**

可灵明确主打"电影级画质+大幅度动作"，3D时空联合注意力机制支持长达3分钟视频续写。它的用户是专业创作者和制作团队，有真实付费能力和持续需求。

**活路二：降本增效的算力策略。**

可灵3.0 Omni模型生成720p视频，黄金会员每秒成本0.48元，铂金会员0.37元。这是Sora同类效果成本的**百分之一**。怎么做到的？快手有自建GPU集群，算力成本远低于OpenAI租用云GPU。同时国产DiT模型在架构上做了大量推理优化。

**活路三：与快手生态协同。**

可灵生成的视频可直接在快手、抖音分发，创作到发布的链路极短。这不是一个孤立的工具，而是内容生产流水线的一环。

### 3.2 即梦AI：低价走量+生态绑定

即梦走的是另一条路：低价走量+字节生态绑定。

**核心策略：用价格换规模。**

即梦Seedance 2.0在2026年Q1经历了一月三涨（从0.44元/秒涨到更高），侧面说明之前定价极低，是在亏本换用户。即便涨价后，成本仍远低于Sora。

**生态优势：抖音+剪映。**

即梦与抖音、剪映深度打通。生成视频一键发布抖音，这在短视频创作者群体中是巨大的效率优势。角色一致性也是即梦的强项，解决了AI视频"人物五官乱飞"的痛点。

### 3.3 国产活下来的底层逻辑

| 维度 | Sora | 可灵/即梦 |
|------|------|-----------|
| 算力来源 | 租用云GPU，成本高 | 自建集群+国产芯片，成本低 |
| 用户定位 | 通用C端，付费意愿弱 | 垂直B端+生态内C端，有付费习惯 |
| 生态绑定 | 无分发渠道 | 快手/抖音生态，创作到发布闭环 |
| 定价策略 | $200/月Pro版，吓跑用户 | 分级会员，按量计费，低门槛 |
| 算力效率 | 通用DiT，未深度优化 | 针对性推理优化，成本降1-2个数量级 |

核心差异只有一个：**Sora是"技术产品"，可灵/即梦是"商业产品"。** 技术产品追求效果上限，商业产品追求投入产出比。当算力成本是收入的1000倍时，前者必死。

---

## 四、算力经济学：AI视频的生死线在哪

Sora的死不只是个案，它揭示了AI视频生成的经济规律。

### 4.1 视频生成的算力消耗模型

一段W秒、H×W分辨率、F帧率的视频，DiT模型的推理计算量可以近似为：

```
FLOPs ≈ C × S² × W × F × N_steps
```

其中：
- C = 模型参数量（Sora约30B）
- S = 空间token数（1080p约3600个patch）
- W = 视频token数（60秒约150帧×3600=54万）
- N_steps = 去噪步数（通常50-100步）

一段60秒1080p视频的总FLOPs约在10^18量级，即1 EFLOP。以H100 GPU的算力（约2 PFLOPS FP16）估算，单张H100需要约500秒。考虑并行效率和重复渲染，实际每段视频需要消耗数十美元的GPU成本。

Sora定价$200/月Pro版，看起来很贵，但只要用户每月生成几段视频，OpenAI就是亏的。

### 4.2 算力优化路线图

达摩院DyDiT架构给出了一个方向：通过时间步长和空间区域的动态资源分配，DiT模型推理算力可削减51%，生成速度提升1.73倍，质量几乎无损。

ColossalAI开源的Video Ocean方案，针对类Sora视频模型做了多维并行和异构内存优化，MFU（模型算力利用率）最高提升2.61倍，10B级模型的保存时间从300秒降至10秒以内。

这些优化意味着：**视频生成的算力成本正在以每年2-3倍的速度下降。** 但在2026年，它仍然比文本生成贵3个数量级。

### 4.3 什么样的AI视频产品能活

从Sora的教训和国产的成功经验，可以提炼出三条生存法则：

**法则一：必须绑定分发生态。** 没有分发渠道的视频生成工具，用户生成完视频无处发布，留存必然归零。可灵绑定快手，即梦绑定抖音，Runway绑定专业影视工作流。

**法则二：算力成本必须低于用户付费意愿。** 这听起来是废话，但Sora就没做到。用户为一段15秒视频尝试10次，每次成本800元人民币，谁付得起？可灵每秒0.37-0.48元，一段60秒视频约22-29元，用户可以接受。

**法则三：做窄场景的深度优化，不做通用工具。** 通用意味着对任何场景都不够好。窄场景可以做针对性的算力优化（如漫剧生成不需要物理仿真的精度），可以积累领域数据飞轮，可以建立用户迁移壁垒。

---

## 五、OpenAI的下一站：从Sora到Spud

Sora关停不是OpenAI的终点，而是战略转向的起点。

### 5.1 GPT-6（Spud）：投入全部算力

代号Spud的GPT-6已于2026年4月14日发布。5-6万亿参数MoE架构，200万Token上下文，Symphony原生多模态统一架构，综合性能较GPT-5.4提升40%。

训练投入：18个月、20亿美元算力（约10万张H100）。

OpenAI的逻辑很清楚：视频生成是一个"算力黑洞+低留存"的生意，而大语言模型+Agent才是高价值、高留存的方向。把Sora的算力释放给Spud，ROI会高得多。

### 5.2 机器人赛道：物理世界比视频世界更值钱

OpenAI关停Sora的同时，正在重新进入机器人领域。物理世界的AI比数字视频的商业价值大几个数量级：工业自动化、家庭服务、物流配送，每个都是万亿级市场。

视频生成是一个"内容工具"，机器人是一个"生产力工具"。前者用户付几十块月费，后者企业付几十万年费。

### 5.3 对从业者的启示

Sora之死给AI从业者的启示不是"视频生成不行"，而是：

1. **技术先进不等于商业成立。** Sora的技术至今领先，但算力经济学不支持。
2. **先算账再写代码。** 算力成本-用户付费-留存率的三角必须闭合。
3. **在中国做AI视频，成本优势是核心壁垒。** 自建算力+国产芯片+生态绑定，这三条Sora一条都没有。
4. **关注算力效率优化，这是视频生成的下一个技术红利。** DyDiT类架构、推理加速、模型蒸馏，这些"不够性感"的工作，比堆参数更决定生死。

---

## 六、代码实战：算力成本估算工具

理解Sora为什么死，不如动手算一算。下面是一个AI视频生成算力成本估算器，帮你判断一个视频生成产品的经济可行性。

```python
"""
AI视频生成算力成本估算器
估算不同配置下生成视频的GPU成本和盈亏平衡点
"""

from dataclasses import dataclass


@dataclass
class VideoGenConfig:
    """视频生成配置"""
    resolution: tuple  # (height, width), e.g. (1080, 1920)
    fps: int           # 帧率
    duration_sec: int  # 视频时长(秒)
    model_params_b: float  # 模型参数量(十亿)
    denoise_steps: int     # 去噪步数
    patch_size: int        # DiT patch大小, 通常2x2


@dataclass
class GPUConfig:
    """GPU配置"""
    name: str
    fp16_tflops: float    # FP16算力(TFLOPS)
    cost_per_hour: float  # 每小时成本(美元)
    memory_gb: int        # 显存(GB)


@dataclass
class BusinessConfig:
    """商业配置"""
    price_per_video: float  # 每段视频售价(美元)
    avg_retries: float      # 用户平均重试次数
    gpu_utilization: float  # GPU利用率(0-1)
    daily_active_users: int # 日活用户
    videos_per_user_per_day: float  # 每用户每天生成视频数


def estimate_flops(config: VideoGenConfig) -> float:
    """
    估算视频生成总FLOPs
    基于DiT架构的近似计算
    """
    h, w = config.resolution
    total_frames = config.fps * config.duration_sec

    # 空间token数 = 每帧patch数
    spatial_tokens = (h // config.patch_size) * (w // config.patch_size)

    # 总token数 = 帧数 × 空间token
    total_tokens = total_frames * spatial_tokens

    # 单步推理FLOPs ≈ 2 × 参数量 × token数 (前向)
    # 注意力机制的计算量与token数呈二次关系，这里简化为线性近似
    single_step_flops = 2 * config.model_params_b * 1e9 * total_tokens

    # 总FLOPs = 单步 × 去噪步数
    total_flops = single_step_flops * config.denoise_steps

    return total_flops


def estimate_cost(
    video_config: VideoGenConfig,
    gpu_config: GPUConfig,
    business_config: BusinessConfig
) -> dict:
    """估算生成成本和盈亏情况"""
    # 单次生成FLOPs
    flops_per_gen = estimate_flops(video_config)

    # 考虑重试：实际FLOPs
    actual_flops = flops_per_gen * business_config.avg_retries

    # GPU算力(FLOPS)
    gpu_flops = gpu_config.fp16_tflops * 1e12 * business_config.gpu_utilization

    # 单段视频生成时间(秒)
    gen_time_sec = actual_flops / gpu_flops

    # 单段视频GPU成本(美元)
    cost_per_video = (gen_time_sec / 3600) * gpu_config.cost_per_hour

    # 日营收
    daily_revenue = (
        business_config.daily_active_users
        * business_config.videos_per_user_per_day
        * business_config.price_per_video
    )

    # 日GPU成本
    daily_gpu_cost = (
        business_config.daily_active_users
        * business_config.videos_per_user_per_day
        * cost_per_video
    )

    # 盈亏平衡价格
    break_even_price = cost_per_video

    return {
        "flops_per_video": f"{flops_per_gen:.2e}",
        "gen_time_sec": round(gen_time_sec, 1),
        "cost_per_video_usd": round(cost_per_video, 2),
        "cost_with_retries_usd": round(cost_per_video * business_config.avg_retries, 2),
        "daily_revenue_usd": round(daily_revenue, 0),
        "daily_gpu_cost_usd": round(daily_gpu_cost, 0),
        "daily_profit_usd": round(daily_revenue - daily_gpu_cost, 0),
        "break_even_price_usd": round(break_even_price, 2),
        "roi_ratio": f"1:{round(daily_gpu_cost / max(daily_revenue, 1), 0)}" if daily_revenue > 0 else "N/A",
    }


def main():
    # 场景一：Sora级配置
    sora_video = VideoGenConfig(
        resolution=(1080, 1920),
        fps=24,
        duration_sec=60,
        model_params_b=30,
        denoise_steps=75,
        patch_size=2,
    )

    # 场景二：可灵级配置（优化后）
    kling_video = VideoGenConfig(
        resolution=(1080, 1920),
        fps=24,
        duration_sec=60,
        model_params_b=15,  # 模型更小但效果接近
        denoise_steps=50,   # 步数优化
        patch_size=2,
    )

    # GPU配置：H100（OpenAI使用）
    h100 = GPUConfig(
        name="NVIDIA H100",
        fp16_tflops=1979,
        cost_per_hour=3.5,  # 云GPU时价
        memory_gb=80,
    )

    # GPU配置：国产算力集群（可灵使用）
    domestic_gpu = GPUConfig(
        name="Domestic GPU Cluster",
        fp16_tflops=1979,
        cost_per_hour=0.8,  # 自建集群成本远低于云GPU
        memory_gb=80,
    )

    # Sora商业配置
    sora_business = BusinessConfig(
        price_per_video=10,   # Pro版$200/月, 约20段视频
        avg_retries=8,        # 可用率5-10%
        gpu_utilization=0.6,
        daily_active_users=50000,
        videos_per_user_per_day=0.3,
    )

    # 可灵商业配置
    kling_business = BusinessConfig(
        price_per_video=3,    # 分级会员, 更低单价
        avg_retries=2,        # 可用率更高
        gpu_utilization=0.75, # 优化后利用率更高
        daily_active_users=200000,
        videos_per_user_per_day=1.0,
    )

    print("=" * 60)
    print("Sora级配置 (H100云GPU)")
    print("=" * 60)
    sora_result = estimate_cost(sora_video, h100, sora_business)
    for k, v in sora_result.items():
        print(f"  {k}: {v}")

    print()
    print("=" * 60)
    print("可灵级配置 (自建算力集群)")
    print("=" * 60)
    kling_result = estimate_cost(kling_video, domestic_gpu, kling_business)
    for k, v in kling_result.items():
        print(f"  {k}: {v}")

    print()
    print("=" * 60)
    print("关键对比")
    print("=" * 60)
    print(f"  Sora单视频成本: ${sora_result['cost_per_video_usd']}")
    print(f"  可灵单视频成本: ${kling_result['cost_per_video_usd']}")
    print(f"  成本差距: {round(float(sora_result['cost_per_video_usd']) / max(float(kling_result['cost_per_video_usd']), 0.01), 1)}x")
    print(f"  Sora日盈亏: ${sora_result['daily_profit_usd']}")
    print(f"  可灵日盈亏: ${kling_result['daily_profit_usd']}")


if __name__ == "__main__":
    main()
```

运行这个工具，你会看到Sora和可灵在同样1080p/60秒视频生成上的成本差距。核心变量不是模型大小，而是**算力成本、可用率（重试次数）和GPU利用率**。

这解释了为什么Sora必死：H100云GPU时价$3.5+8次重试+60%利用率，对比自建集群$0.8/时+2次重试+75%利用率，成本差距超过10倍。

---

## 七、写在最后：Sora的墓志铭

Sora不是失败者。它证明了AI视频生成可以达到电影级效果，激发了整个行业的投入和竞争。可灵、即梦、Runway、HappyHorse，都是在Sora开辟的赛道上跑出来的。

但Sora也是一个警示：**在AI行业，技术领先只是入场券，算力经济学才是生死线。**

当你看到一个炫酷的AI Demo时，先别急着叫好。算一算：

- 生成一次要烧多少算力？
- 用户愿意付多少钱？
- 留存率能撑住吗？
- 有没有生态可以把用户锁住？

Sora用54亿美元的年化成本和1%的留存率，给出了最昂贵的答案。

下一个"Sora"会是谁？或许是某个正在烧钱的AI 3D生成产品，或许是某个"免费无限生成"的AI音乐平台。算力经济学的铁律不会因为技术进步而失效，只会让淘汰来得更快。

因为算力成本在降，但用户的付费意愿不会跟着算力成本一起涨。

---

*数据来源：Appfigures、华尔街日报、经济日报、快手财报、21世纪经济报道、OpenAI官方公告*
