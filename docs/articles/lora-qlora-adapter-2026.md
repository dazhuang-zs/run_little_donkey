# 高效微调实战：LoRA/QLoRA/Adapter原理 + 手写代码，单卡微调7B模型

> 全量微调7B模型要90GB显存，LoRA只要16GB。QLoRA再砍一半到8GB。本文从数学推导到代码实现，把三种高效微调方法讲透，附完整可运行代码。

## 一、为什么需要高效微调

全量微调的显存需求：

```
7B模型全量微调:
  参数(FP16):       14 GB
  梯度(FP16):       14 GB
  Adam状态(FP32):   56 GB
  激活值:           ≈ 8 GB
  ─────────────────────
  总计:             ≈ 92 GB
```

24G显卡连参数+梯度都装不下。高效微调的核心思路：**冻结原始参数，只训练少量新增参数**。

## 二、LoRA：低秩自适应

### 2.1 核心思想

预训练权重 $W_0$ 是一个 $d \times k$ 的矩阵，全量微调要更新所有 $d \times k$ 个参数。LoRA的做法：**不直接更新 $W_0$，而是加上一个低秩矩阵**。

$$W = W_0 + \Delta W = W_0 + BA$$

其中 $B \in \mathbb{R}^{d \times r}$，$A \in \mathbb{R}^{r \times k}$，$r \ll \min(d, k)$。

```
原始: Y = X · W0           [d×k，冻结]

LoRA: Y = X · W0 + X · B · A
                 ↑冻结    ↑可训练
                 [d×r] × [r×k]
                 只需训练 r×(d+k) 个参数
```

以LLaMA-7B的Q投影为例（$d=k=4096$）：

| 方式 | 可训练参数 | 占比 |
|------|-----------|------|
| 全量微调 | 4096 × 4096 = 16.7M | 100% |
| LoRA (r=8) | 4096×8 + 8×4096 = 65K | **0.4%** |

参数量减少了250倍，但效果接近全量微调。

### 2.2 缩放因子α

LoRA引入了一个缩放因子：

$$\Delta W = \frac{\alpha}{r} BA$$

$\alpha/r$ 控制更新的"幅度"。调 $r$ 的时候不需要同步调学习率，因为 $\alpha/r$ 自动调整了。

经验值：$\alpha = 2r$（即 $\alpha/r = 2$），或者 $\alpha = 16, r = 8$。

### 2.3 初始化策略

- $A$：用Kaiming均匀初始化（随机）
- $B$：**全零初始化**

为什么B初始化为零？训练开始时 $\Delta W = BA = 0$，模型行为和原始预训练模型完全一致。微调从预训练模型的起点开始，不会破坏已学到的知识。

### 2.4 手写LoRA代码

```python
import torch
import torch.nn as nn
import math

class LoRALinear(nn.Module):
    """LoRA线性层：在原始线性层旁加一个低秩旁路"""
    def __init__(self, original_linear, r=8, alpha=16, dropout=0.0):
        super().__init__()
        self.original = original_linear  # 冻结的原始层
        self.r = r
        self.alpha = alpha
        self.scaling = alpha / r
        
        d_in = original_linear.in_features
        d_out = original_linear.out_features
        
        # 低秩矩阵A和B
        self.lora_A = nn.Parameter(torch.empty(r, d_in))
        self.lora_B = nn.Parameter(torch.zeros(d_out, r))
        
        # 初始化
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        # B已经全零初始化
        
        # 可选的Dropout
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
        
        # 冻结原始权重
        self.original.weight.requires_grad = False
        if self.original.bias is not None:
            self.original.bias.requires_grad = False
    
    def forward(self, x):
        # 原始路径（冻结）
        original_output = self.original(x)
        
        # LoRA路径（可训练）
        lora_output = self.dropout(x) @ self.lora_A.T @ self.lora_B.T * self.scaling
        
        return original_output + lora_output

def apply_lora_to_model(model, r=8, alpha=16, target_modules=["q_proj", "v_proj"]):
    """给模型的所有目标模块加LoRA"""
    for name, module in model.named_modules():
        if any(target in name for target in target_modules):
            # 找到父模块
            name_parts = name.split('.')
            parent = model
            for part in name_parts[:-1]:
                parent = getattr(parent, part)
            
            # 替换为LoRA层
            last_name = name_parts[-1]
            original_linear = getattr(parent, last_name)
            lora_linear = LoRALinear(original_linear, r=r, alpha=alpha)
            setattr(parent, last_name, lora_linear)
    
    return model

# 使用
model = load_pretrained_model()  # 加载预训练模型
model = apply_lora_to_model(model, r=8, alpha=16)

# 只训练LoRA参数
lora_params = [p for p in model.parameters() if p.requires_grad]
optimizer = torch.optim.AdamW(lora_params, lr=1e-4)

print(f"可训练参数: {sum(p.numel() for p in lora_params):,}")
print(f"总参数: {sum(p.numel() for p in model.parameters()):,}")
print(f"训练比例: {sum(p.numel() for p in lora_params) / sum(p.numel() for p in model.parameters()) * 100:.2f}%")
```

