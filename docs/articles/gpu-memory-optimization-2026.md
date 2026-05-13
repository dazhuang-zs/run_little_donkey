# 大模型显存优化三板斧：混合精度训练 + 梯度累积 + 梯度检查点

> 想用单张24G显卡微调7B模型？不是做梦。本文从显存账本算起，手把手教你三招把显存占用砍到原来的1/4。

## 一、先算账：显存到底花在哪了

训练一个模型，显存要存四样东西：

| 项目 | 占比 | 说明 |
|------|------|------|
| 模型参数 | ~20% | 7B模型FP16约14GB |
| 梯度 | ~20% | 和参数同大小 |
| 优化器状态 | ~40% | Adam需要存m和v两个状态 |
| 激活值 | ~20% | 前向传播的中间结果，用于反向传播 |

以LLaMA-7B为例（FP16，batch_size=1，seq_len=2048）：

```
模型参数:     7B × 2 bytes = 14 GB
梯度:         7B × 2 bytes = 14 GB
Adam状态:     7B × 2 × 4 bytes(FP32) = 56 GB
激活值:       ≈ 8 GB（取决于序列长度和层数）
─────────────────────────────────────
总计:         ≈ 92 GB
```

24G显卡连参数都装不下？别急，下面三招依次拆解。

## 二、第一斧：混合精度训练

### 2.1 核心思想

不是所有计算都需要FP32精度。**用FP16做前向和反向，用FP32维护参数主副本**。

```
FP32参数 (master copy) ──→ 转FP16 ──→ 前向传播(FP16)
                                      ↓
                              反向传播(FP16)
                                      ↓
                              FP16梯度 ──→ 转FP32 ──→ 更新FP32参数
```

为什么需要FP32主副本？因为FP16的精度只有约3.3位有效数字，梯度很小的时候（比如1e-7），FP16直接变成0（下溢出），参数就不更新了。FP32主副本能保留这些微小更新。

### 2.2 Loss Scaling：解决梯度下溢

FP16能表示的最小正数是 6e-8，而很多梯度比这还小。解决办法：在反向传播前把loss放大，反向传播后再把梯度缩小回来。

```
1. loss_scaled = loss × scale_factor (比如 2^16 = 65536)
2. 反向传播，得到 scaled_gradients (FP16)
3. gradients = scaled_gradients / scale_factor (转回真实值)
4. 如果出现NaN/Inf，减小scale_factor，跳过这步更新
```

### 2.3 PyTorch实现

```python
import torch
from torch.cuda.amp import autocast, GradScaler

model = MyModel().cuda()
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
scaler = GradScaler()  # 自动管理loss scaling

for data, target in dataloader:
    optimizer.zero_grad()
    
    # 前向传播：自动用FP16
    with autocast():
        output = model(data)
        loss = criterion(output, target)
    
    # 反向传播：自动做loss scaling
    scaler.scale(loss).backward()
    
    # 参数更新：自动unscale梯度并更新
    scaler.step(optimizer)
    scaler.update()
```

**显存节省**：激活值和梯度从FP32变FP16，节省约**30%-40%**显存。

### 2.4 BF16 vs FP16

| 特性 | FP16 | BF16 |
|------|------|------|
| 指数位 | 5位 | 8位 |
| 尾数位 | 10位 | 7位 |
| 表示范围 | ±65504 | ±3.4e38 |
| 精度 | 较高 | 较低 |
| 需要Loss Scaling | 是 | 否 |
| 硬件要求 | Volta+ | A100+ (Ampere+) |

BF16的指数位和FP32一样，所以表示范围相同，不会溢出，**不需要Loss Scaling**。A100/H100训练优先选BF16。

## 三、第二斧：梯度累积

### 3.1 核心思想

大batch训练更稳定，但显存不够怎么办？**小batch多次前向，累积梯度后再更新**。

```
标准方式: batch_size=64, 一次前向+反向, 更新一次
累积方式: batch_size=8,  前向+反向8次,   更新一次

数学等价: 两种方式看到的梯度是一样的
```

### 3.2 数学推导

单步梯度：
$$g = \frac{1}{B}\sum_{i=1}^{B} \nabla L(x_i)$$

累积梯度：
$$g_{accum} = \frac{1}{K}\sum_{k=1}^{K}\frac{1}{b}\sum_{i=1}^{b}\nabla L(x_{k,i}) = \frac{1}{K \cdot b}\sum_{k,i}\nabla L(x_{k,i})$$

当 $K \cdot b = B$ 时，两种梯度数学等价。

**关键**：每次反向传播后不能调 `optimizer.step()`，也不能调 `optimizer.zero_grad()`。只在累积够了之后再调。

### 3.3 PyTorch实现

```python
accumulation_steps = 8  # 等效batch_size = micro_batch × 8
optimizer.zero_grad()

for i, (data, target) in enumerate(dataloader):
    with autocast():
        output = model(data)
        loss = criterion(output, target)
        loss = loss / accumulation_steps  # 关键：除以累积步数
    
    scaler.scale(loss).backward()
    
    # 每accumulation_steps步才更新一次
    if (i + 1) % accumulation_steps == 0:
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad()
```

**注意**：`loss / accumulation_steps` 这行很关键。如果不除，梯度会放大8倍，相当于学习率放大了8倍。

**显存节省**：batch_size从64降到8，激活值显存减少约**87.5%**。

### 3.4 BatchNorm的坑

梯度累积时，每个micro-batch独立计算BN统计量（均值和方差），而不是在整个等效batch上计算。这会导致BN统计量不准确。

解决方案：
- 换成GroupNorm或LayerNorm（大模型标配，不影响）
- 如果必须用BN：使用SyncBN或手动累积统计量

