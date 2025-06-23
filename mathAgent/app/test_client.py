#!/usr/bin/env python3
"""Test client for Math Agent with MCP integration"""

import asyncio
import json
import httpx
from uuid import uuid4


async def test_math_agent():
    """Test the math agent with various mathematical queries using MCP backend"""
    
    base_url = "http://localhost:8003"
    
    test_cases = [
        "Calculate 2 + 2",
        "What is the square root of 16?",
        "Solve the equation x^2 - 4 = 0",
        "Find the derivative of x^2 + 3x + 2",
        "Calculate the integral of x^2",
        "What is the determinant of [[1,2],[3,4]]?",
        "Find the mean of [1,2,3,4,5]",
        "What is sin(pi/4)?",
        "Solve 2x + 5 = 11",
        "Calculate the standard deviation of [10,12,14,16,18]"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🧮 Testing Math Agent (MCP-based)")
        print("=" * 50)
        
        for i, query in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {query}")
            
            # Create A2A JSON-RPC request
            task_id = str(uuid4())
            message_id = str(uuid4())
            context_id = str(uuid4())
            
            payload = {
                "jsonrpc": "2.0",
                "id": str(uuid4()),
                "method": "message/send",
                "params": {
                    "id": task_id,
                    "message": {
                        "role": "user",
                        "messageId": message_id,
                        "contextId": context_id,
                        "parts": [
                            {
                                "type": "text",
                                "text": query
                            }
                        ]
                    },
                    "configuration": {
                        "acceptedOutputModes": ["text"]
                    }
                }
            }
            
            try:
                # Send request
                response = await client.post(
                    base_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                
                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                    continue
                
                # Handle task polling if needed
                if "result" in result and isinstance(result["result"], dict):
                    task_result = result["result"]
                    
                    if "id" in task_result and "status" in task_result:
                        # Poll for completion
                        task_id = task_result["id"]
                        
                        for attempt in range(10):
                            await asyncio.sleep(0.5)
                            
                            get_payload = {
                                "jsonrpc": "2.0",
                                "id": str(uuid4()),
                                "method": "tasks/get",
                                "params": {
                                    "id": task_id
                                }
                            }
                            
                            get_response = await client.post(
                                base_url,
                                json=get_payload,
                                headers={"Content-Type": "application/json"}
                            )
                            get_response.raise_for_status()
                            
                            get_result = get_response.json()
                            
                            if "result" in get_result and get_result["result"]:
                                task_data = get_result["result"]
                                task_state = task_data.get("status", {}).get("state")
                                
                                if task_state == "completed":
                                    # Extract response
                                    status_message = task_data.get("status", {}).get("message", {})
                                    if status_message and "parts" in status_message:
                                        for part in status_message["parts"]:
                                            if part.get("type") == "text":
                                                print(f"✅ Response: {part.get('text', 'No text')}")
                                                break
                                    break
                                elif task_state == "failed":
                                    print("❌ Task failed")
                                    break
                                elif task_state == "input-required":
                                    # Handle input-required state
                                    status_message = task_data.get("status", {}).get("message", {})
                                    if status_message and "parts" in status_message:
                                        for part in status_message["parts"]:
                                            if part.get("type") == "text":
                                                print(f"✅ Response: {part.get('text', 'No text')}")
                                                break
                                    break
                        else:
                            print("⏰ Task timeout")
                    
                    elif "parts" in task_result:
                        # Direct message response
                        for part in task_result["parts"]:
                            if part.get("type") == "text":
                                print(f"✅ Response: {part.get('text', 'No text')}")
                                break
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        print("\n" + "=" * 50)
        print("🎯 Math Agent testing completed!")


if __name__ == "__main__":
    asyncio.run(test_math_agent()) 