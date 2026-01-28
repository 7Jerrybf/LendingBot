
import aiohttp
import logging
from ..config import Config

logger = logging.getLogger(__name__)

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = Config.DISCORD_WEBHOOK_URL
        
    async def send_message(self, content: str):
        if not self.webhook_url:
            logger.warning("Discord Webhook URL not set, skipping notification.")
            return

        payload = {"content": content}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.webhook_url, json=payload) as resp:
                    if resp.status != 204 and resp.status != 200:
                         logger.error(f"Failed to send Discord notification: {resp.status}")
            except Exception as e:
                logger.error(f"Discord notification error: {e}")

    async def send_report(self, current_apr: float, utilization_rate: float, active_layers: list):
        # Timestamp / Current APR / Utilization Rate
        # Activity: "Spike Hunter triggered..."
        msg = f"**Zenith Report**\n" \
              f"APR: {current_apr:.4f}%\n" \
              f"Utilization: {utilization_rate:.2f}%\n" \
              f"Activity: {', '.join(active_layers)}"
        
        await self.send_message(msg)
