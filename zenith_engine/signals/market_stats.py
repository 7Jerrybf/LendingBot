
from decimal import Decimal
from typing import Dict, Tuple, List
import numpy as np

class MarketStats:
    @staticmethod
    def calculate_vwar(trades: List[Tuple[Decimal, Decimal, float]]) -> float:
        """
        Calculate Volume Weighted Average Rate (VWAR).
        trades: List of (rate, amount, timestamp)
        """
        if not trades:
            return 0.0
            
        total_vol = sum(abs(amount) for _, amount, _ in trades)
        if total_vol == 0:
            return 0.0
        
        weighted_sum = sum(rate * abs(amount) for rate, amount, _ in trades)
        return float(weighted_sum / total_vol)

    @staticmethod
    def calculate_volatility(trades: List[Tuple[Decimal, Decimal, float]], window_size: int = 50) -> float:
        """
        Calculate volatility (std dev of rates) for the last N trades.
        """
        if len(trades) < 2:
            return 0.0
            
        # Take last N trades
        recent_trades = trades[-window_size:]
        rates = [float(r) for r, _, _ in recent_trades]
        
        return float(np.std(rates))

    @staticmethod
    def calculate_depth_skewness(bids: Dict[Decimal, Decimal], asks: Dict[Decimal, Decimal], depth_levels: int = 10) -> float:
        """
        Calculate Order Book Skewness.
        Skewness = (Bid_Vol - Ask_Vol) / (Bid_Vol + Ask_Vol)
        Range: [-1, 1]. Positive = Bullish (More Bids), Negative = Bearish (More Asks).
        """
        sorted_bids = sorted(bids.items(), key=lambda x: x[0], reverse=True)[:depth_levels]
        sorted_asks = sorted(asks.items(), key=lambda x: x[0])[:depth_levels]
        
        bid_vol = sum(amount for _, amount in sorted_bids)
        ask_vol = sum(amount for _, amount in sorted_asks)
        
        if bid_vol + ask_vol == 0:
            return 0.0
            
        return float((bid_vol - ask_vol) / (bid_vol + ask_vol))

    @staticmethod
    def calculate_ofi(current_bids: Dict[Decimal, Decimal], current_asks: Dict[Decimal, Decimal],
                      prev_bids: Dict[Decimal, Decimal], prev_asks: Dict[Decimal, Decimal], depth_levels: int = 5) -> float:
        """
        Calculate Order Flow Imbalance (OFI).
        Simplified version focusing on top-level volume changes.
        OFI > 0: Net buying pressure.
        OFI < 0: Net selling pressure.
        """
        # This is high frequency, so we focus on the best bid/ask changes
        # For simplicity in this initial version, we will just compare total volume at top L levels change
        # A more robust implementation would track specific price levels shifting
        
        def get_top_vol(book: Dict[Decimal, Decimal], reverse: bool) -> Decimal:
            sorted_items = sorted(book.items(), key=lambda x: x[0], reverse=reverse)[:depth_levels]
            return sum(amount for _, amount in sorted_items)

        curr_bid_vol = get_top_vol(current_bids, True)
        prev_bid_vol = get_top_vol(prev_bids, True)
        curr_ask_vol = get_top_vol(current_asks, False)
        prev_ask_vol = get_top_vol(prev_asks, False)
        
        delta_bid = curr_bid_vol - prev_bid_vol
        delta_ask = curr_ask_vol - prev_ask_vol
        
        # OFI = Change in Bid Vol - Change in Ask Vol
        return float(delta_bid - delta_ask)
