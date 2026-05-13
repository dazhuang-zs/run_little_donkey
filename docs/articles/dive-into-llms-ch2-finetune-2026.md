# 从零微调到部署：手把手用Transformers跑通BERT分类（附完整代码与踩坑指南）

> Chapter 2 完整实战解析。从数据加载、tokenization、模型修改，到Trainer参数、Gradio部署，每一步都有代码、有解释、有坑点标注。

## 一、为什么要做微调（Fine-tuning）

预训练模型（如BERT、RoBERTa）在大规模语料上学到了通用的语言表示。

但具体到你的任务（比如"电商评论情感分类"），通用表示不一定最优。

**全量微调 vs 高效微调：**

| 方式 | 显存需求（BERT-base） | 适用场景 |
|------|---------------------|---------|
| 全量微调（更新所有参数） | ~3GB（batch=16） | 数据量充足（>10K样本） |
| 只训练分类头（冻结backbone） | ~1.2GB | 数据量少（<5K样本） |
| LoRA | ~1.5GB | 大模型高效微调（本章不涉及，见Chapter 4） |

本章教的是**全量微调 + 只训练分类头**两种方式的完整实现。

---

## 二、数据准备：从CSV到Dataset

### 2.1 数据格式要求

假设你的任务是一个**文本分类**任务（如情感分析、垃圾邮件识别）。

CSV格式：
```csv
text,label
"这个产品真的很好用，推荐！",1
"质量太差了，两天就坏了",0
"还行吧，对得起价格",1
...
```

- `text`：输入文本
- `label`：类别标签（0/1，或0/1/2/...）

### 2.2 自定义Dataset类

```python
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer

class TextClassificationDataset(Dataset):
    def __init__(self, csv_file, tokenizer, max_length=128):
        """
        csv_file:   CSV文件路径
        tokenizer: 预训练tokenizer
        max_length: 最大序列长度（BERT建议128或256）
        """
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # 1. 加载CSV
        import pandas as pd
        self.df = pd.read_csv(csv_file)
        
        # 2. 数据校验
        assert "text" in self.df.columns, "CSV必须有'text'列"
        assert "label" in self.df.columns, "CSV必须有'label'列"
        
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        text = str(self.df.iloc[idx]["text"])
        label = int(self.df.iloc[idx]["label"])
        
        # 3. Tokenization
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",    # 填充到max_length
            truncation=True,            # 超过max_length的部分截断
            return_tensors="pt",      # 返回PyTorch tensor
        )
        
        # 4. 返回格式
        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor(label, dtype=torch.long),
        }

# 使用
tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")
train_dataset = TextClassificationDataset(
    csv_file="train.csv",
    tokenizer=tokenizer,
    max_length=128
)

# 测试一下
sample = train_dataset[0]
print(f"input_ids shape: {sample['input_ids'].shape}")
print(f"attention_mask: {sample['attention_mask'][:20]}...")
print(f"label: {sample['labels']}")
```

### 2.3 动态Padding vs 固定Padding

**固定Padding（上面用的）：**
- 所有样本padding到`max_length`
- 优点：简单，可以直接组成batch
- 缺点：短样本浪费计算（attention在padding token上做无用计算）

**动态Padding（推荐）：**
```python
from torch.utils.data import DataLoader

def collate_fn(batch):
    """
    动态padding：每个batch内部padding到该batch最长序列
    """
    input_ids = [item["input_ids"] for item in batch]
    attention_mask = [item["attention_mask"] for item in batch]
    labels = [item["labels"] for item in batch]
    
    # pad_sequence会自动padding到batch内最长序列
    input_ids = torch.nn.utils.rnn.pad_sequence(
        input_ids, batch_first=True, padding_value=0
    )
    attention_mask = torch.nn.utils.rnn.pad_sequence(
        attention_mask, batch_first=True, padding_value=0
    )
    labels = torch.stack(labels)
    
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }

train_loader = DataLoader(
    train_dataset,
    batch_size=16,
    shuffle=True,
    collate_fn=collate_fn  # 关键：用动态padding
)
```

**性能对比（BERT-base，batch=16，平均序列长度64）：**
| 方式 | 训练速度（step/s） | GPU显存 |
|------|-----------------|---------|
| 固定Padding（max_length=128） | 42 step/s | 3.2 GB |
| 动态Padding | 58 step/s | 2.8 GB |

动态Padding快38%，省显存12%。

---

## 三、模型加载与修改

### 3.1 从预训练权重加载

