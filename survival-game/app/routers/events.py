"""
事件路由
处理事件触发、选择、结果等
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.game import crud_game
from app.crud.event import crud_event
from app.crud.player import crud_player
from app.database import get_db
from app.models.event import (
    EventWithChoices,
    EventChoiceRequest,
    EventChoiceResult,
    CurrentEventResponse
)
from app.models.db_models import PlayerDB, GameStateDB, EventDB
from app.routers.auth import get_current_active_player

router = APIRouter()


@router.get("/current", response_model=CurrentEventResponse)
async def get_current_event(
    current_player: PlayerDB = Depends(get_current_active_player),
    db: Session = Depends(get_db)
):
    """获取当前事件（如果有的话）"""
    # 获取当前游戏状态
    game_state = crud_game.get_by_player(db, current_player.id, only_active=True)
    if not game_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到进行中的游戏"
        )

    # TODO: 从游戏状态中获取当前事件ID（需要扩展GameStateDB）
    # 暂时返回空，表示没有当前事件
    return CurrentEventResponse(
        success=True,
        data=None
    )


@router.get("/daily", response_model=EventWithChoices)
async def get_daily_event(
    current_player: PlayerDB = Depends(get_current_active_player),
    db: Session = Depends(get_db)
):
    """获取每日事件"""
    # 获取当前游戏状态
    game_state = crud_game.get_by_player(db, current_player.id, only_active=True)
    if not game_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到进行中的游戏"
        )

    # 获取每日事件
    event = crud_event.get_daily_event(db, game_state.day)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="今天没有每日事件"
        )

    # 获取事件选择项
    choices = crud_event.get_event_choices(db, event.id)

    # 转换为响应模型
    from app.models.event import Event, EventChoice
    event_response = Event(
        id=event.id,
        event_code=event.event_code,
        title=event.title,
        description=event.description,
        trigger_type=event.trigger_type,
        trigger_condition=event.trigger_condition,
        min_day=event.min_day,
        max_day=event.max_day,
        weight=event.weight,
        is_active=event.is_active
    )

    choices_response = []
    for choice in choices:
        choice_response = EventChoice(
            id=choice.id,
            event_id=choice.event_id,
            choice_text=choice.choice_text,
            effect_money=choice.effect_money,
            effect_health=choice.effect_health,
            effect_stress=choice.effect_stress,
            effect_hunger=choice.effect_hunger,
            effect_energy=choice.effect_energy,
            effect_job_satisfaction=choice.effect_job_satisfaction,
            effect_relationship=choice.effect_relationship,
            next_event_id=choice.next_event_id,
            is_ending_trigger=choice.is_ending_trigger,
            ending_id=choice.ending_id
        )
        choices_response.append(choice_response)

    return EventWithChoices(
        **event_response.dict(),
        choices=choices_response
    )


@router.get("/random", response_model=EventWithChoices)
async def get_random_event(
    current_player: PlayerDB = Depends(get_current_active_player),
    db: Session = Depends(get_db)
):
    """获取随机事件"""
    # 获取当前游戏状态
    game_state = crud_game.get_by_player(db, current_player.id, only_active=True)
    if not game_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到进行中的游戏"
        )

    # 将游戏状态转换为字典用于条件检查
    game_state_dict = {
        'day': game_state.day,
        'money': game_state.money,
        'health': game_state.health,
        'stress': game_state.stress,
        'hunger': game_state.hunger,
        'energy': game_state.energy,
        'job_level': game_state.job_level,
        'job_satisfaction': game_state.job_satisfaction,
        'relationship': game_state.relationship
    }

    # 获取随机事件
    event = crud_event.get_random_event(db, game_state.day, game_state_dict)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到符合条件的随机事件"
        )

    # 获取事件选择项
    choices = crud_event.get_event_choices(db, event.id)

    # 转换为响应模型
    from app.models.event import Event, EventChoice
    event_response = Event(
        id=event.id,
        event_code=event.event_code,
        title=event.title,
        description=event.description,
        trigger_type=event.trigger_type,
        trigger_condition=event.trigger_condition,
        min_day=event.min_day,
        max_day=event.max_day,
        weight=event.weight,
        is_active=event.is_active
    )

    choices_response = []
    for choice in choices:
        choice_response = EventChoice(
            id=choice.id,
            event_id=choice.event_id,
            choice_text=choice.choice_text,
            effect_money=choice.effect_money,
            effect_health=choice.effect_health,
            effect_stress=choice.effect_stress,
            effect_hunger=choice.effect_hunger,
            effect_energy=choice.effect_energy,
            effect_job_satisfaction=choice.effect_job_satisfaction,
            effect_relationship=choice.effect_relationship,
            next_event_id=choice.next_event_id,
            is_ending_trigger=choice.is_ending_trigger,
            ending_id=choice.ending_id
        )
        choices_response.append(choice_response)

    return EventWithChoices(
        **event_response.dict(),
        choices=choices_response
    )


@router.post("/choose", response_model=EventChoiceResult)
async def choose_event_option(
    choice_request: EventChoiceRequest,
    current_player: PlayerDB = Depends(get_current_active_player),
    db: Session = Depends(get_db)
):
    """处理事件选择"""
    # 获取当前游戏状态
    game_state = crud_game.get_by_player(db, current_player.id, only_active=True)
    if not game_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到进行中的游戏"
        )

    # 获取选择项
    choice = crud_event.get_choice(db, choice_request.choice_id)
    if not choice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="选择项不存在"
        )

    # 获取对应事件
    event = crud_event.get_event(db, choice.event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )

    # 应用选择项效果
    effects = crud_event.apply_choice_effects(choice)
    updated_game_state = crud_game.update_resources(db, game_state, **effects)

    # 检查是否触发结局
    triggered_ending = None
    if choice.is_ending_trigger and choice.ending_id:
        from app.models.db_models import EndingDB, PlayerEndingDB
        ending = db.query(EndingDB).filter(EndingDB.id == choice.ending_id).first()
        if ending:
            # 记录玩家结局
            player_ending = PlayerEndingDB(
                player_id=current_player.id,
                game_state_id=game_state.id,
                ending_id=ending.id,
                score=ending.score
            )
            db.add(player_ending)

            # 更新排行榜
            from app.models.db_models import LeaderboardDB
            leaderboard_entry = LeaderboardDB(
                player_id=current_player.id,
                username=current_player.username,
                ending_id=ending.id,
                ending_title=ending.title,
                score=ending.score,
                total_days=game_state.day
            )
            db.add(leaderboard_entry)

            # 更新玩家最高分
            crud_player.update_best_score(db, current_player, ending.score)

            # 结束游戏
            crud_game.end_game(db, updated_game_state)

            triggered_ending = {
                'ending_id': ending.id,
                'title': ending.title,
                'description': ending.description,
                'is_bad_ending': ending.is_bad_ending,
                'score': ending.score
            }

    # 检查游戏结束条件
    game_over_conditions = crud_game.check_game_over_conditions(db, updated_game_state)
    if any(game_over_conditions.values()):
        crud_game.end_game(db, updated_game_state)

    # 获取下一个事件（如果有）
    next_event = None
    if choice.next_event_id:
        next_event_db = crud_event.get_event(db, choice.next_event_id)
        if next_event_db:
            from app.models.event import Event
            next_event = Event(
                id=next_event_db.id,
                event_code=next_event_db.event_code,
                title=next_event_db.title,
                description=next_event_db.description,
                trigger_type=next_event_db.trigger_type,
                trigger_condition=next_event_db.trigger_condition,
                min_day=next_event_db.min_day,
                max_day=next_event_db.max_day,
                weight=next_event_db.weight,
                is_active=next_event_db.is_active
            )

    # 构建响应
    return EventChoiceResult(
        effects=effects,
        next_event=next_event,
        triggered_ending=triggered_ending
    )