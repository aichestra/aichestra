# 🚀 Quick Start Guide: Testing the Orchestrator Agent

This guide will help you quickly test the orchestrator agent in different scenarios.

## 📋 Prerequisites

- Python 3.10+ (updated for A2A SDK compatibility)
- [uv](https://docs.astral.sh/uv/) package manager
- Terminal access

## 🎉 Recent Fixes (June 2025)
- **CLI Hanging Fixed**: Currency requests now respond quickly
- **Enhanced Routing**: Single currency codes like "usd" route correctly
- **Clean Responses**: Fixed raw JSON display in CLI

## 🏃‍♂️ 5-Minute Test

### Step 1: Install and Test
```bash
# Navigate to orchestrator directory
cd orchestrator

# Install dependencies
uv sync

# Run comprehensive test suite (recommended first step)
uv run -m app.test_orchestrator
```

### Step 2: Try Individual Commands
```bash
# Test ArgoCD routing
uv run -m app -m "List all ArgoCD applications" -v

# Test Currency routing
uv run -m app -m "Convert 100 USD to EUR" -v

# Test skill-based routing
uv run -m app -m "kubernetes cluster management" -v
```

## 🧪 Testing Scenarios

### Scenario 1: ArgoCD Operations
```bash
# Application management
uv run -m app -m "Sync the guestbook application in ArgoCD"
uv run -m app -m "Show me the status of my Kubernetes deployments"
uv run -m app -m "Deploy a new application using GitOps"

# Kubernetes operations
uv run -m app -m "Help me troubleshoot a failing pod"
uv run -m app -m "List all services in my cluster"
```

### Scenario 2: Currency Operations (Enhanced)
```bash
# Exchange rates
uv run -m app -m "What is the current exchange rate for USD to EUR?"
uv run -m app -m "Calculate the exchange rate between GBP and CAD"

# Currency conversion
uv run -m app -m "Convert 100 USD to Japanese Yen"
uv run -m app -m "How much is 50 EUR in USD?"

# Single currency codes (FIXED - now routes correctly)
uv run -m app -m "usd" -v  # Routes to Currency Agent with 60%+ confidence
uv run -m app -m "eur" -v
uv run -m app -m "inr" -v

# Natural language (FIXED - clean responses)
uv run -m app -m "how much is 10 USD in INR?" -v

# Financial data
uv run -m app -m "Get historical currency rates for the last month"
uv run -m app -m "What's the price of Bitcoin in USD?"
```

### Scenario 3: Skill-Based Routing
```bash
# Test skill matching
uv run -m app -m "financial market analysis"
uv run -m app -m "kubernetes cluster management"
uv run -m app -m "gitops workflow management"
```

### Scenario 4: Edge Cases
```bash
# Test default routing
uv run -m app -m "Hello world"
uv run -m app -m "Help me with something"

# Test ambiguous requests
uv run -m app -m "Show me some data"
uv run -m app -m "I need help"
```

## 🔍 Understanding the Output

### Simple Output (default)
```bash
uv run -m app -m "Convert 100 USD to EUR"
```
```
✅ Success
Selected Agent: currency (Currency Agent)
Agent Skills: currency_exchange, financial_data, market_analysis, rate_conversion, historical_data
Confidence: 0.80
Reasoning: Selected Currency Agent based on keywords: convert, usd, eur
Response: Currency Agent would handle: Convert 100 USD to EUR (Agent not running: All connection attempts failed)
```

### Verbose Output (detailed)
```bash
uv run -m app -m "Convert 100 USD to EUR" -v
```
```json
{
  "success": true,
  "request": "Convert 100 USD to EUR",
  "selected_agent_id": "currency",
  "selected_agent_name": "Currency Agent",
  "agent_skills": ["currency_exchange", "financial_data", "market_analysis", "rate_conversion", "historical_data"],
  "confidence": 0.80,
  "reasoning": "Selected Currency Agent based on keywords: convert, usd, eur",
  "response": "Currency Agent would handle: Convert 100 USD to EUR (Agent not running: All connection attempts failed)",
  "metadata": {
    "request_id": "uuid-here",
    "start_timestamp": "2025-01-15T10:30:00Z",
    "agent_scores": {"argocd": 0.0, "currency": 3.0},
    "skill_matches": {"argocd": [], "currency": []},
    "agent_endpoint": "http://localhost:8002"
  }
}
```

## 🔧 Testing with Real Agents (Optional)

If you want to test with actual running agents:

### Terminal 1: Start Currency Agent
```bash
cd ../currencyAgent
uv sync
uv run -m app --port 8002
```

### Terminal 2: Start ArgoCD Agent  
```bash
cd ../argocdAgent
uv sync
uv run -m app --port 8001
```

### Terminal 3: Test Orchestrator
```bash
cd orchestrator
uv run -m app -m "What is the exchange rate for USD to EUR?" -v
```

## 📊 Expected Results

### High Confidence Routing (>80%)
- **ArgoCD**: "Sync the guestbook application in ArgoCD" → 100% confidence
- **Currency**: "What is the current exchange rate for USD to EUR?" → 100% confidence

### Medium Confidence Routing (50-80%)
- **ArgoCD**: "kubernetes cluster management" → 74% confidence
- **Currency**: "Convert 100 USD to Japanese Yen" → 80% confidence

### Low Confidence Routing (<50%)
- **Default**: "Hello world" → 30% confidence (falls back to ArgoCD)

## 🐛 Troubleshooting

### Issue: Import Errors
```bash
# Solution: Reinstall dependencies
uv sync --force
```

### Issue: No Routing Matches
```bash
# Check available agents
uv run -m app -m "test" -v
# Look at the "Available agents" section in verbose output
```

### Issue: Agent Connection Failed
This is expected when agents aren't running. The orchestrator will show:
```
Response: Agent would handle: [request] (Agent not running: All connection attempts failed)
```

## 🎯 Key Features to Test

1. **Keyword Matching**: Try requests with specific keywords like "argocd", "kubernetes", "currency", "exchange"

2. **Skill Matching**: Test skill-based routing with terms like "gitops", "financial_data", "kubernetes_management"

3. **Confidence Scoring**: Notice how confidence varies based on keyword and skill matches

4. **Reasoning**: Check the reasoning field to understand why each agent was selected

5. **Fallback Behavior**: Test with ambiguous requests to see default routing

## 📈 Next Steps

After testing the orchestrator:

1. **Explore the Code**: Check `orchestrator.py` to understand the routing logic
2. **Add New Agents**: Try the dynamic agent addition examples in the README
3. **Build Real Agents**: Create your own specialized agents
4. **Deploy**: Consider containerization and production deployment

## 🤝 Getting Help

If you run into issues:
1. Check the verbose output with `-v` flag
2. Review the test suite results
3. Look at the troubleshooting section in the main README
4. Check the logs for detailed error information

---

**🎉 Happy Testing!** The orchestrator should route your requests intelligently and provide clear reasoning for its decisions. 