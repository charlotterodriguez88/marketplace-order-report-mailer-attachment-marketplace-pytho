import asyncio

from marketplace_report_mailer.handoff_service import handoff_order
from marketplace_report_mailer.models import OrderHandoffRequest


class RecordingSender:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def send_report(self, **request: object) -> str:
        self.calls.append(request)
        return "msg_marketplace_2048"


def order_with_status(status: str) -> OrderHandoffRequest:
    return OrderHandoffRequest.model_validate(
        {
            "order_id": "ORDER-2048",
            "seller": {"display_name": "Northlight Studio"},
            "buyer": {"name": "Mina", "email": "mina@example.com"},
            "assets": [
                {
                    "asset_id": "master-video",
                    "title": "Launch film master",
                    "media_type": "video/mp4",
                    "status": status,
                }
            ],
            "updates": [
                {"title": "First cut reviewed", "published_at": "2026-09-24"}
            ],
        }
    )


def test_handoff_waits_until_every_seller_asset_is_ready() -> None:
    sender = RecordingSender()

    result = asyncio.run(handoff_order(order_with_status("processing"), sender))

    assert result.status == "waiting_for_assets"
    assert result.message_id is None
    assert sender.calls == []


def test_ready_order_emails_a_pdf_to_the_buyer() -> None:
    sender = RecordingSender()

    result = asyncio.run(handoff_order(order_with_status("ready"), sender))

    assert result.status == "emailed"
    assert result.message_id == "msg_marketplace_2048"
    assert sender.calls[0]["to"] == "mina@example.com"
    assert sender.calls[0]["idempotency_key"] == "marketplace-handoff:ORDER-2048"
    assert bytes(sender.calls[0]["pdf"]).startswith(b"%PDF-1.4")
