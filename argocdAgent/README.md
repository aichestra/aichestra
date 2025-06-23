# ArgoCD Agent with LangGraph and MCP

This agent allows you to interact with ArgoCD via natural language using LangGraph and the ArgoCD MCP server. It supports both stdio and HTTP MCP transport modes, with a focus on the stdio mode for simplicity and reliability. **The agent can run standalone or as part of the [intelligent orchestrator system](../orchestrator/README.md)**.

## 🚀 Quick Start with Orchestrator

**Recommended**: Use the orchestrator for intelligent routing to this agent:

```bash
# Navigate to project root
cd ..

# Test orchestrator routing to ArgoCD agent
cd orchestrator
uv sync
uv run -m app -m "List all ArgoCD applications" -v
uv run -m app -m "Sync the guestbook application" -v
```

The orchestrator will automatically route ArgoCD/Kubernetes requests to this agent based on:
- **Keywords**: `argocd`, `kubernetes`, `k8s`, `kubectl`, `deploy`, `application`, `sync`
- **Skills**: `kubernetes_management`, `gitops`, `application_deployment`, `argocd_operations`

## 🏗️ System Integration

This agent integrates with the orchestrator system:

```mermaid
graph TD
    A[User: "Sync my ArgoCD app"] --> B[🤖 Orchestrator Agent]
    B --> C[Skill Analysis]
    C --> D[☸️ ArgoCD Agent - Port 8001]
    D --> E[ArgoCD MCP Server]
    E --> F[ArgoCD API]
    F --> G[Kubernetes Cluster]
```

## Prerequisites

- Python 3.12+
- Node.js (for running the argocd-mcp server)
- ArgoCD API token and endpoint
- Google API key (for Gemini model) or OpenAI API key (optional)

## Installation

Install the agent and its dependencies:

```sh
# Using uv (recommended)
cd argocdAgent
uv sync

# Using pip
pip install -e .
```

## Environment Variables

Set the following environment variables:

```sh
# Required for ArgoCD
export ARGOCD_BASE_URL="https://your-argocd-server.com/"
export ARGOCD_API_TOKEN="your-argocd-api-token"

# Required for LLM (Google Gemini by default)
export GOOGLE_API_KEY="your-google-api-key"

# Optional: Use OpenAI instead of Google
export model_source="openai"
export TOOL_LLM_NAME="gpt-3.5-turbo"
export TOOL_LLM_URL="https://api.openai.com/v1"
export API_KEY="your-openai-api-key"

# Optional: For self-signed certificates
export NODE_TLS_REJECT_UNAUTHORIZED="0"
```

## 🎯 Running Options

### Option 1: Via Orchestrator (Recommended)

Run as part of the intelligent orchestration system:

```bash
# Terminal 1: Start ArgoCD Agent
cd argocdAgent
uv run -m app --port 8001

# Terminal 2: Start Orchestrator
cd ../orchestrator
uv run -m app --port 8000

# Terminal 3: Test routing
cd ../orchestrator
uv run -m app -m "List all applications in my ArgoCD cluster" -v
```

### Option 2: Standalone Agent

Run the agent independently:

```bash
# Start as A2A server
cd argocdAgent
uv run -m app --host localhost --port 8001

# Test directly
uv run -m app.test_client
```

### Option 3: Direct Testing

Test the agent without running a server:

```bash
cd argocdAgent

# Run the test client
uv run -m app.test_client

# Get detailed ArgoCD information
uv run -m app.argocd_info
```

## 🧪 Testing Scenarios

### 📋 Test Suite
The ArgoCD Agent includes comprehensive testing:

- **[Test Documentation](test/README.md)** - Complete testing guide
- **`test_client.py`** - Synchronous ArgoCD operations testing
- **`async_test_client.py`** - Asynchronous operations and performance testing

```bash
# Run synchronous test suite
cd argocdAgent
uv run python test/test_client.py

# Run asynchronous test suite
uv run python test/async_test_client.py

# Expected: ArgoCD connectivity, application management, and GitOps operations work
```

