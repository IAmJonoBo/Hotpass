"""Hotpass MCP (Model Context Protocol) server implementation.

This module implements an MCP stdio server that exposes Hotpass operations
as tools that can be called by AI assistants like GitHub Copilot and Codex.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Represents an MCP tool definition."""

    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class MCPRequest:
    """Represents an MCP request."""

    method: str
    params: dict[str, Any]
    id: int | str | None = None


@dataclass
class MCPResponse:
    """Represents an MCP response."""

    result: Any = None
    error: dict[str, Any] | None = None
    id: int | str | None = None


class HotpassMCPServer:
    """MCP stdio server for Hotpass operations."""

    def __init__(self) -> None:
        """Initialize the MCP server."""
        self.tools = self._register_tools()
        logger.info(f"Initialized Hotpass MCP server with {len(self.tools)} tools")

    def _register_tools(self) -> list[MCPTool]:
        """Register all available MCP tools."""
        return [
            MCPTool(
                name="hotpass.refine",
                description="Run the Hotpass refinement pipeline to clean and normalize data",
                input_schema={
                    "type": "object",
                    "properties": {
                        "input_path": {
                            "type": "string",
                            "description": "Path to input directory or file containing data to refine",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Path where the refined output should be written",
                        },
                        "profile": {
                            "type": "string",
                            "description": "Industry profile to use (e.g., 'aviation', 'generic')",
                            "default": "generic",
                        },
                        "archive": {
                            "type": "boolean",
                            "description": "Whether to create an archive of the refined output",
                            "default": False,
                        },
                    },
                    "required": ["input_path", "output_path"],
                },
            ),
            MCPTool(
                name="hotpass.enrich",
                description="Enrich refined data with additional information from deterministic and optional network sources",
                input_schema={
                    "type": "object",
                    "properties": {
                        "input_path": {
                            "type": "string",
                            "description": "Path to the refined input file",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Path where the enriched output should be written",
                        },
                        "profile": {
                            "type": "string",
                            "description": "Industry profile to use",
                            "default": "generic",
                        },
                        "allow_network": {
                            "type": "boolean",
                            "description": "Whether to allow network-based enrichment (defaults to env vars)",
                            "default": False,
                        },
                    },
                    "required": ["input_path", "output_path"],
                },
            ),
            MCPTool(
                name="hotpass.qa",
                description="Run quality assurance checks and validation",
                input_schema={
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "enum": ["all", "contracts", "docs", "profiles", "ta", "fitness"],
                            "description": "Which QA checks to run",
                            "default": "all",
                        }
                    },
                },
            ),
            MCPTool(
                name="hotpass.explain_provenance",
                description="Explain data provenance for a specific row or dataset",
                input_schema={
                    "type": "object",
                    "properties": {
                        "row_id": {
                            "type": "string",
                            "description": "ID of the row to explain provenance for",
                        },
                        "dataset_path": {
                            "type": "string",
                            "description": "Path to the dataset file",
                        },
                    },
                    "required": ["row_id", "dataset_path"],
                },
            ),
            MCPTool(
                name="hotpass.crawl",
                description="Execute research crawler (requires network permission)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query_or_url": {
                            "type": "string",
                            "description": "Query string or URL to crawl",
                        },
                        "profile": {
                            "type": "string",
                            "description": "Industry profile to use",
                            "default": "generic",
                        },
                        "backend": {
                            "type": "string",
                            "enum": ["deterministic", "research"],
                            "description": "Backend to use for crawling",
                            "default": "deterministic",
                        },
                    },
                    "required": ["query_or_url"],
                },
            ),
            MCPTool(
                name="hotpass.ta.check",
                description="Run Technical Acceptance checks (all quality gates)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "gate": {
                            "type": "integer",
                            "description": "Specific gate to run (1-5), or omit to run all",
                            "enum": [1, 2, 3, 4, 5],
                        }
                    },
                },
            ),
        ]

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an incoming MCP request."""
        try:
            if request.method == "tools/list":
                return MCPResponse(
                    result={
                        "tools": [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "inputSchema": tool.input_schema,
                            }
                            for tool in self.tools
                        ]
                    },
                    id=request.id,
                )

            elif request.method == "tools/call":
                tool_name = request.params.get("name")
                tool_args = request.params.get("arguments", {})

                # Ensure tool_name is a string
                if not isinstance(tool_name, str):
                    return MCPResponse(
                        error={
                            "code": -32602,
                            "message": "Invalid params: tool name must be a string",
                        },
                        id=request.id,
                    )

                result = await self._execute_tool(tool_name, tool_args)
                return MCPResponse(result=result, id=request.id)

            else:
                return MCPResponse(
                    error={"code": -32601, "message": f"Method not found: {request.method}"},
                    id=request.id,
                )

        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return MCPResponse(
                error={"code": -32603, "message": f"Internal error: {str(e)}"}, id=request.id
            )

    async def _execute_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a Hotpass tool."""
        logger.info(f"Executing tool: {tool_name} with args: {args}")

        if tool_name == "hotpass.refine":
            return await self._run_refine(args)
        elif tool_name == "hotpass.enrich":
            return await self._run_enrich(args)
        elif tool_name == "hotpass.qa":
            return await self._run_qa(args)
        elif tool_name == "hotpass.explain_provenance":
            return await self._explain_provenance(args)
        elif tool_name == "hotpass.crawl":
            return await self._run_crawl(args)
        elif tool_name == "hotpass.ta.check":
            return await self._run_ta_check(args)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _run_refine(self, args: dict[str, Any]) -> dict[str, Any]:
        """Run the refine command."""
        cmd = [
            "uv",
            "run",
            "hotpass",
            "refine",
            "--input-dir",
            args["input_path"],
            "--output-path",
            args["output_path"],
        ]

        if "profile" in args:
            cmd.extend(["--profile", args["profile"]])

        if args.get("archive", False):
            cmd.append("--archive")

        result = await self._run_command(cmd)
        return {
            "success": result["returncode"] == 0,
            "output": result["stdout"],
            "error": result["stderr"] if result["returncode"] != 0 else None,
            "output_path": args["output_path"],
        }

    async def _run_enrich(self, args: dict[str, Any]) -> dict[str, Any]:
        """Run the enrich command."""
        cmd = [
            "uv",
            "run",
            "hotpass",
            "enrich",
            "--input",
            args["input_path"],
            "--output",
            args["output_path"],
        ]

        if "profile" in args:
            cmd.extend(["--profile", args["profile"]])

        if "allow_network" in args:
            cmd.append(f"--allow-network={str(args['allow_network']).lower()}")

        result = await self._run_command(cmd)
        return {
            "success": result["returncode"] == 0,
            "output": result["stdout"],
            "error": result["stderr"] if result["returncode"] != 0 else None,
            "output_path": args["output_path"],
        }

    async def _run_qa(self, args: dict[str, Any]) -> dict[str, Any]:
        """Run the qa command."""
        target = args.get("target", "all")
        cmd = ["uv", "run", "hotpass", "qa", target]

        result = await self._run_command(cmd)
        return {
            "success": result["returncode"] == 0,
            "output": result["stdout"],
            "error": result["stderr"] if result["returncode"] != 0 else None,
        }

    async def _explain_provenance(self, args: dict[str, Any]) -> dict[str, Any]:
        """Explain provenance for a row."""
        try:
            from pathlib import Path

            import pandas as pd

            dataset_path = Path(args["dataset_path"])
            if not dataset_path.exists():
                return {
                    "success": False,
                    "error": f"Dataset not found: {dataset_path}",
                }

            # Load the dataset
            df = pd.read_excel(dataset_path)

            # Find the row by ID
            row_id = args["row_id"]
            try:
                row_index = int(row_id)
            except ValueError:
                # Try to find by a column value
                if "id" in df.columns:
                    rows = df[df["id"] == row_id]
                    if rows.empty:
                        return {"success": False, "error": f"Row ID {row_id} not found"}
                    row_index = rows.index[0]
                else:
                    return {"success": False, "error": "Invalid row ID format"}

            if row_index >= len(df):
                return {"success": False, "error": f"Row index {row_index} out of range"}

            row = df.iloc[row_index]

            # Extract provenance columns if they exist
            provenance_info = {}
            provenance_columns = [
                "provenance_source",
                "provenance_timestamp",
                "provenance_confidence",
                "provenance_strategy",
                "provenance_network_status",
            ]

            for col in provenance_columns:
                if col in df.columns:
                    provenance_info[col] = str(row.get(col, "N/A"))

            if not provenance_info:
                return {
                    "success": True,
                    "row_id": row_id,
                    "message": "No provenance information found in dataset",
                }

            return {
                "success": True,
                "row_id": row_id,
                "row_index": row_index,
                "provenance": provenance_info,
                "organization_name": str(row.get("organization_name", "N/A")),
            }

        except Exception as e:
            logger.error(f"Error explaining provenance: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to explain provenance: {str(e)}",
            }

    async def _run_crawl(self, args: dict[str, Any]) -> dict[str, Any]:
        """Run crawler (guarded operation)."""
        # This is a guarded operation - placeholder for Sprint 2
        return {
            "success": False,
            "message": "Crawler not yet fully implemented (coming in Sprint 2)",
            "query_or_url": args.get("query_or_url"),
        }

    async def _run_ta_check(self, args: dict[str, Any]) -> dict[str, Any]:
        """Run Technical Acceptance checks (all quality gates)."""
        gate = args.get("gate")
        cmd = ["python", "scripts/quality/run_all_gates.py", "--json"]

        if gate:
            cmd.extend(["--gate", str(gate)])

        result = await self._run_command(cmd)

        if result["returncode"] == 0:
            # Parse JSON output
            try:
                import json

                output_data = json.loads(result["stdout"])
                return {
                    "success": True,
                    "summary": output_data.get("summary", {}),
                    "gates": output_data.get("gates", []),
                }
            except json.JSONDecodeError:
                return {
                    "success": result["returncode"] == 0,
                    "output": result["stdout"],
                }
        else:
            return {
                "success": False,
                "error": result["stderr"],
                "output": result["stdout"],
            }

    async def _run_command(self, cmd: list[str]) -> dict[str, Any]:
        """Run a command asynchronously."""
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        return {
            "returncode": process.returncode,
            "stdout": stdout.decode("utf-8"),
            "stderr": stderr.decode("utf-8"),
        }

    async def run(self) -> None:
        """Run the MCP server (stdio mode)."""
        logger.info("Starting Hotpass MCP server in stdio mode")

        try:
            while True:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)

                if not line:
                    break

                try:
                    # Parse JSON-RPC request
                    request_data = json.loads(line.strip())
                    request = MCPRequest(
                        method=request_data.get("method"),
                        params=request_data.get("params", {}),
                        id=request_data.get("id"),
                    )

                    # Handle request
                    response = await self.handle_request(request)

                    # Build JSON-RPC response
                    response_data: dict[str, Any] = {"jsonrpc": "2.0"}
                    if response.error:
                        response_data["error"] = response.error
                    else:
                        response_data["result"] = response.result
                    if response.id is not None:
                        response_id: int | str = response.id
                        response_data["id"] = response_id

                    # Write response to stdout
                    print(json.dumps(response_data), flush=True)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": "Parse error"},
                        "id": None,
                    }
                    print(json.dumps(error_response), flush=True)

        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)


async def main() -> None:
    """Main entry point for the MCP server."""
    server = HotpassMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
