#!/usr/bin/env python3
"""
Test MCP-based Math Agent functionality without LLM calls
"""
import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_math_operations():
    """Test various mathematical operations using MCP tools"""
    try:
        # Get the path to the math MCP server
        current_dir = Path(__file__).parent
        math_server_path = current_dir / "math_mcp_server.py"
        
        print(f"🔧 Testing MCP Math Operations")
        print(f"📁 Server path: {math_server_path}")
        
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", str(math_server_path)],
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
                    
                    # Test cases
                    test_cases = [
                        {
                            "name": "Arithmetic Expression",
                            "tool": "calculate_expression",
                            "args": {"expression": "(3 + 5) * 12"},
                            "expected": "96"
                        },
                        {
                            "name": "Equation Solving",
                            "tool": "solve_equation", 
                            "args": {"equation": "2*x + 5 - 15", "variable": "x"},
                            "expected": "5"
                        },
                        {
                            "name": "Derivative Calculation",
                            "tool": "derivative",
                            "args": {"expression": "x**2 + 3*x + 2", "variable": "x"},
                            "expected": "2*x + 3"
                        },
                        {
                            "name": "Integral Calculation", 
                            "tool": "integral",
                            "args": {"expression": "2*x + 3", "variable": "x"},
                            "expected": "x**2 + 3*x"
                        },
                        {
                            "name": "Statistics - Mean",
                            "tool": "statistics_calculator",
                            "args": {"data": "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]", "operation": "mean"},
                            "expected": "5.5"
                        },
                        {
                            "name": "Matrix Multiplication",
                            "tool": "matrix_operations",
                            "args": {"operation": "multiply", "matrix_a": "[[1, 2], [3, 4]]", "matrix_b": "[[5, 6], [7, 8]]"},
                            "expected": "matrix result"
                        }
                    ]
                    
                    print("\n🧮 Running test cases...")
                    for i, test_case in enumerate(test_cases, 1):
                        print(f"\n{i}. Testing {test_case['name']}:")
                        print(f"   Tool: {test_case['tool']}")
                        print(f"   Args: {test_case['args']}")
                        
                        try:
                            result = await session.call_tool(
                                test_case['tool'],
                                test_case['args']
                            )
                            
                            if result and hasattr(result, 'content'):
                                content = result.content
                                if isinstance(content, list) and len(content) > 0:
                                    first_content = content[0]
                                    # Check if it's a TextContent type
                                    if hasattr(first_content, 'type') and first_content.type == 'text':
                                        print(f"   ✅ Result: {first_content.text}")  # type: ignore
                                    else:
                                        print(f"   ✅ Result: {str(first_content)}")
                                else:
                                    print(f"   ✅ Result: {content}")
                            else:
                                print(f"   ✅ Raw result: {result}")
                                
                        except Exception as e:
                            print(f"   ❌ Error: {str(e)}")
                    
                    print("\n🎉 MCP Math Agent testing completed!")
                    
                else:
                    print("❌ No tools found")
                
    except Exception as e:
        print(f"❌ Error testing MCP math operations: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_math_operations()) 