### Via Orchestrator
```bash
cd orchestrator

# High-confidence ArgoCD routing
uv run -m app -m "Sync the guestbook application in ArgoCD" -v      # 100% confidence
uv run -m app -m "List all applications in my cluster" -v           # 99% confidence
uv run -m app -m "Show me the status of my deployments" -v          # 89% confidence

# Skill-based routing
uv run -m app -m "kubernetes cluster management" -v                 # 74% confidence
uv run -m app -m "gitops workflow management" -v                    # 99% confidence
```

### Direct Agent Testing
```bash
cd argocdAgent

# Run the test client
uv run -m app.test_client

# Get detailed ArgoCD information
uv run -m app.argocd_info

# Test with HTTP transport if stdio has issues
uv run -m app.argocd_info --http
```

## Running the Test Client

The test client provides a quick way to verify that the agent is working correctly:

```sh
# Using uv (recommended)
uv run -m app.test_client

# Using python
python -m app.test_client
```

The test client will:
1. Connect to ArgoCD via MCP stdio
2. Test basic ArgoCD operations (list applications, get version, etc.)
3. Test the agent's ability to respond to natural language queries

## Getting Detailed ArgoCD Information

To get detailed information about your ArgoCD applications, use the argocd_info.py script:

```sh
# Using uv (recommended)
uv run -m app.argocd_info

# Using python
python -m app.argocd_info
```

If you're experiencing connection issues with the stdio transport, you can use the HTTP transport instead:

```sh
# Using HTTP transport
uv run -m app.argocd_info --http

# Specify a custom HTTP URL
uv run -m app.argocd_info --http --http-url http://your-argocd-mcp-server:4315
```

This script will:
1. Connect to your ArgoCD server
2. Display the ArgoCD server version
3. List all applications with their health and sync status
4. Show detailed information about each application
5. Identify any out-of-sync applications

### Troubleshooting Connection Issues

If you're experiencing connection issues:

1. **Stdio Transport Issues**: The default stdio transport may hang if there are issues with the Node.js environment or the ArgoCD MCP server. Use the `--http` option to switch to HTTP transport.

2. **HTTP Transport Setup**: To use HTTP transport, you need to run the ArgoCD MCP server in HTTP mode:
   ```sh
   npx argocd-mcp@latest http --port 4315
   ```

3. **Environment Variables**:
   - `ARGOCD_USE_STDIO`: Set to "false" to disable stdio transport
   - `ARGOCD_MCP_HTTP_URL`: Set to the URL of your ArgoCD MCP HTTP server
   - `ARGOCD_MCP_COMMAND`: Customize the command used for stdio transport

## 🔗 Integration with Orchestrator

### Agent Card Configuration

The orchestrator recognizes this agent with the following capabilities:

```python
ArgoCD Agent Card:
- agent_id: "argocd"
- name: "ArgoCD Agent"
- endpoint: "http://localhost:8001"
- skills:
  - kubernetes_management (0.9)
  - gitops (0.95)
  - application_deployment (0.9)
  - argocd_operations (0.95)
  - sync_operations (0.9)
  - resource_monitoring (0.85)
- keywords: ["argocd", "argo cd", "kubernetes", "k8s", "kubectl"]
- capabilities: ["list_applications", "sync_application", "get_application_status"]
```

### Routing Examples

The orchestrator routes these requests to the ArgoCD agent:

| Request | Confidence | Matched Skills/Keywords |
|---------|------------|-------------------------|
| "Sync the guestbook application in ArgoCD" | 100% | argocd, application + argocd_operations |
| "List all applications in my cluster" | 99% | application + application_deployment |
| "kubernetes cluster management" | 74% | kubernetes + kubernetes_management |
| "Deploy using GitOps" | 99% | deploy + gitops, application_deployment |

## Using the ArgoCD Agent in Your Code

### Using the Agent

```python
from app.agent import ArgoCDAgent

# Initialize the agent
agent = ArgoCDAgent()

# Make a query
response = agent.invoke("List all applications", context_id="test-1")
print(response)

# For streaming responses
async for chunk in agent.stream("Sync the frontend application", context_id="test-2"):
    print(chunk['content'])
```

