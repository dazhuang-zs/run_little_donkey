# 模型微调实战：从原理到生产级落地的完整指南

> **阅读时间**：约40分钟 | **代码环境**：Python 3.10+ / PyTorch 2.x / transformers 4.40+ / peft 0.10+
>
> **核心观点**：微调不是"把数据丢进去跑一圈"，而是数据工程 + 训练策略 + 评估体系的系统工程。90%的微调项目失败，不是模型不行，是数据和流程有问题。

---

## 一、微调到底是什么

### 1.1 一句话说清楚

微调 = 拿一个已经训练好的大模型，用你自己的数据再训练一下，让它更适合你的任务。

```
预训练（Pre-training）         微调（Fine-tuning）
─────────────────────────    ─────────────────────────
海量数据（TB级）              你的数据（MB~GB级）
通用能力                      专项能力
成本：百万美元级               成本：几十~几千元
时间：几个月                   时间：几十分钟~几天
模型：GPT-4、Qwen2.5等       模型：你的垂直模型
```

### 1.2 为什么要微调

很多人问："直接用 Prompt 不行吗？"

| 场景 | Prompt 能解决 | 微调才能解决 |
|------|:---:|:---:|
| 简单格式转换 | ✅ | ❌ |
| 单次任务指令 | ✅ | ❌ |
| 风格模仿（几条示例） | ✅ | ❌ |
| 行业术语理解 | ❌ | ✅ |
| 特定输出格式（每次都一样） | ❌ | ✅ |
| 减少推理成本（小模型替代大模型） | ❌ | ✅ |
| 私有知识注入 | ❌ | ✅ |

**关键判断标准**：如果 Prompt 写了 2000 字还搞不定，就该微调了。

### 1.3 微调的三种路线

```
全量微调（Full Fine-tuning）
├── 更新所有参数
├── 效果最好
├── 显存需求最大（7B模型需要约 60GB+）
└── 适合：数据充足、效果优先

参数高效微调（PEFT / LoRA）
├── 只更新少量参数（0.1%~1%）
├── 效果接近全量微调
├── 显存需求小（7B模型约 16GB）
└── 适合：大多数项目（推荐）

量化微调（QLoRA）
├── 先量化再 LoRA
├── 显存需求最小（7B模型约 8GB）
├── 效果略有损失
└── 适合：显存不足的情况
```

---

## 二、项目实战：从零到生产的完整流程

### 2.1 完整流程图

```
需求分析 → 数据准备 → 数据格式化 → 基座模型选择 → 训练配置 → 训练 → 评估 → 部署
   │           │           │              │             │         │       │       │
   │           │           │              │             │         │       │       │
   ▼           ▼           ▼              ▼             ▼         ▼       ▼       ▼
 什么任务？   数据从哪来？  什么格式？     多大模型？    超参？    跑多久？ 达标？  怎么用？
 分类/生成/   爬虫/人工/   Alpaca/        1.8B/7B/     lr/epoch  监控    自动化  vLLM/
 抽取/对话    已有积累     ShareGPT       14B/72B      /batch           评估    TGI
```

### 2.2 第一步：需求分析（最容易被跳过）

**在动手之前，先回答这四个问题**：

```python
class FineTuningRequirement:
    """微调需求分析检查清单"""
    
    def __init__(self):
        self.checklist = {
            "任务类型": None,        # 分类 / 生成 / 抽取 / 对话
            "成功标准": None,        # 准确率 > 90%？BLEU > 60？
            "数据量": None,          # 至少需要 500 条高质量数据
            "是否真的需要微调": None  # Prompt 能不能解决？
        }
    
    def evaluate(self) -> dict:
        """评估是否需要微调"""
        
        checks = []
        
        # 检查1：Prompt 是否能解决
        if self.checklist["是否真的需要微调"] == False:
            return {"recommendation": "先尝试 Prompt Engineering + Few-shot"}
        
        # 检查2：数据量是否足够
        data_count = self.checklist["数据量"] or 0
        if data_count < 100:
            checks.append("❌ 数据不足100条，微调效果不可靠")
        elif data_count < 500:
            checks.append("⚠️ 数据100-500条，建议用 LoRA + 低学习率")
        else:
            checks.append("✅ 数据充足，可以放心微调")
        
        # 检查3：评估标准是否明确
        if not self.checklist["成功标准"]:
            checks.append("❌ 没有明确的成功标准，无法判断微调是否有效")
        
        return {
            "recommendation": "建议微调" if len([c for c in checks if "❌" in c]) == 0 else "先解决问题",
            "checks": checks
        }


# 使用示例
req = FineTuningRequirement()
req.checklist = {
    "任务类型": "抽取",
    "成功标准": "F1 > 0.85",
    "数据量": 2000,
    "是否真的需要微调": True
}
print(req.evaluate())
# {'recommendation': '建议微调', 'checks': ['✅ 数据充足，可以放心微调']}
```

