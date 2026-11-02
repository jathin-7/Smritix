from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class BaseModel(Base):
    __abstract__ = True
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)  # TODO: switch to uuid7
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
