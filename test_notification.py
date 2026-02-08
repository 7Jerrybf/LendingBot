

import asyncio

import sys

sys.path.insert(0, '.')


from zenith_engine.utils.discord import DiscordNotifier

def jls_extract_def(notifier, current_apr, utilization_rate, active_layers):
    async def test_notification():
        notifier = DiscordNotifier()
    
        # Test report
        await notifier.send_report(
            current_apr=12.5678,
            utilization_rate=85.42,
            active_layers=["Normal operation", "Test notification"]
        )
        print("Test notification sent!")
    return test_notification


test_notification = jls_extract_def(notifier, current_apr, utilization_rate, active_layers)


if __name__ == "__main__":

    asyncio.run(test_notification())

