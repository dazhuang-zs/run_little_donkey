# 技术架构设计

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          前端应用层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ 视频上传    │  │ 脚本编辑器  │  │ 预览导出    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              ↓ API网关
┌─────────────────────────────────────────────────────────────────┐
│                          后端服务层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ 视频处理    │  │ AI服务      │  │ 音频合成    │              │
│  │ Service     │  │ Service     │  │ Service     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────┐  ┌─────────────┐                                │
│  │ 任务队列    │  │ 存储服务    │                                │
│  └─────────────┘  └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                          外部服务层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ 视觉AI API  │  │ 语言AI API  │  │ TTS API     │              │
│  │ (GPT-4V等)  │  │ (GPT-4等)   │  │ (Azure等)   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## 技术选型

### AI服务选型

#### 视频理解（Vision Models）

| 服务商 | 模型 | 优势 | 劣势 | 推荐度 |
|--------|------|------|------|--------|
| OpenAI | GPT-4V | 多模态理解强、API稳定 | 成本高 | ★★★★★ |
| Anthropic | Claude 3 | 上下文长、理解能力强 | 国内访问需代理 | ★★★★☆ |
| 阿里云 | 通义千问VL | 国内访问稳定、成本较低 | 能力稍弱 | ★★★★☆ |
| 智谱AI | GLM-4V | 国内访问稳定、性价比高 | 新服务稳定性待验证 | ★★★★☆ |

**推荐方案**: 主用 GPT-4V，备选 通义千问VL

#### 文案生成（LLM）

| 服务商 | 模型 | 优势 | 推荐度 |
|--------|------|------|--------|
| OpenAI | GPT-4 | 效果最好 | ★★★★★ |
| Anthropic | Claude 3.5 Sonnet | 长上下文、效果好 | ★★★★★ |
| 智谱AI | GLM-4 | 国内稳定 | ★★★★☆ |
| DeepSeek | DeepSeek-V3 | 便宜、效果好 | ★★★★☆ |

**推荐方案**: 主用 GPT-4/Claude，备选 DeepSeek/GLM-4

#### 语音合成（TTS）

| 服务商 | 特点 | 音色数量 | 价格 | 推荐度 |
|--------|------|----------|------|--------|
| Azure TTS | 质量高、情感丰富 | 100+ | 较高 | ★★★★★ |
| 阿里云TTS | 国内稳定 | 50+ | 中等 | ★★★★☆ |
| Minimax | 中文效果好、情感自然 | 20+ | 中等 | ★★★★☆ |
| 讯飞TTS | 中文专业 | 30+ | 中等 | ★★★★☆ |

**推荐方案**: 主用 Azure TTS，国内用户用 Minimax/阿里云TTS

### 后端技术栈

```python
# 核心框架
FastAPI==0.109.0          # Web框架，性能好、类型提示友好
uvicorn==0.27.0           # ASGI服务器

# 视频处理
ffmpeg-python==0.2.0      # FFmpeg封装
moviepy==1.0.3            # 视频编辑库
opencv-python==4.9.0      # 图像处理（关键帧提取）
Pillow==10.2.0            # 图像处理

# AI SDK
openai==1.12.0            # OpenAI SDK
anthropic==0.18.0         # Claude SDK
dashscope==1.17.0         # 阿里云通义SDK

# 音频处理
pydub==0.25.1             # 音频处理
python-multipart==0.0.9   # 文件上传

# 任务队列
celery==5.3.6             # 异步任务队列
redis==5.0.1              # Celery后端

# 数据库
sqlalchemy==2.0.25        # ORM
alembic==1.13.1           # 数据库迁移

# 存储
oss2==2.18.4              # 阿里云OSS SDK

# 工具
pydantic==2.6.0           # 数据验证
python-dotenv==1.0.1      # 环境变量管理
loguru==0.7.2             # 日志
```

### 前端技术栈

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "axios": "^1.6.5",
    "element-plus": "^2.5.3",
    "@vueuse/core": "^10.7.2",
    "wavesurfer.js": "^7.7.0",
    "video.js": "^8.10.0"
  },
  "devDependencies": {
    "vite": "^5.0.12",
    "typescript": "^5.3.3",
    "@vitejs/plugin-vue": "^5.0.3"
  }
}
```

## 核心模块设计

### 1. 视频处理服务

```python
# backend/app/services/video_service.py

class VideoService:
    """视频处理核心服务"""
    
    async def upload_video(self, file: UploadFile) -> str:
        """上传视频到存储"""
        pass
    
    async def extract_keyframes(
        self, 
        video_path: str, 
        interval: int = 2
    ) -> List[str]:
        """提取关键帧，返回图片URL列表"""
        pass
    
    async def analyze_video(self, video_path: str) -> VideoAnalysis:
        """分析视频内容（场景、人物、文本等）"""
        pass
    
    async def get_video_info(self, video_path: str) -> VideoInfo:
        """获取视频基本信息（时长、分辨率等）"""
        pass
```

### 2. AI服务

```python
# backend/app/services/ai_service.py

class AIService:
    """AI生成服务"""
    
    async def analyze_frames(
        self, 
        frames: List[str]
    ) -> FrameAnalysis:
        """使用视觉模型分析视频帧"""
        pass
    
    async def generate_script(
        self,
        video_analysis: VideoAnalysis,
        style: NarratorStyle,
        additional_context: Optional[str] = None
    ) -> NarratorScript:
        """生成解说脚本"""
        pass
    
    async def optimize_script(
        self,
        script: str,
        duration: float
    ) -> str:
        """优化脚本时长匹配"""
        pass
