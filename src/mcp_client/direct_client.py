#!/usr/bin/env python3
"""
Direct JSON-RPC MCP Client
Custom implementation to bypass buggy stdio_client from MCP library.
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path


class DirectMCPClient:
    """Direct JSON-RPC MCP client that communicates with FastMCP servers"""

    def __init__(self, script_path: str, server_name: str):
        self.script_path = script_path
        self.server_name = server_name
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.initialized = False

    async def start(self) -> bool:
        """Start the MCP server process and initialize connection"""
        try:
            print(f"    Starting {self.server_name} server process...")

            # Start the FastMCP server subprocess
            self.process = subprocess.Popen(
                [sys.executable, self.script_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,  # Unbuffered for real-time communication
            )

            # Give server a moment to start
            await asyncio.sleep(0.5)

            # Check if process is still running
            if self.process.poll() is not None:
                stderr_output = (
                    self.process.stderr.read()
                    if self.process.stderr
                    else "No error output"
                )
                raise Exception(f"Server process died immediately: {stderr_output}")

            print(f"    Initializing {self.server_name} MCP session...")

            # Send MCP initialization request
            success = await self._initialize_mcp_session()
            if success:
                self.initialized = True
                print(f"    ✓ {self.server_name} MCP client ready")
                return True
            else:
                print(f"    ✗ {self.server_name} MCP initialization failed")
                await self.close()
                return False

        except Exception as e:
            print(f"    Error starting {self.server_name}: {e}")
            await self.close()
            return False

    async def _initialize_mcp_session(self) -> bool:
        """Send MCP initialization request and handle response"""
        try:
            # Prepare MCP initialization request
            init_request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "langgraph-mcp-client", "version": "1.0.0"},
                },
            }

            # Send request
            success = await self._send_request(init_request)
            if not success:
                return False

            # Read and validate response
            response = await self._read_response()
            if not response:
                return False

            # Check if initialization was successful
            if "result" in response and "protocolVersion" in response["result"]:
                print(
                    f"    Server protocol version: {response['result']['protocolVersion']}"
                )

                # Send initialized notification to complete the handshake
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {},
                }

                success = await self._send_request(initialized_notification)
                if success:
                    # Give server a moment to process the notification
                    await asyncio.sleep(0.1)
                    return True
                else:
                    print(f"    Failed to send initialized notification")
                    return False
            else:
                print(f"    Invalid initialization response: {response}")
                return False

        except Exception as e:
            print(f"    MCP initialization error: {e}")
            return False

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the MCP server"""
        if not self.initialized or not self.process:
            return "Error: MCP client not initialized"

        try:
            # Prepare tool call request
            request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }

            # Send request
            success = await self._send_request(request)
            if not success:
                return f"Error: Failed to send tool request for {tool_name}"

            # Read response
            response = await self._read_response()
            if not response:
                return f"Error: No response for tool call {tool_name}"

            # Extract result
            if "result" in response:
                result = response["result"]
                if (
                    "content" in result
                    and isinstance(result["content"], list)
                    and len(result["content"]) > 0
                ):
                    # Extract text from content array
                    content_item = result["content"][0]
                    if "text" in content_item:
                        return content_item["text"]
                    else:
                        return str(content_item)
                else:
                    return str(result)
            elif "error" in response:
                return f"Tool error: {response['error']}"
            else:
                return f"Unexpected response format: {response}"

        except Exception as e:
            return f"Tool call failed: {e}"

    async def list_tools(self) -> List[str]:
        """List available tools on the MCP server"""
        if not self.initialized or not self.process:
            return []

        try:
            # Prepare list tools request
            request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "tools/list",
                "params": {},
            }

            # Send request
            success = await self._send_request(request)
            if not success:
                return []

            # Read response
            response = await self._read_response()
            if not response:
                return []

            # Extract tools list
            if "result" in response and "tools" in response["result"]:
                tools = response["result"]["tools"]
                return [tool["name"] for tool in tools if "name" in tool]
            else:
                return []

        except Exception as e:
            print(f"List tools failed: {e}")
            return []

    async def _send_request(self, request: Dict[str, Any]) -> bool:
        """Send JSON-RPC request to server"""
        try:
            if not self.process or not self.process.stdin:
                return False

            # Convert to JSON and send
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            return True

        except Exception as e:
            print(f"Failed to send request: {e}")
            return False

    async def _read_response(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Read JSON-RPC response from server with timeout"""
        try:
            if not self.process or not self.process.stdout:
                return None

            # Read response with timeout
            future = asyncio.create_task(self._read_line_async())
            try:
                response_line = await asyncio.wait_for(future, timeout=timeout)
            except asyncio.TimeoutError:
                print(f"Timeout waiting for response from {self.server_name}")
                return None

            if not response_line:
                return None

            # Parse JSON response
            try:
                response = json.loads(response_line.strip())
                return response
            except json.JSONDecodeError as e:
                print(f"Invalid JSON response: {response_line[:100]}...")
                return None

        except Exception as e:
            print(f"Failed to read response: {e}")
            return None

    async def _read_line_async(self) -> Optional[str]:
        """Async wrapper for reading a line from stdout"""
        try:
            if not self.process or not self.process.stdout:
                return None

            # Use run_in_executor to make blocking read async
            loop = asyncio.get_event_loop()
            line = await loop.run_in_executor(None, self.process.stdout.readline)
            return line

        except Exception as e:
            print(f"Error reading line: {e}")
            return None

    def _next_request_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id

    async def close(self):
        """Close the MCP client and terminate server process"""
        try:
            if self.process:
                # Try graceful shutdown first
                if self.process.poll() is None:
                    self.process.terminate()

                    # Wait up to 3 seconds for graceful shutdown
                    try:
                        await asyncio.wait_for(
                            asyncio.create_task(asyncio.to_thread(self.process.wait)),
                            timeout=3.0,
                        )
                    except asyncio.TimeoutError:
                        # Force kill if graceful shutdown failed
                        self.process.kill()
                        await asyncio.create_task(asyncio.to_thread(self.process.wait))

                self.process = None
                self.initialized = False
                print(f"    Closed {self.server_name} MCP client")

        except Exception as e:
            print(f"Error closing {self.server_name} client: {e}")
