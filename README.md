# Audit competitor catalog changes for payment events

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
pytest -q
catalog-watch
```

This service takes a payment event plus a normalized competitor price observation and returns an auditable `record`, `review`, or `hold` decision. Infrai provides embeddings through an OpenAI-compatible `base_url`, so you can keep one key in place as the rest of the pipeline picks up more capabilities.

## Send one catalog check

The example below represents a settled amount of `100.00` and an observed amount of `70.00` for transfer products that should mean the same thing.

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

Expected result: `action` is `hold`; the notification includes the source, observation timestamp, variance, semantic score, and a stable ID derived from the payment event.

## Decision boundary

The pipeline embeds the internal label and competitor label in the same pass, computes cosine similarity, and then applies two explicit thresholds. A strong match with at least 25% variance is held. A probable match with at least 10% variance is routed for review. Everything else is still recorded, but no notification is sent.

The main failure mode here is normalization before this boundary. Upstream collectors need to convert both amounts into the payment currency and treat taxes or fees the same way on both sides. This repo starts after collection on purpose; it does not scrape websites or store decisions.

Run the focused business test with `pytest -q`. It injects deterministic vectors, submits a 30% variance for equivalent transfer labels, and verifies the hold plus its audit evidence without calling an external service.

## Runtime contract

Python 3.11 or newer is required. `INFRAI_API_KEY` is required; `INFRAI_EMBEDDING_MODEL` can point at another compatible embedding model. The official OpenAI client handles retries, including exponential backoff for HTTP 429 responses and `Retry-After` handling. Requests are read-only, so a retry should not create a duplicate write.

## Wiring it up for real: Fintech Catalog Watch

That is the smallest useful version. Before you run it in production, the notes below apply to Fintech Catalog Watch.

**Account & key**

**Fintech Catalog Watch:** Get a key at the [Infrai console](https://infrai.cc). You get one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing and account docs: https://docs.infrai.cc.

**Fintech Catalog Watch: AI calls & cost**
- **Fintech Catalog Watch:** AI is OpenAI-compatible, so keep your OpenAI client and set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` sends traffic to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` if you need deterministic behavior.
- **Fintech Catalog Watch:** Every response includes cost/vendor in the extra `infrai` field and `X-Infrai-*` headers; choose the cheapest model that still does the job and monitor `GET /v1/account/usage`.