### 2.3 第二步：数据准备（决定微调成败的 90%）

**数据质量 > 数据数量**。1000 条高质量数据 > 10000 条垃圾数据。

```python
import json
import random
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class FineTuningDataProcessor:
    """微调数据处理器"""
    
    input_file: str
    output_file: str
    format_type: str = "alpaca"  # alpaca / sharegpt / instruction
    
    # 数据质量阈值
    min_input_length: int = 10
    max_input_length: int = 2048
    min_output_length: int = 5
    max_output_length: int = 4096
    deduplicate: bool = True
    
    def load_data(self) -> List[Dict]:
        """加载数据"""
        with open(self.input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    
    def validate_sample(self, sample: Dict) -> tuple[bool, str]:
        """验证单条数据质量"""
        
        instruction = sample.get("instruction", "")
        output = sample.get("output", "")
        
        if len(instruction) < self.min_input_length:
            return False, "指令过短"
        if len(instruction) > self.max_input_length:
            return False, "指令过长"
        if len(output) < self.min_output_length:
            return False, "输出过短"
        if len(output) > self.max_output_length:
            return False, "输出过长"
        if instruction == output:
            return False, "输入输出相同"
        
        return True, "通过"
    
    def process(self) -> Dict:
        """处理数据，返回统计信息"""
        
        raw_data = self.load_data()
        valid_data = []
        invalid_count = {}
        
        for sample in raw_data:
            is_valid, reason = self.validate_sample(sample)
            if is_valid:
                valid_data.append(sample)
            else:
                invalid_count[reason] = invalid_count.get(reason, 0) + 1
        
        # 去重
        if self.deduplicate:
            seen = set()
            deduped = []
            for sample in valid_data:
                key = sample["instruction"] + sample.get("input", "")
                if key not in seen:
                    seen.add(key)
                    deduped.append(sample)
            valid_data = deduped
        
        # 格式转换
        formatted = []
        for sample in valid_data:
            if self.format_type == "alpaca":
                formatted.append({
                    "instruction": sample["instruction"],
                    "input": sample.get("input", ""),
                    "output": sample["output"]
                })
            elif self.format_type == "sharegpt":
                formatted.append({
                    "conversations": [
                        {"from": "human", "value": sample["instruction"]},
                        {"from": "gpt", "value": sample["output"]}
                    ]
                })
        
        # 划分训练集/验证集
        random.shuffle(formatted)
        split_idx = int(len(formatted) * 0.9)
        train_data = formatted[:split_idx]
        val_data = formatted[split_idx:]
        
        # 保存
        Path(self.output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(train_data, f, ensure_ascii=False, indent=2)
        
        val_file = self.output_file.replace(".json", "_val.json")
        with open(val_file, "w", encoding="utf-8") as f:
            json.dump(val_data, f, ensure_ascii=False, indent=2)
        
        return {
            "raw_count": len(raw_data),
            "valid_count": len(valid_data),
            "invalid_reasons": invalid_count,
            "train_count": len(train_data),
            "val_count": len(val_data),
            "dedup_removed": len(raw_data) - len(valid_data) - sum(invalid_count.values())
        }


# 使用示例
processor = FineTuningDataProcessor(
    input_file="data/raw_data.json",
    output_file="data/processed/train.json",
    format_type="alpaca"
)
stats = processor.process()
print(f"数据统计：{stats}")
# 数据统计：{'raw_count': 5000, 'valid_count': 4200, 'invalid_reasons': {'指令过短': 300, '输出过短': 500}, 'train_count': 3780, 'val_count': 420, 'dedup_removed': 0}
```

**数据准备的踩坑经验**：

