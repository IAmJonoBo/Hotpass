"""Hotpass MCP (Model Context Protocol) server.

This module provides an MCP stdio server that exposes Hotpass operations
as tools for AI assistants.
"""

from .server import HotpassMCPServer, MCPTool, MCPRequest, MCPResponse

__all__ = [
    "HotpassMCPServer",
    "MCPTool",
    "MCPRequest",
    "MCPResponse",
]
