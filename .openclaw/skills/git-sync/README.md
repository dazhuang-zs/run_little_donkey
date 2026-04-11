# Git Sync Skill

本地与云端 OpenClaw 协同开发的 Git 同步技能。

## 安装

将此目录复制到你的项目：

```bash
# 复制整个 .openclaw 目录到你的项目根目录
cp -r .openclaw /path/to/your/project/
```

## 快速开始

```bash
# 1. 进入你的项目目录
cd /path/to/your/project

# 2. 初始化 Memory 结构（如果还没有）
./.openclaw/skills/git-sync/scripts/git-sync.sh init

# 3. 提交初始化文件
git add .openclaw/
git commit -m "初始化 git-sync"
git push

# 4. 开始工作！
```

## 日常使用

```bash
# 查看开发准则
./.openclaw/skills/git-sync/scripts/git-sync.sh guide

# 开始工作前
./.openclaw/skills/git-sync/scripts/git-sync.sh sync

# 工作中，定期保存进度
./.openclaw/skills/git-sync/scripts/git-sync.sh checkpoint "完成了 XX 功能"

# 结束工作时
./.openclaw/skills/git-sync/scripts/git-sync.sh sync

# 切换到另一个环境后
./.openclaw/skills/git-sync/scripts/git-sync.sh resume
```

## 目录结构

```
.openclaw/
├── MEMORY.md              # 长期记忆
├── DEVELOPMENT.md         # 开发准则
├── memory/                # 工作日志
│   ├── YYYY-MM-DD.md      # 每日日志
│   ├── tasks.md           # 待办事项
│   └── context.md         # 当前上下文
└── skills/                # OpenClaw 技能
    └── git-sync/
        └── scripts/
            └── git-sync.sh
```

## 命令说明

| 命令 | 说明 |
|------|------|
| `sync` | 完整同步（拉取 + 推送） |
| `status` | 查看同步状态 |
| `checkpoint <msg>` | 创建工作检查点 |
| `resume` | 恢复工作状态 |
| `push-memory` | 仅推送 Memory 文件 |
| `pull-memory` | 仅拉取 Memory 文件 |
| `init` | 初始化 Memory 目录结构 |
| `guide` | 显示开发准则 |

## 注意事项

1. Memory 文件会纳入 Git 版本控制，**不要写入敏感信息**
2. 冲突时需要手动解决
3. 建议在 `.gitignore` 中忽略 `*.conflict` 文件
