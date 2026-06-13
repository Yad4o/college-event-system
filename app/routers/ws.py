"""
WebSocket endpoint — Phase 34.

Clients connect to /ws/notifications?token=<access_token>

Authentication is done via the ?token= query param because the browser
WebSocket API does not support custom headers.

Lifecycle
---------
  1. Client opens  ws://.../ws/notifications?token=<jwt>
  2. Server decodes the token and calls manager.connect(user_id, ws)
  3. Server loops on receive_text() so the socket stays alive
     (client may send any text; it is silently ignored)
  4. On any disconnect / error the socket is pruned from the manager

Push flow (Phase 32 hook already in notification_service):
  notification_service.create_notification()
    -> asyncio.create_task(manager.send_to_user(user_id, payload))
  This delivers the notification JSON over the socket within milliseconds.
"""

import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.utils.jwt import decode_token
from app.utils.ws_manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/notifications")
async def ws_notifications(
    websocket: WebSocket,
    token: str = Query(..., description="Valid JWT access token"),
) -> None:
    """
    Real-time notification stream for the authenticated user.

    Connect with:
        ws://<host>/ws/notifications?token=<access_token>

    The server pushes notification JSON objects whenever a new notification
    is created for this user.  No client messages are expected or processed.
    """
    # ── Authenticate before accepting ────────────────────────────────────────
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4001, reason="Invalid token type")
            return
        user_id = int(payload["sub"])
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # ── Register connection ───────────────────────────────────────────────────
    await manager.connect(user_id, websocket)
    try:
        # Keep the socket alive — receive loop; messages from client are ignored
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                # Send a lightweight ping to detect dead connections
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(user_id, websocket)
