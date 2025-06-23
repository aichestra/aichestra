#!/usr/bin/env python3
"""
Test script for Math MCP server integration
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession


async def test_math_mcp_server():
    """Test the Math MCP server functionality"""
    
    print("🧮 Testing Math MCP Server Integration")
    print("=" * 50)
    
    # Path to the MCP server
    math_mcp_server_path = current_dir / "math_mcp_server.py"
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=[str(math_mcp_server_path)]
    )
    
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            
            # Initialize the session
            await session.initialize()
            
            print("✅ Successfully connected to Math MCP server")
            
            # List available tools
            tools_result = await session.list_tools()
            print(f"📋 Available tools: {len(tools_result.tools)}")
            
            for tool in tools_result.tools:
                print(f"  • {tool.name}: {tool.description}")
            
            # Test cases
            test_cases = [
                {
                    "name": "calculate_expression",
                    "arguments": {"expression": "2 + 2"}
                },
                {
                    "name": "solve_equation", 
                    "arguments": {"equation": "x**2 - 4 = 0"}
                },
                {
                    "name": "derivative",
                    "arguments": {"expression": "x**2 + 3*x + 2"}
                },
                {
                    "name": "matrix_operations",
                    "arguments": {
                        "operation": "determinant",
                        "matrix_a": "[[1,2],[3,4]]"
                    }
                },
                {
                    "name": "statistics_calculator",
                    "arguments": {
                        "data": "[1,2,3,4,5]",
                        "operation": "mean"
                    }
                }
            ]
            
            print("\n🧪 Running test cases:")
            print("-" * 30)
            
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n{i}. Testing {test_case['name']}")
                print(f"   Arguments: {test_case['arguments']}")
                
                try:
                    result = await session.call_tool(
                        test_case['name'],
                        test_case['arguments']
                    )
                    
                    if result and result.content:
                        for content in result.content:
                            if hasattr(content, 'text'):
                                print(f"   ✅ Result: {content.text}")
                            else:
                                print(f"   ✅ Result: {content}")
                    else:
                        print("   ⚠️  No result returned")
                        
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")
            
            print("\n" + "=" * 50)
            print("🎯 Math MCP server testing completed!")
            
    except Exception as e:
        print(f"❌ Failed to connect to Math MCP server: {str(e)}")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_math_mcp_server())
    sys.exit(0 if success else 1) 