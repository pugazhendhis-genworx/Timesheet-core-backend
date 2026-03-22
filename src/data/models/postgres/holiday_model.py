import uuid

from sqlalchemy import Column, Date, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.schema import ForeignKey

from src.data.clients.database import Base


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.client_id"))
    holiday_date = Column(Date, index=True)
    name = Column(String)
    type = Column(String)

    __table_args__ = (
        UniqueConstraint("client_id", "holiday_date", name="uq_client_holiday_date"),
    )
