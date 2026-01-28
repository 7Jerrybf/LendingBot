
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bitfinex API
    API_KEY = os.getenv("BITFINEX_API_KEY")
    API_SECRET = os.getenv("BITFINEX_API_SECRET")
    
    # Symbols
    SYMBOL = "fUSD"  # Funding USD
    
    # Notification
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    
    # Strategy Parameters
    MIN_ORDER_SIZE = 150.0  # USD
    
    # Rate Limiting
    RATE_LIMIT_TOKENS_PER_MIN = 30
    
    # Safety
    MAX_WS_LATENCY_MS = 500
    WS_TIMEOUT_SECONDS = 30
    
    # Signal Thresholds
    PERP_FUNDING_RATE_THRESHOLD = 0.0005  # 0.05%
    TAKER_VOL_Z_SCORE_THRESHOLD = 2.0
    EFFICIENCY_THRESHOLD = 1.25

    # Strategy Weights
    LAYER_WEIGHTS = {
        "BASE": 0.40,
        "ALPHA": 0.30,
        "SPIKE": 0.30
    }
