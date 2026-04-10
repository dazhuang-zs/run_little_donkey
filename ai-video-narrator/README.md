# 🎬 AI 视频解说项目

> 让AI帮你做视频解说，支持多种解说风格，一键生成专业解说视频

## 项目简介

这是一个基于AI的视频解说生成工具，用户可以上传影视片段、电视节目或自己的视频，选择喜欢的解说风格，系统会自动生成解说词并合成解说视频。

## 核心功能

### 1. 解说风格选择
- **专业解说员** - 正式、严谨，适合纪录片、科普内容
- **幽默吐槽风** - 轻松、风趣，适合综艺、影视剧解说
- **情感共情风** - 温暖、感性，适合剧情片、人物故事
- **悬疑推理风** - 紧张、悬疑，适合犯罪剧、悬疑片
- **知识科普风** - 深入浅出，适合教育内容

### 2. 智能内容生成
- AI自动分析视频内容
- 自动生成解说脚本文案
- 支持用户手动编辑修改
- 一键生成配音（TTS）

### 3. 视频处理
- 视频片段导入
- 自动字幕生成
- 画面标注与高亮
- 多平台格式导出

## 技术栈

### AI 核心
- **视频理解**: OpenAI GPT-4V / Claude Vision / 通义千问VL
- **文案生成**: GPT-4 / Claude / 智谱GLM
- **配音合成**: Azure TTS / 阿里云语音合成 / Minimax TTS

### 后端
- **语言**: Python 3.10+
- **Web框架**: FastAPI
- **视频处理**: FFmpeg / MoviePy
- **数据库**: SQLite (开发) / PostgreSQL (生产)

### 前端
- **Web界面**: React / Vue 3
- **桌面应用**: Electron

### 部署
- **Docker容器化**
- **云端存储**: 阿里云OSS / 腾讯云COS

## 项目结构

```
ai-video-narrator/
├── README.md                 # 项目说明
├── docs/                     # 文档目录
│   ├── PRD.md               # 产品需求文档
│   ├── ARCHITECTURE.md      # 技术架构设计
│   ├── TOOLS.md             # 所需工具技能清单
│   └── ROADMAP.md           # 开发路线图
├── backend/                  # 后端服务
│   ├── app/
│   │   ├── api/             # API接口
│   │   ├── core/            # 核心模块
│   │   ├── services/        # 业务服务
│   │   └── models/          # 数据模型
│   ├── requirements.txt
│   └── main.py
├── frontend/                 # 前端应用
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
└── scripts/                  # 工具脚本
    ├── video_processor.py
    └── narrator_generator.py
```

## 快速开始

```bash
# 克隆项目
git clone https://github.com/dazhuang-zs/run_little_donkey.git
cd run_little_donkey/ai-video-narrator

# 安装依赖
pip install -r backend/requirements.txt
cd frontend && npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入API密钥

# 启动服务
python backend/main.py
cd frontend && npm run dev
```

## 开发状态

🚧 项目规划中，即将开始开发

## 作者

大壮 (dazhuang-zs)

## License

MIT