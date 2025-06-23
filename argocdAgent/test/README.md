# ArgoCD Agent Test Suite

This directory contains tests for the ArgoCD Agent, which provides Kubernetes application management and GitOps operations through ArgoCD.

## Prerequisites

Before running tests, ensure you have:

1. **Environment Setup**:
   ```bash
   export ARGOCD_API_TOKEN=your_argocd_api_token
   export ARGOCD_BASE_URL=https://your-argocd-server:8080/
   ```

2. **Dependencies Installed**:
   ```bash
   cd argocdAgent
   uv sync
   ```

3. **ArgoCD Server Access**:
   - ArgoCD server must be accessible
   - Valid API token with appropriate permissions
   - Network connectivity to the ArgoCD instance

## Test Files Overview

### ⚓ Core Functionality Tests

#### `test_client.py`
- **Purpose**: Basic ArgoCD agent functionality test
- **What it tests**: Core ArgoCD operations and API connectivity
- **Run**: `uv run python test/test_client.py`
- **Features tested**:
  - ArgoCD server connectivity
  - Application listing
  - Application status checks
  - Basic GitOps operations

#### `async_test_client.py`
- **Purpose**: Asynchronous ArgoCD agent functionality test
- **What it tests**: Async operations and concurrent ArgoCD calls
- **Run**: `uv run python test/async_test_client.py`
- **Features tested**:
  - Async API calls
  - Concurrent application operations
  - Performance testing
  - Error handling in async context

## Running Tests

### Quick Test
```bash
# From argocdAgent directory
uv run python test/test_client.py
```

### Async Test
```bash
# From argocdAgent directory
uv run python test/async_test_client.py
```

### With ArgoCD Agent Running
```bash
# Terminal 1: Start ArgoCD Agent
cd argocdAgent
uv run app

# Terminal 2: Run tests
cd argocdAgent
uv run python test/test_client.py
uv run python test/async_test_client.py
```

## Test Dependencies

### Required Services
- **ArgoCD Agent**: Should be running on `localhost:8001` for integration tests
- **ArgoCD Server**: Must be accessible at the configured URL
- **Kubernetes Cluster**: ArgoCD should have access to manage applications

### Environment Variables
- `ARGOCD_API_TOKEN`: Valid ArgoCD API token
- `ARGOCD_BASE_URL`: ArgoCD server URL (e.g., https://argocd.example.com:8080/)

## Expected Outputs

### Successful Test Examples

**Server Connectivity**:
```
⚓ Testing ArgoCD server connection
✅ Connected to ArgoCD server: https://argocd.example.com:8080/
```

**Application Listing**:
```
📋 Found applications:
  - app1: Synced, Healthy
  - app2: OutOfSync, Progressing
  - app3: Synced, Healthy
```

**Application Status**:
```
🔍 Application: my-app
📊 Status: Synced
💚 Health: Healthy
🔄 Last Sync: 2024-01-15T10:30:00Z
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**:
   ```
   Error: 401 Unauthorized
   ```
   **Solution**: Check ARGOCD_API_TOKEN is valid and has sufficient permissions

2. **Server Unreachable**:
   ```
   Error: Connection refused
   ```
   **Solution**: Verify ARGOCD_BASE_URL and network connectivity

3. **SSL Certificate Issues**:
   ```
   Error: SSL certificate verification failed
   ```
   **Solution**: Configure SSL settings or use insecure mode for testing

4. **Permission Denied**:
   ```
   Error: 403 Forbidden
   ```
   **Solution**: Ensure API token has required RBAC permissions

### Debug Steps

1. **Check ArgoCD Agent Status**:
   ```bash
   curl http://localhost:8001/.well-known/agent.json
   ```

2. **Test ArgoCD Server Directly**:
   ```bash
   curl -H "Authorization: Bearer $ARGOCD_API_TOKEN" \
        "$ARGOCD_BASE_URL/api/v1/applications"
   ```

3. **Verify Environment Variables**:
   ```bash
   echo $ARGOCD_API_TOKEN
   echo $ARGOCD_BASE_URL
   ```

4. **Check ArgoCD Server Health**:
   ```bash
   curl "$ARGOCD_BASE_URL/healthz"
   ```

## Test Coverage

- ✅ **Server Connectivity**: ArgoCD API connection and authentication
- ✅ **Application Management**: List, get, sync, refresh operations
- ✅ **GitOps Operations**: Repository sync, application deployment
- ✅ **Health Monitoring**: Application and resource health checks
- ✅ **Async Operations**: Concurrent API calls and performance
- ✅ **Error Handling**: Network failures, authentication errors
- ✅ **RBAC Integration**: Permission-based operation testing

## Performance Notes

- **API Rate Limiting**: ArgoCD server may have rate limits
- **Large Clusters**: Tests with many applications may be slower
- **Network Latency**: Remote ArgoCD servers will affect test duration
- **Async Benefits**: Async tests demonstrate performance improvements

## Security Considerations

- **API Tokens**: Use tokens with minimal required permissions
- **Network Security**: Ensure secure communication with ArgoCD server
- **Test Isolation**: Tests should not affect production applications
- **Cleanup**: Tests should clean up any created resources

For more information about the ArgoCD Agent, see the main README in the argocdAgent directory. 