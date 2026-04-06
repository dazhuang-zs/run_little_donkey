"""
游戏路由
处理游戏开始、状态获取、动作执行等
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.crud.game import crud_game
from app.crud.player import crud_player
from app.crud.action import crud_action
from app.crud.event import crud_event
from app.database import get_db
from app.models.game import GameState, GameStateCreate, ActionRequest, ActionResponse, ActionResult
from app.models.event import CurrentEventResponse
from app.models.ending import LeaderboardResponse
from app.routers.auth import get_current_active_player
from app.models.db_models import PlayerDB, GameStateDB

router = APIRouter()


@router.post("/start", response_model=GameState, status_code=status.HTTP_201_CREATED)
async def start_game(
    current_player: PlayerDB = Depends(get_current_active_player),
    db: Session = Depends(get_db)
):
    """开始新游戏"""
    # 检查是否有进行中的游戏
    existing_game = crud_game.get_by_player(db, current_player.id, only_active=True)
    if existing_game:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已有进行中的游戏，请先结束当前游戏"
        )

    # 创建初始游戏状态
    game_state_data = GameStateCreate(
        player_id=current_player.id,
        day=1,
        time_of_day="morning",
        money=settings.INITIAL_MONEY,
        health=settings.INITIAL_HEALTH,
        stress=settings.INITIAL_STRESS,
        hunger=settings.INITIAL_HUNGER,
        energy=settings.INITIAL_ENERGY,
        job_level=settings.INITIAL_JOB_LEVEL,
        job_satisfaction=settings.INITIAL_JOB_SATISFACTION,
        relationship=settings.INITIAL_RELATIONSHIP,
        is_game_over=False
    )

    game_state = crud_game.create(db, game_state_data)

    # 增加玩家游戏次数
    crud_player.increment_games_played(db, current_player)

    return game_state


@router.get("/status", response_model=GameState)
async def get_game_status(
    current_player: PlayerDB = Depends(get_current_active_player),
    db: Session = Depends(get_db)
):
    """获取当前游戏状态"""
    game_state = crud_game.get_by_player(db, current_player.id, only_active=True)
    if not game_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到进行中的游戏"
        )

    return game_state


@router.post("/action", response_model=ActionResponse)
async def perform_action(
    action_request: ActionRequest,
    current_player: PlayerDB = Depends(get_current_active_player),
    db: Session = Depends(get_db)
):
    """执行动作"""
    # 获取当前游戏状态
    game_state = crud_game.get_by_player(db, current_player.id, only_active=True)
    if not game_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到进行中的游戏"
        )

    # 获取动作
    action = crud_action.get_action_by_code(db, action_request.action_code)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="动作不存在"
        )

    # 检查动作是否可用
    available_actions = crud_action.get_available_actions(db, current_player.id, game_state.id)
    if action not in available_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="动作不可用（可能处于冷却中）"
        )

    # 检查玩家是否能承担消耗
    game_state_dict = {
        'money': game_state.money,
        'energy': game_state.energy
    }
    if not crud_action.can_afford_action(game_state_dict, action):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="资源不足，无法执行此动作"
        )

    # 应用动作效果
    effects = crud_action.apply_action_effects(action)
    updated_game_state = crud_game.update_resources(db, game_state, **effects)

    # 记录动作执行
    from app.models.action import PlayerActionCreate
    player_action = PlayerActionCreate(
        player_id=current_player.id,
        game_state_id=game_state.id,
        action_id=action.id,
        cost_money=action.cost_money,
        cost_energy=action.cost_energy
    )
    crud_action.record_player_action(db, player_action)

    # 检查游戏结束条件
    game_over_conditions = crud_game.check_game_over_conditions(db, updated_game_state)
    if any(game_over_conditions.values()):
        crud_game.end_game(db, updated_game_state)

    # 构建响应
    result = ActionResult(
        action_name=action.name,
        cost_money=action.cost_money,
        cost_energy=action.cost_energy,
        effect_money=effects.get('money', 0),
        effect_health=effects.get('health', 0),
        effect_stress=effects.get('stress', 0),
        effect_hunger=effects.get('hunger', 0),
        effect_job_satisfaction=effects.get('job_satisfaction', 0),
        effect_relationship=effects.get('relationship', 0)
    )

    return ActionResponse(
        success=True,
        message=f"成功执行动作：{action.name}",
        data=result.dict()
    )


@router.post("/end", response_model=GameState)
async def end_current_game(
    current_player: PlayerDB = Depends(get_current_active_player),
    db: Session = Depends(get_db)
):
    """结束当前游戏"""
    game_state = crud_game.get_by_player(db, current_player.id, only_active=True)
    if not game_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到进行中的游戏"
        )

    ended_game = crud_game.end_game(db, game_state)

    return ended_game


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取排行榜"""
    from app.models.db_models import LeaderboardDB
    from sqlalchemy import desc

    leaderboard_entries = db.query(LeaderboardDB)\
        .order_by(desc(LeaderboardDB.score), desc(LeaderboardDB.achieved_at))\
        .limit(limit)\
        .all()

    # 转换为响应格式
    entries = []
    for i, entry in enumerate(leaderboard_entries, 1):
        entries.append({
            'rank': i,
            'player_id': entry.player_id,
            'username': entry.username,
            'ending_title': entry.ending_title,
            'score': entry.score,
            'total_days': entry.total_days,
            'achieved_at': entry.achieved_at
        })

    return LeaderboardResponse(
        success=True,
        data={'leaderboard': entries}
    )


@router.get("/available-actions")
async def get_available_actions(
    current_player: PlayerDB = Depends(get_current_active_player),
    db: Session = Depends(get_db)
):
    """获取当前可用动作"""
    game_state = crud_game.get_by_player(db, current_player.id, only_active=True)
    if not game_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到进行中的游戏"
        )

    available_actions = crud_action.get_available_actions(db, current_player.id, game_state.id)

    # 转换为简单格式
    actions_list = []
    for action in available_actions:
        actions_list.append({
            'action_code': action.action_code,
            'name': action.name,
            'description': action.description,
            'cost_money': action.cost_money,
            'cost_energy': action.cost_energy,
            'cooldown_hours': action.cooldown_hours
        })

    return {
        'success': True,
        'data': {'actions': actions_list}
    }