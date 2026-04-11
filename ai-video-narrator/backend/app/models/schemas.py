"""
数据模型定义
"""
from pydantic import BaseModel
from enum import Enum
from typing import List, Optional
from datetime import datetime


class NarratorStyle(str, Enum):
    """解说风格"""
    PROFESSIONAL = "professional"    # 专业解说员
    HUMOROUS = "humorous"            # 幽默吐槽风
    EMOTIONAL = "emotional"          # 情感共情风
    SUSPENSE = "suspense"            # 悬疑推理风
    EDUCATIONAL = "educational"      # 知识科普风


class VoiceOption(str, Enum):
    """配音声音选项"""
    MALE_STANDARD = "male_standard"
    MALE_DEEP = "male_deep"
    FEMALE_SWEET = "female_sweet"
    FEMALE_PROFESSIONAL = "female_professional"
    SPECIAL_CARTOON = "special_cartoon"


class ProjectStatus(str, Enum):
    """项目状态"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    SYNTHESIZING = "synthesizing"
    COMPOSING = "composing"
    COMPLETED = "completed"
    FAILED = "failed"


# ========== 请求模型 ==========

class VideoUploadRequest(BaseModel):
    """视频上传请求"""
    name: Optional[str] = None


class ScriptGenerateRequest(BaseModel):
    """脚本生成请求"""
    project_id: str
    style: NarratorStyle
    additional_context: Optional[str] = None


class ScriptEditRequest(BaseModel):
    """脚本编辑请求"""
    content: str


class AudioSynthesizeRequest(BaseModel):
    """音频合成请求"""
    script_id: str
    voice: VoiceOption
    speed: float = 1.0


class VideoComposeRequest(BaseModel):
    """视频合成请求"""
    project_id: str
    include_subtitles: bool = True


# ========== 响应模型 ==========

class VideoInfo(BaseModel):
    """视频信息"""
    id: str
    name: str
    url: str
    duration: float
    width: int
    height: int
    fps: float
    size: int


class VideoAnalysis(BaseModel):
    """视频分析结果"""
    video_id: str
    duration: float
    scenes: List[str]
    main_subjects: List[str]
    key_moments: List[dict]


class NarratorScript(BaseModel):
    """解说脚本"""
    id: str
    content: str
    style: NarratorStyle
    duration_estimate: float
    segments: List[dict]
    created_at: datetime
    updated_at: datetime


class Project(BaseModel):
    """项目"""
    id: str
    name: str
    video_id: str
    video_url: str
    style: Optional[NarratorStyle] = None
    voice: Optional[VoiceOption] = None
    script: Optional[NarratorScript] = None
    audio_url: Optional[str] = None
    result_url: Optional[str] = None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class ProgressResponse(BaseModel):
    """进度响应"""
    project_id: str
    status: ProjectStatus
    progress: int  # 0-100
    message: str