
from collections import deque
import numpy as np
from typing import List

class SpikePredictor:
    def __init__(self, window_size: int = 300):
        self.window_size = window_size
        self.taker_volumes: deque = deque(maxlen=window_size)
    
    def add_trade(self, amount: float):
        """
        Add a taker trade volume to the sliding window.
        """
        self.taker_volumes.append(amount)
        
    def get_z_score(self, current_volume_5m: float) -> float:
        """
        Calculate Z-Score of the current 5-minute volume against the daily mean (window).
        Z = (X - \mu) / \sigma
        Current logic: Compare 'current_volume_5m' against the stats of 'taker_volumes' history.
        """
        if len(self.taker_volumes) < 10:
            return 0.0
            
        data = np.array(self.taker_volumes)
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return 0.0
            
        return (current_volume_5m - mean) / std

    def is_aggressive(self, current_volume_5m: float, threshold: float = 2.0) -> bool:
        return self.get_z_score(current_volume_5m) > threshold
