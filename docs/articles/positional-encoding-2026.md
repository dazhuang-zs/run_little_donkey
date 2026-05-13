# 位置编码详解：从Sinusoidal到RoPE到ALiBi，三分钟搞懂Transformer怎么记住顺序

> Transformer本身没有顺序概念，"我爱你"和"你爱我"对它来说一模一样。位置编码就是教它分辨顺序的技术。本文从三种主流编码的原理推导到代码实现，彻底讲透。

## 一、为什么需要位置编码

Transformer的核心操作是自注意力：

$$\text{Attention}(Q, K, V) = \text{softmax}(QK^T / \sqrt{d})V$$

这个操作是**置换不变的**（permutation invariant）。把输入token的顺序打乱，输出的注意力权重只是重排了行和列，数值完全一样。

换句话说，对Transformer来说：
- "我 爱 你" → 注意力矩阵A
- "你 爱 我" → 注意力矩阵A'（只是A的行重排，注意力模式完全相同）

这显然不对。位置编码就是在每个token的嵌入向量上加上一个"位置信号"，让模型知道每个token在第几个位置。

## 二、Sinusoidal位置编码：Transformer原版

### 2.1 公式

这是2017年原版Transformer论文的方案：

$$PE_{(pos, 2i)} = \sin(pos / 10000^{2i/d})$$
$$PE_{(pos, 2i+1)} = \cos(pos / 10000^{2i/d})$$

其中：
- $pos$ 是token的位置（0, 1, 2, ...）
- $i$ 是嵌入维度的索引
- $d$ 是嵌入维度

### 2.2 为什么这么设计

两个关键性质：

**性质1：任意固定偏移的位置编码可以通过线性变换得到**

$$PE_{(pos+k)} = T_k \cdot PE_{(pos)}$$

其中 $T_k$ 是一个由 $\sin$ 和 $\cos$ 组成的旋转矩阵。这意味着模型可以通过学习一个线性变换来捕捉相对位置关系。

**性质2：不同维度的频率不同**

低维度（小i）的频率高，变化快，捕捉局部位置关系；高维度（大i）的频率低，变化慢，捕捉全局位置关系。这类似于傅里叶变换，用不同频率的基函数来编码位置。

### 2.3 代码实现

```python
import torch
import math

def sinusoidal_position_encoding(max_len, d_model):
    """生成Sinusoidal位置编码"""
    pe = torch.zeros(max_len, d_model)
    position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
    div_term = torch.exp(
        torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
    )
    pe[:, 0::2] = torch.sin(position * div_term)  # 偶数维度
    pe[:, 1::2] = torch.cos(position * div_term)  # 奇数维度
    return pe  # [max_len, d_model]

# 使用
pe = sinusoidal_position_encoding(max_len=512, d_model=768)
x = token_embedding + pe[:seq_len]  # 加在token嵌入上
```

**问题**：Sinusoidal是**绝对位置编码**，加在输入上，经过多层自注意力后位置信息会逐渐模糊。对短序列够用，长序列外推能力差。

## 三、RoPE：旋转位置编码（当前主流）

### 3.1 核心思想

RoPE（Rotary Position Embedding）不把位置信息加在输入上，而是**把位置信息融入Q和K的点积中**，让注意力权重自然反映相对位置。

目标是让注意力得分只依赖于两个token的**相对位置**（$m - n$），而不是绝对位置：

$$\langle q_m, k_n \rangle = f(m - n)$$

### 3.2 数学推导

考虑2维情况（d=2），Q和K都是2维向量：

$$q_m = \begin{pmatrix} q_0 \\ q_1 \end{pmatrix}, \quad k_n = \begin{pmatrix} k_0 \\ k_1 \end{pmatrix}$$

对q施加位置m的旋转：

$$\hat{q}_m = \begin{pmatrix} \cos m\theta & -\sin m\theta \\ \sin m\theta & \cos m\theta \end{pmatrix} \begin{pmatrix} q_0 \\ q_1 \end{pmatrix}$$

对k施加位置n的旋转（角度不同）：

