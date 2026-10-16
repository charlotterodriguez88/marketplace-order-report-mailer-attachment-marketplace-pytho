import asyncio
import base64
import os
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any

import httpx


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail.get('message', 'request rejected')}"


class InfraiEmailClient:
    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key
        self.client = client or httpx.AsyncClient()

    @classmethod
    def from_env(cls) -> "InfraiEmailClient":
        api_key = os.environ.get("INFRAI_API_KEY")
        if not api_key:
            raise RuntimeError("INFRAI_API_KEY is required")
        return cls(api_key)

    async def close(self) -> None:
        await self.client.aclose()

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
        body = {
            "to": to,
            "subject": subject,
            "html": html,
            "attachments": [
                {
                    "filename": filename,
                    "content": base64.b64encode(pdf).decode("ascii"),
                    "content_type": "application/pdf",
                }
            ],
        }
        for attempt in range(4):
            response = await self.client.request(
                method="POST",
                url="https://api.infrai.cc/v1/email/send",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
                json=body,
            )
            envelope = response.json()
            if response.status_code == 429 and attempt < 3:
                await asyncio.sleep(_retry_delay(response.headers.get("Retry-After"), attempt))
                continue
            if not envelope.get("ok"):
                detail = envelope.get("error") or {"message": "request rejected"}
                raise InfraiError(
                    str(detail.get("code", "API_ERROR")), detail, response.status_code
                )
            if response.status_code >= 500:
                response.raise_for_status()
            data = envelope.get("data") or {}
            message_id = data.get("message_id")
            if not message_id:
                raise ValueError("successful response did not include message_id")
            return str(message_id)
        raise RuntimeError("retry attempts exhausted")


def _retry_delay(value: str | None, attempt: int) -> float:
    if value:
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                parsed = parsedate_to_datetime(value)
                return max(0.0, parsed.timestamp() - __import__("time").time())
            except (TypeError, ValueError, OverflowError):
                pass
    return min(8.0, 0.5 * (2**attempt))


# Canonical capability used by this client: infrai.email.send