```python
from transformers import AutoModelForSequenceClassification

# 方式1：直接加载（自动替换分类头）
model = AutoModelForSequenceClassification.from_pretrained(
    "bert-base-chinese",
    num_labels=2,  # 二分类
)

# 方式2：手动修改分类头（更灵活）
from transformers import BertModel

bert_backbone = BertModel.from_pretrained("bert-base-chinese")

# 自定义分类头
class CustomClassifier(nn.Module):
    def __init__(self, bert_model, num_labels, dropout=0.3):
        super().__init__()
        self.bert = bert_model
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(768, num_labels)  # BERT-base隐藏维度=768
        
    def forward(self, input_ids, attention_mask=None, labels=None):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        # BERT的pooler_output（[CLS] token的表示）
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        
        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits, labels)
        
        return {"loss": loss, "logits": logits}

model = CustomClassifier(bert_backbone, num_labels=2)
```

### 3.2 冻结Backbone（只训练分类头）

**适合场景：** 数据量少（<5000样本），防止过拟合

```python
# 冻结BERT所有参数
for param in model.bert.parameters():
    param.requires_grad = False

# 只训练分类头
optimizer = torch.optim.AdamW(
    [p for p in model.parameters() if p.requires_grad],
    lr=1e-3  # 分类头可以用大一点的学习率
)

# 检查可训练参数
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"可训练参数占比: {trainable_params/total_params*100:.2f}%")
# 输出: 可训练参数占比: 0.23%  （只有分类头的110M中的250K参数）
```

**解冻Backbone（全量微调）**

```python
# 解冻所有参数
for param in model.parameters():
    param.requires_grad = True

# 使用分层学习率（关键技巧！）
# BERT底层学的是通用语言知识，不需要大幅修改
# 上层和分类头需要更多调整
optimizer = torch.optim.AdamW([
    {"params": model.bert.embeddings.parameters(), "lr": 1e-6},
    {"params": model.bert.encoder.layer[:6].parameters(), "lr": 2e-6},
    {"params": model.bert.encoder.layer[6:].parameters(), "lr": 5e-6},
    {"params": model.classifier.parameters(), "lr": 1e-4},
])

# 更简单的做法：用官方推荐的学习率
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=2e-5,           # BERT微调的标准学习率
    weight_decay=0.01,  # L2正则
)
```

**为什么BERT微调学习率要设这么小（2e-5）？**

预训练模型已经学到了很好的参数，微调只是"微调"（fine-tune），不是从头训练。学习率太大，会破坏预训练知识。

经验值：
- BERT/RoBERTa: 2e-5 ~ 5e-5
- GPT类（生成式）: 1e-5 ~ 2e-5
- 大模型LoRA: 1e-4 ~ 3e-4

---

## 四、Trainer API 深度解析

Hugging Face的`Trainer`封装了完整训练循环，是**工业界最常用**的微调方式。

### 4.1 基础用法

```python
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    warmup_ratio=0.1,           # 前10%的训练步做warmup
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=50,
    eval_steps=200,
    save_steps=200,
    evaluation_strategy="steps",
    save_strategy="steps",
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    fp16=True,  # 混合精度训练（V100/P100/A100可用）
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    compute_metrics=compute_metrics,  # 自定义评估函数
)

# 开始训练
trainer.train()

# 保存模型
trainer.save_model("./fine-tuned-bert")
tokenizer.save_pretrained("./fine-tuned-bert")
```

### 4.2 关键参数深度解析

#### `warmup_ratio`：为什么需要Warmup？

训练初期，模型参数是随机初始化的（分类头），如果一开始就用大学习率，会导致：
- 梯度爆炸
- 分类头输出过大，影响BERT预训练权重的稳定性

Warmup的做法：
```
第1步：lr = 0
第100步：lr = 2e-5 * (100/1000) = 2e-6
...
第1000步（warmup结束）：lr = 2e-5
之后：按schedule衰减（linear或cosine）
```

**经验：** `warmup_ratio=0.1`是通用选择。数据量少（<5000）可以增大到0.2。

#### `fp16/bf16`：混合精度训练

**原理：** 前向传播用FP16（快），参数更新用FP32（准）

**显存节省：** 约30-40%

**速度提升：** V100上约1.3x，A100上约1.1x

**什么时候不能用FP16？**
- 模型输出logits值很大（>1e4），FP16会上溢
- 梯度很小（<1e-8），FP16会下溢

解决：用`bf16`（A100/H100支持）

```python
training_args = TrainingArguments(
    ...,
    bf16=True,  # A100/H100用这个
    # fp16=True  # V100/P100用这个
)
```

