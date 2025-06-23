#!/usr/bin/env python3
"""
ArgoCD Agent Async Test Client

This script demonstrates how to use the ArgoCD agent in an async context.
It provides a simple command-line interface to interact with the agent.

Usage:
    python -m app.async_test_client
    uv run -m app.async_test_client
"""

import asyncio
import logging
import os
import sys
from uuid import uuid4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_argocd_agent_async():
    """Test the ArgoCD agent with async methods."""
    from app.agent import ArgoCDAgent
    
    logger.info("Starting ArgoCD Agent Async Test Client")
    logger.info("======================================")
    
    # Set environment variables
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "AIzaSyB36krMkJV9voQS4fOpW8D6_-WhVV817mA")
    os.environ["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
    os.environ["ARGOCD_BASE_URL"] = os.getenv("ARGOCD_BASE_URL", "https://9.30.147.51:8080/")
    os.environ["ARGOCD_API_TOKEN"] = os.getenv("ARGOCD_API_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcmdvY2QiLCJzdWIiOiJhZG1pbjphcGlLZXkiLCJuYmYiOjE3NDk2NzUxODAsImlhdCI6MTc0OTY3NTE4MCwianRpIjoiMjFkMDIyNWYtZDU1ZS00NDllLWFkNDAtMDA1NTY5N2M4NGQ3In0.s-9YzxmexF8k_JgDVFI3raiIqQ9Bo6OrTDB3okWque8")
    
    try:
        # Initialize the agent
        agent = ArgoCDAgent()
        
        # Interactive mode
        logger.info("ArgoCD Agent Interactive Mode")
        logger.info("Type 'exit' or 'quit' to end the session")
        
        context_id = f"interactive-{uuid4().hex}"
        
        while True:
            # Get user input
            user_input = input("\nYour query: ")
            
            # Check for exit command
            if user_input.lower() in ['exit', 'quit']:
                logger.info("Exiting interactive mode")
                break
            
            # Process the query
            logger.info("Processing query...")
            try:
                response = await agent.ainvoke(user_input, context_id)
                print("\nAgent response:")
                print(f"Status: {'Complete' if response['is_task_complete'] else 'Incomplete'}")
                print(f"Content: {response['content']}")
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                print(f"\nError: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in async test client: {e}", exc_info=True)
        return False

async def main():
    """Main function to run the async test client."""
    await test_argocd_agent_async()

if __name__ == "__main__":
    asyncio.run(main())