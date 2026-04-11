"""
事件引擎服务
处理游戏事件触发和选择
"""

import random
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.crud.event import crud_event
from app.crud.game import crud_game
from app.models.event import EventChoiceCreate


class EventEngine:
    """事件引擎"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_current_event(self, player_id: int) -> Optional[Dict[str, Any]]:
        """获取当前触发的事件"""
        game = crud_game.get_active_game(self.db, player_id)
        if not game or game.is_game_over:
            return None
        
        # 根据游戏天数和状态随机触发事件
        # 这里简化处理，随机选择一个事件
        events = crud_event.get_all_active(self.db)
        if not events:
            return None
        
        # 根据权重随机选择
        weights = [event.weight for event in events]
        event = random.choices(events, weights=weights, k=1)[0]
        
        # 获取事件的选择项
        choices = []
        for choice in event.choices:
            choices.append({
                "id": choice.id,
                "choice_text": choice.choice_text,
                "effect_money": choice.effect_money,
                "effect_health": choice.effect_health,
                "effect_stress": choice.effect_stress,
                "effect_hunger": choice.effect_hunger,
                "effect_energy": choice.effect_energy,
                "effect_job_satisfaction": choice.effect_job_satisfaction,
                "effect_relationship": choice.effect_relationship
            })
        
        return {
            "id": event.id,
            "event_code": event.event_code,
            "title": event.title,
            "description": event.description,
            "choices": choices
        }
    
    def process_choice(self, player_id: int, choice_id: int) -> Dict[str, Any]:
        """处理事件选择"""
        game = crud_game.get_active_game(self.db, player_id)
        if not game:
            return {
                "success": False,
                "message": "没有进行中的游戏"
            }
        
        # 获取选择项
        choice = crud_event.get_choice(self.db, choice_id)
        if not choice:
            return {
                "success": False,
                "message": "无效的选择"
            }
        
        # 应用效果
        from app.models.game import GameStateUpdate
        
        new_money = game.money + choice.effect_money
        new_health = max(0, min(100, game.health + choice.effect_health))
        new_stress = max(0, min(100, game.stress + choice.effect_stress))
        new_hunger = max(0, min(100, game.hunger + choice.effect_hunger))
        new_energy = max(0, min(100, game.energy + choice.effect_energy))
        new_job_satisfaction = max(0, min(100, game.job_satisfaction + choice.effect_job_satisfaction))
        new_relationship = max(0, min(100, game.relationship + choice.effect_relationship))
        
        game_update = GameStateUpdate(
            money=new_money,
            health=new_health,
            stress=new_stress,
            hunger=new_hunger,
            energy=new_energy,
            job_satisfaction=new_job_satisfaction,
            relationship=new_relationship
        )
        
        updated_game = crud_game.update(self.db, db_obj=game, obj_in=game_update)
        
        # 检查是否触发结局
        triggered_ending = None
        if choice.is_ending_trigger and choice.ending_id:
            from app.crud.ending import crud_ending
            ending = crud_ending.get(self.db, id=choice.ending_id)
            if ending:
                triggered_ending = {
                    "id": ending.id,
                    "code": ending.code,
                    "title": ending.title,
                    "description": ending.description
                }
                # 结束游戏
                crud_game.update(
                    self.db,
                    db_obj=updated_game,
                    obj_in=GameStateUpdate(is_game_over=True)
                )
        
        return {
            "success": True,
            "message": "选择处理成功",
            "data": {
                "effects": {
                    "money": choice.effect_money,
                    "health": choice.effect_health,
                    "stress": choice.effect_stress,
                    "hunger": choice.effect_hunger,
                    "energy": choice.effect_energy,
                    "job_satisfaction": choice.effect_job_satisfaction,
                    "relationship": choice.effect_relationship
                },
                "updated_game_state": {
                    "money": updated_game.money,
                    "health": updated_game.health,
                    "stress": updated_game.stress,
                    "hunger": updated_game.hunger,
                    "energy": updated_game.energy,
                    "job_satisfaction": updated_game.job_satisfaction,
                    "relationship": updated_game.relationship
                },
                "triggered_ending": triggered_ending
            }
        }
    
    def trigger_random_event(self, player_id: int) -> Optional[Dict[str, Any]]:
        """触发随机事件"""
        # 30% 概率触发事件
        if random.random() > 0.3:
            return None
        
        return self.get_current_event(player_id)


# 创建引擎实例的工厂函数
def get_event_engine(db: Session) -> EventEngine:
    """获取事件引擎实例"""
    return EventEngine(db)
