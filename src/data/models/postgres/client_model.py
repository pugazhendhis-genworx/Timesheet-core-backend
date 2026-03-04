import uuid

from sqlalchemy import UUID, Boolean, Column, DateTime, String, func
from sqlalchemy.orm import relationship

from src.data.clients.database import Base


class Client(Base):
    __tablename__ = "clients"

    client_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_name = Column(String(150))
    client_code = Column(String(50), unique=True)
    client_email = Column(String(150))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    whitelist = relationship("EmailWhitelist", back_populates="client")
