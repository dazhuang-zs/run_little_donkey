# 所需工具技能清单

## 🛠️ 开发所需技能

### 后端开发

| 技能 | 重要度 | 学习成本 | 说明 |
|------|--------|----------|------|
| Python 3.10+ | ★★★★★ | 低 | 后端主要语言 |
| FastAPI | ★★★★★ | 中 | Web框架，支持异步和类型提示 |
| FFmpeg | ★★★★★ | 高 | 视频处理核心工具，必须掌握 |
| MoviePy | ★★★★☆ | 中 | 视频编辑Python库 |
| OpenCV | ★★★★☆ | 高 | 图像处理、关键帧提取 |
| Celery | ★★★☆☆ | 中 | 异步任务队列 |
| SQLAlchemy | ★★★☆☆ | 低 | ORM框架 |
| Redis | ★★★☆☆ | 低 | 缓存和Celery后端 |

### 前端开发

| 技能 | 重要度 | 学习成本 | 说明 |
|------|--------|----------|------|
| Vue 3 | ★★★★★ | 中 | 前端框架（备选React） |
| TypeScript | ★★★★☆ | 中 | 类型安全 |
| Video.js | ★★★★☆ | 中 | 视频播放器 |
| Wavesurfer.js | ★★★☆☆ | 中 | 音频波形可视化 |
| Element Plus | ★★★☆☆ | 低 | UI组件库 |

### AI服务调用

| 技能 | 重要度 | 学习成本 | 说明 |
|------|--------|----------|------|
| OpenAI API | ★★★★★ | 低 | GPT-4V视频分析、GPT-4文案生成 |
| Prompt Engineering | ★★★★★ | 中 | 提示词设计，直接影响生成质量 |
| Claude API | ★★★★☆ | 低 | 备选AI服务 |
| 通义千问 API | ★★★☆☆ | 低 | 国内用户备选 |
| Azure TTS | ★★★★★ | 低 | 语音合成 |
| 阿里云/Minimax TTS | ★★★★☆ | 低 | 国内用户备选 |

### 云服务与部署

| 技能 | 重要度 | 学习成本 | 说明 |
|------|--------|----------|------|
| Docker | ★★★★☆ | 中 | 容器化部署 |
| 阿里云OSS | ★★★★☆ | 低 | 存储（备选腾讯云COS） |
| Nginx | ★★★☆☆ | 中 | 反向代理 |
| PostgreSQL | ★★★☆☆ | 低 | 生产数据库 |

---

## 📚 学习路径建议

### 阶段1: 基础准备（1-2周）

```
Python基础 → FastAPI入门 → FFmpeg基础命令
```

**推荐资源**：
- FastAPI官方文档：https://fastapi.tiangolo.com/zh/
- FFmpeg命令大全：https://ffmpeg.org/ffmpeg.html
- MoviePy文档：https://zulko.github.io/moviepy/

### 阶段2: AI服务接入（1周）

```
OpenAI API调用 → Prompt Engineering → TTS服务集成
```

**推荐资源**：
- OpenAI Cookbook：https://github.com/openclaw/ai-cookbook
- Prompt Engineering Guide：https://www.promptingguide.ai/zh
- Azure TTS文档：https://learn.microsoft.com/zh-cn/azure/cognitive-services/speech-service/

### 阶段3: 视频处理核心（2周）

```
关键帧提取 → FFmpeg视频合成 → 音视频同步
```

### 阶段4: 前端开发（1-2周）

```
Vue 3基础 → 视频播放器集成 → 音频波形组件
```

---

## 🔧 推荐开发工具

### IDE与编辑器

- **VS Code** - 推荐插件：
  - Python、Pylance
  - Vue - Official
  - FFmpeg Explorer
  - GitLens

### 命令行工具

```bash
# FFmpeg（必需）
# macOS: brew install ffmpeg
# Ubuntu: apt install ffmpeg
# Windows: 下载安装包

# Redis（本地开发）
# macOS: brew install redis
# Ubuntu: apt install redis-server

# Docker（部署）
# 各平台官网下载安装
```

### API测试工具

- **Postman** - API测试
- **HTTPie** - 命令行HTTP客户端

### 视频处理工具

- **HandBrake** - 视频转码预览
- **VLC** - 视频播放测试

---

## 🎯 你需要掌握的核心技能

### 必须掌握（不做不出）

1. **Python + FastAPI** - 后端基础
2. **FFmpeg基础命令** - 视频剪辑、合并、转码
3. **OpenAI API调用** - 视频分析和文案生成
4. **TTS服务调用** - 语音合成
5. **Prompt Engineering** - 控制AI生成质量

### 建议掌握（提升效率）

1. **Docker** - 部署和环境一致性
2. **Celery + Redis** - 异步任务处理长耗时操作
3. **云存储OSS** - 视频/音频存储
4. **Vue 3** - 前端界面

### 可选掌握（锦上添花）

1. **OpenCV进阶** - 视频特效处理
2. **AE模板自动化** - 高级视频特效
3. **更多AI模型** - DeepSeek、Claude等

---

## 💡 现有技能复用

根据你的背景（Python经验），可以直接复用：

| 现有技能 | 项目应用 |
|----------|----------|
| Python基础 | 后端开发、脚本工具 |
| GitHub使用 | 代码管理、协作 |

需要新学习的主要是：

1. **FastAPI** - 如果之前用的是Flask/Django，FastAPI上手很快
2. **FFmpeg** - 视频处理的核心，需要花时间
3. **AI API调用** - 相对简单，主要在Prompt设计

---

## 📝 技能检测清单

开发前请确认：

- [ ] Python 3.10+ 环境配置完成
- [ ] FFmpeg 安装并可使用基本命令
- [ ] OpenAI API Key 已获取
- [ ] 了解 FastAPI 基本用法
- [ ] 了解 FFmpeg 常用命令（剪辑、合并、转码）
- [ ] 了解如何调用 OpenAI API
- [ ] 了解 TTS 服务调用方式

如果以上有不确定的项，建议先针对性学习再开始开发。