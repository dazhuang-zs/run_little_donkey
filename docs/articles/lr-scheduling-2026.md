# 学习率调度全解析：Warmup + Cosine Decay + 1Cycle，为什么你的模型训不好

> 训练loss下不去、验证loss飙升、收敛太慢，90%的锅在学习率。本文用6种调度器的原理推导 + PyTorch实战代码 + 对比实验，帮你彻底搞懂怎么选学习率策略。

## 一、为什么学习率这么难调

学习率是训练中最敏感的超参数。太大，梯度爆炸、loss震荡；太小，收敛慢、卡在局部最优。

想象你从山顶下山找最低点：
- 学习率太大 = 每步跨太远，在谷底来回跳，永远下不去
- 学习率太小 = 每步挪一毫米，下山要走到天荒地老
- 好的策略 = 先大步快走（快速接近谷底），再小步精调（精准找到最低点）

这就是**学习率调度**的核心思想：训练过程中动态调整学习率。

## 二、6种主流调度器详解

### 2.1 StepLR：阶梯衰减

最朴素的做法，每隔固定步数把学习率乘以一个衰减因子。

```python
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.1)
# 效果：前30个epoch lr=0.1，30-60 epoch lr=0.01，60-90 epoch lr=0.001
```

**问题**：衰减时刻是人工定的，很难恰好踩在最优时机。衰减瞬间loss会突然跳升。

### 2.2 ExponentialLR：指数衰减

每一步都衰减一点点，曲线更平滑。

```python
scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.95)
# 每个epoch: lr = lr * 0.95
# 100个epoch后: lr = 0.1 * 0.95^100 ≈ 0.00059
```

**问题**：后期学习率衰减太慢，浪费训练时间。适合训练初期快速探索的场景。

### 2.3 CosineAnnealingLR：余弦退火

这是目前**最主流**的调度策略，几乎所有大模型都在用。

数学公式：

$$\eta_t = \eta_{min} + \frac{1}{2}(\eta_{max} - \eta_{min})(1 + \cos(\frac{t}{T}\pi))$$

其中 $t$ 是当前步数，$T$ 是总步数。

核心特点：
- 前期学习率下降慢（大步探索）
- 中期加速下降
- 后期下降又变慢（精细调整）
- 整体曲线像半个余弦波，非常平滑

```python
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer, T_max=100, eta_min=1e-6
)
```

**为什么有效**：前期的"慢衰减"保留了足够的探索能力，后期的"慢衰减"保证了收敛精度。中间的快速过渡恰好匹配了训练从"探索"到"利用"的转换。

### 2.4 Warmup + Cosine Decay：大模型标配

直接用大学习率开始训练，模型参数还是随机初始化的，梯度方向不稳定，容易崩。Warmup的核心思想：**先热身，再冲刺**。

```
阶段1 (Warmup): lr从0线性增长到目标值，比如前1000步
阶段2 (Cosine Decay): lr按余弦曲线从目标值衰减到接近0
```

这就是GPT、LLaMA、Mistral等所有主流大模型的训练策略。

```python
from torch.optim.lr_scheduler import LambdaLR
import math

def get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps):
    def lr_lambda(current_step):
        # Warmup阶段：线性增长
        if current_step < warmup_steps:
            return float(current_step) / float(max(1, warmup_steps))
        # Cosine Decay阶段
        progress = float(current_step - warmup_steps) / float(
            max(1, total_steps - warmup_steps)
        )
        return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))
    
    return LambdaLR(optimizer, lr_lambda)

# 使用
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
scheduler = get_cosine_schedule_with_warmup(
    optimizer, warmup_steps=1000, total_steps=100000
)
```

**Warmup为什么有效**：
1. 训练初期参数随机，梯度方向不稳定，大学习率会导致参数更新幅度过大
2. Warmup期间梯度统计量（Adam的一阶/二阶矩）逐渐稳定
3. 等统计量稳定后，再用大学习率才安全

**经验值**：
- GPT-3: warmup = 总步数的0.2%
- LLaMA: warmup = 2000步
- 一般经验: warmup步数 = 总步数的1%-5%

### 2.5 1Cycle：超级收敛

1Cycle是一个被低估的策略，能在更少的epoch里达到更高的精度。

核心思想：学习率走一个完整的周期——先升后降，再升一点点。

```
阶段1: lr从低到高（探索阶段）
阶段2: lr从高到低（精细调整）
阶段3: lr再小幅上升一点点（跳出局部最优）
```

```python
scheduler = torch.optim.lr_scheduler.OneCycleLR(
    optimizer,
    max_lr=0.01,           # 峰值学习率
    total_steps=1000,      # 总步数
    pct_start=0.3,         # 前30%步数用于warmup
    anneal_strategy='cos', # 退火策略用余弦
    final_div_factor=100,  # 最终lr = max_lr / 100
)
```

**为什么叫"超级收敛"**：Leslie Smith的论文证明，1Cycle配合大学习率，可以在5个epoch内达到原来20个epoch的精度。原因是中间的"大学习率"阶段起到了正则化的作用，帮助模型跳出尖锐的局部最优，找到更平坦的最优解。

### 2.6 ReduceLROnPlateau：自适应衰减

不按固定规则衰减，而是根据验证loss的表现来决定。

```python
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.5, patience=5
)
# 验证loss连续5个epoch不下降，就把lr减半
```

**适用场景**：小模型微调、不确定最优训练时长时。缺点是依赖验证集评估，每次评估有额外开销。