| 坑 | 表现 | 解决方法 |
|------|------|----------|
| 数据格式不统一 | 同样的问题，不同格式的答案 | 写格式校验脚本，逐条检查 |
| 输出太短 | 模型学会了"敷衍回答" | 过滤掉输出少于10字的样本 |
| 重复数据 | 模型过拟合某些模式 | 去重（基于 instruction 去重） |
| 数据分布不均 | 模型偏向高频类别 | 按类别采样，保证平衡 |
| 人工标注不一致 | 同样的问题，不同标注员给不同答案 | 标注指南 + 交叉验证 |

### 2.4 第三步：基座模型选择

```python
class BaseModelSelector:
    """基座模型选择器"""
    
    MODELS = {
        # 中文场景
        "qwen2.5-1.8b": {
            "params": "1.8B",
            "lora_vram": "~6GB",
            "full_vram": "~15GB",
            "chinese": "优秀",
            "reasoning": "一般",
            "recommend": "轻量级任务、显存紧张"
        },
        "qwen2.5-7b": {
            "params": "7B",
            "lora_vram": "~16GB",
            "full_vram": "~60GB",
            "chinese": "优秀",
            "reasoning": "良好",
            "recommend": "大多数项目首选（推荐）"
        },
        "qwen2.5-14b": {
            "params": "14B",
            "lora_vram": "~30GB",
            "full_vram": "~120GB",
            "chinese": "优秀",
            "reasoning": "优秀",
            "recommend": "效果优先、资源充足"
        },
        "qwen2.5-72b": {
            "params": "72B",
            "lora_vram": "~160GB",
            "full_vram": "~600GB",
            "chinese": "优秀",
            "reasoning": "顶级",
            "recommend": "工业级、多卡训练"
        },
        # 英文场景
        "llama3.1-8b": {
            "params": "8B",
            "lora_vram": "~18GB",
            "full_vram": "~65GB",
            "chinese": "一般",
            "reasoning": "良好",
            "recommend": "英文任务首选"
        },
        "mistral-7b": {
            "params": "7B",
            "lora_vram": "~16GB",
            "full_vram": "~60GB",
            "chinese": "较差",
            "reasoning": "良好",
            "recommend": "英文、代码任务"
        }
    }
    
    def select(self, task: str, vram_gb: int, language: str = "zh") -> list:
        """选择合适的模型"""
        
        candidates = []
        for name, info in self.MODELS.items():
            if vram_gb < 16 and info["lora_vram"] != f"~{vram_gb}GB":
                # 显存不够的排除
                lora_vram = int(info["lora_vram"].replace("~", "").replace("GB", ""))
                if lora_vram > vram_gb:
                    continue
            
            if language == "zh" and info["chinese"] in ["较差", "一般"]:
                continue
            
            candidates.append((name, info))
        
        # 按推荐度排序
        candidates.sort(key=lambda x: 0 if "推荐" in x[1]["recommend"] else 1)
        return candidates


# 使用示例
selector = BaseModelSelector()
models = selector.select(task="抽取", vram_gb=24, language="zh")
for name, info in models:
    print(f"{name}: {info['recommend']}")
# qwen2.5-7b: 大多数项目首选（推荐）
# qwen2.5-14b: 效果优先、资源充足
```

**选型建议**：

- **中文任务**：Qwen2.5 系列（无脑选）
- **英文任务**：Llama 3.1 / Mistral
- **代码任务**：Qwen2.5-Coder / DeepSeek-Coder
- **显存 < 16GB**：QLoRA + 7B 模型
- **显存 24GB**：LoRA + 7B 模型（最佳性价比）
- **显存 80GB**：LoRA + 14B 或全量微调 7B

---

## 三、LoRA 微调实战（完整可运行代码）

### 3.1 训练脚本

