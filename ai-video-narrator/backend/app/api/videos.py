"""
视频相关API
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
import os

from app.models.schemas import VideoInfo

router = APIRouter()

# 临时存储（生产环境用数据库）
videos_db = {}


@router.post("/", response_model=VideoInfo)
async def upload_video(file: UploadFile = File(...)):
    """上传视频"""
    # 生成ID
    video_id = str(uuid.uuid4())
    
    # 保存文件
    upload_dir = "uploads/videos"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{video_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # TODO: 使用FFmpeg获取视频信息
    video_info = VideoInfo(
        id=video_id,
        name=file.filename,
        url=f"/static/videos/{video_id}_{file.filename}",
        duration=0.0,  # 待实现
        width=0,
        height=0,
        fps=0.0,
        size=len(content)
    )
    
    videos_db[video_id] = video_info
    
    return video_info


@router.get("/{video_id}", response_model=VideoInfo)
async def get_video(video_id: str):
    """获取视频信息"""
    if video_id not in videos_db:
        raise HTTPException(status_code=404, detail="视频不存在")
    return videos_db[video_id]


@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """删除视频"""
    if video_id not in videos_db:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # TODO: 删除文件
    del videos_db[video_id]
    return {"message": "删除成功"}