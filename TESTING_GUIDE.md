# A2A Orchestrator System Testing Guide

This guide provides step-by-step instructions for testing the complete A2A orchestrator system with all agents.

## 🎉 Recent Fixes (2025-06-17)

### ✅ CLI Hanging Issue Fixed
- **Issue**: CLI would hang when requesting currency conversions like "usd"
- **Root Cause**: Orchestrator didn't handle "input-required" task state from agents
- **Fix**: Enhanced `_forward_request_to_agent` to handle all task states
- **Test**: Try `usd` or `how much is 10 USD in EUR?` - should respond quickly

### ✅ Currency Routing Improved  
- **Issue**: Single currency codes like "usd" routed to ArgoCD instead of Currency Agent
- **Root Cause**: Currency skill tags didn't include specific currency codes
- **Fix**: Added currency codes (usd, eur, inr, gbp, jpy, dollar) to skill tags
- **Test**: `usd` now routes to Currency Agent with 60%+ confidence

### ✅ CLI Response Formatting Fixed
- **Issue**: CLI showed raw JSON instead of clean answers
- **Root Cause**: `format_ai_response` didn't handle orchestrator artifacts
- **Fix**: Updated CLI to extract clean text from response artifacts
- **Test**: Responses now show clean answers like "10 USD is 862.6 INR"

## Prerequisites

### Environment Setup
```bash
# Set environment variables
export ARGOCD_BASE_URL="https://9.30.147.51:8080/"
export ARGOCD_API_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcmdvY2QiLCJzdWIiOiJhZG1pbjphcGlLZXkiLCJuYmYiOjE3NDk2NzUxODAsImlhdCI6MTc0OTY3NTE4MCwianRpIjoiMjFkMDIyNWYtZDU1ZS00NDllLWFkNDAtMDA1NTY5N2M4NGQ3In0.s-9YzxmexF8k_JgDVFI3raiIqQ9Bo6OrTDB3okWque8"
export NODE_TLS_REJECT_UNAUTHORIZED="0"
```

### Dependencies Check
```bash
# Verify uv is installed
uv --version

# Verify Node.js for ArgoCD MCP
node --version
npm --version

# Check Python version
python3 --version
```

## Testing Individual Agents

### 1. Test Orchestrator Agent (Port 8000)

#### Terminal 1: Start Orchestrator
```bash
cd orchestrator
uv run -m app --port 8000
```

#### Run Orchestrator Tests
```bash
# Comprehensive test suite
cd orchestrator
uv run python test/test_orchestrator.py

# Expected: All routing tests pass with detailed agent selection logic
```

#### Verify Orchestrator Health
```bash
# In another terminal
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Test agent discovery
curl http://localhost:8000/agents
# Expected: List of registered agents
```

### 2. Test Currency Agent (Port 8002)

#### Terminal 2: Start Currency Agent
```bash
cd currencyAgent
uv run -m app --port 8002
```

#### Run Currency Agent Tests
```bash
# Comprehensive test suite
cd currencyAgent
uv run python test/test_client.py

# Expected: Currency conversion and exchange rate tests pass
```

#### Test Currency Operations
```bash
# Health check
curl http://localhost:8002/health

# Test currency conversion
curl -X POST http://localhost:8002/execute \
  -H "Content-Type: application/json" \
  -d '{"action": "convert", "params": {"from": "USD", "to": "EUR", "amount": 100}}'

# Test exchange rates
curl -X POST http://localhost:8002/execute \
  -H "Content-Type: application/json" \
  -d '{"action": "rates", "params": {"base": "USD"}}'
```

### 3. Test Math Agent (Port 8003)

#### Terminal 3: Start Math Agent
```bash
cd mathAgent
uv run -m app --port 8003
```

#### Run Math Agent Tests
```bash
# Quick functionality test
cd mathAgent
uv run python test/simple_test.py

# Comprehensive MCP + LLM integration test
uv run python test/comprehensive_test.py

# Test MCP connection directly
uv run python test/test_mcp_connection.py

# Test all MCP mathematical tools
uv run python test/test_mcp_agent.py

# Test mathematical functions directly
uv run python test/test_math_functions.py

# Test orchestrator routing for math queries
uv run python test/test_orchestrator_routing.py

# Debug routing decisions
uv run python test/debug_routing.py

# Expected: All 8 test files pass demonstrating MCP integration, 
# mathematical operations, and proper orchestrator routing
```

#### Test Mathematical Operations
```bash
# Health check
curl http://localhost:8003/health

# Test basic calculation
curl -X POST http://localhost:8003 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "message/send",
    "params": {
      "id": "task-1",
      "message": {
        "role": "user",
        "messageId": "msg-1",
        "contextId": "ctx-1",
        "parts": [{"type": "text", "text": "Calculate 2 + 2"}]
      }
    }
  }'

# Test equation solving
curl -X POST http://localhost:8003 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-2",
    "method": "message/send",
    "params": {
      "id": "task-2",
      "message": {
        "role": "user",
        "messageId": "msg-2",
        "contextId": "ctx-2",
        "parts": [{"type": "text", "text": "Solve x^2 - 4 = 0"}]
      }
    }
  }'

# Test matrix operations
curl -X POST http://localhost:8003 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-3",
    "method": "message/send",
    "params": {
      "id": "task-3",
      "message": {
        "role": "user",
        "messageId": "msg-3",
        "contextId": "ctx-3",
        "parts": [{"type": "text", "text": "What is the determinant of [[1,2],[3,4]]?"}]
      }
    }
  }'
```

