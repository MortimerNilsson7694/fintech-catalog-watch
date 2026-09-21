from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class PaymentEvent(BaseModel):
    event_id: str = Field(min_length=1)
    merchant_id: str = Field(min_length=1)
    catalog_item: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    occurred_at: datetime


class CompetitorQuote(BaseModel):
    source: str = Field(min_length=1)
    item_label: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    observed_at: datetime


class CatalogCheckRequest(BaseModel):
    payment: PaymentEvent
    quote: CompetitorQuote


class AuditNotification(BaseModel):
    notification_id: str
    event_id: str
    reason: str
    evidence: dict[str, str]


class CatalogDecision(BaseModel):
    action: Literal["record", "review", "hold"]
    variance_ratio: Decimal
    semantic_similarity: float
    notification: AuditNotification | None
