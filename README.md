# 🐴 Run Little Donkey

> 小毛驴系列作品集 —— AI + 趣味 + 实战

本仓库包含 5 个独立子项目，涵盖 AI 内容生成、游戏开发、数据爬取与分析等方向。

---

## 📂 项目总览

| # | 项目 | 类型 | 简介 |
|---|------|------|------|
| 1 | `ai-video-narrator` | AI 应用 | AI 视频解说生成器 |
| 2 | `province-conquest` | 游戏 | 问鼎中原 · 省份争霸动画视频 |
| 3 | `survival-game` | 游戏 | 重生之月薪 2000 · 文字生存模拟 |
| 4 | `comment-insight` | 数据分析 | 社交平台评论洞察助手 |
| 5 | `spider-xhs` | 爬虫 | 小红书数据爬虫 + 导出分析工具 |

---

## 1. 🎬 ai-video-narrator — AI 视频解说

**一句话**：上传视频片段，AI 自动生成解说词并合成配音视频。

### 核心功能
- 5 种解说风格：专业/幽默吐槽/情感共情/悬疑推理/知识科普
- AI 自动分析视频内容，生成解说脚本文案
- 支持用户手动编辑脚本
- TTS 配音合成 + 字幕生成

### 文档说明

| 文件 | 内容 |
|------|------|
| `README.md` | 项目介绍与快速开始 |
| `docs/PRD.md` | 产品需求文档 |
| `docs/ARCHITECTURE.md` | 技术架构设计 |
| `docs/ANALYSIS.md` | 产品分析报告 |
| `docs/ROADMAP.md` | 产品路线图 |
| `docs/TOOLS.md` | 工具链说明 |

### 技术栈
`Python (FastAPI)` + `Node.js` + 前端页面

---

## 2. 🗺️ province-conquest — 问鼎中原

**一句话**：34 个省级行政区六维属性 PK，颜色感染扩张动画，无交互自动播放。

### 核心玩法
- 6 维属性对决：统帅/武力/智谋/政治/魅力/技艺
- 每省历史名人参与战斗
- 并发 PK，右侧实时展示所有对决
- 颜色渐变感染，胜负直观呈现

### 文档说明

| 文件 | 内容 |
|------|------|
| `DESIGN.md` | 产品设计文档 |
| `HEROES.md` | 各省历史名人数据 |
| `PK-RULES.md` | 对决规则说明 |
| `HISTORIAN-SCRIPT.md` | 旁白脚本 |
| `VIDEO-PRODUCTION.md` | 视频制作流程 |
| `OPTIMIZATION.md` | 性能优化记录 |

### 技术栈
`纯 HTML/CSS/JS` + `ECharts 5` + `DataV GeoJSON`

---

## 3. 🏠 survival-game — 重生之月薪 2000

**一句话**：扮演月薪 2000 元的打工人，在资源匮乏中做出人生选择，体验生存与成长。

### 核心玩法
- 文字冒险式生存模拟
- 事件驱动系统，触发各种随机人生事件
- 多结局设计（逆袭/躺平/摆烂/猝死等）
- 玩家属性成长与行动管理

### 文档说明

| 文件 | 内容 |
|------|------|
| `PRD.md` | 产品需求文档 |
| `backend-design.md` | 后端架构设计 |
| `tests/test_game.py` | 游戏核心逻辑测试 |

### 技术栈
`Python (FastAPI)` + `SQLite` + `HTML/JS` 前端

---

## 4. 💬 comment-insight — 评论洞察助手

**一句话**：输入小红书/大众点评等热门内容链接，AI 自动提炼真实体验、避坑建议、优缺点。

### 核心功能
- 多平台评论爬取（小红书为主）
- 评论去水军、情绪分析
- 关键词提取：高赞评论/踩坑/真实体验
- 数据可视化展示

### 文档说明

| 文件 | 内容 |
|------|------|
| `PRD.md` | 产品需求文档 |
| `DEVELOPMENT.md` | 开发记录 |
| `OPTIMIZATION.md` | 性能优化记录 |
| `QUICKSTART.md` | 快速开始指南 |

### 技术栈
`Python` + `FastAPI` + `Playwright` + 小红书 PC 端 API

---

## 5. 🕷️ spider-xhs — 小红书爬虫

**一句话**：本地 Cookie 驱动的小红书数据爬取工具，支持笔记、评论、用户搜索与 Markdown 导出。

### 核心功能
- 笔记详情爬取（标题/正文/互动数据）
- 全量评论 + 二级评论获取
- 关键词搜索笔记
- Markdown 格式导出（供 LLM 分析）
- Web 可视化界面

### 文档说明

| 文件 | 内容 |
|------|------|
| `README.md` | 项目介绍 |
| `WEB-ARCHITECTURE-DESIGN.md` | Web 架构设计 |
| `export_markdown.py` | 命令行导出工具 |

### 核心模块

| 文件 | 功能 |
|------|------|
| `apis/xhs_pc_apis.py` | 小红书 PC 端 API 封装 |
| `apis/xhs_creator_apis.py` | 创作者 API |
| `xhs_utils/xhs_util.py` | 笔记相关工具函数 |
| `xhs_utils/cookie_util.py` | Cookie 管理 |
| `web/main.py` | Web 服务入口 |
| `web/templates/` | 前端 HTML 模板 |

### 技术栈
`Python (Flask)` + `Node.js` + `Playwright` + 小红书 JS 逆向

---

## 📚 参考项目（本地学习用）

> 以下为 RAG 应用立项参考项目，已加入 `.gitignore`，仅供本地学习。

| 项目 | 地址 | 简介 |
|------|------|------|
| **FastGPT** | `labring/FastGPT` | 知识库问答，RAG + 工作流，国内生态好 |
| **RAGFlow** | `infiniflow/ragflow` | 企业级 RAG，文档解析极强，RAG 调参最细 |

### 为什么选这两个

| 维度 | FastGPT | RAGFlow |
|------|---------|---------|
| 文档解析 | 强 | 极强（OCR/表格/版面分析） |
| RAG 调参粒度 | 基础 | 细粒度（适合学习调优） |
| 国产模型支持 | 好 | 一般 |
| 代码复杂度 | 中等 | 较高 |
| 适合作为立项参考 | ✅ | ✅ |

---

## 🔧 通用技术栈汇总

```
ai-video-narrator  → Python (FastAPI) + Node.js
province-conquest   → 纯 HTML/CSS/JS + ECharts
survival-game      → Python (FastAPI) + SQLite + HTML/JS
comment-insight    → Python + FastAPI + Playwright
spider-xhs         → Python (Flask) + Node.js + JS 逆向
```

---

## 📌 快速导航

```
想看游戏？
  → province-conquest/index.html        （直接浏览器打开）
  → survival-game/static/index.html     （本地运行 python main.py）

想爬小红书？
  → spider-xhs/main.py                  （先配置 Cookie）
  → spider-xhs/export_markdown.py       （命令行导出）

想分析评论？
  → comment-insight/QUICKSTART.md       （按文档启动）

想做视频解说？
  → ai-video-narrator/README.md          （按文档配置环境）

想学习 RAG 应用？
  → FastGPT/                             （参考架构与 RAG 工作流）
  → ragflow/                              （参考文档解析与调参）
```

---

*持续更新中 🚀*