```python
"""
LoRA 微调训练脚本
支持：Qwen2.5 / Llama3 / Mistral 等模型
"""

import os
import json
import torch
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset


@dataclass
class LoRATrainingConfig:
    """LoRA 训练配置"""
    
    # 模型配置
    model_name: str = "Qwen/Qwen2.5-7B-Instruct"
    tokenizer_name: Optional[str] = None
    
    # 数据配置
    train_file: str = "data/processed/train.json"
    val_file: str = "data/processed/train_val.json"
    max_seq_length: int = 2048
    
    # LoRA 配置
    lora_r: int = 16              # LoRA 秩（8/16/32/64）
    lora_alpha: int = 32          # LoRA alpha（通常是 r 的 2 倍）
    lora_dropout: float = 0.05    # LoRA dropout
    target_modules: list = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",  # attention
        "gate_proj", "up_proj", "down_proj"        # MLP
    ])
    
    # 训练配置
    output_dir: str = "output/lora-qwen2.5-7b"
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4    # 等效 batch_size = 4*4 = 16
    learning_rate: float = 2e-4             # LoRA 推荐 1e-4 ~ 5e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    lr_scheduler_type: str = "cosine"       # cosine 比 linear 更稳定
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100
    save_total_limit: int = 3
    
    # 优化配置
    fp16: bool = False
    bf16: bool = True                       # A100/H100 用 bf16
    gradient_checkpointing: bool = True      # 节省显存


class LoRATrainer:
    """LoRA 微调训练器"""
    
    def __init__(self, config: LoRATrainingConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        
    def load_tokenizer(self):
        """加载 tokenizer"""
        
        tokenizer_name = self.config.tokenizer_name or self.config.model_name
        self.tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_name,
            trust_remote_code=True,
            padding_side="right"  # 训练用 right，推理用 left
        )
        
        # 确保 pad_token 存在
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        print(f"Tokenizer 加载完成，词表大小：{len(self.tokenizer)}")
        return self.tokenizer
    
    def load_model(self):
        """加载模型 + LoRA"""
        
        print(f"加载模型：{self.config.model_name}")
        
        # 加载基座模型
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            torch_dtype=torch.bfloat16 if self.config.bf16 else torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        
        # 配置 LoRA
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.target_modules,
            bias="none",
        )
        
        # 应用 LoRA
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
        # 输出示例：trainable params: 39,976,960 || all params: 7,615,308,800 || trainable%: 0.5251%
        
        # 开启梯度检查点（省显存）
        if self.config.gradient_checkpointing:
            self.model.enable_input_require_grads()
            self.model.gradient_checkpointing_enable()
        
        return self.model
    
    def prepare_dataset(self):
        """准备数据集"""
        
        def format_alpaca(example):
            """Alpaca 格式 → 模型输入"""
            if example.get("input"):
                prompt = (
                    f"### Instruction:\n{example['instruction']}\n\n"
                    f"### Input:\n{example['input']}\n\n"
                    f"### Response:\n{example['output']}"
                )
            else:
                prompt = (
                    f"### Instruction:\n{example['instruction']}\n\n"
                    f"### Response:\n{example['output']}"
                )
            return {"text": prompt}
        
        def tokenize_function(example):
            """tokenize"""
            result = self.tokenizer(
                example["text"],
                truncation=True,
                max_length=self.config.max_seq_length,
                padding=False,
            )
            # 自回归训练：labels = input_ids
            result["labels"] = result["input_ids"].copy()
            return result
        
        # 加载训练数据
        with open(self.config.train_file, "r", encoding="utf-8") as f:
            train_data = json.load(f)
        
        train_dataset = Dataset.from_list(train_data)
        train_dataset = train_dataset.map(format_alpaca)
        train_dataset = train_dataset.map(tokenize_function, remove_columns=train_dataset.column_names)
        
        # 加载验证数据
        val_dataset = None
        if os.path.exists(self.config.val_file):
            with open(self.config.val_file, "r", encoding="utf-8") as f:
                val_data = json.load(f)
            
            val_dataset = Dataset.from_list(val_data)
            val_dataset = val_dataset.map(format_alpaca)
            val_dataset = val_dataset.map(tokenize_function, remove_columns=val_dataset.column_names)
        
        print(f"训练集：{len(train_dataset)} 条，验证集：{len(val_dataset) if val_dataset else 0} 条")
        return train_dataset, val_dataset
    
    def train(self):
        """执行训练"""
        
        # 加载组件
        self.load_tokenizer()
        self.load_model()
        train_dataset, val_dataset = self.prepare_dataset()
        
        # 训练参数
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            warmup_ratio=self.config.warmup_ratio,
            lr_scheduler_type=self.config.lr_scheduler_type,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_strategy="steps" if val_dataset else "no",
            eval_steps=self.config.eval_steps if val_dataset else None,
            save_total_limit=self.config.save_total_limit,
            fp16=self.config.fp16,
            bf16=self.config.bf16,
            gradient_checkpointing=self.config.gradient_checkpointing,
            report_to="tensorboard",
            load_best_model_at_end=True if val_dataset else False,
            metric_for_best_model="eval_loss" if val_dataset else None,
        )
        
        # 数据整理器
        data_collator = DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer,
            padding=True,
            max_length=self.config.max_seq_length,
        )
        
        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
        )
        
        # 开始训练
        print("=" * 50)
        print("开始 LoRA 微调训练")
        print("=" * 50)
        trainer.train()
        
        # 保存最终模型
        final_dir = os.path.join(self.config.output_dir, "final")
        trainer.save_model(final_dir)
        self.tokenizer.save_pretrained(final_dir)
        print(f"模型已保存到：{final_dir}")
        
        return trainer


if __name__ == "__main__":
    config = LoRATrainingConfig(
        model_name="Qwen/Qwen2.5-7B-Instruct",
        train_file="data/processed/train.json",
        val_file="data/processed/train_val.json",
        output_dir="output/lora-qwen2.5-7b",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        learning_rate=2e-4,
        lora_r=16,
    )
    
    trainer = LoRATrainer(config)
    trainer.train()
```