### 4. Test ArgoCD Agent (Port 8001)

#### Terminal 4: Start ArgoCD MCP Server
```bash
ARGOCD_BASE_URL="https://9.30.147.51:8080/" \
ARGOCD_API_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcmdvY2QiLCJzdWIiOiJhZG1pbjphcGlLZXkiLCJuYmYiOjE3NDk2NzUxODAsImlhdCI6MTc0OTY3NTE4MCwianRpIjoiMjFkMDIyNWYtZDU1ZS00NDllLWFkNDAtMDA1NTY5N2M4NGQ3In0.s-9YzxmexF8k_JgDVFI3raiIqQ9Bo6OrTDB3okWque8" \
NODE_TLS_REJECT_UNAUTHORIZED="0" \
npx argocd-mcp@latest stdio
```

#### Terminal 5: Start ArgoCD Agent
```bash
cd argocdAgent
uv run -m app --port 8001
```

#### Run ArgoCD Agent Tests
```bash
# Synchronous operations test
cd argocdAgent
uv run python test/test_client.py

# Asynchronous operations test
uv run python test/async_test_client.py

# Expected: ArgoCD connectivity, application listing, and GitOps operations work
```

#### Test ArgoCD Operations
```bash
# Health check
curl http://localhost:8001/health

# List applications
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{"action": "list_applications", "params": {}}'

# Get application details
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{"action": "get_application", "params": {"name": "your-app-name"}}'
```

### 5. Test Orchestrator Client

#### Run Client Tests
```bash
# Test WebSocket push notifications
cd orchestrator_client
uv run python test/push_notification_listener.py

# Expected: WebSocket connection, notification handling, and real-time communication work
```

#### Interactive Client Testing
```bash
# Start orchestrator first
cd orchestrator && uv run -m app --port 8000

# In another terminal, start orchestrator client
cd orchestrator_client && uv run . --agent http://localhost:8000

# Test queries:
# > "what is 2+3"           # Should route to Math Agent
# > "usd to eur"            # Should route to Currency Agent  
# > "list applications"     # Should route to ArgoCD Agent
```

## Full System Integration Testing

### 6-Terminal Setup

1. **Terminal 1**: ArgoCD MCP Server (see command above)
2. **Terminal 2**: Currency Agent (`cd currencyAgent && uv run -m app --port 8002`)
3. **Terminal 3**: Math Agent (`cd mathAgent && uv run -m app --port 8003`)
4. **Terminal 4**: ArgoCD Agent (`cd argocdAgent && uv run -m app --port 8001`)
5. **Terminal 5**: Orchestrator (`cd orchestrator && uv run -m app --port 8000`)
6. **Terminal 6**: Orchestrator Client (`cd orchestrator_client && uv run . --agent http://localhost:8000`)

### Test Orchestrator Routing

#### Currency-related requests (should route to Currency Agent)
```bash
# High confidence currency conversion
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Convert 100 USD to EUR"}'

# Currency rate request
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Get current exchange rates for USD"}'

# Single currency code (FIXED - now routes to Currency Agent)
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "usd"}'

# Natural language currency question (FIXED - clean responses)
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "how much is 10 USD in INR?"}'
```

#### Math-related requests (should route to Math Agent)
```bash
# High confidence math calculation
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate 2 + 2"}'

# Equation solving
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Solve x^2 - 4 = 0"}'

# Calculus operations
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Find the derivative of x^2 + 3x + 2"}'

# Matrix operations
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the determinant of [[1,2],[3,4]]?"}'

# Statistics
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate the mean of [1,2,3,4,5]"}'
```

#### ArgoCD-related requests (should route to ArgoCD Agent)
```bash
# High confidence ArgoCD operation
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Sync ArgoCD application myapp"}'

# Kubernetes management
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "List all kubernetes applications"}'
```

#### Generic requests (should show routing decision)
```bash
# Low confidence - should show routing logic
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello world"}'
```

## Interactive Client Testing

### Terminal 6: Start Orchestrator Client
```bash
cd orchestrator_client
uv run .
```

### Orchestrator Client Test Commands 

```console
gyliu513@Guangyas-MacBook-Pro orchestrator_client % uv run . --agent http://localhost:8000
Will use headers: {}
======= Agent Card ========
{"capabilities":{"pushNotifications":true,"streaming":false},"defaultInputModes":["text"],"defaultOutputModes":["text"],"description":"Intelligent agent that routes requests to specialized agents using LangGraph","name":"Smart Orchestrator Agent","skills":[{"description":"Intelligent request routing to specialized agents","id":"request_routing","name":"Request Routing","tags":["routing","orchestration"]},{"description":"Multi-agent system coordination and management","id":"agent_coordination","name":"Agent Coordination","tags":["coordination","management"]},{"description":"Skill-based agent selection and matching","id":"skill_matching","name":"Skill Matching","tags":["matching","selection"]}],"url":"http://localhost:8000/","version":"1.0.0"}
=========  starting a new task ========

What do you want to send to the agent? (:q or quit to exit): what is 2+3
Select a file path to attach? (press enter to skip):

============================================================
🤖 AI RESPONSE
============================================================
5
============================================================
=========  starting a new task ========

What do you want to send to the agent? (:q or quit to exit): how much is 10 USD in INR?
Select a file path to attach? (press enter to skip):

============================================================
🤖 AI RESPONSE
============================================================
10 USD is 862.6 INR
============================================================
=========  starting a new task ========

What do you want to send to the agent? (:q or quit to exit):
```