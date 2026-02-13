# 09_data_server/websocket.py
import asyncio
import websockets
import json
from typing import Dict, List, Callable, Optional, Set
from datetime import datetime
import logging
from collections import defaultdict
from enum import Enum

from .config import get_config, POLYGON_TIMEZONE
from .exceptions import PolygonWebSocketError, PolygonAuthenticationError, PolygonNetworkError
from .utils import normalize_ohlcv_data
from .validators import validate_ohlcv_integrity


class PolygonWebSocketClient:
    """
    WebSocket client for real-time Polygon.io data

    Handles connection management, authentication, subscriptions,
    and real-time data streaming with automatic reconnection.

    Supports both stocks and crypto markets.
    """

    def __init__(self, config=None, storage=None, market='stocks'):
        """
        Initialize WebSocket client

        Args:
            config: Configuration object (uses default if None)
            storage: Optional StorageManager for caching real-time data
            market: Market type ('stocks' or 'crypto')
        """
        self.config = config or get_config()
        self.storage = storage
        self.logger = self.config.get_logger(__name__)

        # Set market type and corresponding WebSocket URL
        self.market = market
        if market == 'crypto':
            self.ws_url = 'wss://socket.polygon.io/crypto'
        else:
            # Default to stocks for backwards compatibility
            self.ws_url = getattr(self.config, 'websocket_url', 'wss://socket.polygon.io/stocks')

        self.connection = None
        self.authenticated = False
        self.running = False

        # Subscription management
        self.subscriptions = defaultdict(set)  # {symbol: {channels}}
        self.callbacks = defaultdict(list)  # {symbol: [callbacks]}

        # Reconnection settings
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1.0  # seconds
        self.max_reconnect_delay = 30.0

        # Performance tracking
        self.message_count = 0
        self.last_message_time = None
        self.connection_start_time = None

    def _format_channel_for_market(self, channel: str, symbol: str) -> str:
        """
        Format subscription channel based on market type

        Args:
            channel: Channel type (T, Q, A, etc.)
            symbol: Symbol to subscribe to

        Returns:
            Formatted subscription string
        """
        if self.market == 'crypto':
            # Convert symbol format for crypto
            # X:BTCUSD -> BTC-USD
            if symbol.startswith("X:"):
                symbol = symbol[2:]  # Remove X:
                # Convert BTCUSD to BTC-USD
                if "USD" in symbol:
                    symbol = symbol.replace("USD", "-USD")
                elif "EUR" in symbol:
                    symbol = symbol.replace("EUR", "-EUR")
                elif "BTC" in symbol and symbol != "BTC":
                    symbol = symbol.replace("BTC", "-BTC")

            # Map channels to crypto format
            channel_map = {
                'T': 'XT',  # Trades
                'Q': 'XQ',  # Quotes
                'A': 'XA',  # Aggregates
                'AM': 'XA',  # Also aggregates for crypto
                'L2': 'XL2'  # Level 2 book
            }
            channel = channel_map.get(channel, f"X{channel}")
            return f"{channel}.{symbol}"
        else:
            # Standard stock format
            return f"{channel}.{symbol}"

    async def connect(self):
        """
        Establish WebSocket connection and authenticate

        Returns:
            bool: True if connected successfully

        Raises:
            PolygonWebSocketError: Connection failed
            PolygonAuthenticationError: Authentication failed
        """
        try:
            self.logger.info(f"Connecting to {self.market} WebSocket: {self.ws_url}")

            # Create WebSocket connection
            self.connection = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )

            # Authenticate
            await self._authenticate()

            self.running = True
            self.reconnect_attempts = 0
            self.connection_start_time = datetime.now()

            self.logger.info(f"{self.market.capitalize()} WebSocket connected and authenticated successfully")
            return True

        except websockets.exceptions.WebSocketException as e:
            self.logger.error(f"WebSocket connection failed: {e}")
            raise PolygonWebSocketError(f"Connection failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            raise PolygonNetworkError(f"Network error: {e}")

    async def _authenticate(self):
        auth_msg = {
            "action": "auth",
            "params": self.config.api_key
        }

        self.logger.info(f"Sending authentication request for {self.market}...")
        await self.connection.send(json.dumps(auth_msg))

        # First message is usually the connection confirmation
        response = await self.connection.recv()
        data = json.loads(response)
        self.logger.debug(f"First response: {json.dumps(data, indent=2)}")

        # Check if this is just a connection message
        if isinstance(data, list) and len(data) > 0:
            first_msg = data[0]
            if (first_msg.get("ev") == "status" and
                    first_msg.get("status") == "connected"):
                self.logger.info("Connection confirmed, waiting for auth response...")
                # Wait for the actual auth response
                response = await self.connection.recv()
                data = json.loads(response)
                self.logger.debug(f"Auth response: {json.dumps(data, indent=2)}")

        # Now check for authentication success
        auth_success = False

        if isinstance(data, list) and len(data) > 0:
            first_msg = data[0]
            if first_msg.get("status") == "auth_success":
                auth_success = True
            elif (first_msg.get("ev") == "status" and
                  first_msg.get("status") == "auth_success"):
                auth_success = True

        elif isinstance(data, dict):
            if data.get("status") == "auth_success":
                auth_success = True
            elif (data.get("ev") == "status" and
                  data.get("status") == "auth_success"):
                auth_success = True
            elif data.get("message") == "authenticated":
                auth_success = True

        if auth_success:
            self.authenticated = True
            self.logger.info(f"{self.market.capitalize()} authentication successful")
            return
        else:
            self.logger.error(f"Authentication failed. Response: {json.dumps(data)}")
            raise PolygonAuthenticationError(f"Authentication failed: {data}")

    async def subscribe(self, symbols: List[str], channels: List[str],
                        callback: Callable, subscription_id: Optional[str] = None):
        """
        Subscribe to real-time data for symbols

        Args:
            symbols: List of ticker symbols
            channels: List of channel types ['T', 'Q', 'A', 'AM']
                     T = Trades, Q = Quotes, A = Aggregates, AM = Aggregate Minute
            callback: Async function to call with data
            subscription_id: Optional ID to track this subscription

        Returns:
            str: Subscription ID for later unsubscribe
        """
        if not self.authenticated:
            raise PolygonWebSocketError("Must be authenticated before subscribing")

        # Filter channels based on market
        if self.market == 'crypto':
            # Crypto supports different channels
            valid_channels = {'T', 'Q', 'A', 'L2'}
            # Remove unsupported channels
            channels = [c for c in channels if c in valid_channels]
            if not channels:
                self.logger.warning("No valid channels for crypto subscription, defaulting to trades")
                channels = ['T']
        else:
            # Stock validation
            valid_channels = {'T', 'Q', 'A', 'AM'}
            invalid_channels = set(channels) - valid_channels
            if invalid_channels:
                self.logger.warning(f"Removing invalid channels: {invalid_channels}")
                channels = [c for c in channels if c in valid_channels]

        # Store callbacks
        sub_id = subscription_id or f"sub_{datetime.now().timestamp()}"
        for symbol in symbols:
            self.callbacks[symbol].append((sub_id, callback))
            self.subscriptions[symbol].update(channels)

        # Build subscription message with market-specific formatting
        subscriptions = []
        for channel in channels:
            for symbol in symbols:
                sub_str = self._format_channel_for_market(channel, symbol)
                subscriptions.append(sub_str)

        if not subscriptions:
            self.logger.warning("No valid subscriptions to send")
            return sub_id

        sub_msg = {
            "action": "subscribe",
            "params": ",".join(subscriptions)
        }

        self.logger.info(f"Subscribing to {self.market}: {subscriptions}")
        await self.connection.send(json.dumps(sub_msg))
        self.logger.info(f"Subscribed to {len(subscriptions)} channels for {len(symbols)} symbols")

        return sub_id

    async def unsubscribe(self, symbols: List[str], channels: Optional[List[str]] = None,
                          subscription_id: Optional[str] = None):
        """
        Unsubscribe from real-time data

        Args:
            symbols: List of symbols to unsubscribe
            channels: Specific channels to unsubscribe (all if None)
            subscription_id: Remove specific subscription callback
        """
        if not self.authenticated:
            return

        # Remove callbacks if subscription_id provided
        if subscription_id:
            for symbol in symbols:
                self.callbacks[symbol] = [
                    (sid, cb) for sid, cb in self.callbacks[symbol]
                    if sid != subscription_id
                ]

        # Determine channels to unsubscribe
        if channels is None:
            channels = list(set().union(*[self.subscriptions[s] for s in symbols]))

        # Build unsubscribe message with market-specific formatting
        unsubscriptions = []
        for channel in channels:
            for symbol in symbols:
                unsub_str = self._format_channel_for_market(channel, symbol)
                unsubscriptions.append(unsub_str)

        unsub_msg = {
            "action": "unsubscribe",
            "params": ",".join(unsubscriptions)
        }

        await self.connection.send(json.dumps(unsub_msg))
        self.logger.info(f"Unsubscribed from {len(unsubscriptions)} channels")

        # Update tracking
        for symbol in symbols:
            if channels:
                self.subscriptions[symbol] -= set(channels)
            else:
                self.subscriptions[symbol].clear()

    async def listen(self):
        """
        Main listening loop for receiving data

        Handles incoming messages, errors, and reconnection
        """
        while self.running:
            try:
                if not self.connection or (hasattr(self.connection, 'state') and self.connection.state.name != 'OPEN'):
                    await self._reconnect()
                    continue

                # Receive message
                message = await self.connection.recv()
                await self._handle_message(message)

            except websockets.exceptions.ConnectionClosedError as e:
                self.logger.warning(f"WebSocket connection closed: {e}")
                await self._reconnect()

            except websockets.exceptions.WebSocketException as e:
                self.logger.error(f"WebSocket error: {e}")
                await self._reconnect()

            except Exception as e:
                self.logger.error(f"Unexpected error in listen loop: {e}")
                # Don't reconnect for unknown errors, just log
                await asyncio.sleep(0.1)  # Prevent tight loop

    async def _handle_message(self, message: str):
        """
        Process incoming WebSocket message

        Args:
            message: Raw message string from WebSocket
        """
        try:
            data = json.loads(message)

            # Handle different message types
            if isinstance(data, list):
                for item in data:
                    await self._process_data_item(item)
            else:
                await self._process_data_item(data)

            # Update metrics
            self.message_count += 1
            self.last_message_time = datetime.now()

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    async def _process_data_item(self, data: Dict):
        """
        Process individual data item

        Args:
            data: Parsed data dictionary
        """
        event_type = data.get('ev')

        # Get symbol based on market type
        if self.market == 'crypto':
            # Crypto uses 'pair' field
            symbol = data.get('pair', data.get('sym'))

            # Convert back to standard format for callbacks
            # BTC-USD -> X:BTCUSD
            if symbol and '-' in symbol:
                symbol = f"X:{symbol.replace('-', '')}"
        else:
            symbol = data.get('sym')

        if not event_type or not symbol:
            return

        # Get callbacks for this symbol
        callbacks = self.callbacks.get(symbol, [])

        # Process based on event type and market
        processed_data = None

        if self.market == 'crypto':
            if event_type == 'XT':  # Crypto Trade
                processed_data = self._process_crypto_trade(data, symbol)
            elif event_type == 'XQ':  # Crypto Quote
                processed_data = self._process_crypto_quote(data, symbol)
            elif event_type == 'XA':  # Crypto Aggregate
                processed_data = self._process_crypto_aggregate(data, symbol)
        else:
            # Stock processing
            if event_type == 'T':  # Trade
                processed_data = self._process_trade(data)
            elif event_type == 'Q':  # Quote
                processed_data = self._process_quote(data)
            elif event_type in ['A', 'AM']:  # Aggregate
                processed_data = self._process_aggregate(data)

        # Handle status messages
        if event_type == 'status':
            await self._handle_status_message(data)
            return

        # Call registered callbacks
        if processed_data:
            for sub_id, callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(processed_data)
                    else:
                        callback(processed_data)
                except Exception as e:
                    self.logger.error(f"Callback error for {symbol}: {e}")

            # Optionally update storage
            if self.storage and hasattr(self.storage, 'update_realtime'):
                try:
                    await self.storage.update_realtime(symbol, processed_data)
                except Exception as e:
                    self.logger.error(f"Storage update error: {e}")

    def _process_trade(self, data: Dict) -> Dict:
        """Process stock trade data"""
        return {
            'event_type': 'trade',
            'symbol': data['sym'],
            'timestamp': data['t'],
            'price': data['p'],
            'size': data['s'],
            'conditions': data.get('c', []),
            'exchange': data.get('x'),
            'trade_id': data.get('i')
        }

    def _process_crypto_trade(self, data: Dict, symbol: str) -> Dict:
        """Process crypto trade data"""
        return {
            'event_type': 'crypto_trade',
            'symbol': symbol,
            'pair': data.get('pair'),
            'timestamp': data.get('t'),
            'price': data.get('p'),
            'size': data.get('s'),
            'conditions': data.get('c', []),
            'exchange': data.get('x'),
            'trade_id': data.get('i')
        }

    def _process_quote(self, data: Dict) -> Dict:
        """Process stock quote data"""
        return {
            'event_type': 'quote',
            'symbol': data['sym'],
            'timestamp': data['t'],
            'bid_price': data.get('bp'),
            'bid_size': data.get('bs'),
            'ask_price': data.get('ap'),
            'ask_size': data.get('as'),
            'exchange': data.get('x')
        }

    def _process_crypto_quote(self, data: Dict, symbol: str) -> Dict:
        """Process crypto quote data"""
        return {
            'event_type': 'crypto_quote',
            'symbol': symbol,
            'pair': data.get('pair'),
            'timestamp': data.get('t'),
            'bid_price': data.get('bp'),
            'bid_size': data.get('bs'),
            'ask_price': data.get('ap'),
            'ask_size': data.get('as'),
            'exchange': data.get('x')
        }

    def _process_aggregate(self, data: Dict) -> Dict:
        """Process stock aggregate bar data"""
        return {
            'event_type': 'aggregate',
            'symbol': data['sym'],
            'timestamp': data.get('s', data.get('t')),
            'open': data['o'],
            'high': data['h'],
            'low': data['l'],
            'close': data['c'],
            'volume': data['v'],
            'vwap': data.get('vw'),
            'transactions': data.get('n')
        }

    def _process_crypto_aggregate(self, data: Dict, symbol: str) -> Dict:
        """Process crypto aggregate data"""
        return {
            'event_type': 'crypto_aggregate',
            'symbol': symbol,
            'pair': data.get('pair'),
            'timestamp': data.get('s', data.get('t')),
            'open': data.get('o'),
            'high': data.get('h'),
            'low': data.get('l'),
            'close': data.get('c'),
            'volume': data.get('v'),
            'vwap': data.get('vw')
        }

    async def _handle_status_message(self, data: Dict):
        """Handle status messages from server"""
        status = data.get('status')
        message = data.get('message', '')

        self.logger.info(f"Status message: {status} - {message}")

        # Handle specific status types
        if status == 'error':
            self.logger.error(f"Server error: {message}")

    async def _reconnect(self):
        """
        Attempt to reconnect with exponential backoff
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.error("Max reconnection attempts reached, stopping")
            self.running = False
            return

        self.reconnect_attempts += 1
        delay = min(
            self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)),
            self.max_reconnect_delay
        )

        self.logger.info(f"Reconnecting in {delay} seconds (attempt {self.reconnect_attempts})")
        await asyncio.sleep(delay)

        try:
            await self.connect()

            # Resubscribe to previous subscriptions
            if self.subscriptions:
                for symbol, channels in self.subscriptions.items():
                    if channels:
                        # Find callbacks for this symbol
                        callbacks = self.callbacks.get(symbol, [])
                        if callbacks:
                            # Use first callback for resubscription
                            _, callback = callbacks[0]
                            await self.subscribe([symbol], list(channels), callback)

        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")

    async def disconnect(self):
        """
        Disconnect WebSocket connection
        """
        self.running = False

        if self.connection:
            try:
                await self.connection.close()
            except Exception as e:
                self.logger.debug(f"Error closing connection: {e}")

        self.authenticated = False
        self.logger.info(f"{self.market.capitalize()} WebSocket disconnected")

    def get_status(self) -> Dict:
        """Get current connection status"""
        is_connected = False
        if self.connection is not None:
            try:
                is_connected = self.connection.state.name == 'OPEN'
            except:
                is_connected = self.connection is not None

        return {
            'market': self.market,
            'connected': is_connected,
            'authenticated': self.authenticated,
            'running': self.running,
            'subscriptions': {
                symbol: list(channels)
                for symbol, channels in self.subscriptions.items()
            },
            'message_count': self.message_count,
            'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None,
            'uptime_seconds': (
                (datetime.now() - self.connection_start_time).total_seconds()
                if self.connection_start_time else 0
            ),
            'reconnect_attempts': self.reconnect_attempts
        }

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()