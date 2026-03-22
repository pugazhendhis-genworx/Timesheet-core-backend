import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from src.data.clients.database import Base


class Paycode(Base):
    __tablename__ = "paycodes"

    paycode_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paycode = Column(String(50), unique=True)
    paycode_name = Column(String(150))

    @property
    def code(self):
        """Alias for paycode attribute for backward compatibility."""
        return self.paycode
