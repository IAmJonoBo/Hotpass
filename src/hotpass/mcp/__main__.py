"""Entry point for running Hotpass MCP server as a module.

Usage:
    python -m hotpass.mcp.server
    OR
    uv run python -m hotpass.mcp.server
"""

from .server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