## 三、PyTorch实战对比

下面用同一个模型对比不同调度器的效果：

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import (
    StepLR, ExponentialLR, CosineAnnealingLR,
    OneCycleLR, ReduceLROnPlateau, LambdaLR
)
import math

# 简单分类模型
class SimpleModel(nn.Module):
    def __init__(self, input_dim=784, hidden_dim=256, num_classes=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, num_classes)
        )
    def forward(self, x):
        return self.net(x)

# 生成模拟数据
def generate_data(n_samples=5000, input_dim=784, num_classes=10):
    X = torch.randn(n_samples, input_dim)
    y = torch.randint(0, num_classes, (n_samples,))
    return X, y

# 训练函数
def train_model(scheduler_name, model, X, y, epochs=50, lr=0.1):
    optimizer = optim.SGD(model.parameters(), lr=lr, momentum=0.9)
    criterion = nn.CrossEntropyLoss()
    
    total_steps = epochs * (len(X) // 64)
    
    # 创建调度器
    if scheduler_name == 'Step':
        scheduler = StepLR(optimizer, step_size=15, gamma=0.1)
    elif scheduler_name == 'Exponential':
        scheduler = ExponentialLR(optimizer, gamma=0.95)
    elif scheduler_name == 'Cosine':
        scheduler = CosineAnnealingLR(optimizer, T_max=epochs)
    elif scheduler_name == 'WarmupCosine':
        scheduler = get_cosine_schedule_with_warmup(
            optimizer, warmup_steps=total_steps // 10, total_steps=total_steps
        )
    elif scheduler_name == '1Cycle':
        scheduler = OneCycleLR(
            optimizer, max_lr=lr, total_steps=total_steps, pct_start=0.3
        )
    
    losses = []
    lrs = []
    
    for epoch in range(epochs):
        epoch_loss = 0
        for i in range(0, len(X), 64):
            batch_X = X[i:i+64]
            batch_y = y[i:i+64]
            
            optimizer.zero_grad()
            output = model(batch_X)
            loss = criterion(output, batch_y)
            loss.backward()
            optimizer.step()
            
            if scheduler_name == '1Cycle' or scheduler_name == 'WarmupCosine':
                scheduler.step()
            
            epoch_loss += loss.item()
            lrs.append(optimizer.param_groups[0]['lr'])
        
        if scheduler_name not in ['1Cycle', 'WarmupCosine']:
            scheduler.step()
        
        avg_loss = epoch_loss / (len(X) // 64)
        losses.append(avg_loss)
    
    return losses, lrs

# 运行对比
X, y = generate_data()
results = {}

for name in ['Step', 'Exponential', 'Cosine', 'WarmupCosine', '1Cycle']:
    model = SimpleModel()
    losses, lrs = train_model(name, model, X, y)
    results[name] = {'losses': losses, 'lrs': lrs, 'final_loss': losses[-1]}

# 输出对比
print(f"{'调度器':<15} {'最终Loss':<12}")
print("-" * 27)
for name, data in sorted(results.items(), key=lambda x: x[1]['final_loss']):
    print(f"{name:<15} {data['final_loss']:<12.4f}")
```

## 四、对比总结

| 调度器 | 收敛速度 | 最终精度 | 超参数难度 | 适用场景 |
|--------|---------|---------|-----------|---------|
| StepLR | 中 | 中 | 需要调step_size | 简单任务、快速验证 |
| ExponentialLR | 快（前期） | 中低 | 只需调gamma | 短训练、快速实验 |
| CosineAnnealingLR | 快 | 高 | 只需T_max | 通用、CV任务 |
| **Warmup+Cosine** | **快** | **最高** | **warmup步数** | **大模型训练标配** |
| 1Cycle | **最快** | 高 | max_lr关键 | 小模型、少epoch |
| ReduceLROnPlateau | 慢 | 高 | patience敏感 | 微调、不确定训练时长 |

## 五、面试高频问题

**Q1: 为什么大模型训练必须用Warmup？**

训练初期参数随机，梯度方向不稳定。Adam优化器的二阶矩（梯度平方的指数移动平均）需要一定步数才能收敛到稳定值。如果一开始就用大学习率，不稳定的梯度统计量会导致参数更新方向错误，甚至梯度爆炸。Warmup给了统计量稳定的时间。

**Q2: Cosine Decay比Step Decay好在哪里？**

Step Decay在衰减瞬间会导致loss突然跳升（因为学习率突然变小10倍，模型需要重新适应）。Cosine Decay是平滑过渡，不会产生这种冲击。此外，Cosine Decay前期的"慢衰减"保留了探索能力，后期的"慢衰减"保证了精度。

**Q3: 1Cycle为什么能实现超级收敛？**

1Cycle中间的大学习率阶段起到了隐式正则化的作用。大学习率让模型跳出尖锐的局部最优，找到更平坦的最优解。平坦最优解的泛化能力更强，所以测试精度更高。

**Q4: Warmup步数怎么定？**

经验值：总步数的1%-5%。GPT-3用0.2%（因为总步数极大），LLaMA用2000步。如果训练初期loss不降反升，增大warmup；如果收敛太慢，减小warmup。

**Q5: 学习率初始值怎么选？**

- Adam/AdamW: 1e-4 到 5e-4（大模型通常3e-4）
- SGD+Momentum: 0.1 到 0.01
- 更好的方法：用LR Range Test，从小到大线性增长lr，画loss曲线，选loss下降最快的区域
