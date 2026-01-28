
import asyncio
import logging
from decimal import Decimal
import os
import signal
from typing import List

from zenith_engine.config import Config
from zenith_engine.state import State, Order
from zenith_engine.connectivity.websocket_client import WebSocketClient
from zenith_engine.connectivity.rest_client import RestClient
from zenith_engine.signals.market_stats import MarketStats
from zenith_engine.signals.external import ExternalSignals
from zenith_engine.signals.spike_predictor import SpikePredictor
from zenith_engine.strategy.distribution import DistributionStrategy
from zenith_engine.strategy.rebalancer import Rebalancer
from zenith_engine.utils.discord import DiscordNotifier

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ZenithEngine")

class ZenithEngine:
    def __init__(self):
        self.state = State()
        self.ws_client = WebSocketClient(self.state)
        self.rest_client = RestClient()
        self.external_signals = ExternalSignals()
        self.spike_predictor = SpikePredictor()
        self.dist_strategy = DistributionStrategy()
        self.rebalancer = Rebalancer()
        self.discord = DiscordNotifier()
        
        self.running = True

    async def _update_signals(self):
        """Periodic Signal Updates"""
        while self.running:
            try:
                # 1. External: Perp Funding Rate (Every 60s)
                rate = await self.external_signals.get_perp_funding_rate()
                self.state.perp_funding_rate = rate
                
                if rate > Config.PERP_FUNDING_RATE_THRESHOLD:
                    # Logic: If perp funding is high, maybe increase bias?
                    # User spec: "increase the Spike_Probability_Score" -> Implies logic in distribution/state
                    pass
                
                # 2. Taker Volume (Simulated or via WS Trade channel if implemented)
                # For now, we rely on what we have.
                pass
                
            except Exception as e:
                logger.error(f"Signal Update Error: {e}")
            
            await asyncio.sleep(60)

    async def _rebalance_loop(self):
        """Dynamic Re-balancing Loop (Every 10s)"""
        while self.running:
            try:
                # Check connection safety
                if not self.ws_client.connected:
                    logger.warning("WS Disconnected, skipping rebalance.")
                    await asyncio.sleep(1)
                    continue
                
                # Calculate VWAR and Volatility from Book/History
                # Note: Real VWAR requires Trade History. 
                # For this implementation, we approximate using Mid-Price or active Book VWAP if no trades.
                # Let's use Book VWAP for simplicity or mock it?
                # Ideally, the WS client tracks trades.
                
                # Calculate VWAR and Volatility from Trade History
                vwar = 0.0
                volatility = 0.0001 # Default low vol
                
                if self.state.trades:
                    vwar = MarketStats.calculate_vwar(self.state.trades)
                    volatility = MarketStats.calculate_volatility(self.state.trades)
                    
                    # Update Spike Predictor
                    # Get latest trade volume (roughly)
                    last_trade_vol = float(self.state.trades[-1][1])
                    self.spike_predictor.add_trade(abs(last_trade_vol))
                    
                    # Check Spike Z-Score
                    z_score = self.spike_predictor.get_z_score(abs(last_trade_vol)) # Simplified, usually per minute
                    if z_score > Config.TAKER_VOL_Z_SCORE_THRESHOLD:
                        self.state.is_aggressive_mode = True
                    else:
                        self.state.is_aggressive_mode = False
                        
                elif self.state.bids:
                    # Fallback to Best Bid
                    vwar = float(max(self.state.bids.keys()))
                
                # Calculate Signal Bias
                signal_bias = 0.0
                if self.state.perp_funding_rate > Decimal(str(Config.PERP_FUNDING_RATE_THRESHOLD)):
                    signal_bias = 0.05 # +5%
                    
                # Check Aggressive Mode
                if self.state.is_aggressive_mode:
                    signal_bias += 0.10
                    
                # Generate Target Distribution
                # We need Available Balance. 
                # Note: We should fetch wallet balance via REST if not tracked via WS Auth.
                # For now assumes State has it (updated via another loop or mock).
                # Let's mock balance for the "Engine" loop to verify logic.
                available_cap = self.state.available_balance
                if available_cap < Config.MIN_ORDER_SIZE:
                    # Try to free up? Or just wait?
                    pass
                    
                orders_to_place = self.dist_strategy.generate_orders(
                    available_cap, vwar, volatility, signal_bias
                )
                
                # Rebalance Check
                # Iterate existing orders, calculate Eta, decide to Cancel/Replace.
                # Simplified: Just print what we WOULD do.
                
                logger.info(f"Cycle: VWAR={vwar:.6f} Bias={signal_bias} Orders={len(orders_to_place)}")
                
                # Send Report periodically (mock logic)
                # await self.discord.send_report(...)
                
            except Exception as e:
                logger.error(f"Rebalance Loop Error: {e}")
                
            await asyncio.sleep(10)

    async def start(self):
        logger.info("Starting Zenith Liquidity Engine...")
        
        # Start WS in background
        asyncio.create_task(self.ws_client.connect())
        
        # Start Signal Loop
        asyncio.create_task(self._update_signals())
        
        # Start Rebalance Loop
        await self._rebalance_loop()
        
    async def shutdown(self):
        self.running = False
        await self.external_signals.close()
        # Cancel all orders safely?
        logger.info("Shutdown complete.")

if __name__ == "__main__":
    engine = ZenithEngine()
    
    loop = asyncio.get_event_loop()
    
    # Handle Signals
    def handle_exit():
        asyncio.create_task(engine.shutdown())
        
    try:
        loop.run_until_complete(engine.start())
    except KeyboardInterrupt:
        handle_exit()
