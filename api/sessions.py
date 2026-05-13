from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from api.support import require_identity
from services.session_service import session_service


class SessionSaveRequest(BaseModel):
    kind: str = Field(..., min_length=1)
    item: dict[str, Any] = Field(default_factory=dict)


def _raise_bad_request(exc: ValueError) -> None:
    raise HTTPException(status_code=400, detail={"error": str(exc)}) from exc


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
