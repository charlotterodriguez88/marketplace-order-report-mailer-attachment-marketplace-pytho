from fastapi import FastAPI, HTTPException

from .handoff_service import handoff_order
from .infrai_email import InfraiEmailClient, InfraiError
from .models import HandoffResult, OrderHandoffRequest

app = FastAPI(title="Marketplace report mailer")


@app.post("/orders/handoff", response_model=HandoffResult)
async def create_handoff(order: OrderHandoffRequest) -> HandoffResult:
    client = InfraiEmailClient.from_env()
    try:
        return await handoff_order(order, client)
    except InfraiError as error:
        caller_status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": error.code, "message": str(error)},
        ) from error
    finally:
        await client.close()

