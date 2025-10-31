# Agent orchestration configuration

The files in this directory define prototype [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) settings for Hotpass agents that invoke Prefect deployments. The goal is to gate agentic automation behind explicit tooling allowlists and audit trails.

## Files

- `mcp_server.yaml` — describes the Prefect-side MCP server, including the tools agents may request and the approval gates that must be satisfied before a flow runs.
- `mcp_client.yaml` — sample client capabilities and broker wiring for a Hotpass operator agent.

## Usage

1. Update the allowlisted repositories, drives, or Prefect deployments to match your environment.
2. Register the server definition with the MCP runtime that backs your Prefect work pool. The example assumes the Prefect broker is reachable via `prefect://local`.
3. Distribute the client profile to the agent runtime. Agents surface the declared role when initiating requests so approvals can be enforced.
4. Point `HOTPASS_AGENT_POLICY_PATH` to `mcp_server.yaml` before launching the Prefect worker so the orchestration layer can load the allowlist at runtime.

The policies complement the Prefect tasks added in `hotpass.orchestration` that validate and log agent-triggered runs. Update both the policy files and Prefect deployment metadata when onboarding new agent roles.
