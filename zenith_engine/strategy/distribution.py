
import numpy as np
from decimal import Decimal
from typing import List, Dict, Tuple
from ..config import Config

class DistributionStrategy:
    @staticmethod
    def calculate_vwar(trades: List[Tuple[float, float]]) -> float:
        """
        Calculate Volume Weighted Average Rate (VWAR).
        trades: List of (rate, amount)
        """
        total_vol = sum(amount for _, amount in trades)
        if total_vol == 0:
            return 0.0
        
        weighted_sum = sum(rate * amount for rate, amount in trades)
        return weighted_sum / total_vol

    @staticmethod
    def truncated_gaussian_distribution(mean: float, std: float, n_points: int = 10) -> List[float]:
        """
        Generate a truncated Gaussian distribution of rates.
        We want rates > mean usually for lending.
        """
        # Simple sampling
        samples = np.random.normal(mean, std, n_points * 2)
        # Filter items > mean (since we want to lend higher) or just around mean?
        # User says: "Orders at mu + 0.5sigma" etc.
        # Actually the algorithm specifies Layers, not just a random distribution for all orders.
        # But maybe we need it for "Laddered" filling.
        return [float(x) for x in samples if x > 0][:n_points]

    def generate_orders(self, available_capital: Decimal, vwar: float, volatility: float, signal_bias: float) -> List[Dict]:
        """
        Generate execution layers based on capital and stats.
        Mean = VWAR * (1 + Signal_Bias)
         Layers:
         - Base (40%): Best Bid
         - Alpha (30%): Mean + 0.5 * Vol
         - Spike (30%): Mean + 3.0 * Vol
        """
        mu = vwar * (1 + signal_bias)
        sigma = volatility
        
        total_cap = float(available_capital)
        orders = []
        
        # Base Layer (40%)
        # Note: "Best Bid" isn't passed here, so we return a placeholder rate or 
        # the caller must supply it. Let's assume the caller provides Best Bid info or we use a flag.
        # For this function, let's just return the target rates structure.
        
        # Strategy Weights from Config
        base_amt = total_cap * Config.LAYER_WEIGHTS["BASE"]
        alpha_amt = total_cap * Config.LAYER_WEIGHTS["ALPHA"]
        spike_amt = total_cap * Config.LAYER_WEIGHTS["SPIKE"]
        
        # Alpha Rate
        alpha_rate = mu + (0.5 * sigma)
        
        # Spike Rate
        spike_rate = mu + (3.0 * sigma)
        
        # We need at least MIN_ORDER_SIZE for each
        # If capital is too small, we might skip layers.
        # This logic should be handled here.
        
        # Base Layer (Target: Best Bid, will be set by caller)
        if base_amt >= Config.MIN_ORDER_SIZE:
             orders.append({
                "layer": "BASE",
                "amount": base_amt,
                "rate_target": "BEST_BID" 
            })
            
        # Alpha Layer
        if alpha_amt >= Config.MIN_ORDER_SIZE:
            orders.append({
                "layer": "ALPHA",
                "amount": alpha_amt,
                "rate": alpha_rate
            })
            
        # Spike Hunter
        if spike_amt >= Config.MIN_ORDER_SIZE:
            orders.append({
                "layer": "SPIKE",
                "amount": spike_amt,
                "rate": spike_rate
            })
            
        return orders
