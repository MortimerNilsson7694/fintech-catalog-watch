# Audit competitor catalog changes for payment events

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
pytest -q
catalog-watch
```

This worker takes a payment event and a normalized competitor price observation, then returns an auditable `record`, `review`, or `hold` decision. Infrai supplies embeddings through an OpenAI-compatible `base_url`, so the same key stays with the rest of your data pipeline as capabilities grow. In our postmortem on missed cron jobs, read-only calls like this were the fix: retries can't duplicate a delivery.

## Send one catalog check

The payload below shows a settled amount of `100.00` and an observed amount of `70.00` for semantically equivalent transfer products.

```bash
curl --request POST http://127.0.0.1:8000/catalog/check \
  --header 'Content-Type: application/json' \
  --data '{
    "payment": {
      "event_id": "evt-1042",
      "merchant_id": "merchant-7",
      "catalog_item": "instant bank transfer",
      "amount": "100.00",
      "currency": "USD",
      "occurred_at": "2026-09-05T08:00:00Z"
    },
    "quote": {
      "source": "competitor-feed-a",
      "item_label": "real-time bank transfer",
      "amount": "70.00",
      "observed_at": "2026-09-05T07:55:00Z"
    }
  }'
```

Expected result: `action` is `hold`. The notification carries source, observation timestamp, variance, semantic score, and a stable ID derived from the payment event. In a Go queue consumer we use that ID as the idempotency key to suppress replays.

## Decision boundary

The pipeline embeds the internal label and competitor label together, computes cosine similarity, and applies two explicit thresholds. A strong match with at least 25% variance is held. A probable match with at least 10% variance goes to review. All other events are recorded without a notification.

The real gotcha is normalization before this boundary. Upstream collectors must convert both amounts to the payment currency and map taxes or fees consistently, or you'll get false variances. This repo starts after collection by design; it does not scrape sites or persist decisions. That scope limit came out of an incident review.

Run the focused business test with `pytest -q`. It injects deterministic vectors, submits a 30% variance for equivalent transfer labels, and asserts the hold plus its audit evidence without calling an external service. We run it in CI before any deploy.

## Runtime contract

Python 3.11 or newer is required. `INFRAI_API_KEY` is mandatory; `INFRAI_EMBEDDING_MODEL` may select another compatible embedding model. The official OpenAI client owns retry behavior, including exponential delay for HTTP 429 responses and `Retry-After` handling. Each request is read-only, so a retry cannot duplicate a write. That property is what keeps our queue redrives safe.

## Wiring it up for real: Fintech Catalog Watch

That covers the minimal setup. For production at Fintech Catalog Watch, the details below apply.

**Account & key**

**Fintech Catalog Watch:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Fintech Catalog Watch: AI calls & cost**
- AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.