"""
SQLAlchemy 数据库模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PlayerDB(Base):
    """玩家数据库模型"""
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    total_games_played = Column(Integer, default=0)
    best_score = Column(Integer, default=0)

    # 关系
    game_states = relationship("GameStateDB", back_populates="player", cascade="all, delete-orphan")
    player_endings = relationship("PlayerEndingDB", back_populates="player", cascade="all, delete-orphan")
    player_actions = relationship("PlayerActionDB", back_populates="player", cascade="all, delete-orphan")


class GameStateDB(Base):
    """游戏状态数据库模型"""
    __tablename__ = "game_states"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    day = Column(Integer, default=1)
    time_of_day = Column(String(10), default="morning")
    money = Column(Integer, default=2000)
    health = Column(Integer, default=100)
    stress = Column(Integer, default=0)
    hunger = Column(Integer, default=0)
    energy = Column(Integer, default=100)
    job_level = Column(Integer, default=1)
    job_satisfaction = Column(Integer, default=50)
    relationship = Column(Integer, default=50)
    is_game_over = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    player = relationship("PlayerDB", back_populates="game_states")
    player_endings = relationship("PlayerEndingDB", back_populates="game_state", cascade="all, delete-orphan")
    player_actions = relationship("PlayerActionDB", back_populates="game_state", cascade="all, delete-orphan")


class EventDB(Base):
    """事件数据库模型"""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_code = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    trigger_type = Column(String(20), nullable=False)
    trigger_condition = Column(Text, nullable=True)
    min_day = Column(Integer, default=1)
    max_day = Column(Integer, default=30)
    weight = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)

    # 关系
    choices = relationship("EventChoiceDB", back_populates="event", cascade="all, delete-orphan")


class EventChoiceDB(Base):
    """事件选择项数据库模型"""
    __tablename__ = "event_choices"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    choice_text = Column(String(500), nullable=False)
    effect_money = Column(Integer, default=0)
    effect_health = Column(Integer, default=0)
    effect_stress = Column(Integer, default=0)
    effect_hunger = Column(Integer, default=0)
    effect_energy = Column(Integer, default=0)
    effect_job_satisfaction = Column(Integer, default=0)
    effect_relationship = Column(Integer, default=0)
    next_event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    is_ending_trigger = Column(Boolean, default=False)
    ending_id = Column(Integer, ForeignKey("endings.id"), nullable=True)

    # 关系
    event = relationship("EventDB", back_populates="choices", foreign_keys=[event_id])
    next_event = relationship("EventDB", foreign_keys=[next_event_id], remote_side=[EventDB.id])
    ending = relationship("EndingDB", back_populates="event_choices")


class ActionDB(Base):
    """动作数据库模型"""
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    action_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    cost_money = Column(Integer, default=0)
    cost_energy = Column(Integer, default=0)
    effect_health = Column(Integer, default=0)
    effect_stress = Column(Integer, default=0)
    effect_hunger = Column(Integer, default=0)
    effect_job_satisfaction = Column(Integer, default=0)
    effect_relationship = Column(Integer, default=0)
    cooldown_hours = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)


class PlayerActionDB(Base):
    """玩家动作执行记录数据库模型"""
    __tablename__ = "player_actions"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    game_state_id = Column(Integer, ForeignKey("game_states.id", ondelete="CASCADE"), nullable=False)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    cost_money = Column(Integer, nullable=True)
    cost_energy = Column(Integer, nullable=True)

    # 关系
    player = relationship("PlayerDB", back_populates="player_actions")
    game_state = relationship("GameStateDB", back_populates="player_actions")
    action = relationship("ActionDB")


class EndingDB(Base):
    """结局数据库模型"""
    __tablename__ = "endings"

    id = Column(Integer, primary_key=True, index=True)
    ending_code = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    condition_type = Column(String(20), nullable=False)
    condition_value = Column(Integer, nullable=True)
    is_bad_ending = Column(Boolean, default=False)
    score = Column(Integer, default=0)

    # 关系
    event_choices = relationship("EventChoiceDB", back_populates="ending")
    player_endings = relationship("PlayerEndingDB", back_populates="ending", cascade="all, delete-orphan")


class PlayerEndingDB(Base):
    """玩家结局记录数据库模型"""
    __tablename__ = "player_endings"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    game_state_id = Column(Integer, ForeignKey("game_states.id", ondelete="CASCADE"), nullable=False)
    ending_id = Column(Integer, ForeignKey("endings.id"), nullable=False)
    achieved_at = Column(DateTime(timezone=True), server_default=func.now())
    score = Column(Integer, default=0)

    # 关系
    player = relationship("PlayerDB", back_populates="player_endings")
    game_state = relationship("GameStateDB", back_populates="player_endings")
    ending = relationship("EndingDB", back_populates="player_endings")


class LeaderboardDB(Base):
    """排行榜数据库模型"""
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(50), nullable=False)
    ending_id = Column(Integer, ForeignKey("endings.id"), nullable=False)
    ending_title = Column(String(200), nullable=False)
    score = Column(Integer, nullable=False)
    total_days = Column(Integer, nullable=False)
    achieved_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    player = relationship("PlayerDB")
    ending = relationship("EndingDB")