### 3.2 训练启动命令

```bash
# 单卡训练
python train_lora.py

# 多卡训练（2卡）
torchrun --nproc_per_node=2 train_lora.py

# 指定显卡
CUDA_VISIBLE_DEVICES=0 python train_lora.py

# QLoRA（显存不够时）
# 只需在配置中加：
# quantization_config = BitsAndBytesConfig(
#     load_in_4bit=True,
#     bnb_4bit_quant_type="nf4",
#     bnb_4bit_compute_dtype=torch.bfloat16,
# )
```

---

## 四、高阶用法

### 4.1 多任务微调

一个模型同时学会多个任务，比多个单任务模型更实用。

```python
class MultiTaskLoRA:
    """多任务 LoRA 微调"""
    
    def __init__(self, base_model: str):
        self.base_model = base_model
        self.task_loras = {}  # 每个任务一个 LoRA adapter
    
    def add_task(self, task_name: str, train_file: str, lora_r: int = 16):
        """添加任务"""
        
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_r,
            lora_alpha=lora_r * 2,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        )
        
        self.task_loras[task_name] = {
            "config": lora_config,
            "train_file": train_file,
        }
        
        print(f"添加任务：{task_name}，LoRA rank={lora_r}")
    
    def train_all(self, output_dir: str):
        """逐任务训练，每个任务保存独立的 LoRA adapter"""
        
        for task_name, task_info in self.task_loras.items():
            print(f"\n{'='*50}")
            print(f"训练任务：{task_name}")
            print(f"{'='*50}")
            
            # 每次重新加载基座模型
            model = AutoModelForCausalLM.from_pretrained(
                self.base_model,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
            )
            
            # 应用该任务的 LoRA
            model = get_peft_model(model, task_info["config"])
            model.print_trainable_parameters()
            
            # 训练...（同上面的训练流程）
            
            # 保存该任务的 LoRA adapter
            task_output = os.path.join(output_dir, task_name)
            model.save_pretrained(task_output)
            print(f"任务 {task_name} 的 LoRA 已保存到：{task_output}")
            
            # 释放显存
            del model
            torch.cuda.empty_cache()
    
    def inference(self, task_name: str, prompt: str):
        """推理时切换 LoRA adapter"""
        
        # 加载基座模型
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        
        # 加载指定任务的 LoRA
        adapter_path = os.path.join("output/multi-task", task_name)
        model = PeftModel.from_pretrained(model, adapter_path)
        model.eval()
        
        # 推理
        inputs = self.tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=512)
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)


# 使用示例
mtl = MultiTaskLoRA("Qwen/Qwen2.5-7B-Instruct")
mtl.add_task("ner", "data/ner/train.json", lora_r=16)         # 命名实体识别
mtl.add_task("sentiment", "data/sentiment/train.json", lora_r=8)  # 情感分析
mtl.add_task("summary", "data/summary/train.json", lora_r=16)     # 摘要生成
mtl.train_all("output/multi-task")
```

