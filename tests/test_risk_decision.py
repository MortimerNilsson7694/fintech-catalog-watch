from datetime import UTC, datetime
from decimal import Decimal

from catalog_risk_service.decision import assess_catalog_event
from catalog_risk_service.models import CatalogCheckRequest, CompetitorQuote, PaymentEvent


def test_holds_large_variance_for_semantic_match() -> None:
    request = CatalogCheckRequest(
        payment=PaymentEvent(
            event_id="evt-1042",
            merchant_id="merchant-7",
            catalog_item="instant bank transfer",
            amount=Decimal("100.00"),
            currency="USD",
            occurred_at=datetime(2026, 9, 5, 8, 0, tzinfo=UTC),
        ),
        quote=CompetitorQuote(
            source="competitor-feed-a",
            item_label="real-time bank transfer",
            amount=Decimal("70.00"),
            observed_at=datetime(2026, 9, 5, 7, 55, tzinfo=UTC),
        ),
    )

    result = assess_catalog_event(request, lambda texts: [[1.0, 0.0], [0.9, 0.1]])

    assert result.action == "hold"
    assert result.variance_ratio == Decimal("0.3")
    assert result.notification is not None
    assert result.notification.notification_id == "catalog-evt-1042"
    assert result.notification.evidence["competitor_source"] == "competitor-feed-a"
