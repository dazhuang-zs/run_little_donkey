"""
动作CRUD操作
"""

from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.action import ActionCreate, PlayerActionCreate
from app.models.db_models import ActionDB, PlayerActionDB


class CRUDAction:
    """动作CRUD类"""

    def get_action(self, db: Session, action_id: int) -> Optional[ActionDB]:
        """根据ID获取动作"""
        return db.query(ActionDB).filter(ActionDB.id == action_id).first()

    def get_action_by_code(self, db: Session, action_code: str) -> Optional[ActionDB]:
        """根据动作代码获取动作"""
        return db.query(ActionDB).filter(ActionDB.action_code == action_code).first()

    def get_all_actions(self, db: Session) -> List[ActionDB]:
        """获取所有动作"""
        return db.query(ActionDB).filter(ActionDB.is_available == True).all()

    def get_available_actions(self, db: Session, player_id: int, game_state_id: int) -> List[ActionDB]:
        """获取当前可用的动作"""
        # 获取所有可用动作
        all_actions = self.get_all_actions(db)

        # 检查冷却时间
        available_actions = []
        for action in all_actions:
            if action.cooldown_hours == 0:
                available_actions.append(action)
            else:
                # 检查最近是否执行过该动作
                last_action = db.query(PlayerActionDB).filter(
                    PlayerActionDB.player_id == player_id,
                    PlayerActionDB.game_state_id == game_state_id,
                    PlayerActionDB.action_id == action.id
                ).order_by(PlayerActionDB.executed_at.desc()).first()

                if not last_action:
                    available_actions.append(action)
                else:
                    # 检查是否超过冷却时间
                    cooldown_time = last_action.executed_at + timedelta(hours=action.cooldown_hours)
                    if datetime.now() > cooldown_time:
                        available_actions.append(action)

        return available_actions

    def create_action(self, db: Session, action: ActionCreate) -> ActionDB:
        """创建新动作"""
        db_action = ActionDB(**action.dict())
        db.add(db_action)
        db.commit()
        db.refresh(db_action)
        return db_action

    def record_player_action(self, db: Session, player_action: PlayerActionCreate) -> PlayerActionDB:
        """记录玩家动作执行"""
        db_player_action = PlayerActionDB(**player_action.dict())
        db.add(db_player_action)
        db.commit()
        db.refresh(db_player_action)
        return db_player_action

    def can_afford_action(self, game_state: dict, action: ActionDB) -> bool:
        """检查玩家是否能承担动作消耗"""
        if game_state['money'] < action.cost_money:
            return False
        if game_state['energy'] < action.cost_energy:
            return False
        return True

    def apply_action_effects(self, action: ActionDB) -> dict:
        """获取动作效果"""
        return {
            'money': -action.cost_money + (action.effect_money if hasattr(action, 'effect_money') else 0),
            'energy': -action.cost_energy,
            'health': action.effect_health,
            'stress': action.effect_stress,
            'hunger': action.effect_hunger,
            'job_satisfaction': action.effect_job_satisfaction,
            'relationship': action.effect_relationship,
        }


crud_action = CRUDAction()