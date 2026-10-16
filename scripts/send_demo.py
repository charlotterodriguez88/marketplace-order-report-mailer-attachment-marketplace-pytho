import asyncio
import json

from marketplace_report_mailer.handoff_service import handoff_order
from marketplace_report_mailer.infrai_email import InfraiEmailClient
from marketplace_report_mailer.models import OrderHandoffRequest


async def main() -> None:
    order = OrderHandoffRequest.model_validate(
        {
            "order_id": "ORDER-2048",
            "seller": {"display_name": "Northlight Studio"},
            "buyer": {"name": "Mina", "email": "chenhua@changba.com"},
            "assets": [
                {
                    "asset_id": "master-video",
                    "title": "Launch film master",
                    "media_type": "video/mp4",
                    "status": "ready",
                },
                {
                    "asset_id": "cover-art",
                    "title": "Campaign cover art",
                    "media_type": "image/png",
                    "status": "ready",
                },
            ],
            "updates": [
                {"title": "Color pass approved", "published_at": "2026-09-25"}
            ],
        }
    )
    client = InfraiEmailClient.from_env()
    try:
        result = await handoff_order(order, client)
        print(json.dumps(result.model_dump(), indent=2))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
