#!/usr/bin/env python3
"""
Comprehensive test for MCP math agent with LLM integration
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent import process_math_request

async def test_comprehensive_math():
    """Test various mathematical operations with LLM integration"""
    test_cases = [
        "What is (3 + 5) × 12?",
        "Solve the equation 2x + 5 = 15",
        "Calculate the derivative of x^2 + 3x + 2",
        "Find the integral of 2x + 3",
        "What is the mean of the numbers 1, 2, 3, 4, 5?",
        "Multiply the matrices [[1,2],[3,4]] and [[5,6],[7,8]]"
    ]
    
    print("🧮 Testing MCP Math Agent with LLM Integration")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. 🔢 Question: {test_case}")
        try:
            result = await process_math_request(test_case)
            print(f"   📊 Answer: {result}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    print("\n🎉 Comprehensive testing completed!")

if __name__ == "__main__":
    asyncio.run(test_comprehensive_math()) 