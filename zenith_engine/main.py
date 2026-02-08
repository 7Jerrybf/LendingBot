
import asyncio
import logging
from decimal import Decimal
from datetime import datetime, time as dt_time
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
                
            except Exception as e:
                logger.error(f"Rebalance Loop Error: {e}")
                
            await asyncio.sleep(10)

    async def _daily_status_notification(self):
        """Send daily status notification at 1:00 PM"""
        while self.running:
            try:
                now = datetime.now()
                target_time = now.replace(hour=13, minute=0, second=0, microsecond=0)
                
                # If already past 1 PM today, schedule for tomorrow
                if now >= target_time:
                    target_time = target_time.replace(day=now.day + 1)
                
                # Calculate seconds until target time
                wait_seconds = (target_time - now).total_seconds()
                logger.info(f"Next daily notification scheduled in {wait_seconds:.0f} seconds")
                
                await asyncio.sleep(wait_seconds)
                
                # Send daily status
                await self._send_status_report()
                
                # Wait a bit to avoid double triggers
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Daily notification error: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour

    async def _send_status_report(self):
        """Generate and send status report"""
        try:
            # Calculate current metrics
            vwar = 0.0
            if self.state.trades:
                vwar = MarketStats.calculate_vwar(self.state.trades)
            elif self.state.bids:
                vwar = float(max(self.state.bids.keys()))
            
            # Calculate APR (VWAR * 365 * 100 for percentage)
            current_apr = vwar * 365 * 100
            
            # Calculate utilization
            total_equity = self.state.get_total_equity()
            if total_equity > 0:
                utilization = float(self.state.lent_balance / total_equity * 100)
            else:
                utilization = 0.0
            
            # Active layers info
            active_layers = []
            if self.state.is_aggressive_mode:
                active_layers.append("🔥 Aggressive Mode Active")
            if self.state.pending_orders:
                active_layers.append(f"📊 {len(self.state.pending_orders)} pending orders")
            if not active_layers:
                active_layers.append("✅ Normal operation")
            
            await self.discord.send_report(current_apr, utilization, active_layers)
            logger.info("Daily status notification sent")
            
        except Exception as e:
            logger.error(f"Failed to send status report: {e}")

    async def start(self):
        logger.info("Starting Zenith Liquidity Engine...")
        
        # Start WS in background
        asyncio.create_task(self.ws_client.connect())
        
        # Start Signal Loop
        asyncio.create_task(self._update_signals())
        
        # Start Daily Notification Scheduler
        asyncio.create_task(self._daily_status_notification())
        
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
