"""
结局 CRUD 操作
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.db_models import EndingDB


class CRUDEnding:
    """结局 CRUD 操作类"""

    def get(self, db: Session, ending_id: int) -> Optional[EndingDB]:
        """通过ID获取结局"""
        return db.query(EndingDB).filter(EndingDB.id == ending_id).first()

    def get_by_code(self, db: Session, ending_code: str) -> Optional[EndingDB]:
        """通过代码获取结局"""
        return db.query(EndingDB).filter(EndingDB.ending_code == ending_code).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[EndingDB]:
        """获取多个结局"""
        return db.query(EndingDB).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: dict) -> EndingDB:
        """创建结局"""
        db_obj = EndingDB(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


crud_ending = CRUDEnding()
