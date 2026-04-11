"""
游戏引擎服务
处理游戏核心逻辑
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.config import settings
from app.crud.game import crud_game
from app.crud.action import crud_action
from app.models.game import GameStateCreate, GameStateUpdate, ActionResult


class GameEngine:
    """游戏引擎"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def start_new_game(self, player_id: int) -> Dict[str, Any]:
        """开始新游戏"""
        # 检查是否已有进行中的游戏
        existing_game = crud_game.get_active_game(self.db, player_id)
        if existing_game:
            # 结束旧游戏
            crud_game.update(
                self.db,
                db_obj=existing_game,
                obj_in=GameStateUpdate(is_game_over=True)
            )
        
        # 创建新游戏状态
        game_data = GameStateCreate(
            player_id=player_id,
            day=1,
            time_of_day="morning",
            money=settings.INITIAL_MONEY,
            health=settings.INITIAL_HEALTH,
            stress=settings.INITIAL_STRESS,
            hunger=settings.INITIAL_HUNGER,
            energy=settings.INITIAL_ENERGY,
            job_level=settings.INITIAL_JOB_LEVEL,
            job_satisfaction=settings.INITIAL_JOB_SATISFACTION,
            relationship=settings.INITIAL_RELATIONSHIP
        )
        
        game = crud_game.create(self.db, obj_in=game_data)
        
        return {
            "game_id": game.id,
            "player_id": game.player_id,
            "day": game.day,
            "money": game.money,
            "health": game.health,
            "stress": game.stress,
            "hunger": game.hunger,
            "energy": game.energy,
            "job_level": game.job_level,
            "job_satisfaction": game.job_satisfaction,
            "relationship": game.relationship,
            "message": "游戏开始！你是一个月薪2000的实习生，努力生存下去吧！"
        }
    
    def get_game_state(self, player_id: int) -> Optional[Dict[str, Any]]:
        """获取游戏状态"""
        game = crud_game.get_active_game(self.db, player_id)
        if not game:
            return None
        
        return {
            "id": game.id,
            "player_id": game.player_id,
            "day": game.day,
            "time_of_day": game.time_of_day,
            "money": game.money,
            "health": game.health,
            "stress": game.stress,
            "hunger": game.hunger,
            "energy": game.energy,
            "job_level": game.job_level,
            "job_satisfaction": game.job_satisfaction,
            "relationship": game.relationship,
            "is_game_over": game.is_game_over,
            "created_at": game.created_at,
            "updated_at": game.updated_at
        }
    
    def execute_action(self, player_id: int, action_code: str) -> Dict[str, Any]:
        """执行动作"""
        # 获取游戏状态
        game = crud_game.get_active_game(self.db, player_id)
        if not game:
            return {
                "success": False,
                "message": "没有进行中的游戏，请先开始新游戏"
            }
        
        if game.is_game_over:
            return {
                "success": False,
                "message": "游戏已结束"
            }
        
        # 获取动作定义
        action = crud_action.get_by_code(self.db, action_code)
        if not action:
            return {
                "success": False,
                "message": f"未知的动作: {action_code}"
            }
        
        # 检查资源是否足够
        if game.energy < action.cost_energy:
            return {
                "success": False,
                "message": "精力不足，无法执行此动作"
            }
        
        if game.money < action.cost_money:
            return {
                "success": False,
                "message": "金钱不足，无法执行此动作"
            }
        
        # 计算效果
        new_money = game.money - action.cost_money + action.effect_money
        new_health = max(0, min(100, game.health + action.effect_health))
        new_stress = max(0, min(100, game.stress + action.effect_stress))
        new_hunger = max(0, min(100, game.hunger + action.effect_hunger))
        new_energy = max(0, min(100, game.energy - action.cost_energy + action.effect_energy))
        new_job_satisfaction = max(0, min(100, game.job_satisfaction + action.effect_job_satisfaction))
        new_relationship = max(0, min(100, game.relationship + action.effect_relationship))
        
        # 更新游戏状态
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
        ending = self._check_ending(updated_game)
        if ending:
            crud_game.update(
                self.db,
                db_obj=updated_game,
                obj_in=GameStateUpdate(is_game_over=True)
            )
        
        return {
            "success": True,
            "message": f"执行动作: {action.name}",
            "data": {
                "action_result": {
                    "action_name": action.name,
                    "cost_money": action.cost_money,
                    "cost_energy": action.cost_energy,
                    "effect_money": action.effect_money,
                    "effect_health": action.effect_health,
                    "effect_stress": action.effect_stress,
                    "effect_hunger": action.effect_hunger,
                    "effect_job_satisfaction": action.effect_job_satisfaction,
                    "effect_relationship": action.effect_relationship
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
                "triggered_ending": ending
            }
        }
    
    def _check_ending(self, game) -> Optional[Dict[str, Any]]:
        """检查是否触发结局"""
        # 破产结局
        if game.money < -5000:
            return {
                "code": "bankruptcy",
                "title": "破产",
                "description": "你欠下了巨额债务，不得不回老家。",
                "is_bad_ending": True
            }
        
        # 健康崩溃
        if game.health <= 0:
            return {
                "code": "health_collapse",
                "title": "健康崩溃",
                "description": "你的身体被工作压垮了，住进了医院。",
                "is_bad_ending": True
            }
        
        # 压力崩溃
        if game.stress >= 100:
            return {
                "code": "stress_collapse",
                "title": "精神崩溃",
                "description": "巨大的压力让你无法承受，选择了离职。",
                "is_bad_ending": True
            }
        
        # 财务自由（好结局）
        if game.money >= 100000:
            return {
                "code": "financial_freedom",
                "title": "财务自由",
                "description": "恭喜你！你通过努力实现了财务自由！",
                "is_bad_ending": False
            }
        
        # 升职加薪（好结局）
        if game.job_level >= 5 and game.money >= 50000:
            return {
                "code": "promotion",
                "title": "升职加薪",
                "description": "你的努力得到了回报，成功升职加薪！",
                "is_bad_ending": False
            }
        
        return None
    
    def get_available_actions(self, player_id: int) -> list:
        """获取当前可执行的动作"""
        game = crud_game.get_active_game(self.db, player_id)
        if not game:
            return []
        
        actions = crud_action.get_all_available(self.db)
        available = []
        
        for action in actions:
            can_execute = True
            reason = None
            
            if game.energy < action.cost_energy:
                can_execute = False
                reason = "精力不足"
            elif game.money < action.cost_money:
                can_execute = False
                reason = "金钱不足"
            
            available.append({
                "code": action.code,
                "name": action.name,
                "description": action.description,
                "cost_money": action.cost_money,
                "cost_energy": action.cost_energy,
                "can_execute": can_execute,
                "reason": reason
            })
        
        return available


# 创建引擎实例的工厂函数
def get_game_engine(db: Session) -> GameEngine:
    """获取游戏引擎实例"""
    return GameEngine(db)