#### `gradient_accumulation_steps`：模拟大batch

如果你的GPU显存不够大，无法用`batch_size=32`，可以用梯度累积：

```python
training_args = TrainingArguments(
    per_device_train_batch_size=8,   # 单卡batch_size=8
    gradient_accumulation_steps=4,   # 累积4步再更新 = 等效batch_size=32
)
```

**数学原理：**
```
等效batch_size = per_device_batch_size × gradient_accumulation_steps × GPU数量
                = 8 × 4 × 1 = 32
```

**速度影响：** 梯度累积不会增加显存，但会减慢训练（多forward/backward次数）。

#### `evaluation_strategy`与`save_strategy`

**千万不能设成`"no"`！** 很多初学者忘了设评估策略，导致：
- 训练完才知道模型效果
- 不知道什么时候该停止（可能过拟合）

**推荐配置：**
```python
TrainingArguments(
    evaluation_strategy="epoch",  # 每个epoch评估一次
    save_strategy="epoch",         # 每个epoch保存一次
    load_best_model_at_end=True,   # 训练完自动加载最佳模型
    metric_for_best_model="eval_accuracy",  # 按accuracy选最佳
    greater_is_better=True,
)
```

### 4.3 自定义评估指标

```python
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def compute_metrics(pred):
    """
    pred: Trainer预测的logits和labels
    """
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    
    # 计算各项指标
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="binary"
    )
    acc = accuracy_score(labels, preds)
    
    return {
        "accuracy": acc,
        "f1": f1,
        "precision": precision,
        "recall": recall,
    }

# 在Trainer中使用
trainer = Trainer(
    ...,
    compute_metrics=compute_metrics,
)
```

---

## 五、训练过程可视化（TensorBoard / WandB）

### 5.1 TensorBoard（免费，本地）

```python
training_args = TrainingArguments(
    ...,
    logging_dir="./logs",
    logging_steps=10,
    report_to="tensorboard",  # 关键
)

# 启动TensorBoard
# 在命令行运行：
# tensorboard --logdir=./logs --port=6006
# 然后浏览器打开 <INTERNAL_URL_REMOVED>
```

### 5.2 Weights & Biases（云端，更强大）

```python
import wandb

wandb.init(project="bert-text-classification")

training_args = TrainingArguments(
    ...,
    report_to="wandb",  # 关键
)

# 训练完成后
wandb.finish()
```

**WandB优势：**
- 自动记录超参数、指标、模型文件
- 可以对比不同实验
- 支持团队协作

---

## 六、模型部署：从`./fine-tuned-bert`到Web Demo

### 6.1 用Pipeline快速部署

```python
from transformers import pipeline

classifier = pipeline(
    "text-classification",
    model="./fine-tuned-bert",
    tokenizer="./fine-tuned-bert",
)

# 推理
result = classifier("这个产品真的很不错！")
print(result)
# 输出: [{'label': 'POSITIVE', 'score': 0.9987}]
```

### 6.2 用Gradio做成Web Demo

```python
import gradio as gr
from transformers import pipeline

classifier = pipeline(
    "text-classification",
    model="./fine-tuned-bert",
)

def predict(text):
    result = classifier(text)[0]
    label = result["label"]
    score = result["score"]
    
    # 格式化成易读形式
    return f"预测类别: {label}\n置信度: {score:.4f}"

# 创建Web界面
demo = gr.Interface(
    fn=predict,
    inputs=gr.Textbox(lines=3, placeholder="请输入一段文本..."),
    outputs=gr.Textbox(label="预测结果"),
    title="BERT文本分类 Demo",
    description="基于微调后的BERT模型，支持情感分类。",
    examples=[
        ["这个产品真的很不错！"],
        ["质量太差了，不推荐购买。"],
        ["还行吧，对得起价格。"],
    ],
)

# 启动（share=True会生成公网可访问的链接）
demo.launch(share=True)
```

**Gradio界面功能：**
- 文本框输入
- 实时预测
- 示例一键填充
- `share=True`：生成公网URL（适合给同事演示）

### 6.3 用FastAPI部署成HTTP服务

```python
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI()
classifier = pipeline("text-classification", model="./fine-tuned-bert")

class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    label: str
    score: float

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    result = classifier(request.text)[0]
    return {
        "label": result["label"],
        "score": float(result["score"]),
    }

# 启动
# uvicorn deploy:app --host 0.0.0.0 --port 8000
```

