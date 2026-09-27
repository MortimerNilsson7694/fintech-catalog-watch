from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:
    BaseModel = None


if BaseModel is not None:
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
else:
    @dataclass
    class PaymentEvent:
        event_id: str
        merchant_id: str
        catalog_item: str
        amount: Decimal
        currency: str
        occurred_at: datetime

        def __post_init__(self) -> None:
            if not self.event_id or not self.merchant_id or not self.catalog_item:
                raise ValueError("event_id, merchant_id, and catalog_item must not be empty")
            if self.amount <= 0:
                raise ValueError("amount must be greater than zero")
            if len(self.currency) != 3 or not self.currency.isalpha() or not self.currency.isupper():
                raise ValueError("currency must be a three-letter uppercase code")


    @dataclass
    class CompetitorQuote:
        source: str
        item_label: str
        amount: Decimal
        observed_at: datetime

        def __post_init__(self) -> None:
            if not self.source or not self.item_label:
                raise ValueError("source and item_label must not be empty")
            if self.amount <= 0:
                raise ValueError("amount must be greater than zero")


    @dataclass
    class CatalogCheckRequest:
        payment: PaymentEvent
        quote: CompetitorQuote


    @dataclass
    class AuditNotification:
        notification_id: str
        event_id: str
        reason: str
        evidence: dict[str, str]


    @dataclass
    class CatalogDecision:
        action: Literal["record", "review", "hold"]
        variance_ratio: Decimal
        semantic_similarity: float
        notification: AuditNotification | None
