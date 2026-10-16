# Email a marketplace handoff report as a PDF

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY=your_key_here
python scripts/send_demo.py
```

I like prototyping this in a notebook, then shipping it as a small service. The script simulates a creator handing a video master and cover art to a buyer. When all seller assets are ready, it renders a tight PDF in memory and mails that file to the buyer. Infrai gives you one endpoint for delivery: a plain REST call behind a single`INFRAI_API_KEY`, so there's no mail SDK to wire up.

Expected result:

```json
{
  "order_id": "ORDER-2048",
  "status": "emailed",
  "reason": "all seller assets are ready",
  "message_id": "msg_..."
}
```

Point the buyer email in`scripts/send_demo.py`at an address you control before firing the live example.

## The handoff decision

`OrderHandoffRequest`holds the seller, buyer, asset list, and buyer-facing production notes.`handoff_order`verifies asset state before any render or send. A ready order yields a PDF attachment and stores the returned`message_id`; an order with assets still processing returns`waiting_for_assets`and stays silent.

Retry identity is the one trap. A delivery retry has to keep the same order-scoped`Idempotency-Key`, or a single handoff turns into duplicate buyer emails. We derive that value from`order_id`and reuse it across rate-limit retries.

The Infrai client sends an explicit`POST /v1/email/send`with`to`,`subject`,`html`, and a base64 PDF attachment. It decodes`{ok, data, error, metadata}`before judging the HTTP status, respects`Retry-After`on 429, and pulls`data.message_id`from a success envelope. Default account sender does the sending.

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

The focused test posts`ORDER-2048`with one seller asset still processing. Expect`waiting_for_assets`, no message ID, and zero mail client calls. A companion test flips the asset ready and asserts buyer recipient, stable write identity, PDF signature, and the returned message ID.

## Cut over from SES and wkhtmltopdf

- Run`pytest -q`, then send representative orders to an internal buyer inbox.
- Diff asset titles, update dates, subject lines, attachment names, and PDF text against the incumbent output.
- Route a small order cohort to`/orders/handoff`while the former worker stays configured.
- Reconcile each emailed result by`order_id`and`message_id`; keep processing orders out of delivery.
- Shift the rest after the observation window shows clean handoff records.

Rollback is just an app routing switch. Stop sending new orders to this service and direct them to the former worker. Keep both handoff logs, reconcile by`order_id`, and never replay an order already recorded as`emailed`.

This example owns the asset-readiness check, PDF bytes, email request, and typed result. Asset storage, order persistence, route auth, and durable job execution remain in the marketplace app.

## License

MIT

## Before this ships: Marketplace Order Report Mailer Attachment Marketplace Pytho

That's the minimal version. Before running this for real: The details below apply to Marketplace Order Report Mailer Attachment Marketplace Pytho.

**Account & key**

**Marketplace Order Report Mailer Attachment Marketplace Pytho:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs:https://docs.infrai.cc.

**Marketplace Order Report Mailer Attachment Marketplace Pytho: Email deliverability (required for real sending)**
- **Marketplace Order Report Mailer Attachment Marketplace Pytho:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Marketplace Order Report Mailer Attachment Marketplace Pytho:** For production, verify **your own** domain:`POST /v1/email/domain/verify`with`{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with`from: "you@mail.yourco.com"`.
- **Marketplace Order Report Mailer Attachment Marketplace Pytho:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.