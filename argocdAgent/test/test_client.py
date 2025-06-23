import asyncio
import logging
import os
import sys
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_argocd_agent_direct():
    """Test the ArgoCD agent directly with simple queries."""
    logger.info("\n=== Testing ArgoCD Agent with Real ArgoCD Server ===")
    
    # Set environment variables
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "AIzaSyB36krMkJV9voQS4fOpW8D6_-WhVV817mA")
    os.environ["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
    os.environ["ARGOCD_BASE_URL"] = os.getenv("ARGOCD_BASE_URL", "https://9.30.147.51:8080/")
    os.environ["ARGOCD_API_TOKEN"] = os.getenv("ARGOCD_API_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcmdvY2QiLCJzdWIiOiJhZG1pbjphcGlLZXkiLCJuYmYiOjE3NDk2NzUxODAsImlhdCI6MTc0OTY3NTE4MCwianRpIjoiMjFkMDIyNWYtZDU1ZS00NDllLWFkNDAtMDA1NTY5N2M4NGQ3In0.s-9YzxmexF8k_JgDVFI3raiIqQ9Bo6OrTDB3okWque8")
    
    try:
        # Import here to ensure environment variables are set before import
        from app.agent import ArgoCDAgent
        
        # Create the real ArgoCD agent
        logger.info("Initializing ArgoCD Agent...")
        agent = ArgoCDAgent()
        
        # First check if the ArgoCD server is accessible
        server_accessible, message = await agent.check_argocd_server()
        if not server_accessible:
            logger.error(f"ArgoCD server is not accessible: {message}")
            return False
        
        logger.info(f"ArgoCD server check: {message}")
        
        # Test queries
        test_queries = [
            "List all applications",
            "Get the ArgoCD server version",
            "What is the health status of all applications?"
        ]
        
        context_id = f"test-{uuid4().hex}"
        
        for i, query in enumerate(test_queries):
            logger.info(f"\nTest Query {i+1}: '{query}'")
            
            # Use the agent to process the query asynchronously
            logger.info("Sending query to ArgoCD agent...")
            try:
                response = await agent.ainvoke(query, context_id)
                logger.info(f"Response: {response['content']}")
            except Exception as e:
                logger.error(f"Error processing query: {e}", exc_info=True)
                continue
        
        # Clean up resources
        await agent.cleanup()
        logger.info("\nArgoCD agent testing completed!")
        return True
        
    except Exception as e:
        logger.error(f"Error during ArgoCD agent testing: {e}", exc_info=True)
        return False

async def main():
    """Main function to run all tests."""
    logger.info("Starting ArgoCD Agent tests")
    
    # Run direct agent test
    direct_success = await test_argocd_agent_direct()
    
    # Report overall results
    if direct_success:
        logger.info("\n✅ Basic tests passed successfully!")
        logger.info("\nNote: For full MCP integration testing, you'll need to:")
        logger.info("1. Ensure 'npx argocd-mcp@latest stdio' works in your terminal")
        logger.info("2. Verify your ArgoCD credentials are correct")
        logger.info("3. Run the agent in a real application context")
        return 0
    else:
        logger.error("\n❌ Some tests failed. See logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))