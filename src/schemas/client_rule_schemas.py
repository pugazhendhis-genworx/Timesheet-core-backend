from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class RuleConfig(BaseModel):
    ot_threshold: Decimal = Field(
        default=Decimal("8"), description="Daily hours above which overtime applies"
    )
    dt_threshold: Decimal = Field(
        default=Decimal("12"),
        description="Daily hours above which double time applies",
    )
    reg_markup_rate: Decimal = Field(
        default=Decimal("1.0"), description="Markup multiplier for regular hours"
    )
    ot_markup_rate: Decimal = Field(
        default=Decimal("1.5"), description="Markup multiplier for overtime hours"
    )
    dt_markup_rate: Decimal = Field(
        default=Decimal("2.0"), description="Markup multiplier for double time hours"
    )
    reg_pay: Decimal = Field(..., description="Pay rate for regular hours")
    ot_pay: Decimal = Field(..., description="Pay rate for overtime hours")
    dt_pay: Decimal = Field(..., description="Pay rate for double time hours")
    holiday_pay: Decimal = Field(..., description="Pay rate for holidays")

    @field_serializer(
        "ot_threshold",
        "dt_threshold",
        "reg_markup_rate",
        "ot_markup_rate",
        "dt_markup_rate",
        "reg_pay",
        "ot_pay",
        "dt_pay",
        "holiday_pay",
    )
    def serialize_decimal(self, value):
        if isinstance(value, Decimal):
            return float(value)
        return value


class ClientRuleCreate(BaseModel):
    client_id: UUID
    rule_type: str = "TIMESHEET_CALCULATION"
    rule_config: RuleConfig


class ClientRuleResponse(BaseModel):
    """Schema for returning client rule data from the database."""

    rule_id: UUID = Field(default_factory=uuid4)
    client_id: UUID
    rule_type: str
    rule_config: RuleConfig
    is_active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ClientRuleUpdate(BaseModel):
    is_active: bool | None = None
    rule_config: RuleConfig | None = None
