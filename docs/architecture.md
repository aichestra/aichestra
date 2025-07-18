# Aichestra Architecture

## Overview

Aichestra is an intelligent multi-agent orchestration system built with LangGraph and A2A Protocol. The system features intelligent request routing, specialized agents for different domains, and dynamic capability discovery.

## System Components

### Core Components

```mermaid
graph TD
    subgraph "Core Components"
        Orchestrator["Smart Orchestrator"]
        OrchestratorClient["Orchestrator Client"]
    end
    
    subgraph "Agent Ecosystem"
        MathAgent["Math Agent"]
        CurrencyAgent["Currency Agent"]
        ArgocdAgent["ArgoCD Agent"]
    end
    
    subgraph "External Services"
        MathMCP["Math MCP Server"]
        FrankfurterAPI["Frankfurter API"]
        ArgocdMCP["ArgoCD MCP Server"]
    end
    
    OrchestratorClient -->|Sends requests| Orchestrator
    Orchestrator -->|Routes requests| MathAgent
    Orchestrator -->|Routes requests| CurrencyAgent
    Orchestrator -->|Routes requests| ArgocdAgent
    
    MathAgent -->|Uses| MathMCP
    CurrencyAgent -->|Uses| FrankfurterAPI
    ArgocdAgent -->|Uses| ArgocdMCP
```

### Smart Orchestrator Architecture

```mermaid
graph TD
    subgraph "Smart Orchestrator"
        Router["Router State Machine"]
        AgentRegistry["Agent Registry"]
        SkillMatcher["Skill Matcher"]
        ConfidenceScorer["Confidence Scorer"]
    end
    
    subgraph "A2A Integration"
        A2AClient["A2A Client"]
        CardResolver["A2A Card Resolver"]
    end
    
    subgraph "API Layer"
        FastAPI["FastAPI Endpoints"]
        AgentManagementAPI["Agent Management API"]
    end
    
    Router -->|Uses| SkillMatcher
    Router -->|Uses| ConfidenceScorer
    Router -->|Consults| AgentRegistry
    
    A2AClient -->|Communicates with| AgentRegistry
    CardResolver -->|Resolves| AgentRegistry
    
    FastAPI -->|Exposes| AgentManagementAPI
    AgentManagementAPI -->|Manages| AgentRegistry
```

### Agent Communication Flow

```mermaid
sequenceDiagram
    participant User
    participant Client as Orchestrator Client
    participant Orchestrator
    participant Agent as Specialized Agent
    participant External as External Service
    
    User->>Client: Send request
    Client->>Orchestrator: Forward request
    Orchestrator->>Orchestrator: Analyze request
    Orchestrator->>Orchestrator: Match skills
    Orchestrator->>Orchestrator: Calculate confidence
    Orchestrator->>Agent: Route request
    Agent->>External: Call external service
    External->>Agent: Return data
    Agent->>Orchestrator: Return response
    Orchestrator->>Client: Forward response
    Client->>User: Display response
```

## Component Details

### 1. Smart Orchestrator

The Smart Orchestrator is the central component of the system, responsible for routing requests to the appropriate specialized agent based on their capabilities.

#### Key Features:
- **Dynamic Agent Discovery**: Automatically discovers agent capabilities from AgentCards
- **Skill-Based Matching**: Routes requests based on agent skills, tags, and descriptions
- **Confidence Scoring**: Provides confidence scores for routing decisions
- **Real-time Registration**: Agents can be registered/unregistered dynamically

#### Implementation:
- Built with LangGraph for workflow orchestration
- Uses A2A Protocol for standardized agent communication
- Implements a FastAPI server for agent management

#### Core Classes:
- `SmartOrchestrator`: Main orchestrator class that manages agent routing
- `OrchestratorAgentExecutor`: A2A-compatible executor for the orchestrator
- `RouterState`: State machine for request routing

### 2. Specialized Agents

The system includes several specialized agents, each designed to handle specific types of requests.

#### Math Agent

**Purpose**: Performs mathematical calculations and analysis

**Features**:
- Arithmetic calculations and expression evaluation
- Algebraic equation solving
- Calculus operations (derivatives and integrals)
- Matrix operations and linear algebra
- Statistical analysis

