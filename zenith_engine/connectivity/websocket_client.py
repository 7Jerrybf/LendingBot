
import asyncio
import websockets
import json
import logging
import time
from decimal import Decimal
from ..config import Config
from ..state import State

logger = logging.getLogger(__name__)

class WebSocketClient:
    def __init__(self, state: State):
        self.state = state
        self.uri = "wss://api-pub.bitfinex.com/ws/2"
        self.connected = False
        self.last_pong = 0
        self.chan_map = {} # ID -> Channel Name
        
    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    self.connected = True
                    logger.info("Connected to Bitfinex WS")
                    self.chan_map = {}
                    
                    # Subscribe to Funding Book
                    await websocket.send(json.dumps({
                        "event": "subscribe",
                        "channel": "book",
                        "symbol": Config.SYMBOL,
                        "prec": "P0",
                        "frec": "F0",
                        "len": "100"
                    }))
                    
                    # Subscribe to Trades
                    await websocket.send(json.dumps({
                        "event": "subscribe",
                        "channel": "trades",
                        "symbol": Config.SYMBOL
                    }))
                    
                    # Ping loop
                    asyncio.create_task(self._heartbeat(websocket))
                    
                    async for message in websocket:
                        await self._handle_message(message)
                        self.state.last_update_time = time.time()
                        
            except Exception as e:
                logger.error(f"WS Connection error: {e}")
                self.connected = False
                await asyncio.sleep(5)  # Reconnect delay

    async def _heartbeat(self, websocket):
        while self.connected:
            try:
                if time.time() - self.state.last_update_time > Config.WS_TIMEOUT_SECONDS:
                    logger.warning("No data received for 30s, reconnecting...")
                    await websocket.close()
                    break
            except Exception:
                break
            await asyncio.sleep(5)

    async def _handle_message(self, message):
        data = json.loads(message)
        
        if isinstance(data, dict):
            if "event" in data:
                if data["event"] == "info":
                    return
                if data["event"] == "subscribed":
                    chan_id = data["chanId"]
                    channel = data["channel"]
                    logger.info(f"Subscribed to {channel} (ID: {chan_id})")
                    self.chan_map[chan_id] = channel
                    return

        if isinstance(data, list):
            # [CHANNEL_ID, [DATA]] or [CHANNEL_ID, "hb"]
            chan_id = data[0]
            if data[1] == "hb":
                return
            
            channel_name = self.chan_map.get(chan_id)
            if not channel_name:
                return

            if channel_name == "book":
                self._handle_book(data[1])
            elif channel_name == "trades":
                self._handle_trades(data)

    def _handle_book(self, content):
        if len(content) > 0:
            if isinstance(content[0], list):
                # Snapshot
                bids = {}
                asks = {}
                for entry in content:
                    rate, period, count, amount = entry
                    rate_dec = Decimal(str(rate))
                    amount_dec = Decimal(str(amount))
                    
                    if amount_dec > 0: # Bid/Borrow
                        bids[rate_dec] = amount_dec
                    else: # Ask/Lend
                        asks[rate_dec] = -amount_dec
                        
                self.state.update_book(bids, asks)
            else:
                # Update
                rate, period, count, amount = content
                rate_dec = Decimal(str(rate))
                amount_dec = Decimal(str(amount))
                
                if count == 0:
                    if rate_dec in self.state.bids: del self.state.bids[rate_dec]
                    if rate_dec in self.state.asks: del self.state.asks[rate_dec]
                else:
                    if amount_dec > 0:
                        self.state.bids[rate_dec] = amount_dec
                    else:
                        self.state.asks[rate_dec] = -amount_dec

    def _handle_trades(self, data):
        # Format: [CHAN_ID, "te", [ID, MTS, AMOUNT, RATE, PERIOD]]
        # Snapshot: [CHAN_ID, [[ID, MTS, AMOUNT, RATE, PERIOD], ...]]
        
        content = data[1]
        
        if isinstance(content, list):
            # Snapshot
            for trade in content:
                self._add_trade(trade)
        elif content == "te" or content == "tu":
            trade = data[2]
            self._add_trade(trade)
            
    def _add_trade(self, trade_data):
        # [ID, MTS, AMOUNT, RATE, PERIOD]
        # Funding Trades:
        # Rate is index 3
        try:
            # Check ID
            trade_id, mts, amount, rate, period = trade_data
            
            rate_dec = Decimal(str(rate))
            amount_dec = Decimal(str(amount)) # Positive/Negative implies direction
            
            # Add to state (Keep last N trades)
            self.state.trades.append((rate_dec, amount_dec, mts))
            
            # Prune old trades (e.g., keep last 1000)
            if len(self.state.trades) > 1000:
                self.state.trades = self.state.trades[-1000:]
                
        except Exception as e:
            logger.error(f"Error parsing trade: {e}")
