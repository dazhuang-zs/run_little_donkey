# 大模型分布式训练：DP/TP/PP/ZeRO四种并行策略，选错亏几百万

> 训练一个70B模型，单卡？不可能。8卡？不够。256卡怎么协作才能把训练跑起来？不同并行策略的显存分配、通信开销、适用场景完全不同。选错了，要么OOM要么慢到天荒地老。本文把四种策略掰开揉碎讲清楚。

## 一、问题：一张卡装不下

LLaMA-70B的训练资源需求：

```
模型参数（BF16）:   70B × 2 bytes = 140 GB
梯度（BF16）:       70B × 2 bytes = 140 GB
Adam状态（FP32）:   70B × 2 × 4 bytes = 560 GB
激活值:             ≈ 40 GB（batch=1, seq=2048）
────────────────────────────────────────────
总计:               ≈ 880 GB
```

一张A100只有80GB。需要11张卡才装得下参数和优化器状态，这还不算通信开销。

分布式训练的本质问题：**怎么把880GB的工作分到多张卡上，且让它们高效协作**。

## 二、数据并行（DP）：最朴素的做法

### 2.1 原理

每张卡持有一份完整的模型副本，但看不同的数据。每个训练步：

1. 每张卡拿到不同的mini-batch数据
2. 各自独立做前向 + 反向
3. AllReduce同步梯度
4. 各自独立更新参数

```
GPU 0: [完整模型] → 数据Batch0 → 前向 → 反向 → 梯度0 ─┐
GPU 1: [完整模型] → 数据Batch1 → 前向 → 反向 → 梯度1 ─┤ AllReduce
GPU 2: [完整模型] → 数据Batch2 → 前向 → 反向 → 梯度2 ─┤ → 平均梯度
GPU 3: [完整模型] → 数据Batch3 → 前向 → 反向 → 梯度3 ─┘
                                                          ↓
                                          每张卡用平均梯度更新参数
```

### 2.2 代码

```python
import torch
import torch.nn as nn
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

def setup_ddp():
    dist.init_process_group("nccl")
    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)

def train_ddp():
    model = MyModel().cuda()
    model = DDP(model, device_ids=[local_rank])
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
    
    for batch in dataloader:
        optimizer.zero_grad()
        output = model(batch)
        loss = output.loss
        loss.backward()  # DDP自动同步梯度
        optimizer.step()
```

### 2.3 优缺点

| 优点 | 缺点 |
|------|------|
| 实现最简单 | 每张卡要装完整模型 |
| 线性加速（通信不成为瓶颈时） | 模型太大就OOM |
| 几乎不改代码 | 显存利用率低（冗余存储） |

**结论**：模型能单卡装下就用DP，装不下就必须换别的。

## 三、张量并行（TP）：把一层切开

### 3.1 原理

把一个层的参数按维度切分到多张卡上。以线性层 $Y = XW$ 为例：

**列切分**（Column Parallelism）：

$$W = [W_1 | W_2], \quad Y = [XW_1 | XW_2]$$

GPU 0算 $XW_1$，GPU 1算 $XW_2$，结果拼接就是完整输出。

**行切分**（Row Parallelism）：

$$W = \begin{bmatrix} W_1 \\ W_2 \end{bmatrix}, \quad Y = X_1 W_1 + X_2 W_2$$

GPU 0算 $X_1 W_1$，GPU 1算 $X_2 W_2$，结果相加就是完整输出。

### 3.2 Transformer的TP方案

Megatron-LM的经典方案：MLP层用列切分+行切分组合。

```
MLP: X → [GeLU(XW1)] → YW2 → 输出
         ↑列切分          ↑行切分

GPU 0: X → GeLU(X·W1_0) → Y_0·W2_0 ─┐
GPU 1: X → GeLU(X·W1_1) → Y_1·W2_1 ─┤ AllReduce求和
                                       ↓
                                    完整输出
```

关键：GeLU是非线性的，不能在切分后做。列切分保证了GeLU在每张卡上独立计算，结果拼接后等价于完整计算。

### 3.3 代码

