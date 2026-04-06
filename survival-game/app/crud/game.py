"""
游戏状态CRUD操作
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.game import GameStateCreate, GameStateUpdate
from app.models.db_models import GameStateDB, PlayerDB


class CRUDGame:
    """游戏状态CRUD类"""

    def get(self, db: Session, game_state_id: int) -> Optional[GameStateDB]:
        """根据ID获取游戏状态"""
        return db.query(GameStateDB).filter(GameStateDB.id == game_state_id).first()

    def get_by_player(self, db: Session, player_id: int, only_active: bool = True) -> Optional[GameStateDB]:
        """根据玩家ID获取游戏状态"""
        query = db.query(GameStateDB).filter(GameStateDB.player_id == player_id)
        if only_active:
            query = query.filter(GameStateDB.is_game_over == False)
        return query.order_by(GameStateDB.created_at.desc()).first()

    def get_all_by_player(self, db: Session, player_id: int) -> List[GameStateDB]:
        """获取玩家的所有游戏状态"""
        return db.query(GameStateDB).filter(GameStateDB.player_id == player_id).all()

    def create(self, db: Session, game_state: GameStateCreate) -> GameStateDB:
        """创建新游戏状态"""
        db_game_state = GameStateDB(**game_state.dict())
        db.add(db_game_state)
        db.commit()
        db.refresh(db_game_state)
        return db_game_state

    def update(self, db: Session, db_game_state: GameStateDB, game_update: GameStateUpdate) -> GameStateDB:
        """更新游戏状态"""
        update_data = game_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_game_state, field, value)
        db.add(db_game_state)
        db.commit()
        db.refresh(db_game_state)
        return db_game_state

    def delete(self, db: Session, game_state_id: int) -> Optional[GameStateDB]:
        """删除游戏状态"""
        db_game_state = self.get(db, game_state_id)
        if db_game_state:
            db.delete(db_game_state)
            db.commit()
        return db_game_state

    def end_game(self, db: Session, db_game_state: GameStateDB) -> GameStateDB:
        """结束游戏"""
        db_game_state.is_game_over = True
        db.add(db_game_state)
        db.commit()
        db.refresh(db_game_state)
        return db_game_state

    def advance_day(self, db: Session, db_game_state: GameStateDB) -> GameStateDB:
        """推进到第二天"""
        db_game_state.day += 1
        if db_game_state.day > 30:
            db_game_state.is_game_over = True
        db.add(db_game_state)
        db.commit()
        db.refresh(db_game_state)
        return db_game_state

    def update_resources(self, db: Session, db_game_state: GameStateDB, **kwargs) -> GameStateDB:
        """更新游戏资源"""
        for key, value in kwargs.items():
            if hasattr(db_game_state, key):
                current_value = getattr(db_game_state, key)
                # 确保资源值在合理范围内
                if key in ['health', 'energy']:
                    new_value = max(0, min(100, current_value + value))
                elif key in ['stress', 'hunger']:
                    new_value = max(0, min(100, current_value + value))
                elif key == 'job_satisfaction':
                    new_value = max(0, min(100, current_value + value))
                elif key == 'relationship':
                    new_value = max(0, min(100, current_value + value))
                elif key == 'money':
                    new_value = current_value + value
                else:
                    new_value = current_value + value
                setattr(db_game_state, key, new_value)
        db.add(db_game_state)
        db.commit()
        db.refresh(db_game_state)
        return db_game_state

    def check_game_over_conditions(self, db: Session, db_game_state: GameStateDB) -> dict:
        """检查游戏结束条件"""
        conditions = {
            'health': db_game_state.health <= 0,
            'stress': db_game_state.stress >= 100,
            'hunger': db_game_state.hunger >= 100,
            'money': db_game_state.money < -10000,
            'max_day': db_game_state.day > 30,
        }
        return conditions


crud_game = CRUDGame()