**Implementation**:
- Uses LangGraph ReAct agent pattern
- Integrates with a custom MCP (Model Context Protocol) server
- Leverages SymPy and NumPy for mathematical operations

#### Currency Agent

**Purpose**: Handles currency exchange and financial data

**Features**:
- Currency conversion between different currencies
- Exchange rate lookup
- Historical rate analysis

**Implementation**:
- Uses LangGraph ReAct agent pattern
- Integrates with Frankfurter API for exchange rate data
- Implements structured response format

#### ArgoCD Agent

**Purpose**: Manages Kubernetes and GitOps operations

**Features**:
- List ArgoCD applications
- Sync applications
- Check deployment status

**Implementation**:
- Uses LangGraph ReAct agent pattern
- Integrates with ArgoCD MCP server
- Implements fallback to direct API if MCP fails

### 3. Orchestrator Client

**Purpose**: Provides a command-line interface for interacting with the orchestrator

**Features**:
- Interactive command-line interface
- Agent registration and management
- Multi-turn conversation support
- Push notification support

**Implementation**:
- Uses A2A Client for communication
- Supports both A2A protocol and FastAPI endpoints
- Implements hybrid approach with fallbacks

### 4. A2A Protocol Integration

The system uses the A2A (Agent-to-Agent) Protocol for standardized communication between components.

```mermaid
graph TD
    subgraph "A2A Protocol Components"
        AgentCard["Agent Card"]
        A2AClient["A2A Client"]
        A2AServer["A2A Server"]
        CardResolver["Card Resolver"]
    end
    
    subgraph "Communication Flow"
        SendMessage["Send Message"]
        GetTask["Get Task"]
        TaskUpdate["Task Update"]
        PushNotification["Push Notification"]
    end
    
    AgentCard -->|Defines| A2AClient
    AgentCard -->|Registered with| A2AServer
    CardResolver -->|Fetches| AgentCard
    
    A2AClient -->|Initiates| SendMessage
    A2AClient -->|Polls| GetTask
    A2AServer -->|Emits| TaskUpdate
    A2AServer -->|Sends| PushNotification
```

## Technical Architecture

### Technology Stack

```mermaid
graph TD
    subgraph "Frontend"
        CLI["Command Line Interface"]
    end
    
    subgraph "Backend"
        FastAPI["FastAPI"]
        LangGraph["LangGraph"]
        A2ASDK["A2A SDK"]
    end
    
    subgraph "AI/ML"
        GoogleAI["Google Gemini"]
        OpenAI["OpenAI"]
    end
    
    subgraph "External Services"
        MCP["MCP Protocol"]
        FrankfurterAPI["Frankfurter API"]
        ArgoCD["ArgoCD API"]
    end
    
    CLI -->|Interacts with| FastAPI
    FastAPI -->|Uses| LangGraph
    FastAPI -->|Uses| A2ASDK
    
    LangGraph -->|Orchestrates| GoogleAI
    LangGraph -->|Orchestrates| OpenAI
    
    A2ASDK -->|Communicates with| MCP
    A2ASDK -->|Communicates with| FrankfurterAPI
    A2ASDK -->|Communicates with| ArgoCD
```

### Data Flow

```mermaid
flowchart TD
    User[User] -->|Request| Client[Orchestrator Client]
    Client -->|A2A Request| Orchestrator[Smart Orchestrator]
    
    Orchestrator -->|Analyze Request| SkillMatcher[Skill Matcher]
    SkillMatcher -->|Match Skills| AgentSelector[Agent Selector]
    
    AgentSelector -->|Route Request| MathAgent[Math Agent]
    AgentSelector -->|Route Request| CurrencyAgent[Currency Agent]
    AgentSelector -->|Route Request| ArgocdAgent[ArgoCD Agent]
    
    MathAgent -->|Process Request| MathMCP[Math MCP Server]
    MathMCP -->|Calculate| MathResult[Math Result]
    MathResult -->|Return| MathAgent
    
    CurrencyAgent -->|Process Request| FrankfurterAPI[Frankfurter API]
    FrankfurterAPI -->|Exchange Rates| CurrencyResult[Currency Result]
    CurrencyResult -->|Return| CurrencyAgent
    
    ArgocdAgent -->|Process Request| ArgocdMCP[ArgoCD MCP Server]
    ArgocdMCP -->|K8s Operations| ArgocdResult[ArgoCD Result]
    ArgocdResult -->|Return| ArgocdAgent
    
    MathAgent -->|Response| Orchestrator
    CurrencyAgent -->|Response| Orchestrator
    ArgocdAgent -->|Response| Orchestrator
    
    Orchestrator -->|Final Response| Client
    Client -->|Display| User
```