```python
import torch
import torch.nn as nn
import torch.distributed as dist

class ColumnParallelLinear(nn.Module):
    """列切分线性层"""
    def __init__(self, in_features, out_features, world_size):
        super().__init__()
        self.out_features_per_partition = out_features // world_size
        self.weight = nn.Parameter(
            torch.empty(self.out_features_per_partition, in_features)
        )
        # 只存1/world_size的参数
    
    def forward(self, x):
        # 每张卡算自己那部分
        output = torch.matmul(x, self.weight.T)  # [batch, out/world_size]
        return output  # 外部拼接或直接用

class RowParallelLinear(nn.Module):
    """行切分线性层"""
    def __init__(self, in_features, out_features, world_size):
        super().__init__()
        self.in_features_per_partition = in_features // world_size
        self.weight = nn.Parameter(
            torch.empty(out_features, self.in_features_per_partition)
        )
    
    def forward(self, x):
        # x已经是切分后的输入
        output_partial = torch.matmul(x, self.weight.T)
        # AllReduce求和得到完整输出
        dist.all_reduce(output_partial, op=dist.ReduceOp.SUM)
        return output_partial
```

### 3.4 优缺点

| 优点 | 缺点 |
|------|------|
| 显存按卡数线性减少 | 每层都需要通信（AllReduce） |
| 单层计算不变 | 通信量大，只在节点内（NVLink）高效 |
| 不需要改训练逻辑 | 跨节点通信延迟会抵消加速效果 |

**经验**：TP的通信频率太高（每层2次AllReduce），通常只在**同一节点内**（8卡，NVLink互连）使用。跨节点用DP或PP。

## 四、流水线并行（PP）：把模型按层切开

### 4.1 原理

把模型的不同层放在不同卡上。比如12层模型，4张卡：

```
GPU 0: Layer 0-3   → 前向结果传给GPU 1
GPU 1: Layer 4-7   → 前向结果传给GPU 2
GPU 2: Layer 8-11  → 前向结果传给GPU 3
GPU 3: Layer 12-15 → 计算loss，反向传播
```

### 4.2 泡泡问题

朴素PP的问题是**流水线气泡**（pipeline bubble）：只有最后一张卡在做反向传播时，前面的卡都在空等。

```
时间 →  1  2  3  4  5  6  7  8
GPU 0: F0 F1 F2 F3          B0 B1 B2 B3   (F=前向, B=反向)
GPU 1:       F0 F1 F2 F3          B0 B1 B2 B3
GPU 2:             F0 F1 F2 F3          B0 B1 B2 B3
GPU 3:                   F0 F1 F2 F3 B0 B1 B2 B3
```

GPU 0在前向阶段做完后就空等了很久才轮到反向传播。气泡率 = (p-1)/p，p是流水线阶段数。

### 4.3 解决：微批次（Micro-batch）

把一个batch切成多个micro-batch，让不同micro-batch的前向和反向交错执行：

```
时间 →  1   2   3   4   5   6   7   8
GPU 0: F00 F01 F02 B00 B01 B02 F03 B03
GPU 1:     F00 F01 B00 F02 B01 F03 B02 B03
...
```

气泡率从 (p-1)/p 降低到 (p-1)/(m+p-1)，m是micro-batch数。m越大，气泡越少。

### 4.4 优缺点

| 优点 | 缺点 |
|------|------|
| 显存按卡数线性减少 | 有流水线气泡 |
| 通信量小（只传激活值） | 实现复杂（需要微批次调度） |
| 跨节点通信友好 | 需要合理切分阶段 |

## 五、ZeRO：微软的显存优化方案

### 5.1 核心思想

DP的问题是每张卡都存完整模型。但仔细看，显存分三部分：

1. **参数**（Parameters）
2. **梯度**（Gradients）
3. **优化器状态**（Optimizer States，占最大头）

ZeRO的做法：**把这三部分分别切分到不同卡上**，需要时再通过通信收集。

### 5.2 三个阶段

| 阶段 | 切分内容 | 每卡显存（70B模型，64卡） |
|------|---------|------------------------|
| ZeRO-1 | 优化器状态 | ~15 GB（原始880/64≈14 + 参数+梯度） |
| ZeRO-2 | + 梯度 | ~9 GB |
| ZeRO-3 | + 参数 | ~4 GB |

