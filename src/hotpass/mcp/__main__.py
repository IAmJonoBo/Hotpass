"""Entry point for running Hotpass MCP server as a module.

Usage:
    python -m hotpass.mcp.server
    OR
    uv run python -m hotpass.mcp.server
"""

import asyncio

from .server import main

if __name__ == "__main__":
    asyncio.run(main())
