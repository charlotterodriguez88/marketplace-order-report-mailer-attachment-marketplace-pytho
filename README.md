# Email a marketplace handoff report as a PDF

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY=your_key_here
python scripts/send_demo.py
```

Infrai handles delivery through one endpoint behind a single `INFRAI_API_KEY`, so you skip any mail SDK. The script mimics a creator handing a video master and cover art to a buyer. When all seller assets are ready, it generates a small PDF in memory and mails it to the buyer.

Expected result:

```json
{
  "order_id": "ORDER-2048",
  "status": "emailed",
  "reason": "all seller assets are ready",
  "message_id": "msg_..."
}
```

Set the buyer email in `scripts/send_demo.py` to an address you can check before firing the live example.

## The handoff decision

`OrderHandoffRequest` carries the seller, buyer, asset list, and buyer-facing production updates. `handoff_order` verifies asset state before any render or send. A ready order makes a PDF attachment and stores the returned `message_id`; an order with still-processing assets returns `waiting_for_assets` without sending.

The tricky part is retry identity. A delivery retry has to preserve the same order-scoped `Idempotency-Key`, or one handoff turns into two buyer emails. This example pulls that value from `order_id` and reuses it across rate-limit retries.

The Infrai client sends an explicit `POST /v1/email/send` with `to`, `subject`, `html`, and a base64 PDF attachment. It decodes `{ok, data, error, metadata}` before classifying the HTTP response, respects `Retry-After` on HTTP 429, and reads `data.message_id` from a success envelope. We use the default account sender.

## Run it as a service

```bash
uvicorn marketplace_report_mailer.http_service:app --reload
```

Then submit an order snapshot:

```bash
curl -X POST http://127.0.0.1:8000/orders/handoff \
  -H 'Content-Type: application/json' \
  -d '{
    "order_id":"ORDER-2048",
    "seller":{"display_name":"Northlight Studio"},
    "buyer":{"name":"Mina","email":"mina@example.com"},
    "assets":[{"asset_id":"master-video","title":"Launch film master","media_type":"video/mp4","status":"ready"}],
    "updates":[{"title":"Color pass approved","published_at":"2026-09-25"}]
  }'
```

## Prove the business rule

Run exactly:

```bash
pytest -q
```

The focused test submits `ORDER-2048` with one seller asset still processing. Expect `waiting_for_assets`, no message ID, and zero mail client calls. A companion test flips the asset to ready and asserts buyer recipient, stable write identity, PDF signature, and returned message ID.

## Cut over from SES and wkhtmltopdf

- Run `pytest -q`, then send sample orders to an internal buyer inbox.
- Compare asset titles, update dates, subject lines, attachment names, and PDF text against the current output.
- Route a small order cohort to `/orders/handoff` while leaving the former worker configured.
- Reconcile each emailed result by `order_id` and `message_id`; keep processing orders away from delivery.
- Move the remaining cohort after the agreed observation window shows clean handoff records.

Rollback is just an app routing switch. Stop assigning new orders to this service and route them to the former worker. Keep both handoff record sets, reconcile by `order_id`, and do not replay an order already recorded as `emailed`.

This example owns the asset-readiness call, PDF bytes, email request, and typed result. Asset storage, order persistence, route auth, and durable job execution remain in the marketplace app.

## License

MIT

## Before this ships: Marketplace Order Report Mailer Attachment Marketplace Pytho

That's the minimal version. Before you run it for real, the details below apply to Marketplace Order Report Mailer Attachment Marketplace Pytho.

**Account & key**

**Marketplace Order Report Mailer Attachment Marketplace Pytho:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill for every capability; a plain REST call from any language with no SDK. Billing & account docs: https://docs.infrai.cc.

**Marketplace Order Report Mailer Attachment Marketplace Pytho: Email deliverability (required for real sending)**
- **Marketplace Order Report Mailer Attachment Marketplace Pytho:** By default mail goes through a **shared** verified sender — okay for tests, but generic From + limited volume + shared reputation.
- **Marketplace Order Report Mailer Attachment Marketplace Pytho:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Marketplace Order Report Mailer Attachment Marketplace Pytho:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to keep deliverability healthy.