### HTTP Agent (if needed)

```python
from app.agent_http import ArgoCDAgentHTTP

# Initialize the agent
agent = ArgoCDAgentHTTP()

# Make a query
response = agent.invoke("Get the health status of all applications", context_id="test-3")
print(response)
```

## Example Queries

### Natural Language Queries
- "List all applications"
- "Get the health status of the application named 'frontend'"
- "Sync the 'backend-api' application"
- "Show me the ArgoCD server version"
- "What applications are out of sync?"
- "Tell me about the resources in the 'monitoring' application"

### Orchestrator Routing Examples
```bash
# These will be routed to ArgoCD agent with high confidence
uv run -m app -m "List all ArgoCD applications"
uv run -m app -m "Sync my Kubernetes application"
uv run -m app -m "Show deployment status"
uv run -m app -m "Help with GitOps workflow"
```

## 🚀 Full System Setup

To run the complete orchestrated system:

### Terminal 1: ArgoCD MCP Server
```bash
# Set environment variables
export ARGOCD_BASE_URL="https://your-argocd-server.com/"
export ARGOCD_API_TOKEN="your-argocd-api-token"
export NODE_TLS_REJECT_UNAUTHORIZED="0"

# Start ArgoCD MCP server (runs automatically with agent)
```

### Terminal 2: ArgoCD Agent
```bash
cd argocdAgent
uv run -m app --port 8001
```

### Terminal 3: Orchestrator
```bash
cd ../orchestrator
uv run -m app --port 8000
```

### Terminal 4: CLI Client
```bash
cd ../cli
uv run . --agent http://localhost:8000

# Now you can interact naturally:
# > "List all my ArgoCD applications"
# > "Sync the guestbook application"
# > "Show me deployment status"
```

## Running as an A2A Server

The agent can also be run as an A2A (Agent-to-Agent) server:

```sh
# Using uv
uv run -m app.__main__ --host localhost --port 8001

# Using python
python -m app.__main__ --host localhost --port 8001
```

## 🐛 Troubleshooting

### Connection Issues
- **MCP Connection Issues**: Ensure the ArgoCD server is accessible and the API token is valid
- **NODE_TLS_REJECT_UNAUTHORIZED**: Set to "0" if you're using a self-signed certificate
- **LLM API Key**: Verify that your Google API key or OpenAI API key is valid

### Orchestrator Integration Issues
```bash
# Test if agent is reachable from orchestrator
curl http://localhost:8001/health

# Check orchestrator routing
cd ../orchestrator
uv run -m app -m "test argocd" -v

# Verify environment variables
echo $ARGOCD_BASE_URL
echo $ARGOCD_API_TOKEN
```

### Agent Not Responding
```bash
# Check if agent is running
lsof -i :8001

# Restart agent
cd argocdAgent
uv run -m app --port 8001

# Test agent directly
uv run -m app.test_client
```

## 📚 Related Documentation

- **[Main Project README](../README.md)** - Complete system overview
- **[Orchestrator README](../orchestrator/README.md)** - Intelligent routing system
- **[Orchestrator Blog Post](../orchestrator/BLOG_POST.md)** - Technical architecture
- **[Orchestrator Client README](../orchestrator_client/README.md)** - Interactive client interface

## Notes

- The agent uses Google's Gemini model by default; you can change to OpenAI by setting the environment variables
- For production use, consider securing your API tokens and using proper authentication
- The agent is designed to work with ArgoCD's API via the MCP protocol
- **Best used with the orchestrator** for intelligent request routing and multi-agent coordination

---

## 🎉 Quick Test Commands

```bash
# Test orchestrator routing (recommended)
cd ../orchestrator && uv run -m app -m "List ArgoCD applications" -v

# Test agent directly
cd argocdAgent && uv run -m app.test_client

# Get ArgoCD information
cd argocdAgent && uv run -m app.argocd_info
```