$$\hat{k}_n = \begin{pmatrix} \cos n\theta & -\sin n\theta \\ \sin n\theta & \cos n\theta \end{pmatrix} \begin{pmatrix} k_0 \\ k_1 \end{pmatrix}$$

点积：

$$\hat{q}_m \cdot \hat{k}_n = q_0 k_0 \cos(m-n)\theta + q_1 k_1 \cos(m-n)\theta + ...$$

**结果**：点积只依赖相对位置 $(m-n)$！这正是我们想要的。

推广到高维：将d维向量两两分组，每组用不同的 $\theta_i$ 旋转：

$$\theta_i = 10000^{-2i/d}, \quad i = 0, 1, 2, ..., d/2-1$$

### 3.3 代码实现

```python
import torch
import torch.nn as nn
import math

class RotaryEmbedding(nn.Module):
    def __init__(self, dim, max_seq_len=8192):
        super().__init__()
        # 计算每组的旋转角度
        inv_freq = 1.0 / (10000 ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)
        
        # 预计算所有位置的cos和sin
        t = torch.arange(max_seq_len).float()
        freqs = torch.outer(t, inv_freq)  # [max_seq_len, dim/2]
        self.register_buffer('cos_cached', freqs.cos())  # [max_seq_len, dim/2]
        self.register_buffer('sin_cached', freqs.sin())  # [max_seq_len, dim/2]
    
    def forward(self, seq_len):
        return self.cos_cached[:seq_len], self.sin_cached[:seq_len]

def apply_rotary_emb(x, cos, sin):
    """对x应用旋转位置编码
    x: [batch, heads, seq_len, dim]
    cos/sin: [seq_len, dim/2]
    """
    # 把x拆成两两一组
    d = x.shape[-1]
    x1, x2 = x[..., :d//2], x[..., d//2:]
    
    # 扩展维度以匹配
    cos = cos.unsqueeze(0).unsqueeze(0)  # [1, 1, seq_len, dim/2]
    sin = sin.unsqueeze(0).unsqueeze(0)
    
    # 旋转
    out1 = x1 * cos - x2 * sin
    out2 = x1 * sin + x2 * cos
    
    return torch.cat([out1, out2], dim=-1)

# 使用
rope = RotaryEmbedding(dim=64, max_seq_len=2048)
cos, sin = rope(seq_len=128)
q_rotated = apply_rotary_emb(q, cos, sin)
k_rotated = apply_rotary_emb(k, cos, sin)
```

### 3.4 RoPE的优势

1. **相对位置编码**：注意力权重只依赖相对位置，天然支持平移不变性
2. **乘法融合**：位置信息通过旋转矩阵乘法融入Q和K，不是简单加法，信息保持更好
3. **远程衰减**：相对距离越远，点积越小，符合直觉（距离远的token关联度通常低）

**使用者**：LLaMA、Mistral、Qwen、DeepSeek等几乎所有2023年以后的模型。

### 3.5 RoPE的问题：长度外推

RoPE在训练长度内表现很好，但超过训练长度后性能急剧下降。原因：训练时模型没见过更大位置的旋转角度，无法泛化。

解决方案（NTK-aware Scaling）：

```python
def ntk_aware_rope(dim, max_seq_len, base=10000, scale=1.0):
    """NTK-aware缩放的RoPE，支持更长序列"""
    # 调整base来扩展频率范围
    new_base = base * (scale ** (dim / (dim - 2)))
    inv_freq = 1.0 / (new_base ** (torch.arange(0, dim, 2).float() / dim))
    # ... 其余同上
```

## 四、ALiBi：不用位置编码的位置编码

### 4.1 核心思想

ALiBi（Attention with Linear Biases）的做法更极端：**不加任何位置编码到输入上**，而是在注意力分数上直接减去一个与距离成正比的偏置。

$$\text{attention}(q_i, k_j) = q_i \cdot k_j - m \cdot |i - j|$$

其中 $m$ 是一个可调的斜率（不同注意力头用不同的斜率）。

### 4.2 为什么有效

- 距离越远的token，注意力分数被减去的值越大，受到的"惩罚"越重
- 这直接编码了"近处token更重要"的先验
- 斜率 $m$ 按几何级数从 $2^{-8}$ 到 $2^{0}$ 分配给不同注意力头

