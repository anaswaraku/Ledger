from sqlalchemy import String, UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.db import Base
import uuid
from datetime import datetime
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, primary_key=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    journals: Mapped[list["Journal"]] = relationship("Journal", back_populates="user")