### 2.5 LoRA应该加在哪些层？

| 选择 | 可训练参数 | 效果 |
|------|-----------|------|
| 只加Q和V | 最少 | 够用（大多数场景） |
| 加Q、K、V、O | 中等 | 更好（推荐） |
| 加所有线性层（QKVO+MLP） | 较多 | 最好（复杂任务） |

**经验**：简单任务加Q/V就够了，复杂任务加Q/K/V/O或所有线性层。

### 2.6 LoRA的推理优势

训练完成后，把 $\Delta W = BA$ 合并回原始权重：

$$W_{merged} = W_0 + \frac{\alpha}{r} BA$$

合并后，模型结构和原始模型完全一样，**推理时零额外开销**。这是LoRA相比Adapter最大的优势。

```python
def merge_lora_weights(model):
    """将LoRA权重合并回原始权重"""
    for name, module in model.named_modules():
        if isinstance(module, LoRALinear):
            # 计算 ΔW = α/r * B @ A
            delta_w = module.scaling * module.lora_B @ module.lora_A
            
            # 合并到原始权重
            module.original.weight.data += delta_w
            
            # 替换回普通线性层
            name_parts = name.split('.')
            parent = model
            for part in name_parts[:-1]:
                parent = getattr(parent, part)
            setattr(parent, name_parts[-1], module.original)
```

## 三、QLoRA：量化 + LoRA

### 3.1 核心思想

QLoRA = **4-bit量化**的基座模型 + **BF16的LoRA**。

显存对比：

| 方式 | 模型显存（7B） | 可训练参数 |
|------|---------------|-----------|
| 全量微调（FP16） | ~92 GB | 7B |
| LoRA（FP16） | ~16 GB | ~4M |
| QLoRA（4-bit基座+BF16 LoRA） | **~6 GB** | ~4M |

QLoRA把基座模型量化到4-bit，只占原来1/4的显存，但LoRA部分仍然用BF16训练，保证梯度精度。

### 3.2 三项关键技术

**1）4-bit NormalFloat量化（NF4）**

不是均匀量化，而是假设权重服从正态分布，按分位数量化。对于正态分布的权重，NF4比均匀4-bit精度更高。

**2）双重量化**

量化参数（缩放因子）本身也做量化：先量化到FP32，再量化到FP8。节省约0.4bit/param的显存。

**3）分页优化器**

优化器状态在GPU显存不足时自动卸载到CPU内存，避免OOM。

### 3.3 代码（使用bitsandbytes）

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import torch

# QLoRA量化配置
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",            # NormalFloat4
    bnb_4bit_compute_dtype=torch.bfloat16, # 计算用BF16
    bnb_4bit_use_double_quant=True,        # 双重量化
)

# 加载4-bit模型
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_config,
    device_map="auto"
)

# 准备模型以支持梯度检查点
from peft import prepare_model_for_kbit_training
model = prepare_model_for_kbit_training(model)

# 配置LoRA
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# 输出: trainable params: 13,107,200 || all params: 6,738,415,616 || trainable%: 0.1945
```

### 3.4 QLoRA vs LoRA效果

QLoRA论文的结论：**QLoRA在4-bit基座上训练的LoRA，效果和FP16基座上的LoRA几乎相同**。

| 模型 | 基座精度 | 平均得分 |
|------|---------|---------|
| LLaMA-65B LoRA | FP16 | 69.4 |
| LLaMA-65B QLoRA | NF4 | **69.2** |

差距0.2个点，完全可以接受。

## 四、Adapter：插入适配层

### 4.1 核心思想

在Transformer的每个块中插入小型神经网络（Adapter模块），只训练Adapter参数。

```
原始Transformer块:
  x → Self-Attention → Add → FFN → Add → 输出