**ZeRO-1**：只切优化器状态。每张卡只存1/N的优化器状态，参数和梯度仍然完整。更新参数时，各卡只需通信自己负责的那部分梯度。

**ZeRO-2**：切优化器状态 + 梯度。每张卡只存1/N的梯度和优化器状态。

**ZeRO-3**：全切。参数也切了，前向和反向时需要All-Gather收集完整参数。

### 5.3 代码（DeepSpeed）

```python
import deepspeed

# ZeRO配置
ds_config = {
    "train_batch_size": 128,
    "gradient_accumulation_steps": 4,
    "zero_optimization": {
        "stage": 3,          # 使用ZeRO-3
        "offload_param": {   # 参数卸载到CPU
            "device": "cpu",
            "pin_memory": True
        },
        "offload_optimizer": {  # 优化器状态卸载到CPU
            "device": "cpu",
            "pin_memory": True
        },
        "overlap_comm": True,   # 通信与计算重叠
        "contiguous_gradients": True
    },
    "bf16": {"enabled": True},
    "gradient_clipping": 1.0,
}

model, optimizer, _, scheduler = deepspeed.initialize(
    model=model,
    optimizer=optimizer,
    config=ds_config
)

for batch in dataloader:
    outputs = model(batch)
    loss = outputs.loss
    model.backward(loss)
    model.step()
```

### 5.4 ZeRO vs DP/TP/PP

| 维度 | DP | TP | PP | ZeRO-3 |
|------|----|----|-----|--------|
| 切分对象 | 数据 | 层内参数 | 层间 | 所有状态 |
| 通信量 | 低（只同步梯度） | 高（每层2次AllReduce） | 低（只传激活） | 中（All-Gather） |
| 实现难度 | 低 | 高 | 高 | 中（DeepSpeed封装） |
| 扩展性 | 受限于单卡显存 | 受限于NVLink | 受限于气泡 | **最佳** |

## 六、实际选型策略

```
能不能单卡装下模型？
  ├── 能 → 数据并行（DP），最简单
  └── 不能 → 需要多少卡？
        ├── 2-8卡（单节点） → 张量并行（TP）
        │   └── 8卡还不够 → TP + ZeRO
        ├── 8-64卡（多节点） → TP（节点内）+ DP（节点间）
        │   └── 显存还是不够 → TP + ZeRO + DP
        └── 64+卡（大规模） → 3D并行：TP + PP + DP
                              └── 加ZeRO进一步优化
```

**真实案例**：

| 模型 | 规模 | 训练配置 |
|------|------|---------|
| GPT-3 | 175B | TP=8, PP=64, DP=96 |
| LLaMA-70B | 70B | TP=8, PP=8, DP=64 + ZeRO-1 |
| LLaMA-7B | 7B | DP=128 + ZeRO-1 |

## 七、面试高频问题

**Q1: TP和PP的区别是什么？**

TP是按层内维度切分（同一层参数分布在多卡），PP是按层间切分（不同层在不同卡）。TP通信频繁（每层2次AllReduce）但无气泡，PP通信少但有流水线气泡。通常在节点内用TP，节点间用PP。

**Q2: ZeRO-3和模型并行的区别？**

ZeRO-3是动态切分：参数平时是切分的，计算时通过All-Gather临时收集完整参数。模型并行是静态切分：每张卡只负责部分计算，不需要临时收集。ZeRO-3更灵活但通信量更大。

**Q3: 为什么TP不适合跨节点？**

TP每层需要2次AllReduce，如果跨节点走InfiniBand，延迟远高于NVLink（~10us vs ~1us），通信时间会超过计算时间，反而变慢。

**Q4: 3D并行怎么确定TP/PP/DP的比例？**

经验法则：TP = 节点内GPU数（充分利用NVLink），PP = 模型层数/每阶段的层数（平衡各阶段计算量），DP = 总GPU数/(TP×PP)。

**Q5: ZeRO的Offload是什么？**

把参数或优化器状态从GPU显存卸载到CPU内存。GPU显存不够时，可以用CPU内存补充。代价是CPU-GPU数据传输延迟，训练速度会慢2-3倍。通常是最后手段。