### 4.3 代码实现

```python
import torch
import torch.nn as nn
import math

class ALiBiAttention(nn.Module):
    def __init__(self, num_heads, head_dim):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = head_dim
        
        # 每个头的斜率：几何级数 2^(-8/n), 2^(-16/n), ...
        # n是头的编号
        slopes = 2 ** (-8 * torch.arange(1, num_heads + 1) / num_heads)
        self.register_buffer('slopes', slopes)
    
    def forward(self, q, k, v):
        """
        q, k, v: [batch, heads, seq_len, head_dim]
        """
        seq_len = q.size(2)
        
        # 计算标准注意力分数
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        # [batch, heads, seq_len, seq_len]
        
        # 生成距离矩阵
        positions = torch.arange(seq_len, device=q.device)
        distance = positions.unsqueeze(0) - positions.unsqueeze(1)  # [seq_len, seq_len]
        distance = distance.abs()  # 取绝对值
        
        # ALiBi偏置：每个头有不同的斜率
        # slopes: [heads] → 扩展为 [1, heads, seq_len, seq_len]
        alibi_bias = -self.slopes.view(1, -1, 1, 1) * distance.unsqueeze(0).unsqueeze(0)
        
        # 加上因果mask
        causal_mask = torch.triu(
            torch.ones(seq_len, seq_len, device=q.device), diagonal=1
        ).bool()
        alibi_bias.masked_fill_(causal_mask.unsqueeze(0).unsqueeze(0), float('-inf'))
        
        scores = scores + alibi_bias
        attn = torch.softmax(scores, dim=-1)
        
        return torch.matmul(attn, v)
```

### 4.4 ALiBi的优势

1. **零额外参数**：不加位置编码，不加可学习参数
2. **长度外推极强**：训练时用1024长度，推理时直接用2048甚至更长，性能几乎不降
3. **实现简单**：只需在注意力分数上加一个线性偏置

**使用者**：BLOOM、MPT、Baichuan等。

## 五、三种编码对比

| 特性 | Sinusoidal | RoPE | ALiBi |
|------|-----------|------|-------|
| 位置类型 | 绝对 | 相对 | 相对 |
| 融入方式 | 加在输入上 | 乘在Q/K上 | 加在注意力分数上 |
| 长度外推 | 差 | 中（需NTK扩展） | **强** |
| 实现复杂度 | 低 | 中 | 低 |
| 主流模型 | 原版Transformer | LLaMA/Mistral/Qwen | BLOOM/MPT |
| 远程衰减 | 无 | 天然有 | 人为设定 |

**2026年现状**：RoPE是绝对主流（因为性能最好），ALiBi在长序列场景有优势，Sinusoidal基本淘汰。

## 六、面试高频问题

**Q1: 为什么RoPE比绝对位置编码好？**

绝对位置编码是加在输入上的，经过多层自注意力后位置信息会被稀释。RoPE通过旋转矩阵把位置信息融入Q和K的关系中，每一层都会重新应用，位置信息不会丢失。此外，RoPE编码的是相对位置，天然支持平移不变性。

**Q2: RoPE的长度外推问题怎么解决？**

三种主流方案：1) Position Interpolation（位置插值）：把长序列的位置压缩到训练长度内；2) NTK-aware Scaling：调整RoPE的base频率，让高频分量保持不变；3) YaRN：结合前两者，分别处理高频和低频分量。目前YaRN效果最好。

**Q3: ALiBi为什么外推能力强？**

ALiBi的偏置只依赖相对距离，跟绝对位置无关。推理时无论序列多长，偏置只是距离乘以斜率，计算方式和训练时完全一致，不需要外推到未见过的位置。

**Q4: 为什么不同注意力头用不同的ALiBi斜率？**

不同头关注不同粒度的信息。斜率大的头（近处惩罚重）关注局部模式，斜率小的头关注全局模式。这种多粒度设计让模型同时捕捉局部和全局关系。

**Q5: RoPE的远程衰减是什么意思？**

RoPE点积的期望值随相对距离增大而减小。这是因为旋转角度的差异越大，两个旋转后的向量点积越小。这符合语言直觉：距离远的token关联度通常更低。
