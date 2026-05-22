#!/usr/bin/env python3
"""
Q-SpecTrum MCP Server — thin wrapper around brain_core McpRouter.
Usage: python qspectrum_mcp_server.py [--provider mock]
Speaks JSON-RPC 2.0 over stdio (MCP protocol).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

import argparse

from brain_core.mcp_router import McpRouter
from qspectrum_engine import MockLLMProvider, QSpectrumEngine

parser = argparse.ArgumentParser()
parser.add_argument("--provider", default="mock")
args = parser.parse_args()

provider_name = args.provider
if provider_name == "mock":
    llm = MockLLMProvider()
else:
    from qspectrum_engine import create_llm_provider
    llm, _ = create_llm_provider(provider_name)

engine = QSpectrumEngine(llm_provider=llm)
router = McpRouter(engine, provider_name)

request_id = 0

def send_msg(msg):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def handle_request(msg):
    global request_id
    method = msg.get("method", "")
    msg_id = msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        request_id = msg_id
        send_msg({"jsonrpc": "2.0", "id": msg_id, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {"name": "qspectrum-mcp", "version": "1.0.0"}
        }})
        return

    if method in ("notifications/initialized", "notifications/cancelled"):
        return

    if method == "tools/list":
        send_msg({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": router.list_tools()}})
        return

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        result = router.call_tool(tool_name, arguments)
        # call_tool returns {"error": "..."} on failure
        if result.get("error"):
            send_msg({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": result["error"]}})
            return
        send_msg({"jsonrpc": "2.0", "id": msg_id, "result": {
            "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
        }})
        return

    if method == "resources/list":
        send_msg({"jsonrpc": "2.0", "id": msg_id, "result": {"resources": [
            {"uri": "qspectrum://status", "name": "Engine Status", "mimeType": "application/json"},
            {"uri": "qspectrum://roles", "name": "All Roles", "mimeType": "application/json"},
        ]}})
        return

    if method == "resources/read":
        uri = params.get("uri", "")
        if uri == "qspectrum://status":
            data = router.call_tool("get_status")
        elif uri == "qspectrum://roles":
            data = router.call_tool("get_roles")
        else:
            send_msg({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32602, "message": f"Resource not found: {uri}"}})
            return
        send_msg({"jsonrpc": "2.0", "id": msg_id, "result": {
            "contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(data, ensure_ascii=False, indent=2)}]
        }})
        return

    send_msg({"jsonrpc": "2.0", "id": msg_id if msg_id else None,
              "error": {"code": -32601, "message": f"Method not found: {method}"}})

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            handle_request(msg)
        except json.JSONDecodeError:
            send_msg({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}})
        except Exception as e:
            send_msg({"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Internal error: {e}"}})

if __name__ == "__main__":
    main()
