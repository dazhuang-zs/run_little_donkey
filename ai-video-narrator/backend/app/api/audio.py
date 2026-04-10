"""
音频合成API
"""
from fastapi import APIRouter, HTTPException
from typing import List
import uuid

from app.models.schemas import VoiceOption, AudioSynthesizeRequest

router = APIRouter()


@router.get("/voices")
async def get_voices():
    """获取可用声音列表"""
    return {
        "voices": [
            {
                "id": "male_standard",
                "name": "标准男声",
                "gender": "male",
                "style": "professional",
                "preview_url": "/static/voices/male_standard_preview.mp3"
            },
            {
                "id": "male_deep",
                "name": "磁性男声",
                "gender": "male",
                "style": "deep",
                "preview_url": "/static/voices/male_deep_preview.mp3"
            },
            {
                "id": "female_sweet",
                "name": "甜美女声",
                "gender": "female",
                "style": "sweet",
                "preview_url": "/static/voices/female_sweet_preview.mp3"
            },
            {
                "id": "female_professional",
                "name": "专业女声",
                "gender": "female",
                "style": "professional",
                "preview_url": "/static/voices/female_professional_preview.mp3"
            },
            {
                "id": "special_cartoon",
                "name": "卡通音色",
                "gender": "neutral",
                "style": "cartoon",
                "preview_url": "/static/voices/special_cartoon_preview.mp3"
            }
        ]
    }


@router.post("/synthesize")
async def synthesize_audio(request: AudioSynthesizeRequest):
    """合成语音"""
    # TODO: 调用TTS服务
    audio_id = str(uuid.uuid4())
    
    return {
        "audio_id": audio_id,
        "audio_url": f"/static/audio/{audio_id}.mp3",
        "duration": 30.0,  # 假设30秒
        "voice": request.voice,
        "status": "completed"
    }


@router.get("/{audio_id}")
async def get_audio(audio_id: str):
    """获取音频信息"""
    return {
        "audio_id": audio_id,
        "audio_url": f"/static/audio/{audio_id}.mp3",
        "duration": 30.0
    }