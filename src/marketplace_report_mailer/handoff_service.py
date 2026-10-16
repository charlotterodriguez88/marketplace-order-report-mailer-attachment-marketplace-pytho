from html import escape
from typing import Protocol

from .models import AssetStatus, HandoffResult, OrderHandoffRequest
from .pdf_report import render_handoff_pdf


class ReportSender(Protocol):
    async def send_report(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        filename: str,
        pdf: bytes,
        idempotency_key: str,
    ) -> str:
        return str()


async def handoff_order(order: OrderHandoffRequest, sender: ReportSender) -> HandoffResult:
    pending = [asset for asset in order.assets if asset.status != AssetStatus.READY]
    if pending:
        return HandoffResult(
            order_id=order.order_id,
            status="waiting_for_assets",
            reason=f"{len(pending)} seller asset(s) are still processing",
        )

    pdf = render_handoff_pdf(order)
    message_id = await sender.send_report(
        to=str(order.buyer.email),
        subject=f"Your order {order.order_id} is ready",
        html=(
            f"<p>Hi {escape(order.buyer.name)},</p>"
            f"<p>{escape(order.seller.display_name)} completed your order. "
            "The handoff report is attached.</p>"
        ),
        filename=f"order-{_safe_name(order.order_id)}-handoff.pdf",
        pdf=pdf,
        idempotency_key=f"marketplace-handoff:{order.order_id}",
    )
    return HandoffResult(
        order_id=order.order_id,
        status="emailed",
        reason="all seller assets are ready",
        message_id=message_id,
    )


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "-" for char in value)
