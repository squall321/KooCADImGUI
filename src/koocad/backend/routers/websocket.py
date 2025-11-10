"""
WebSocket router for real-time updates.

Provides real-time updates for:
- Job progress
- Job status changes
- Error notifications
- 3D preview updates
"""

from __future__ import annotations

import asyncio
import json
from typing import Dict, Set

try:
    from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    APIRouter = None  # type: ignore
    WebSocket = None  # type: ignore
    WebSocketDisconnect = None  # type: ignore
    Depends = None  # type: ignore

from koocad.backend.database import get_db
from koocad.backend.models.job import Job

if WEBSOCKET_AVAILABLE:
    router = APIRouter()
else:
    router = None  # type: ignore


class ConnectionManager:
    """WebSocket connection manager."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """Accept and register WebSocket connection.

        Args:
            websocket: WebSocket connection.
            user_id: User ID.
        """
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        """Remove WebSocket connection.

        Args:
            websocket: WebSocket connection.
            user_id: User ID.
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(
        self, message: dict, user_id: int
    ) -> None:
        """Send message to all connections for a user.

        Args:
            message: Message to send.
            user_id: User ID.
        """
        if user_id not in self.active_connections:
            return

        # Send to all active connections for this user
        disconnected = set()
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection closed
                disconnected.add(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.active_connections[user_id].discard(connection)

    async def broadcast_job_update(
        self,
        job_id: int,
        user_id: int,
        status: str,
        progress: float,
        error: str | None = None,
    ) -> None:
        """Broadcast job update to user.

        Args:
            job_id: Job ID.
            user_id: User ID.
            status: Job status.
            progress: Progress percentage (0-100).
            error: Optional error message.
        """
        message = {
            "type": "job_update",
            "job_id": job_id,
            "status": status,
            "progress": progress,
        }
        if error:
            message["error"] = error

        await self.send_personal_message(message, user_id)


# Global connection manager
if WEBSOCKET_AVAILABLE:
    manager = ConnectionManager()


if WEBSOCKET_AVAILABLE:

    @router.websocket("/ws/{user_id}")
    async def websocket_endpoint(
        websocket: WebSocket,
        user_id: int,
    ) -> None:
        """WebSocket endpoint for real-time updates.

        Args:
            websocket: WebSocket connection.
            user_id: User ID.
        """
        await manager.connect(websocket, user_id)
        try:
            # Send connection confirmation
            await websocket.send_json({
                "type": "connection",
                "status": "connected",
                "user_id": user_id,
            })

            # Keep connection alive and handle incoming messages
            while True:
                # Receive message from client
                data = await websocket.receive_text()

                try:
                    message = json.loads(data)

                    # Handle different message types
                    if message.get("type") == "ping":
                        # Respond to ping with pong
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": message.get("timestamp"),
                        })
                    elif message.get("type") == "subscribe_job":
                        # Client wants to subscribe to job updates
                        job_id = message.get("job_id")
                        await websocket.send_json({
                            "type": "subscribed",
                            "job_id": job_id,
                        })

                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON",
                    })

        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
        except Exception as e:
            print(f"WebSocket error: {e}")
            manager.disconnect(websocket, user_id)


    async def notify_job_progress(
        job_id: int,
        user_id: int,
        progress: float,
        status: str,
        error: str | None = None,
    ) -> None:
        """Notify user of job progress via WebSocket.

        This function is called by Celery tasks to send updates.

        Args:
            job_id: Job ID.
            user_id: User ID.
            progress: Progress percentage (0-100).
            status: Job status.
            error: Optional error message.
        """
        await manager.broadcast_job_update(
            job_id=job_id,
            user_id=user_id,
            status=status,
            progress=progress,
            error=error,
        )