```

### 3. 音频服务

```python
# backend/app/services/audio_service.py

class AudioService:
    """音频合成服务"""
    
    async def synthesize_speech(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        emotion: Optional[str] = None
    ) -> str:
        """合成语音，返回音频URL"""
        pass
    
    async def merge_audio(
        self,
        narration_audio: str,
        bgm_audio: Optional[str] = None,
        bgm_volume: float = 0.3
    ) -> str:
        """合并解说音频和背景音乐"""
        pass
```

### 4. 合成服务

```python
# backend/app/services/compose_service.py

class ComposeService:
    """视频合成服务"""
    
    async def compose_video(
        self,
        video_path: str,
        audio_path: str,
        subtitles: Optional[List[Subtitle]] = None,
        style: Optional[ComposeStyle] = None
    ) -> str:
        """合成最终视频"""
        pass
    
    async def generate_subtitles(
        self,
        text: str,
        audio_duration: float
    ) -> List[Subtitle]:
        """生成字幕时间轴"""
        pass
```

## 数据模型

```python
# backend/app/models/schemas.py

from pydantic import BaseModel
from enum import Enum
from typing import List, Optional
from datetime import datetime

class NarratorStyle(str, Enum):
    PROFESSIONAL = "professional"    # 专业解说员
    HUMOROUS = "humorous"            # 幽默吐槽风
    EMOTIONAL = "emotional"          # 情感共情风
    SUSPENSE = "suspense"            # 悬疑推理风
    EDUCATIONAL = "educational"      # 知识科普风

class VoiceOption(str, Enum):
    MALE_STANDARD = "male_standard"
    MALE_DEEP = "male_deep"
    FEMALE_SWEET = "female_sweet"
    FEMALE_PROFESSIONAL = "female_professional"
    SPECIAL_CARTOON = "special_cartoon"

class VideoAnalysis(BaseModel):
    """视频分析结果"""
    duration: float
    scenes: List[str]              # 场景描述列表
    main_subjects: List[str]       # 主要人物/物体
    text_content: List[str]        # OCR识别的文字
    key_moments: List[dict]        # 关键时刻（时间点+描述）

class NarratorScript(BaseModel):
    """解说脚本"""
    content: str                   # 脚本内容
    segments: List[dict]           # 分段（时间+文本）
    duration_estimate: float       # 预估时长
    style: NarratorStyle

class Project(BaseModel):
    """项目"""
    id: str
    name: str
    video_url: str
    style: NarratorStyle
    voice: VoiceOption
    script: Optional[NarratorScript]
    audio_url: Optional[str]
    result_url: Optional[str]
    status: str                    # pending/processing/completed/failed
    created_at: datetime
    updated_at: datetime
```

## API设计

### RESTful API

```yaml
# 视频管理
POST   /api/videos                # 上传视频
GET    /api/videos/{id}           # 获取视频信息
DELETE /api/videos/{id}           # 删除视频

# 分析与生成
POST   /api/analyze/{video_id}    # 分析视频
POST   /api/generate/script       # 生成脚本
PUT    /api/scripts/{id}          # 编辑脚本

# 音频合成
POST   /api/synthesize            # 合成语音
GET    /api/voices                # 获取可用声音列表

# 视频合成
POST   /api/compose               # 合成最终视频
GET    /api/download/{id}         # 下载结果视频

# 项目管理
POST   /api/projects              # 创建项目
GET    /api/projects              # 获取项目列表
GET    /api/projects/{id}         # 获取项目详情
PUT    /api/projects/{id}         # 更新项目
DELETE /api/projects/{id}         # 删除项目
```

### WebSocket API（实时进度）

```
ws://host/ws/project/{project_id}

# 消息格式
{
  "type": "progress",
  "stage": "analyzing|generating|synthesizing|composing",
  "progress": 0-100,
  "message": "正在分析视频内容..."
}
```

## 部署架构

### 开发环境

```
本地开发
├── 前端: localhost:5173 (Vite dev server)
├── 后端: localhost:8000 (Uvicorn)
├── 数据库: SQLite
└── 存储: 本地文件系统
```

### 生产环境

```
┌─────────────┐     ┌─────────────┐
│   CDN       │────▶│  OSS存储    │
│  (静态资源)  │     │ (视频/音频)  │
└─────────────┘     └─────────────┘
                            │
┌─────────────┐     ┌──────▼──────┐
│   Nginx     │────▶│   API服务   │
│  (反向代理)  │     │  (Docker)   │
└─────────────┘     └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  PostgreSQL │
                    │   Redis     │
                    └─────────────┘
```

## 成本估算

### API调用成本（按月，100活跃用户）

| 服务 | 月调用量 | 单价 | 月成本 |
|------|----------|------|--------|
| GPT-4V分析 | 1000次 | ¥0.5/次 | ¥500 |
| GPT-4生成 | 3000次 | ¥0.1/次 | ¥300 |
| Azure TTS | 50万字符 | ¥4/万字符 | ¥200 |
| OSS存储 | 100GB | ¥0.12/GB/月 | ¥12 |
| 流量 | 500GB | ¥0.5/GB | ¥250 |
| **合计** | - | - | **¥1262/月** |

### 优化建议

1. 使用DeepSeek/GLM-4替代GPT-4可降低50%成本
2. 使用阿里云TTS可降低30%成本
3. 实现结果缓存可减少重复调用