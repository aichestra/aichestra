#!/usr/bin/env python3
"""
Test MCP connection without requiring Google API key
"""
import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_connection():
    """Test MCP server connection and tool loading"""
    try:
        # Get the path to the math MCP server
        current_dir = Path(__file__).parent
        math_server_path = current_dir / "math_mcp_server.py"
        
        print(f"🔧 Testing MCP server at: {math_server_path}")
        
        server_params = StdioServerParameters(
            command="python3",
            args=[str(math_server_path)],
        )
        
        print("🚀 Starting MCP client connection...")
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("🔗 Initializing session...")
                await session.initialize()
                
                print("📋 Listing available tools...")
                tools_result = await session.list_tools()
                
                if tools_result and hasattr(tools_result, 'tools'):
                    tools = tools_result.tools
                    print(f"✅ Found {len(tools)} MCP tools:")
                    for tool in tools:
                        print(f"  - {tool.name}: {tool.description}")
                    
                    # Test a simple calculation
                    print("\n🧮 Testing calculate_expression tool...")
                    call_result = await session.call_tool(
                        "calculate_expression",
                        {"expression": "2 + 3 * 4"}
                    )
                    
                    if call_result and hasattr(call_result, 'content'):
                        print(f"📊 Result: {call_result.content}")
                    else:
                        print(f"📊 Raw result: {call_result}")
                        
                else:
                    print("❌ No tools found")
                
    except Exception as e:
        print(f"❌ Error testing MCP connection: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_connection()) 