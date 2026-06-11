from __future__ import annotations

import asyncio
import json
import queue
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.support import require_identity
from services.session_service import session_service


class SessionSaveRequest(BaseModel):
    kind: str = Field(..., min_length=1)
    item: dict[str, Any] = Field(default_factory=dict)


def _raise_bad_request(exc: ValueError) -> None:
    raise HTTPException(status_code=400, detail={"error": str(exc)}) from exc


def _format_sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def create_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/sessions")
    async def list_sessions(
        kind: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ):
        identity = require_identity(authorization)
        try:
            return await run_in_threadpool(session_service.list_sessions, identity, kind)
        except ValueError as exc:
            _raise_bad_request(exc)

    @router.get("/api/sessions/{kind}/{session_id}")
    async def get_session(kind: str, session_id: str, authorization: str | None = Header(default=None)):
        identity = require_identity(authorization)
        try:
            item = await run_in_threadpool(session_service.get_session, identity, kind, session_id)
        except ValueError as exc:
            _raise_bad_request(exc)
        if item is None:
            raise HTTPException(status_code=404, detail={"error": "session not found"})
        return {"item": item}

    @router.get("/api/sessions/{kind}/{session_id}/candidates")
    async def list_session_candidates(
        kind: str,
        session_id: str,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=200),
        authorization: str | None = Header(default=None),
    ):
        identity = require_identity(authorization)
        try:
            page = await run_in_threadpool(
                session_service.list_session_candidates,
                identity,
                kind,
                session_id,
                offset=offset,
                limit=limit,
            )
        except ValueError as exc:
            _raise_bad_request(exc)
        if page is None:
            raise HTTPException(status_code=404, detail={"error": "session not found"})
        return page

    @router.get("/api/sessions/{kind}/{session_id}/events")
    async def stream_session_events(
        kind: str,
        session_id: str,
        request: Request,
        authorization: str | None = Header(default=None),
    ):
        identity = require_identity(authorization)
        owner_id = str(identity.get("id") or "").strip() or "anonymous"
        try:
            item = await run_in_threadpool(session_service.get_session_metadata, identity, kind, session_id)
        except ValueError as exc:
            _raise_bad_request(exc)
        if item is None:
            raise HTTPException(status_code=404, detail={"error": "session not found"})
        subscriber = session_service.subscribe(owner_id, kind, session_id)

        async def events():
            try:
                yield _format_sse("session", item)
                while not await request.is_disconnected():
                    try:
                        message = await asyncio.to_thread(subscriber.get, True, 15)
                    except queue.Empty:
                        yield _format_sse("heartbeat", {})
                        continue
                    event_name = str(message.get("event") or "message")
                    if event_name == "session":
                        yield _format_sse("session", message.get("item") if isinstance(message.get("item"), dict) else {})
                    elif event_name == "session-delta":
                        yield _format_sse("session-delta", message.get("delta") if isinstance(message.get("delta"), dict) else {})
                    elif event_name == "deleted":
                        yield _format_sse("deleted", {"id": message.get("id")})
                    else:
                        yield _format_sse(event_name, message)
            finally:
                session_service.unsubscribe(owner_id, kind, session_id, subscriber)

        return StreamingResponse(events(), media_type="text/event-stream")

    @router.post("/api/sessions")
    async def save_session(body: SessionSaveRequest, authorization: str | None = Header(default=None)):
        identity = require_identity(authorization)
        try:
            item = await run_in_threadpool(session_service.save_session, identity, body.kind, body.item)
        except ValueError as exc:
            _raise_bad_request(exc)
        return {"item": item}

    @router.delete("/api/sessions/{kind}/{session_id}")
    async def delete_session(kind: str, session_id: str, authorization: str | None = Header(default=None)):
        identity = require_identity(authorization)
        try:
            await run_in_threadpool(session_service.delete_session, identity, kind, session_id)
        except ValueError as exc:
            _raise_bad_request(exc)
        return {"ok": True}

    return router
