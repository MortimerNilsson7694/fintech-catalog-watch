from collections.abc import Callable, Sequence
from decimal import Decimal
from math import sqrt

from .models import AuditNotification, CatalogCheckRequest, CatalogDecision

Embed = Callable[[Sequence[str]], list[list[float]]]


def cosine(left: list[float], right: list[float]) -> float:
    denominator = sqrt(sum(x * x for x in left)) * sqrt(sum(x * x for x in right))
    if denominator == 0:
        return 0.0
    return sum(x * y for x, y in zip(left, right, strict=True)) / denominator


def assess_catalog_event(request: CatalogCheckRequest, embed: Embed) -> CatalogDecision:
    vectors = embed([request.payment.catalog_item, request.quote.item_label])
    similarity = cosine(vectors[0], vectors[1])
    variance = abs(request.payment.amount - request.quote.amount) / request.payment.amount

    action = "record"
    reason = ""
    if similarity >= 0.85 and variance >= Decimal("0.25"):
        action = "hold"
        reason = "matched item differs by at least 25%"
    elif similarity >= 0.75 and variance >= Decimal("0.10"):
        action = "review"
        reason = "probable match differs by at least 10%"

    notification = None
    if action != "record":
        notification = AuditNotification(
            notification_id=f"catalog-{request.payment.event_id}",
            event_id=request.payment.event_id,
            reason=reason,
            evidence={
                "competitor_source": request.quote.source,
                "observed_at": request.quote.observed_at.isoformat(),
                "variance_ratio": str(variance.quantize(Decimal("0.0001"))),
                "semantic_similarity": f"{similarity:.4f}",
            },
        )

    return CatalogDecision(
        action=action,
        variance_ratio=variance,
        semantic_similarity=similarity,
        notification=notification,
    )
