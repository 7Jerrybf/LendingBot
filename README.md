# Zenith Liquidity Engine

A high-performance, async-first Bitfinex Lending Bot designed to optimize capital utilization and yield through micro-structural analysis and dynamic re-balancing.

## Features

- **Micro-structural Analysis**: Tracks Limit Order Book (LOB) to determine optimal lending rates.
- **External Signal Integration**: Utilizes Perp Funding Rates and other external signals for decision making.
- **Dynamic Re-balancing**: Automatically re-allocates funds based on efficiency thresholds.
- **Laddered Distribution**: Uses a Truncated Gaussian Distribution for capital allocation across different rates.
- **Execution Guardrails**: Includes rate limiting, safety switches, and rigorous error handling.
- **Notification System**: Integrated Discord notifications for critical updates and bot status.
- **Async Architecture**: Built with Python's `asyncio` for non-blocking operations.

## Architecture

The project is structured into several key modules:

- `zenith_engine/`: Core engine code.
  - `connectivity/`: Handles WebSocket and REST API connections (Bitfinex).
  - `signals/`: Processes market data and external signals (e.g., funding rates, spikes).
  - `strategy/`: Implements the lending strategy (distribution, rebalancing).
  - `utils/`: Utility functions and helpers (Discord, logging).
  - `state.py`: Manages the global state of the bot.
  - `config.py`: Configuration management.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/7Jerrybf/LendingBot.git
    cd LendingBot
    ```

2.  **Environment Variables:**
    Create a `.env` file in the root directory and add your API keys and configuration:
    ```env
    BFX_API_KEY=your_api_key
    BFX_API_SECRET=your_api_secret
    DISCORD_WEBHOOK_URL=your_webhook_url
    ```

3.  **Run with Docker:**
    ```bash
    docker-compose up --build -d
    ```

    Or run locally (requires Python 3.11+):
    ```bash
    pip install -r requirements.txt
    python -m zenith_engine.main
    ```

## Logic Overview

The bot operates on an event loop that:
1.  Ingests real-time order book data via WebSockets.
2.  Calculates funding stats and analyzes taker volume.
3.  Applies a laddered distribution strategy to place offers.
4.  Monitors active loans and offers, re-balancing when efficiency drops below a set threshold.

## License

[MIT License](LICENSE)
