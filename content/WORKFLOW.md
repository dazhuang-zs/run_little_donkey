# 工作流速查（cheat-on-content）

> 这是 `/cheat-init` 在你的项目根创建的速查文档。完整规范在 cheat-on-content 的 `SKILL.md`。

---

## 一句话流程

```
找选题 → /cheat-seed 写草稿 → 用户改写 → /cheat-score 打分 → /cheat-predict 启动预测 → 拍摄 → /cheat-shoot → 发布 → /cheat-publish → T+3天 /cheat-retro 复盘 → 累计偏差 → /cheat-bump 升级rubric
```

---

## 五个阶段对应触发词

### ① 选题阶段

| 想做什么 | 触发词 |
|---|---|
| 看 candidates.md 排序后的推荐 | "推荐选题" / "下一篇做什么" |
| 抓今天的热点拓展 candidates | "抓热点" |
| 看当前状态 | "状态" |

### ② 打分 + 预测

| 想做什么 | 触发词 | 写文件吗 |
|---|---|---|
| 看一份稿子的 rubric 分（探索） | "打分这篇 path/to/draft.md" | 否 |
| 给最终稿写正式 immutable 预测日志 | "启动预测 path/to/draft.md" | 是 |

> **score 与 predict 的核心区别**：
> - score 是探索，无副作用，可反复跑
> - predict 是承诺，写完文件被 hook 锁死

### ③ 发布登记

发完后立刻：

```
"已发布 https://..."
```

### ④ 复盘

T+3 天后：

```
"复盘 predictions/xxx.md"
```

或直接：

```
"复盘"
```

### ⑤ Rubric 升级（罕见）

满足条件才提议：

```
"升级 rubric --propose 'ER 权重 1.5→2.0'"
```

---

## 三条不可妥协的原则

1. **盲预测**：预测段写在看到任何数据之前，写完不可改
2. **升级 = 全量重打**：bump 必须校准池全量重打分 + 跨模型独立审
3. **rubric 是工作台不是博物馆**：被吸收/被推翻的观察都删掉

---

## 文件结构

```
content/
├── rubric_notes.md          # 评分规则真实来源
├── script_patterns.md       # 写作 pattern 沉淀
├── WORKFLOW.md              # 本文件
├── STATUS.md                # 看板
├── .cheat-state.json        # 状态文件
├── scripts/                 # 拍前草稿
├── predictions/             # immutable 预测日志
└── videos/                  # 拍后工作目录
```

---

## 下一步

1. **写一份稿子**
2. 跑 `打分这篇 scripts/xxx.md`
3. 准备发布前跑 `启动预测 scripts/xxx.md`
4. 发布后说 `已发布 https://...`
5. T+3 天跑 `复盘`

第 5 篇之后解锁 `/cheat-bump`。
