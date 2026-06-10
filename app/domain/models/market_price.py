from sqlalchemy import String, UUID, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db import Base
import uuid
from datetime import datetime
from decimal import Decimal


class MarketPrices(Base):
    __tablename__ = "marketprices"

    id: Mapped[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, primary_key=True)
    currency_from: Mapped[str] = mapped_column(String(3))
    currency_to: Mapped[str] = mapped_column(String(3))
    price: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)

    date: Mapped[datetime] = mapped_column(Date, nullable=False)
