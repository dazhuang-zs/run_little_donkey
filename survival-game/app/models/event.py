"""
事件模型
"""

from typing import Optional, List
from pydantic import BaseModel


class EventBase(BaseModel):
    """事件基础模型"""
    event_code: str
    title: str
    description: str
    trigger_type: str  # daily, random, conditional
    trigger_condition: Optional[str] = None
    min_day: int = 1
    max_day: int = 30
    weight: int = 10
    is_active: bool = True


class EventCreate(EventBase):
    """创建事件模型"""
    pass


class EventInDB(EventBase):
    """数据库中的事件模型"""
    id: int

    model_config = {"from_attributes": True}


class Event(EventBase):
    """返回给客户端的事件模型"""
    id: int

    model_config = {"from_attributes": True}


class EventChoiceBase(BaseModel):
    """事件选择项基础模型"""
    choice_text: str
    effect_money: int = 0
    effect_health: int = 0
    effect_stress: int = 0
    effect_hunger: int = 0
    effect_energy: int = 0
    effect_job_satisfaction: int = 0
    effect_relationship: int = 0
    next_event_id: Optional[int] = None
    is_ending_trigger: bool = False
    ending_id: Optional[int] = None


class EventChoiceCreate(EventChoiceBase):
    """创建事件选择项模型"""
    event_id: int


class EventChoiceInDB(EventChoiceBase):
    """数据库中的事件选择项模型"""
    id: int
    event_id: int

    model_config = {"from_attributes": True}


class EventChoice(EventChoiceBase):
    """返回给客户端的事件选择项模型"""
    id: int
    event_id: int

    model_config = {"from_attributes": True}


class EventWithChoices(Event):
    """包含选择项的事件模型"""
    choices: List[EventChoice] = []


class EventChoiceRequest(BaseModel):
    """事件选择请求模型"""
    choice_id: int


class EventChoiceResult(BaseModel):
    """事件选择结果模型"""
    effects: dict
    next_event: Optional[Event] = None
    triggered_ending: Optional[dict] = None


class CurrentEventResponse(BaseModel):
    """当前事件响应模型"""
    success: bool = True
    data: Optional[dict] = None