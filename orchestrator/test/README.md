# Orchestrator Test Suite

This directory contains tests for the Smart Orchestrator Agent, which intelligently routes requests to specialized agents using LangGraph and A2A SDK.

## Prerequisites

Before running tests, ensure you have:

1. **Dependencies Installed**:
   ```bash
   cd orchestrator
   uv sync
   ```

2. **Agent Services Running** (for integration tests):
   - **ArgoCD Agent**: `localhost:8001`
   - **Currency Agent**: `localhost:8002`
   - **Math Agent**: `localhost:8003`

## Test Files Overview

### 🔀 Core Functionality Tests

#### `test_orchestrator.py`
- **Purpose**: Comprehensive orchestrator functionality test
- **What it tests**: Request routing, agent selection, and coordination
- **Run**: `uv run python test/test_orchestrator.py`
- **Features tested**:
  - Agent discovery and registration
  - Request analysis and routing logic
  - Skill-based agent matching
  - Confidence scoring
  - Response forwarding
  - Error handling and fallbacks

## Running Tests

### Quick Test (Unit Testing)
```bash
# From orchestrator directory
uv run python test/test_orchestrator.py
```

### Integration Test (with all agents running)
```bash
# Terminal 1: Start ArgoCD Agent
cd argocdAgent && uv run app

# Terminal 2: Start Currency Agent
cd currencyAgent && uv run app

# Terminal 3: Start Math Agent
cd mathAgent && uv run app

# Terminal 4: Start Orchestrator
cd orchestrator && uv run app

# Terminal 5: Run tests
cd orchestrator
uv run python test/test_orchestrator.py
```

## Test Dependencies

### Required Services (for integration tests)
- **ArgoCD Agent**: `http://localhost:8001` - Kubernetes/GitOps operations
- **Currency Agent**: `http://localhost:8002` - Currency exchange and financial data
- **Math Agent**: `http://localhost:8003` - Mathematical calculations and analysis

### Agent Card Requirements
Each agent must serve its agent card at `/.well-known/agent.json` endpoint for proper discovery.

## Expected Outputs

### Successful Test Examples

**Agent Discovery**:
```
🔀 Testing Orchestrator Agent Discovery
✅ Loaded ArgoCD Agent from http://localhost:8001
✅ Loaded Currency Agent from http://localhost:8002
✅ Loaded Math Agent from http://localhost:8003
```

**Request Routing**:
```
🎯 Testing Request Routing
Query: "what is 2+3"
Selected Agent: Math Agent
Confidence: 0.80
Reasoning: Selected Math Agent based on keywords: what is, +
```

**Agent Coordination**:
```
📊 Agent Scores:
  - Math Agent: 2.5 (arithmetic_calculation, keywords: what is, +)
  - Currency Agent: 0.0 (no matching skills)
  - ArgoCD Agent: 0.0 (no matching skills)
```

## Test Coverage

### 🧠 Routing Intelligence Tests
- **Keyword Matching**: Tests skill tag recognition
- **Skill Scoring**: Validates agent selection algorithm
- **Confidence Calculation**: Ensures accurate confidence scores
- **Fallback Logic**: Tests default agent selection

### 🔗 Integration Tests
- **Agent Discovery**: Dynamic agent card fetching
- **Request Forwarding**: A2A protocol communication
- **Response Handling**: Message parsing and formatting
- **Error Recovery**: Network failures and timeouts

### 📋 Query Categories Tested

#### Math Queries → Math Agent
- "what is 2+3"
- "calculate 5 * 6"
- "solve equation x + 2 = 5"
- "find derivative of x^2"
- "what is the mean of [1,2,3,4,5]"

#### Currency Queries → Currency Agent
- "convert 100 USD to EUR"
- "exchange rate for GBP"
- "bitcoin price"

#### Kubernetes Queries → ArgoCD Agent
- "list applications"
- "sync my-app"
- "kubernetes cluster status"

## Troubleshooting

### Common Issues

1. **Agent Not Found**:
   ```
   ❌ Error loading agent argocd from http://localhost:8001: Connection refused
   ```
   **Solution**: Start the required agent services

2. **Agent Card Fetch Failed**:
   ```
   ⚠️ Failed to load agent card from http://localhost:8002
   ```
   **Solution**: Ensure agent serves `/.well-known/agent.json` endpoint

3. **Wrong Agent Selected**:
   ```
   Expected: Math Agent, Got: ArgoCD Agent
   ```
   **Solution**: Check agent skill tags and orchestrator keyword matching

4. **Request Forwarding Failed**:
   ```
   ⚠️ Could not forward request: HTTP 500
   ```
   **Solution**: Verify target agent is healthy and accepting requests

### Debug Steps

1. **Check Orchestrator Status**:
   ```bash
   curl http://localhost:8000/.well-known/agent.json
   ```

2. **Test Agent Endpoints**:
   ```bash
   curl http://localhost:8001/.well-known/agent.json  # ArgoCD
   curl http://localhost:8002/.well-known/agent.json  # Currency
   curl http://localhost:8003/.well-known/agent.json  # Math
   ```

3. **Manual Routing Test**:
   ```bash
   curl -X POST http://localhost:8000 \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":"1","method":"message/send","params":{"id":"test","message":{"role":"user","messageId":"msg1","contextId":"ctx1","parts":[{"type":"text","text":"what is 2+3"}]},"configuration":{"acceptedOutputModes":["text"]}}}'
   ```

## Performance Notes

- **Agent Discovery**: Cached after initial load
- **Skill Matching**: O(n) complexity per agent
- **Request Forwarding**: Adds ~100-200ms overhead
- **Concurrent Requests**: Supports multiple simultaneous routing

## Architecture Notes

### Routing Algorithm
1. **Request Analysis**: Extract keywords and intent
2. **Agent Scoring**: Calculate match scores for each agent
3. **Selection**: Choose highest scoring agent (with fallback)
4. **Forwarding**: Send request using A2A protocol
5. **Response**: Return agent response to client

### Skill Matching Logic
- **Keyword Weight**: 1.0 per matched skill tag
- **Skill Weight**: 1.5 per matched skill name
- **Confidence**: Score / 5.0 (capped at 1.0)
- **Fallback**: ArgoCD agent if no matches

For more information about the Orchestrator architecture, see the main README in the orchestrator directory. 