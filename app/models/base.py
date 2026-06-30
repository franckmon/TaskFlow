from sqlalchemy import Column, DateTime, Integer

from app.core.database import Base
from app.core.time import utc_now


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
