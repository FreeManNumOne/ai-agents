"""
Moon Dev's WebSocket Module
Real-time data feeds for trading agents

Components:
- HyperliquidWebSocket: Low-level WebSocket client
- PriceFeed: Real-time price streaming with events
- OrderBookFeed: Real-time L2 order book data
- WebSocketDataManager: Unified manager for API replacement

Usage:
    # Start WebSocket feeds at app startup
    from src.websocket import start_websocket_feeds
    start_websocket_feeds()

    # Use drop-in replacement functions
    from src.websocket import get_current_price, ask_bid
    price = get_current_price('BTC')
    ask, bid, _ = ask_bid('ETH')
"""

from src.websocket.hyperliquid_ws import HyperliquidWebSocket
from src.websocket.price_feed import PriceFeed, get_price_feed, get_current_price_ws, get_ask_bid_ws
from src.websocket.orderbook_feed import OrderBookFeed, get_orderbook_feed, get_l2_book_ws
from src.websocket.data_manager import (
    WebSocketDataManager,
    get_data_manager,
    start_websocket_feeds,
    stop_websocket_feeds,
    get_current_price,
    ask_bid,
    get_market_info,
    is_websocket_enabled,
    is_websocket_connected,
    get_data_source,
)

__all__ = [
    # Low-level WebSocket client
    'HyperliquidWebSocket',
    # Price feed
    'PriceFeed',
    'get_price_feed',
    'get_current_price_ws',
    'get_ask_bid_ws',
    # Order book feed
    'OrderBookFeed',
    'get_orderbook_feed',
    'get_l2_book_ws',
    # Data manager (recommended for most use cases)
    'WebSocketDataManager',
    'get_data_manager',
    'start_websocket_feeds',
    'stop_websocket_feeds',
    # Drop-in replacement functions
    'get_current_price',
    'ask_bid',
    'get_market_info',
    # Utility functions
    'is_websocket_enabled',
    'is_websocket_connected',
    'get_data_source',
]
