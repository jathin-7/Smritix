from __future__ import annotations
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User

project_memories = Table(
    "project_memories",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id"), primary_key=True),
    Column("memory_id", ForeignKey("memories.id"), primary_key=True)
)

class Project(BaseModel):
    __tablename__ = "projects"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    user: Mapped["User"] = relationship("User", back_populates="projects")
