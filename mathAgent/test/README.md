# Math Agent Test Suite

This directory contains comprehensive tests for the Math Agent, which uses MCP (Model Context Protocol) to provide mathematical operations through natural language processing.

## Prerequisites

Before running tests, ensure you have:

1. **Environment Setup**:
   ```bash
   export GOOGLE_API_KEY=your_google_api_key_here
   ```

2. **Dependencies Installed**:
   ```bash
   cd mathAgent
   uv sync
   ```

## Test Files Overview

### 🧮 Core Functionality Tests

#### `simple_test.py`
- **Purpose**: Basic math agent functionality test
- **What it tests**: Simple arithmetic operations
- **Run**: `uv run python test/simple_test.py`
- **Example output**: Tests "What is 5 + 7?" and returns "12"

#### `comprehensive_test.py`
- **Purpose**: Full MCP math agent testing with LLM integration
- **What it tests**: All mathematical operations with natural language queries
- **Run**: `uv run python test/comprehensive_test.py`
- **Tests covered**:
  - Arithmetic: "(3 + 5) × 12"
  - Equation solving: "2x + 5 = 15"
  - Calculus: "derivative of x^2 + 3x + 2"
  - Integration: "integral of 2x + 3"
  - Statistics: "mean of numbers 1, 2, 3, 4, 5"
  - Matrix operations: "multiply matrices [[1,2],[3,4]] and [[5,6],[7,8]]"

### 🔧 MCP Protocol Tests

#### `test_mcp_connection.py`
- **Purpose**: Test MCP server connection without LLM
- **What it tests**: Direct MCP server communication
- **Run**: `uv run python test/test_mcp_connection.py`
- **Key features**: Tests MCP tools loading and basic calculation

#### `test_mcp_agent.py`
- **Purpose**: Comprehensive MCP tool testing
- **What it tests**: All 6 MCP mathematical tools individually
- **Run**: `uv run python test/test_mcp_agent.py`
- **Tools tested**:
  - `calculate_expression`: Arithmetic evaluation
  - `solve_equation`: Algebraic equation solving
  - `derivative`: Calculus derivatives
  - `integral`: Calculus integration
  - `matrix_operations`: Matrix calculations
  - `statistics_calculator`: Statistical analysis

#### `test_math_functions.py`
- **Purpose**: Direct mathematical function testing
- **What it tests**: Core mathematical operations without MCP
- **Run**: `uv run python test/test_math_functions.py`
- **Coverage**: Tests SymPy and NumPy operations directly

### 🔀 Orchestrator Integration Tests

#### `test_orchestrator_routing.py`
- **Purpose**: Test orchestrator routing for math queries
- **What it tests**: Whether the orchestrator correctly routes math queries to the math agent
- **Run**: `uv run python test/test_orchestrator_routing.py`
- **Queries tested**:
  - "what is 2+3"
  - "calculate 5 * 6"
  - "solve equation x + 2 = 5"
  - "find derivative of x^2"
  - "what is the mean of [1,2,3,4,5]"

#### `debug_routing.py`
- **Purpose**: Detailed debugging of orchestrator routing logic
- **What it tests**: Agent scoring and skill matching for routing decisions
- **Run**: `uv run python test/debug_routing.py`
- **Output**: Detailed breakdown of why specific agents are selected

## Running All Tests

### Quick Test Suite
```bash
# From mathAgent directory
uv run python test/simple_test.py
uv run python test/test_mcp_connection.py
```

### Full Test Suite
```bash
# From mathAgent directory
uv run python test/comprehensive_test.py
uv run python test/test_mcp_agent.py
uv run python test/test_math_functions.py
```

### Orchestrator Integration Tests
```bash
# From mathAgent directory
uv run python test/test_orchestrator_routing.py
uv run python test/debug_routing.py
```

## Test Dependencies

### Required Services
- **Math Agent**: Must be running on `localhost:8003`
- **Orchestrator**: Must be running on `localhost:8000` (for routing tests)
- **Other Agents**: ArgoCD (8001) and Currency (8002) agents for routing comparison

### Starting Services
```bash
# Terminal 1: Start Math Agent
cd mathAgent
uv run app

# Terminal 2: Start Orchestrator (for routing tests)
cd orchestrator
uv run app

# Terminal 3: Run tests
cd mathAgent
uv run python test/[test_file].py
```

## Expected Outputs

### Successful Test Examples

**Simple Test**:
```
🔢 Testing: What is 5 + 7?
📊 Result: 12
```

**MCP Connection Test**:
```
✅ Found 6 MCP tools:
  - calculate_expression: Evaluate a mathematical expression safely using SymPy
  - solve_equation: Solve an algebraic equation using SymPy
  ...
📊 Result: Result: 14.0
```

**Comprehensive Test**:
```
1. 🔢 Question: What is (3 + 5) × 12?
   📊 Answer: (3 + 5) × 12 = 96

2. 🔢 Question: Solve the equation 2x + 5 = 15
   📊 Answer: x = 5
```

## Troubleshooting

### Common Issues

1. **API Key Missing**:
   ```
   Error: GOOGLE_API_KEY environment variable is required
   ```
   **Solution**: Set the environment variable with a valid Google API key

2. **MCP Connection Failed**:
   ```
   Error: unhandled errors in a TaskGroup
   ```
   **Solution**: Ensure all dependencies are installed with `uv sync`

3. **Routing to Wrong Agent**:
   ```
   Selected Agent: ArgoCD Agent (should be Math Agent)
   ```
   **Solution**: Restart the math agent to update agent card with new skill tags

4. **Import Errors**:
   ```
   ModuleNotFoundError: No module named 'app'
   ```
   **Solution**: Run tests from the mathAgent directory, not from the test subdirectory

### Debug Steps

1. **Check Math Agent Status**:
   ```bash
   curl http://localhost:8003/.well-known/agent.json
   ```

2. **Test MCP Server Directly**:
   ```bash
   uv run python test/test_mcp_connection.py
   ```

3. **Verify Environment**:
   ```bash
   echo $GOOGLE_API_KEY
   ```

## Test Coverage

- ✅ **Arithmetic Operations**: Basic and advanced calculations
- ✅ **Equation Solving**: Linear, quadratic, polynomial equations
- ✅ **Calculus**: Derivatives and integrals
- ✅ **Matrix Operations**: Multiplication, determinant, inverse
- ✅ **Statistics**: Mean, median, standard deviation
- ✅ **MCP Protocol**: Tool loading, communication, error handling
- ✅ **LLM Integration**: Natural language processing
- ✅ **Orchestrator Routing**: Agent selection and forwarding
- ✅ **Error Handling**: API limits, connection failures

## Performance Notes

- **Rate Limiting**: Tests include delays to avoid Google API rate limits
- **Connection Pooling**: Each test creates fresh MCP connections
- **Memory Usage**: Tests clean up resources automatically
- **Timeout Handling**: 30-second timeouts for agent communication

For more information about the Math Agent architecture, see the main README in the mathAgent directory. 