**多任务 LoRA 的好处**：
- 基座模型只存一份（7B）
- 每个任务的 LoRA adapter 只有几十 MB
- 推理时按需加载，切换速度快

### 4.2 LoRA 合并

训练完成后，把 LoRA 权重合并回基座模型，推理时不需要额外加载。

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def merge_lora(
    base_model: str,
    lora_path: str,
    output_path: str,
):
    """合并 LoRA 到基座模型"""
    
    print(f"加载基座模型：{base_model}")
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.bfloat16,
        device_map="cpu",  # 合并时用 CPU，不占 GPU 显存
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    
    print(f"加载 LoRA：{lora_path}")
    model = PeftModel.from_pretrained(model, lora_path)
    
    print("合并 LoRA 权重...")
    model = model.merge_and_unload()
    
    print(f"保存合并后的模型到：{output_path}")
    model.save_pretrained(output_path, safe_serialization=True)
    tokenizer.save_pretrained(output_path)
    
    print("✅ 合并完成！")
    
    # 验证
    print(f"合并后模型大小：{sum(p.numel() for p in model.parameters()) / 1e9:.2f}B 参数")


# 使用示例
merge_lora(
    base_model="Qwen/Qwen2.5-7B-Instruct",
    lora_path="output/lora-qwen2.5-7b/final",
    output_path="output/merged-qwen2.5-7b"
)
```

### 4.3 持续微调（Continual Fine-tuning）

在已有的 LoRA 基础上继续微调，不是从头开始。

```python
class ContinualLoRATrainer:
    """持续微调训练器"""
    
    def __init__(self, base_model: str, existing_lora: str):
        self.base_model = base_model
        self.existing_lora = existing_lora
    
    def train(self, new_data_file: str, output_dir: str):
        """在已有 LoRA 基础上继续训练"""
        
        # 加载基座模型
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        
        # 加载已有的 LoRA 权重（不是重新初始化）
        model = PeftModel.from_pretrained(model, self.existing_lora)
        model.print_trainable_parameters()
        
        # ⚠️ 关键：降低学习率（持续微调用更小的学习率）
        training_args = TrainingArguments(
            output_dir=output_dir,
            learning_rate=5e-5,       # 比初始训练低一个数量级
            num_train_epochs=1,       # 少训练几个 epoch
            per_device_train_batch_size=4,
            warmup_ratio=0.05,
            lr_scheduler_type="cosine",
        )
        
        # 训练...（同上面的训练流程）
        
        return model


# 使用示例
continual = ContinualLoRATrainer(
    base_model="Qwen/Qwen2.5-7B-Instruct",
    existing_lora="output/lora-qwen2.5-7b/final"
)
continual.train(
    new_data_file="data/new_task/train.json",
    output_dir="output/lora-qwen2.5-7b-continual"
)
```

### 4.4 DPO 微调（对齐人类偏好）

LoRA 微调让模型学会任务，DPO 微调让模型学会"什么样的回答更好"。

```python
from trl import DPOTrainer, DPOConfig


