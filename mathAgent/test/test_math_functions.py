#!/usr/bin/env python3
"""
Simple test for mathematical functions without MCP
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the handler functions directly from the MCP server
from math_mcp_server import (
    handle_calculate_expression,
    handle_solve_equation,
    handle_derivative,
    handle_integral,
    handle_matrix_operations,
    handle_statistics_calculator
)


async def test_math_functions():
    """Test mathematical functions directly"""
    
    print("🧮 Testing Math Functions Directly")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "calculate_expression",
            "handler": handle_calculate_expression,
            "args": {"expression": "2 + 2"}
        },
        {
            "name": "solve_equation", 
            "handler": handle_solve_equation,
            "args": {"equation": "x**2 - 4 = 0"}
        },
        {
            "name": "derivative",
            "handler": handle_derivative,
            "args": {"expression": "x**2 + 3*x + 2"}
        },
        {
            "name": "integral",
            "handler": handle_integral,
            "args": {"expression": "x**2"}
        },
        {
            "name": "matrix_operations",
            "handler": handle_matrix_operations,
            "args": {
                "operation": "determinant",
                "matrix_a": "[[1,2],[3,4]]"
            }
        },
        {
            "name": "statistics_calculator",
            "handler": handle_statistics_calculator,
            "args": {
                "data": "[1,2,3,4,5]",
                "operation": "mean"
            }
        }
    ]
    
    print("\n🧪 Running test cases:")
    print("-" * 30)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['name']}")
        print(f"   Arguments: {test_case['args']}")
        
        try:
            result = await test_case['handler'](test_case['args'])
            
            if result:
                for content in result:
                    if hasattr(content, 'text'):
                        print(f"   ✅ Result: {content.text}")
                    else:
                        print(f"   ✅ Result: {content}")
            else:
                print("   ⚠️  No result returned")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 Mathematical functions testing completed!")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_math_functions())
    sys.exit(0 if success else 1) 