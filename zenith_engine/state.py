
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import time

@dataclass
class Order:
    id: int
    amount: Decimal
    rate: Decimal
    period: int
    timestamp: float
    type: str # 'LIMIT', etc.

class State:
    def __init__(self):
        self.available_balance: Decimal = Decimal("0.0")
        self.lent_balance: Decimal = Decimal("0.0")
        self.pending_orders: Dict[int, Order] = {}
        
        # L2 Order Book Snapshot (Price -> Amount)
        self.bids: Dict[Decimal, Decimal] = {}
        self.asks: Dict[Decimal, Decimal] = {}
        
        # Trade History for VWAR/Vol (Rate, Amount, Timestamp)
        self.trades: List[Tuple[Decimal, Decimal, float]] = []
        
        # Signals
        self.perp_funding_rate: Decimal = Decimal("0.0")
        self.taker_volume_z_score: float = 0.0
        self.is_aggressive_mode: bool = False
        self.last_update_time: float = time.time()
        
    def update_balance(self, available: Decimal, lent: Decimal):
        self.available_balance = available
        self.lent_balance = lent
        self.last_update_time = time.time()

    def add_order(self, order: Order):
        self.pending_orders[order.id] = order
        
    def remove_order(self, order_id: int):
        if order_id in self.pending_orders:
            del self.pending_orders[order_id]
            
    def get_total_equity(self) -> Decimal:
        # Simple approximation
        return self.available_balance + self.lent_balance

    def update_book(self, bids: Dict[Decimal, Decimal], asks: Dict[Decimal, Decimal]):
        self.bids = bids
        self.asks = asks
        self.last_update_time = time.time()
