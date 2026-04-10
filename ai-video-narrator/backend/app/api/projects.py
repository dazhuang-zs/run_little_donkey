"""
项目管理API
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
from datetime import datetime

from app.models.schemas import (
    Project, 
    ProjectStatus,
    NarratorStyle,
    VoiceOption
)

router = APIRouter()

# 临时存储
projects_db = {}


@router.post("/", response_model=Project)
async def create_project(
    name: str,
    video_id: str,
    video_url: str
):
    """创建项目"""
    project_id = str(uuid.uuid4())
    
    project = Project(
        id=project_id,
        name=name,
        video_id=video_id,
        video_url=video_url,
        style=None,
        voice=None,
        script=None,
        audio_url=None,
        result_url=None,
        status=ProjectStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    projects_db[project_id] = project
    return project


@router.get("/", response_model=List[Project])
async def list_projects():
    """获取项目列表"""
    return list(projects_db.values())


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """获取项目详情"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="项目不存在")
    return projects_db[project_id]


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    style: Optional[NarratorStyle] = None,
    voice: Optional[VoiceOption] = None
):
    """更新项目"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project = projects_db[project_id]
    
    if style:
        project.style = style
    if voice:
        project.voice = voice
    
    project.updated_at = datetime.now()
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    del projects_db[project_id]
    return {"message": "删除成功"}


@router.post("/{project_id}/compose")
async def compose_video(project_id: str):
    """合成视频"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # TODO: 启动视频合成任务
    project = projects_db[project_id]
    project.status = ProjectStatus.COMPOSING
    project.updated_at = datetime.now()
    
    return {
        "message": "合成任务已启动",
        "project_id": project_id
    }


@router.get("/{project_id}/progress")
async def get_progress(project_id: str):
    """获取项目进度"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project = projects_db[project_id]
    
    return {
        "project_id": project_id,
        "status": project.status,
        "progress": 0,  # TODO: 实际进度
        "message": "处理中..."
    }