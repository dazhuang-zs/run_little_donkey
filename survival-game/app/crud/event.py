"""
事件CRUD操作
"""

from typing import Optional, List
from sqlalchemy.orm import Session
import random

from app.models.event import EventCreate, EventChoiceCreate
from app.models.db_models import EventDB, EventChoiceDB


class CRUDEvent:
    """事件CRUD类"""

    def get_event(self, db: Session, event_id: int) -> Optional[EventDB]:
        """根据ID获取事件"""
        return db.query(EventDB).filter(EventDB.id == event_id).first()

    def get_event_by_code(self, db: Session, event_code: str) -> Optional[EventDB]:
        """根据事件代码获取事件"""
        return db.query(EventDB).filter(EventDB.event_code == event_code).first()

    def get_events_by_type(self, db: Session, trigger_type: str) -> List[EventDB]:
        """根据触发类型获取事件"""
        return db.query(EventDB).filter(EventDB.trigger_type == trigger_type, EventDB.is_active == True).all()

    def get_random_event(self, db: Session, day: int, game_state: dict) -> Optional[EventDB]:
        """获取随机事件"""
        # 获取符合天数范围的事件
        query = db.query(EventDB).filter(
            EventDB.is_active == True,
            EventDB.min_day <= day,
            EventDB.max_day >= day,
            EventDB.trigger_type == 'random'
        )

        # 根据权重选择事件
        events = query.all()
        if not events:
            return None

        # 加权随机选择
        weighted_events = []
        for event in events:
            # 检查触发条件
            if event.trigger_condition:
                # TODO: 实现条件检查
                pass
            weighted_events.extend([event] * event.weight)

        return random.choice(weighted_events) if weighted_events else None

    def get_daily_event(self, db: Session, day: int) -> Optional[EventDB]:
        """获取每日事件"""
        event = db.query(EventDB).filter(
            EventDB.is_active == True,
            EventDB.trigger_type == 'daily',
            EventDB.min_day <= day,
            EventDB.max_day >= day
        ).first()
        return event

    def create_event(self, db: Session, event: EventCreate) -> EventDB:
        """创建新事件"""
        db_event = EventDB(**event.dict())
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event

    def get_event_choices(self, db: Session, event_id: int) -> List[EventChoiceDB]:
        """获取事件的所有选择项"""
        return db.query(EventChoiceDB).filter(EventChoiceDB.event_id == event_id).all()

    def get_choice(self, db: Session, choice_id: int) -> Optional[EventChoiceDB]:
        """根据ID获取选择项"""
        return db.query(EventChoiceDB).filter(EventChoiceDB.id == choice_id).first()

    def create_choice(self, db: Session, choice: EventChoiceCreate) -> EventChoiceDB:
        """创建事件选择项"""
        db_choice = EventChoiceDB(**choice.dict())
        db.add(db_choice)
        db.commit()
        db.refresh(db_choice)
        return db_choice

    def apply_choice_effects(self, choice: EventChoiceDB) -> dict:
        """应用选择项效果"""
        return {
            'money': choice.effect_money,
            'health': choice.effect_health,
            'stress': choice.effect_stress,
            'hunger': choice.effect_hunger,
            'energy': choice.effect_energy,
            'job_satisfaction': choice.effect_job_satisfaction,
            'relationship': choice.effect_relationship,
        }


crud_event = CRUDEvent()