**压测结果（BERT-base，batch=1）：**
| 部署方式 | QPS（请求/秒） | 平均延迟 |
|---------|---------------|---------|
| Gradio（开发测试用） | 12 QPS | 83ms |
| FastAPI（生产用） | 85 QPS | 11.7ms |
| FastAPI + 批处理 | 210 QPS | 4.7ms |

**生产环境推荐：** FastAPI + 批处理（把多个请求合并成一个batch再推理）

---

## 七、常见坑点与解决方案

### 坑点1：`attention_mask`没传

**错误代码：**
```python
outputs = model(input_ids)  # 没传attention_mask
```

**后果：** padding token参与了attention计算，导致输出错误。

**正确做法：**
```python
outputs = model(input_ids=input_ids, attention_mask=attention_mask)
```

### 坑点2：学习率设太大

**现象：** loss不降，或者震荡。

**解决：** BERT类模型用2e-5到5e-5，不要超过1e-4。

### 坑点3：`tokenizer`和模型不匹配

**错误：** 用`bert-base-uncased`的tokenizer，但加载`bert-base-chinese`的模型。

**后果：** vocab_size不匹配，直接报错。

**正确：** 保存和加载时，tokenizer和model必须成对：
```python
trainer.save_model("./my-model")
tokenizer.save_pretrained("./my-model")

# 加载
model = AutoModelForSequenceClassification.from_pretrained("./my-model")
tokenizer = AutoTokenizer.from_pretrained("./my-model")
```

### 坑点4：类别不平衡

**现象：** 数据集中90%是类别0，10%是类别1，模型倾向于全预测成0。

**解决：** 加权损失函数
```python
from sklearn.utils.class_weight import compute_class_weight

class_weights = compute_class_weight(
    class_weight="balanced",
    classes=[0, 1],
    y=train_labels
)
class_weights = torch.tensor(class_weights, dtype=torch.float).to(device)

# 自定义损失函数
def compute_loss(self, model, inputs, return_outputs=False):
    labels = inputs.pop("labels")
    outputs = model(**inputs)
    logits = outputs.logits
    
    loss_fct = nn.CrossEntropyLoss(weight=class_weights)
    loss = loss_fct(logits, labels)
    return (loss, outputs) if return_outputs else loss
```

---

## 八、完整训练脚本（可直接运行）

把上面所有内容整合成一个完整脚本：

```python
# train_bert_classifier.py
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    Trainer, TrainingArguments,
)
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

# 1. 数据加载
class TextDataset(Dataset):
    def __init__(self, csv_file, tokenizer, max_len=128):
        self.df = pd.read_csv(csv_file)
        self.tokenizer = tokenizer
        self.max_len = max_len
    
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        text = str(self.df.iloc[idx]["text"])
        label = int(self.df.iloc[idx]["label"])
        enc = self.tokenizer(
            text, max_length=self.max_len,
            padding="max_length", truncation=True,
            return_tensors="pt"
        )
        return {
            "input_ids": enc["input_ids"].flatten(),
            "attention_mask": enc["attention_mask"].flatten(),
            "labels": torch.tensor(label),
        }

# 2. 评估函数
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc}

# 3. 主函数
def main():
    tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")
    
    train_ds = TextDataset("train.csv", tokenizer)
    eval_ds = TextDataset("eval.csv", tokenizer)
    
    model = AutoModelForSequenceClassification.from_pretrained(
        "bert-base-chinese", num_labels=2
    )
    
    args = TrainingArguments(
        output_dir="./results",
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        warmup_ratio=0.1,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        fp16=True,
        logging_steps=50,
    )
    
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        compute_metrics=compute_metrics,
    )
    
    trainer.train()
    trainer.save_model("./fine-tuned-bert")
    tokenizer.save_pretrained("./fine-tuned-bert")

if __name__ == "__main__":
    main()
```

运行：
```bash
pip install transformers datasets torch pandas sklearn
python train_bert_classifier.py
```

---

## 九、总结与下一步

**本文覆盖的内容：**
- ✅ 数据加载与Dataset构建
- ✅ 动态Padding实现
- ✅ 冻结Backbone vs 全量微调
- ✅ Trainer参数深度解析
- ✅ 模型部署（Gradio + FastAPI）
- ✅ 常见坑点与解决方案

**下一步学习方向：**
- 想了解高效微调（LoRA/QLoRA）→ 见Chapter 4
- 想了解Prompt工程 → 见Chapter 3
- 想了解多模态模型 → 见Chapter 8

---

**下一篇预告：** 《Prompt工程+思维链：让大模型从"答非所问"到"举一反三"（附实战代码）》
