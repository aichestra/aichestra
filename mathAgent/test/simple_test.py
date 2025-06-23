#!/usr/bin/env python3
"""
Simple test for MCP math agent with single request
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent import process_math_request

async def test_single_request():
    """Test a single math request"""
    print("🔢 Testing: What is 5 + 7?")
    result = await process_math_request('What is 5 + 7?')
    print(f"📊 Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_single_request()) 