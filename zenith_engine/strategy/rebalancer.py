
from decimal import Decimal
from ..config import Config

class Rebalancer:
    @staticmethod
    def calculate_efficiency_threshold(r_target: float, r_current: float, r_market: float, 
                                       t_wait: float = 0, t_exec: float = 0) -> float:
        """
        Calculate Efficiency Threshold (Eta).
        Formula: Eta = ((R_target - R_current) * 2880) / (R_market * (T_wait + T_exec))
        
        Where:
        - 2880: Constant (Wait, is this minutes in 2 days? 48 * 60 = 2880? 
                Or maybe seconds? 
                User formula: ((R_target - R_current) * 2880) / ...
                Let's assume the user provided constant is correct.
        """
        if r_market == 0 or (t_wait + t_exec) == 0:
            return 0.0
            
        numerator = (r_target - r_current) * 2880
        denominator = r_market * (t_wait + t_exec)
        
        return numerator / denominator

    @staticmethod
    def should_rebalance(eta: float) -> bool:
        """
        Action: Only execute Cancel-Replace if eta > 1.25
        """
        return eta > Config.EFFICIENCY_THRESHOLD