加Adapter后:
  x → Self-Attention → Add → [Adapter↓→Adapter↑] → FFN → Add → [Adapter↓→Adapter↑] → 输出
                                       ↑只训练这个                        ↑只训练这个
```

### 4.2 Bottleneck Adapter

最经典的Adapter设计：先降维，再升维，中间加非线性激活。

```python
class Adapter(nn.Module):
    def __init__(self, dim, bottleneck_dim=64, dropout=0.1):
        super().__init__()
        self.down_proj = nn.Linear(dim, bottleneck_dim)   # 降维
        self.up_proj = nn.Linear(bottleneck_dim, dim)     # 升维
        self.act = nn.GELU()
        self.dropout = nn.Dropout(dropout)
        self.ln = nn.LayerNorm(dim)
        
        # 初始化：让Adapter初始输出接近0
        nn.init.zeros_(self.up_proj.weight)
        nn.init.zeros_(self.up_proj.bias)
    
    def forward(self, x):
        residual = x
        x = self.down_proj(x)
        x = self.act(x)
        x = self.dropout(x)
        x = self.up_proj(x)
        return residual + x  # 残差连接
```

### 4.3 Adapter vs LoRA

| 维度 | Adapter | LoRA |
|------|---------|-------|
| 插入方式 | 加新模块 | 旁路矩阵 |
| 可训练参数 | 中等 | 少 |
| 推理开销 | **有**（多几层计算） | **无**（可合并） |
| 多任务切换 | 保留多个Adapter | 保留多个LoRA权重 |
| 效果 | 好 | 相当或略好 |

**关键区别**：LoRA的权重可以合并回原始权重，推理零开销。Adapter是额外的模块，推理时必须经过，有额外延迟。所以在推理敏感场景，LoRA是更好的选择。

## 五、三种方法对比总结

| 维度 | LoRA | QLoRA | Adapter |
|------|------|-------|---------|
| 显存（7B） | ~16 GB | **~6 GB** | ~20 GB |
| 可训练参数 | 0.1%-1% | 0.1%-1% | 1%-5% |
| 推理开销 | **零**（可合并） | **零**（可合并） | 有 |
| 效果 | 接近全量 | 接近全量 | 接近全量 |
| 实现难度 | 低 | 低 | 低 |
| 硬件要求 | 16G+ GPU | 8G+ GPU | 24G+ GPU |

**选型建议**：
- 有16G+ GPU → LoRA
- 只有8G GPU → QLoRA
- 需要多任务灵活切换 → Adapter或LoRA

## 六、面试高频问题

**Q1: LoRA为什么用低秩矩阵就能工作？**

预训练模型学到的权重矩阵通常有很低的"内在秩"（intrinsic rank）。微调时不需要改变权重空间的所有方向，只需调整少数几个关键方向就够了。低秩矩阵恰好捕捉了这些关键方向。Aloy等人的实验证明，r=8就能达到全量微调95%以上的效果。

**Q2: LoRA的r怎么选？**

r=4-8：简单任务（文本分类、格式转换）
r=16-32：中等任务（翻译、摘要）
r=64-128：复杂任务（代码生成、数学推理）
不确定就从r=8开始试。

**Q3: QLoRA为什么4-bit基座不影响效果？**

因为LoRA的梯度计算是BF16的，只有前向传播的基座部分是4-bit。反向传播时，梯度通过BF16的LoRA路径流动，精度得到保证。4-bit只影响前向激活值的精度，对梯度方向的影响很小。

**Q4: LoRA可以合并多个微调结果吗？**

可以但需要小心。简单线性合并（权重相加）只在任务相似时有效。更好的做法是：1) 各任务独立训练LoRA，推理时动态加载；2) 用TIES或Dare方法做智能合并，减少冲突。

**Q5: 为什么B初始化为零而A随机初始化？**

如果A和B都随机初始化，训练开始时 $\Delta W = BA$ 不为零，模型输出会偏离预训练模型的输出，可能破坏已有知识。B为零保证了初始时 $\Delta W = 0$，模型从预训练起点开始微调。A随机初始化保证梯度有足够的多样性，不会所有方向都一样。
