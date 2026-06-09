from sqlalchemy import String, UUID, TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.db import Base
import uuid
from datetime import datetime
from sqlalchemy.sql import func


class Journal(Base):
    __tablename__ = "journals"

    id: Mapped[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, primary_key=True)

    user_id: Mapped[UUID] = mapped_column(
        UUID,
        ForeignKey("users.id"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="journals")

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="journal")
    accounts: Mapped[list["Account"]] = relationship(back_populates="journal")
