from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from carepath.deps import CurrentUser, get_current_user

router = APIRouter(tags=["实时事件"])


async def event_stream() -> AsyncIterator[str]:
    while True:
        payload = {
            "type": "heartbeat",
            "at": datetime.now(UTC).isoformat(),
        }
        yield f"event: heartbeat\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
        await asyncio.sleep(15)


@router.get("/events/stream")
async def stream_events(
    current: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
