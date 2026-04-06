"""
玩家CRUD操作
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
import bcrypt

from app.models.player import PlayerCreate, PlayerUpdate
from app.models.db_models import PlayerDB


def hash_password(password: str) -> str:
    """哈希密码"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


class CRUDPlayer:
    """玩家CRUD类"""

    def get(self, db: Session, player_id: int) -> Optional[PlayerDB]:
        """根据ID获取玩家"""
        return db.query(PlayerDB).filter(PlayerDB.id == player_id).first()

    def get_by_username(self, db: Session, username: str) -> Optional[PlayerDB]:
        """根据用户名获取玩家"""
        return db.query(PlayerDB).filter(PlayerDB.username == username).first()

    def get_by_email(self, db: Session, email: str) -> Optional[PlayerDB]:
        """根据邮箱获取玩家"""
        return db.query(PlayerDB).filter(PlayerDB.email == email).first()

    def get_by_username_or_email(self, db: Session, username: str, email: str) -> Optional[PlayerDB]:
        """根据用户名或邮箱获取玩家"""
        return db.query(PlayerDB).filter(
            or_(PlayerDB.username == username, PlayerDB.email == email)
        ).first()

    def create(self, db: Session, player: PlayerCreate) -> PlayerDB:
        """创建新玩家"""
        hashed_password = hash_password(player.password)
        db_player = PlayerDB(
            username=player.username,
            email=player.email,
            password_hash=hashed_password
        )
        db.add(db_player)
        db.commit()
        db.refresh(db_player)
        return db_player

    def update(self, db: Session, db_player: PlayerDB, player_update: PlayerUpdate) -> PlayerDB:
        """更新玩家信息"""
        update_data = player_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_player, field, value)
        db.add(db_player)
        db.commit()
        db.refresh(db_player)
        return db_player

    def update_last_login(self, db: Session, db_player: PlayerDB) -> PlayerDB:
        """更新最后登录时间"""
        db_player.last_login_at = db.func.now()
        db.add(db_player)
        db.commit()
        db.refresh(db_player)
        return db_player

    def increment_games_played(self, db: Session, db_player: PlayerDB) -> PlayerDB:
        """增加游戏次数"""
        db_player.total_games_played += 1
        db.add(db_player)
        db.commit()
        db.refresh(db_player)
        return db_player

    def update_best_score(self, db: Session, db_player: PlayerDB, score: int) -> PlayerDB:
        """更新最高分"""
        if score > db_player.best_score:
            db_player.best_score = score
            db.add(db_player)
            db.commit()
            db.refresh(db_player)
        return db_player

    def delete(self, db: Session, player_id: int) -> Optional[PlayerDB]:
        """删除玩家"""
        db_player = self.get(db, player_id)
        if db_player:
            db.delete(db_player)
            db.commit()
        return db_player

    def authenticate(self, db: Session, username: str, password: str) -> Optional[PlayerDB]:
        """认证玩家"""
        db_player = self.get_by_username(db, username)
        if not db_player:
            return None
        if not verify_password(password, db_player.password_hash):
            return None
        return db_player


crud_player = CRUDPlayer()