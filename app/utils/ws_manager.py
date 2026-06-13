"""
WebSocket connection manager — Phase 34.

Tracks active WebSocket connections per user_id.
Multiple tabs / devices are supported: a user can have several concurrent sockets.

Usage
-----
  # In the WS route:
  await manager.connect(user_id, websocket)

  # From notification_service (after DB flush, before commit):
  import asyncio
  asyncio.create_task(manager.send_to_user(user_id, payload))

  # On disconnect:
  manager.disconnect(user_id, websocket)
"""

import asyncio
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # user_id -> list of active WebSocket connections
        self._connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Accept the WebSocket and register it for *user_id*."""
        await websocket.accept()
        self._connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """Remove *websocket* from the registry. Safe to call even if not found."""
        sockets = self._connections.get(user_id, [])
        if websocket in sockets:
            sockets.remove(websocket)
        if not sockets:
            self._connections.pop(user_id, None)

    def is_connected(self, user_id: int) -> bool:
        """Return True if the user has at least one live socket."""
        return bool(self._connections.get(user_id))

    async def send_to_user(self, user_id: int, payload: dict) -> None:
        """
        Push *payload* as JSON to every socket open for *user_id*.

        Dead sockets are cleaned up silently — a closed socket raises an
        exception on send which we catch and use to prune the registry.
        """
        sockets = list(self._connections.get(user_id, []))
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    async def broadcast(self, payload: dict) -> None:
        """Push *payload* to every connected user. Useful for platform announcements."""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, payload)


# Single global instance imported by both the WS router and notification_service
manager = ConnectionManager()