class DPOFineTuner:
    """DPO 偏好对齐微调"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    def prepare_dpo_data(self, data_file: str) -> Dataset:
        """准备 DPO 数据"""
        
        with open(data_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        dpo_data = []
        for item in raw_data:
            dpo_data.append({
                "prompt": item["prompt"],
                "chosen": item["good_response"],   # 好的回答
                "rejected": item["bad_response"],   # 差的回答
            })
        
        return Dataset.from_list(dpo_data)
    
    def train(self, data_file: str, output_dir: str):
        """DPO 训练"""
        
        # 加载模型
        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        
        # 加载参考模型（DPO 需要）
        model_ref = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # 准备数据
        dataset = self.prepare_dpo_data(data_file)
        
        # DPO 配置
        dpo_config = DPOConfig(
            output_dir=output_dir,
            per_device_train_batch_size=2,
            gradient_accumulation_steps=8,
            learning_rate=5e-5,           # DPO 用更小的学习率
            num_train_epochs=1,
            bf16=True,
            beta=0.1,                      # DPO beta（越大越保守）
            max_length=2048,
            remove_unused_columns=False,
        )
        
        # DPO Trainer
        trainer = DPOTrainer(
            model=model,
            ref_model=model_ref,
            args=dpo_config,
            train_dataset=dataset,
            processing_class=tokenizer,
        )
        
        trainer.train()
        trainer.save_model(os.path.join(output_dir, "final"))
        
        return trainer


# 使用示例
dpo = DPOFineTuner("output/merged-qwen2.5-7b")
dpo.train("data/dpo/preference_data.json", "output/dpo-qwen2.5-7b")
```

**DPO 数据示例**：
```json
[
  {
    "prompt": "解释什么是机器学习",
    "good_response": "机器学习是人工智能的一个分支，通过数据训练算法，让计算机自动发现规律并做出预测。简单说，就是让机器从数据中'学习'，而不是靠人手动写规则。",
    "bad_response": "机器学习就是AI，AI就是机器学习。"
  }
]
```

---

## 五、评估体系

### 5.1 自动化评估

```python
import numpy as np
from collections import defaultdict


class FineTuningEvaluator:
    """微调模型评估器"""
    
    def __init__(self, model_path: str, tokenizer_path: str):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        self.model.eval()
    
    def evaluate_generation(self, test_file: str) -> dict:
        """评估生成质量"""
        
        with open(test_file, "r", encoding="utf-8") as f:
            test_data = json.load(f)
        
        results = {
            "total": len(test_data),
            "empty_output": 0,
            "avg_output_length": 0,
            "format_compliance": 0,
            "keyword_coverage": 0,
        }
        
        output_lengths = []
        format_correct = 0
        keyword_found = 0
        
        for item in test_data:
            prompt = item["instruction"]
            expected = item["output"]
            
            # 生成
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.1,       # 评估时用低温度，更稳定
                    do_sample=True,
                )
            
            generated = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True
            )
            
            if not generated.strip():
                results["empty_output"] += 1
            
            output_lengths.append(len(generated))
            
            # 格式检查（以 JSON 输出为例）
            if expected.startswith("{"):
                try:
                    json.loads(generated)
                    format_correct += 1
                except:
                    pass
            else:
                format_correct += 1  # 非JSON格式默认通过
            
            # 关键词覆盖
            expected_keywords = set(expected.split()[:10])
            generated_keywords = set(generated.split())
            if expected_keywords & generated_keywords:
                keyword_found += 1
        
        results["avg_output_length"] = np.mean(output_lengths)
        results["format_compliance"] = format_correct / len(test_data)
        results["keyword_coverage"] = keyword_found / len(test_data)
        
        return results
    
    def compare_with_base(self, base_model_path: str, test_file: str) -> dict:
        """和基座模型对比"""
        
        base_evaluator = FineTuningEvaluator(base_model_path, base_model_path)
        
        base_results = base_evaluator.evaluate_generation(test_file)
        ft_results = self.evaluate_generation(test_file)
        
        comparison = {
            "base_model": base_results,
            "fine_tuned": ft_results,
            "improvement": {
                key: ft_results[key] - base_results[key]
                for key in ["format_compliance", "keyword_coverage"]
                if key in base_results and key in ft_results
            }
        }
        
        return comparison


# 使用示例
evaluator = FineTuningEvaluator(
    model_path="output/merged-qwen2.5-7b",
    tokenizer_path="output/merged-qwen2.5-7b"
)
results = evaluator.evaluate_generation("data/processed/train_val.json")
print(f"评估结果：{json.dumps(results, indent=2, ensure_ascii=False)}")
```

### 5.2 评估指标选择

| 任务类型 | 推荐指标 | 说明 |
|----------|----------|------|
| 分类 | Accuracy / F1 | 简单直接 |
| 生成 | BLEU / ROUGE | 参考性指标，别迷信 |
| 抽取 | F1 / Exact Match | 严格匹配 |
| 对话 | 人工评估 + GPT-4 评估 | 自动指标不可靠 |
| 格式输出 | 格式合规率 | 最实用的指标 |

---

## 六、部署

### 6.1 vLLM 部署（推荐）

```bash
# 启动 vLLM 服务
python -m vllm.entrypoints.openai.api_server \
    --model output/merged-qwen2.5-7b \
    --served-model-name my-finetuned-model \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9 \
    --dtype bfloat16

# 测试
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-finetuned-model",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 256
  }'
```

### 6.2 LoRA 动态加载部署

不需要合并，推理时按需加载 LoRA adapter。

```bash
# 启动 vLLM 服务，指定 LoRA adapter
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --enable-lora \
    --lora-modules \
        ner=output/lora-ner/final \
        sentiment=output/lora-sentiment/final \
        summary=output/lora-summary/final \
    --host 0.0.0.0 \
    --port 8000

# 调用特定任务的 LoRA
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ner",
    "messages": [{"role": "user", "content": "分析这句话中的实体"}]
  }'
```

**动态加载的好处**：一个基座模型 + N 个 LoRA adapter，显存只占一份。

---

## 七、踩坑记录

### 7.1 训练阶段的坑

| 坑 | 症状 | 解决方法 |
|------|------|----------|
| 学习率太大 | loss 震荡不收敛 | LoRA 用 1e-4 ~ 5e-4，全量微调用 1e-5 ~ 5e-5 |
| 学习率太小 | loss 不下降 | 逐步调大，每次翻倍 |
| batch size 太大 | OOM | 减小 batch_size，增大 gradient_accumulation_steps |
| 数据太少 | 过拟合，训练 loss 下降但验证 loss 上升 | 增加数据，加 dropout，减少 epoch |
| 数据太多 | 欠拟合，loss 下不去 | 增大 lora_r，增大学习率 |
| padding 策略不对 | 训练不稳定 | 训练用 padding_side="right" |
| 没有验证集 | 不知道什么时候停 | 必须留验证集，用 eval_loss 判断 |

### 7.2 推理阶段的坑

| 坑 | 症状 | 解决方法 |
|------|------|----------|
| 重复生成 | "好的好的好的好的..." | 加 repetition_penalty=1.1 |
| 空输出 | 模型什么都不输出 | 检查 max_new_tokens，调高 temperature |
| 格式不对 | 输出不是期望的 JSON 格式 | 训练数据中加入格式示例 |
| 性能下降 | 微调后不如基座模型 | 灾难性遗忘，减少 epoch 或加 DPO 对齐 |
| LoRA 加载失败 | 找不到 adapter_config.json | 确保保存了完整目录 |

### 7.3 最容易被忽略的问题

**灾难性遗忘**：微调后模型变"笨"了。

```
症状：微调后，模型在目标任务上表现变好，但通用能力下降。

原因：训练数据太单一，模型"忘了"其他能力。

解决方法：
1. 混入 10-20% 的通用数据（如 Alpaca 通用数据集）
2. 减少训练 epoch（3 → 1~2）
3. 降低学习率
4. 使用 DPO 对齐（保持通用能力的同时学会新任务）
```

---

## 八、生产级最佳实践清单

```
✅ 数据质量
  ├── 每条数据都人工检查过
  ├── 去重、去噪、格式统一
  ├── 留 10% 做验证集
  └── 混入 10-20% 通用数据防遗忘

✅ 训练策略
  ├── 先 LoRA 跑基线，效果不够再全量微调
  ├── 学习率从 2e-4 开始，根据 loss 调整
  ├── 用 cosine scheduler
  ├── 开启 gradient checkpointing 省显存
  └── 保存至少 3 个 checkpoint，选最好的

✅ 评估
  ├── 自动评估 + 人工评估
  ├── 和基座模型对比
  ├── 测试集绝不能用于训练
  └── 关注灾难性遗忘指标

✅ 部署
  ├── 合并 LoRA 后用 vLLM 部署
  ├── 或动态加载多个 LoRA adapter
  ├── 设置 max_model_len 防止 OOM
  └── 监控推理延迟和吞吐量

✅ 持续迭代
  ├── 收集线上 bad case
  ├── 定期持续微调
  ├── 新数据和旧数据混合训练
  └── 版本管理：每个版本有明确的 changelog
```

---

## 总结

微调的本质是**数据工程**，不是调参。

1. **数据决定上限**，模型和算法只是逼近上限
2. **LoRA 是性价比之王**，90% 的项目用 LoRA 就够了
3. **评估不是可选项**，没有评估的微调就是盲人摸象
4. **部署要考虑成本**，LoRA 动态加载比合并更灵活
5. **持续迭代比一次到位更重要**，先跑通基线再优化

微调的投入产出比很高。一个微调好的 7B 模型，在垂直任务上可以接近甚至超过 GPT-4，而推理成本只有十分之一。这就是微调的价值。
