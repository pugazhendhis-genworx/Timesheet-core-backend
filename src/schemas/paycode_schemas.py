from uuid import UUID

from pydantic import BaseModel


class PaycodeCreate(BaseModel):
    paycode: str
    paycode_name: str


class PaycodeResponse(BaseModel):
    paycode_id: UUID
    paycode: str
    paycode_name: str

    class Config:
        from_attributes = True
