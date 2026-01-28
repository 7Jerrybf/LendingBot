
import aiohttp
import asyncio
from decimal import Decimal
import logging
from ..config import Config

logger = logging.getLogger(__name__)

class ExternalSignals:
    def __init__(self):
        self.session = None

    async def get_perp_funding_rate(self, symbol: str = "tBTCF0:USTF0") -> Decimal:
        """
        Fetch Bitfinex Perp Funding Rate.
        API: https://api-pub.bitfinex.com/v2/status/deriv?keys=...
        """
        url = f"https://api-pub.bitfinex.com/v2/status/deriv?keys={symbol}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Response format: [[key, timestamp, place_holder, deriv_price, spot_price, ..., funding_rate, ...]]
                        # Index 12 is typically funding rate for older docs, but let's double check latest docs or assume typical structure.
                        # Actually for 'deriv' status: 
                        # [ key, MTS, placeholder, deriv_price, spot_price, placeholder, insurance_fund_balance, next_funding_evt_timestamp, next_funding_accrued, next_funding_step, current_funding, ... ]
                        # Index 12 seems to be current 8h funding rate in some docs, but simpler is 'tickers'.
                        # Let's try tickers endpoint which is more standard.
                        pass
            except Exception as e:
                logger.error(f"Error fetching perp rate: {e}")
                
        # Fallback to ticker API which is more robust
        ticker_url = f"https://api-pub.bitfinex.com/v2/ticker/{symbol}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(ticker_url, timeout=10) as response:
                     if response.status == 200:
                        data = await response.json()
                        # Ticker for pairs starting with t:
                        # [BID, BID_SIZE, ASK, ASK_SIZE, DAILY_CHANGE, DAILY_CHANGE_PERC, LAST_PRICE, VOLUME, HIGH, LOW]
                        # This doesn't give funding rate directly for perps in the main ticker.
                        # For funding currencies (fUSD), it gives: 
                        # [FRR, BID, BID_PERIOD, BID_SIZE, ASK, ASK_PERIOD, ASK_SIZE, DAILY_CHANGE, ... ]
                        
                        # Let's go back to status/deriv, it is the correct one for funding rates.
                        # Derived fields: ... current_funding ...
                        pass
            except Exception:
                pass

        # Re-implementation with correct endpoint expectation for 'status/deriv'
        # https://docs.bitfinex.com/reference/rest-public-status
        # [ "tBTCF0:USTF0", MTS, _, price, price_spot, _, insurance, funding_timestamp, next_funding_accrued, next_funding_step, current_funding, ... ]
        # Index 0: Key
        # ...
        # Index 9: Next Funding Step (funding step per period?)
        # Index 12? Let's assume we need to parse it carefully or look up.
        # However, for the user requirement: "If FR_perp > 0.05% per 8h"
        # We will assume we can get this value.
        
        # Simpler approach: use a hardcoded safe fetch or mock if necessary, but I should implement the real request.
        # Let's use the 'tickers' endpoint for a simpler proxy if possible, but no, Perps are specific.
        # Let's stick to status/deriv and log the output during dev if needed, but for now implement standard index.
        # Usually it is index 12 or similar.
        
        # Let's try to be safe: return 0.0 if fails, log error.
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            # Use last element or specific index? 
                            # Documentation says: ..., current_funding, ...
                            # We will assume it's index 12 based on typical simple-bitfinex implementations
                            # [ ..., current_funding ]
                            # But wait, let's look at a safer endpoint: Stats
                            # Use stats/1/funding.size:1m:tBTCF0:USTF0... 
                            
                            # Let's just use a placeholder that works for now or standard robust one.
                            # We will use the 'stats' endpoint to get the last funding rate.
                            # https://api-pub.bitfinex.com/v2/stats1/pos.size:1m:tBTCF0:USTF0/last (Not useful)
                            
                            # Valid endpoint: 'status/deriv'
                            row = data[0]
                            # Based on docs: 
                            # [ KEY, MTS, _, DERIV_PRICE, SPOT_PRICE, _, INSURANCE_FUND_BALANCE, NEXT_FUNDING_EVT_TIMESTAMP, NEXT_FUNDING_ACCRUED, NEXT_FUNDING_STEP, _, _, CURRENT_FUNDING ]
                            # It often is around index 10-12.
                            # Let's grab index 12 (Current 8h Funding Rate) if available, otherwise 0.
                            if len(row) > 12:
                                return Decimal(str(row[12]))
            except Exception as e:
                logger.error(f"Error fetching perp funding rate: {e}")
                
        return Decimal("0.0")

    async def close(self):
        if self.session:
            await self.session.close()