## Agent Registration and Discovery

```mermaid
sequenceDiagram
    participant Client
    participant Orchestrator
    participant AgentRegistry
    participant NewAgent
    
    Client->>Orchestrator: Register agent request
    Orchestrator->>NewAgent: Fetch agent card
    NewAgent->>Orchestrator: Return agent card
    Orchestrator->>AgentRegistry: Add agent
    Orchestrator->>Orchestrator: Extract capabilities
    Orchestrator->>Orchestrator: Update skill keywords
    Orchestrator->>Client: Confirm registration
    
    Client->>Orchestrator: List agents request
    Orchestrator->>AgentRegistry: Get all agents
    AgentRegistry->>Orchestrator: Return agent list
    Orchestrator->>Client: Return formatted agent list
```

## Deployment Architecture

```mermaid
graph TD
    subgraph "Client Layer"
        CLI["CLI Client"]
    end
    
    subgraph "Orchestration Layer"
        Orchestrator["Smart Orchestrator"]
        API["Management API"]
    end
    
    subgraph "Agent Layer"
        MathAgent["Math Agent"]
        CurrencyAgent["Currency Agent"]
        ArgocdAgent["ArgoCD Agent"]
    end
    
    subgraph "Service Layer"
        MathMCP["Math MCP Server"]
        FrankfurterAPI["Frankfurter API"]
        ArgocdMCP["ArgoCD MCP Server"]
    end
    
    CLI -->|HTTP/A2A| Orchestrator
    Orchestrator -->|A2A| MathAgent
    Orchestrator -->|A2A| CurrencyAgent
    Orchestrator -->|A2A| ArgocdAgent
    
    MathAgent -->|MCP| MathMCP
    CurrencyAgent -->|HTTP| FrankfurterAPI
    ArgocdAgent -->|MCP/HTTP| ArgocdMCP
    
    CLI -->|HTTP| API
    API -->|Manages| Orchestrator
```

## Extensibility

The system is designed to be highly extensible, allowing new agents to be added dynamically. The agent template provides a starting point for creating new specialized agents.

### Creating a New Agent

To create a new agent:

1. Use the `agentTemplate` as a starting point
2. Implement the required interfaces:
   - `agent.py`: Core agent logic
   - `agent_executor.py`: A2A protocol integration
   - `__main__.py`: Entry point and server setup
3. Register the agent with the orchestrator

### Agent Template Structure

```mermaid
graph TD
    subgraph "Agent Template"
        Main["__main__.py"]
        Agent["agent.py"]
        Executor["agent_executor.py"]
    end
    
    subgraph "Configuration"
        AgentConfig["agent_config.py"]
        PluginConfig["plugin_config.py"]
    end
    
    subgraph "Plugins"
        BasePlugin["base_plugin.py"]
        APIPlugin["api_plugin.py"]
        MCPPlugin["mcp_plugin.py"]
        PluginManager["plugin_manager.py"]
    end
    
    Main -->|Imports| Agent
    Main -->|Imports| Executor
    
    Agent -->|Uses| AgentConfig
    Agent -->|Uses| PluginManager
    
    PluginManager -->|Manages| BasePlugin
    PluginManager -->|Manages| APIPlugin
    PluginManager -->|Manages| MCPPlugin
    
    APIPlugin -->|Configured by| PluginConfig
    MCPPlugin -->|Configured by| PluginConfig
```

## Conclusion

Aichestra provides a flexible, extensible framework for building intelligent multi-agent systems. The architecture allows for easy addition of new specialized agents, while the smart orchestrator ensures that requests are routed to the most appropriate agent based on their capabilities.

The use of standardized protocols like A2A and MCP ensures interoperability between components, while the LangGraph framework provides robust workflow orchestration capabilities.
