#!/usr/bin/env python3
"""Test MCP server using the official MCP client library"""

import asyncio
import sys

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def test_server(python_cmd, server_script):
    """Test MCP server using client library"""
    print(f"Testing MCP server: {python_cmd} {server_script}")

    # Create server parameters
    server_params = StdioServerParameters(
        command=python_cmd,
        args=[server_script]
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize
            print("Initializing...")
            await session.initialize()

            # List tools
            print("Listing tools...")
            tools_result = await session.list_tools()

            print(f"✅ Found {len(tools_result.tools)} tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Test search
            print("\nTesting search...")
            result = await session.call_tool(
                "search_code",
                arguments={"query": "test", "limit": 5}
            )

            print(f"✅ Search result: {result.content[0].text[:100]}...")

            return True

async def main():
    if len(sys.argv) < 2:
        print("Usage: test_mcp_client.py <server_script>")
        sys.exit(1)

    server_script = sys.argv[1]
    python_cmd = sys.argv[2] if len(sys.argv) > 2 else sys.executable

    try:
        success = await test_server(python_cmd, server_script)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