## 四、第三斧：梯度检查点

### 4.1 核心思想

正常训练时，前向传播会把每一层的激活值存下来，供反向传播用。这些激活值占大量显存。

梯度检查点的做法：**前向传播时不存中间激活值，反向传播时重新算**。

```
正常方式:
  Layer1 → 存激活1 → Layer2 → 存激活2 → Layer3 → 存激活3 → ...
  反向: 直接用存的激活值

检查点方式:
  Layer1 → 不存 → Layer2 → 存检查点2 → Layer3 → 不存 → Layer4 → 存检查点4 → ...
  反向: 从最近的检查点重新前向，算出需要的激活值
```

每隔几层存一个检查点，其余层的激活值需要时重新计算。

### 4.2 显存 vs 计算的权衡

假设模型有 $n$ 层，每隔 $k$ 层存一个检查点：

| 方式 | 激活值显存 | 额外计算 |
|------|-----------|---------|
| 不用检查点 | $O(n)$ | 0 |
| 每层都是检查点 | $O(1)$ | 1次完整前向 |
| 每k层一个检查点 | $O(\sqrt{n})$ | 约30%额外前向计算 |

最优策略是每 $\sqrt{n}$ 层存一个检查点，这样显存和计算都达到 $O(\sqrt{n})$。

### 4.3 PyTorch实现

```python
from torch.utils.checkpoint import checkpoint

class CheckpointBlock(nn.Module):
    """带梯度检查点的Transformer块"""
    def __init__(self, dim, num_heads):
        super().__init__()
        self.attn = nn.MultiheadAttention(dim, num_heads)
        self.ffn = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.GELU(),
            nn.Linear(dim * 4, dim)
        )
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)
    
    def _forward(self, x):
        # 标准前向传播（检查点会调用这个）
        x = x + self.attn(self.norm1(x), self.norm1(x), self.norm1(x))[0]
        x = x + self.ffn(self.norm2(x))
        return x
    
    def forward(self, x):
        # 使用梯度检查点：不存中间激活值
        return checkpoint(self._forward, x, use_reentrant=False)

# 完整模型
class CheckpointTransformer(nn.Module):
    def __init__(self, dim=768, num_heads=12, num_layers=12):
        super().__init__()
        self.layers = nn.ModuleList([
            CheckpointBlock(dim, num_heads) for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(dim)
    
    def forward(self, x):
        for layer in self.layers:
            x = layer(x)  # 每层都用检查点
        return self.norm(x)
```

**显存节省**：激活值显存从 $O(n)$ 降到 $O(\sqrt{n})$，12层模型节省约**60%-70%**激活值显存。

**代价**：训练速度慢约25%-30%（因为要重新计算前向传播）。

## 五、三招叠加效果

以LLaMA-7B为例，batch_size=1，seq_len=2048：

| 优化方式 | 显存占用 | 相对原始 | 训练速度 |
|---------|---------|---------|---------|
| 原始（FP32，无优化） | ~92 GB | 100% | 1.0x |
| +混合精度（FP16） | ~60 GB | 65% | 1.3x（更快） |
| +梯度累积（bs 64→8） | ~35 GB | 38% | 1.0x（持平） |
| +梯度检查点 | **~20 GB** | **22%** | 0.75x（慢25%） |

单张24G显卡，三招叠加大约能训7B模型。

## 六、实战：单卡微调7B模型完整代码

```python
import torch
from torch.cuda.amp import autocast, GradScaler
from torch.utils.checkpoint import checkpoint

def train_7b_model():
    # 加载模型（BF16节省显存，A100/H100优先）
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    
    model = load_llama_7b()  # 你的模型加载逻辑
    model = model.to(dtype).cuda()
    model.gradient_checkpointing_enable()  # 启用梯度检查点
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    scaler = GradScaler(enabled=(dtype == torch.float16))
    
    accumulation_steps = 8  # 等效batch=8
    optimizer.zero_grad()
    
    for step, batch in enumerate(dataloader):
        with autocast(dtype=dtype):
            output = model(batch["input_ids"].cuda())
            loss = output.loss / accumulation_steps
        
        scaler.scale(loss).backward()
        
        if (step + 1) % accumulation_steps == 0:
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()
            
            if step % 100 == 0:
                print(f"Step {step}, Loss: {loss.item() * accumulation_steps:.4f}")

if __name__ == "__main__":
    train_7b_model()
```

## 七、面试高频问题

**Q1: 混合精度训练为什么不能全用FP16？**

FP16的表示范围太小（最大65504），梯度很小时会下溢出变成0。FP32主副本保证了参数更新的精度。实际做法是用FP16做矩阵运算（快），用FP32做参数更新（准）。

**Q2: 梯度累积和增大batch_size数学上完全等价吗？**

几乎等价，但有两个差异：1) BatchNorm的统计量是每个micro-batch独立计算的；2) Dropout的随机mask每次不同。对于用LayerNorm的大模型，这两个差异可以忽略。

**Q3: 梯度检查点为什么省显存但慢速度？**

省显存是因为不存中间激活值。慢速度是因为反向传播时需要从检查点重新计算前向传播来恢复激活值。这是典型的用计算换显存。

**Q4: BF16和FP16怎么选？**

有A100/H100选BF16，没有就选FP16。BF16不需要Loss Scaling，训练更稳定。FP16精度更高但容易溢出，需要额外的GradScaler。

**Q5: 三招能不能叠加使用？**

可以而且应该叠加。三者优化的是显存的不同部分：混合精度优化参数和激活值的精度，梯度累积优化batch大小，梯度检查点优化激活值的存储。互不冲突。
