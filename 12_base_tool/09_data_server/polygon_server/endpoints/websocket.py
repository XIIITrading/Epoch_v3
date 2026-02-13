"""
WebSocket endpoints for real-time data streaming
Supports both stocks and crypto markets
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, List, Optional
import json
import asyncio
from datetime import datetime
import logging

# Import from parent polygon module
from ... import PolygonWebSocketClient
from ..config import config

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}

        # Multiple Polygon clients for different markets
        self.polygon_clients: Dict[str, PolygonWebSocketClient] = {}
        self.listen_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            del self.client_subscriptions[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_to_client(self, client_id: str, data: dict):
        """Send data to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(data)
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")

    async def ensure_polygon_connected(self, market: str):
        """Ensure Polygon WebSocket is connected for specific market"""
        if market not in self.polygon_clients:
            logger.info(f"Creating Polygon {market} WebSocket client")

            # Create market-specific client
            self.polygon_clients[market] = PolygonWebSocketClient(market=market)
            await self.polygon_clients[market].connect()

            # Start listen task
            self.listen_tasks[market] = asyncio.create_task(
                self.polygon_clients[market].listen()
            )
            logger.info(f"Connected to Polygon {market} WebSocket")

    def determine_market(self, symbol: str) -> str:
        """Determine which market a symbol belongs to"""
        if symbol.startswith("X:"):
            return "crypto"
        else:
            return "stocks"

    async def subscribe_client(self, client_id: str, symbols: List[str], channels: List[str]):
        """Subscribe client to symbols with proper market routing"""

        # Group symbols by market
        stocks = []
        crypto = []

        for symbol in symbols:
            if symbol.startswith("X:"):
                crypto.append(symbol)
            else:
                stocks.append(symbol)

        results = []

        # Handle stock subscriptions
        if stocks:
            try:
                await self.ensure_polygon_connected("stocks")

                # Create callback for stocks
                async def stock_callback(data):
                    await self.send_to_client(client_id, {
                        "type": "market_data",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    })

                sub_id = f"{client_id}_stocks"
                await self.polygon_clients['stocks'].subscribe(
                    stocks, channels, stock_callback, sub_id
                )

                self.client_subscriptions[client_id].update(stocks)
                results.append(f"Subscribed to stocks: {stocks}")
                logger.info(f"Subscribed {client_id} to stocks: {stocks}")

            except Exception as e:
                logger.error(f"Stock subscription failed: {e}")
                results.append(f"Stock subscription error: {e}")

        # Handle crypto subscriptions
        if crypto:
            try:
                await self.ensure_polygon_connected("crypto")

                # Filter out unsupported channels for crypto
                crypto_channels = [c for c in channels if c != 'AS']

                # Create callback for crypto
                async def crypto_callback(data):
                    await self.send_to_client(client_id, {
                        "type": "market_data",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    })

                sub_id = f"{client_id}_crypto"
                await self.polygon_clients['crypto'].subscribe(
                    crypto, crypto_channels, crypto_callback, sub_id
                )

                self.client_subscriptions[client_id].update(crypto)
                results.append(f"Subscribed to crypto: {crypto}")
                logger.info(f"Subscribed {client_id} to crypto: {crypto}")

            except Exception as e:
                logger.error(f"Crypto subscription failed: {e}")
                results.append(f"Crypto subscription error: {e}")

        return f"client_{client_id}", results


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint supporting stocks and crypto"""
    await manager.connect(websocket, client_id)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Polygon data stream",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                symbols = data.get("symbols", [])
                channels = data.get("channels", ["T"])

                if symbols:
                    sub_id, results = await manager.subscribe_client(
                        client_id, symbols, channels
                    )

                    await websocket.send_json({
                        "type": "subscribed",
                        "symbols": symbols,
                        "channels": channels,
                        "subscription_id": sub_id,
                        "results": results
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No symbols provided"
                    })

            elif action == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    status = {
        "active_clients": len(manager.active_connections),
        "client_ids": list(manager.active_connections.keys()),
        "polygon_connected": len(manager.polygon_clients) > 0,
        "polygon_markets": {}
    }

    for market, client in manager.polygon_clients.items():
        status["polygon_markets"][market] = client.get_status()

    return status