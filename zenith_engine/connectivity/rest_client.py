
import aiohttp
import time
import hmac
import hashlib
import json
import logging
from .rate_limiter import RateLimiter
from ..config import Config

logger = logging.getLogger(__name__)

class RestClient:
    def __init__(self):
        self.api_key = Config.API_KEY
        self.api_secret = Config.API_SECRET
        self.url = "https://api.bitfinex.com/v2"
        self.rate_limiter = RateLimiter(Config.RATE_LIMIT_TOKENS_PER_MIN)
        
    def _generate_signature(self, path: str, body: str, nonce: str) -> str:
        signature_payload = f"/api/v2{path}{nonce}{body}"
        return hmac.new(
            self.api_secret.encode('utf-8'),
            signature_payload.encode('utf-8'),
            hashlib.sha384
        ).hexdigest()
        
    async def _post(self, path: str, payload: dict):
        await self.rate_limiter.acquire()
        
        nonce = str(int(time.time() * 1000000))
        body = json.dumps(payload)
        signature = self._generate_signature(path, body, nonce)
        
        headers = {
            "bfx-nonce": nonce,
            "bfx-apikey": self.api_key,
            "bfx-signature": signature,
            "content-type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.url}{path}", data=body, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        text = await resp.text()
                        logger.error(f"API Error {resp.status}: {text}")
                        return None
            except Exception as e:
                logger.error(f"Request failed: {e}")
                return None

    async def submit_offer(self, symbol: str, amount: str, rate: str, period: int):
        """
        Submit a funding offer.
        Note: Rate is per day? API usually expects rate per period or year?
        Bitfinex API expects Flash Return Rate (FRR) or specific rate.
        Usually rate is passed as string.
        """
        payload = {
            "type": "LIMIT",
            "symbol": symbol,
            "amount": amount,
            "rate": rate,
            "period": period,
            "flags": 0
        }
        return await self._post("/auth/w/funding/offer/submit", payload)

    async def cancel_offer(self, offer_id: int):
        payload = {"id": offer_id}
        return await self._post("/auth/w/funding/offer/cancel", payload)
    
    async def get_active_offers(self, symbol: str):
        # Implementation to sync state
        # Endpoint: /auth/r/funding/offers/SYMBOL
        # But this is GET, signature is different for GET usually? 
        # Bitfinex v2 auth is mainly for POST but GET also uses auth headers.
        # However, for simplicity and since we use WS for updates, this might be auxiliary.
        # Wait, the v2 auth process is the same for GET.
        # But we need to support GET in `_request` if we want to use it.
        # For now, let's stick to POST for actions.
        pass
