"""
脚本相关API
"""
from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from datetime import datetime

from app.models.schemas import (
    NarratorScript, 
    ScriptGenerateRequest, 
    ScriptEditRequest,
    NarratorStyle
)

router = APIRouter()

# 临时存储
scripts_db = {}


@router.post("/generate")
async def generate_script(request: ScriptGenerateRequest):
    """生成解说脚本"""
    # TODO: 调用AI服务生成脚本
    script_id = str(uuid.uuid4())
    
    # 示例脚本（实际由AI生成）
    sample_content = f"""
【开场】
今天我们来聊聊这个视频的内容，风格是{request.style.value}...

【主体】
...（AI根据视频内容生成）...

【结尾】
感谢观看，我们下期再见！
"""
    
    script = NarratorScript(
        id=script_id,
        content=sample_content,
        style=request.style,
        duration_estimate=30.0,
        segments=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    scripts_db[script_id] = script
    return script


@router.get("/{script_id}", response_model=NarratorScript)
async def get_script(script_id: str):
    """获取脚本"""
    if script_id not in scripts_db:
        raise HTTPException(status_code=404, detail="脚本不存在")
    return scripts_db[script_id]


@router.put("/{script_id}", response_model=NarratorScript)
async def edit_script(script_id: str, request: ScriptEditRequest):
    """编辑脚本"""
    if script_id not in scripts_db:
        raise HTTPException(status_code=404, detail="脚本不存在")
    
    script = scripts_db[script_id]
    script.content = request.content
    script.updated_at = datetime.now()
    
    return script