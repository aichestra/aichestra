# Orchestrator Client Test Suite

This directory contains tests for the A2A Orchestrator Client, which provides command-line interface for interacting with A2A agents and listening to push notifications.

## Prerequisites

Before running tests, ensure you have:

1. **Dependencies Installed**:
   ```bash
cd orchestrator_client
uv sync
```

2. **Agent Services Running** (for integration tests):
   - **Orchestrator**: `localhost:8000` (recommended entry point)
   - **Individual Agents**: ArgoCD (8001), Currency (8002), Math (8003)

## Test Files Overview

### 📱 Push Notification Tests

#### `push_notification_listener.py`
- **Purpose**: Test push notification functionality and real-time updates
- **What it tests**: WebSocket connections, notification handling, message parsing
- **Run**: `uv run python test/push_notification_listener.py`
- **Features tested**:
  - WebSocket connection establishment
  - Push notification subscription
  - Real-time message receiving
  - Notification parsing and display
  - Connection resilience and reconnection

## Running Tests

### Push Notification Test
```bash
# From orchestrator_client directory
uv run python test/push_notification_listener.py
```

### Integration Test (with services running)
```bash
# Terminal 1: Start Orchestrator
cd orchestrator && uv run app

# Terminal 2: Start Client Push Notification Listener
cd orchestrator_client
uv run python test/push_notification_listener.py

# Terminal 3: Send test messages (optional)
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"message/send","params":{"id":"test","message":{"role":"user","messageId":"msg1","contextId":"ctx1","parts":[{"type":"text","text":"what is 2+3"}]},"configuration":{"acceptedOutputModes":["text"]}}}'
```

## Test Dependencies

### Required Services
- **A2A Agents**: Any running A2A-compatible agent for push notifications
- **WebSocket Support**: Agents must support push notification WebSocket endpoints

### Network Requirements
- **WebSocket Connection**: Agents must expose WebSocket endpoints
- **Real-time Communication**: Low-latency network connection recommended

## Expected Outputs

### Successful Test Examples

**WebSocket Connection**:
```
📱 Testing Push Notification Listener
🔗 Connecting to WebSocket: ws://localhost:8000/notifications
✅ Connected successfully
```

**Notification Receiving**:
```
📨 Received notification:
  Type: message_response
  Context: ctx1
  Message: The answer is 5
  Timestamp: 2024-01-15T10:30:00Z
```

**Connection Management**:
```
🔄 Connection lost, attempting reconnection...
⏳ Reconnecting in 5 seconds...
✅ Reconnected successfully
```

## Test Coverage

### 🔗 Connection Management
- **WebSocket Establishment**: Initial connection setup
- **Authentication**: Token-based authentication if required
- **Heartbeat**: Keep-alive mechanism testing
- **Reconnection**: Automatic reconnection on failure

### 📨 Notification Handling
- **Message Parsing**: JSON message deserialization
- **Type Filtering**: Different notification types
- **Context Tracking**: Message context and threading
- **Error Handling**: Malformed message handling

### 🔄 Real-time Features
- **Live Updates**: Real-time message streaming
- **Buffering**: Message queuing during disconnection
- **Ordering**: Message sequence preservation
- **Filtering**: Selective notification subscription

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**:
   ```
   Error: Connection refused to ws://localhost:8000/notifications
   ```
   **Solution**: Ensure target agent is running and supports WebSocket notifications

2. **Authentication Required**:
   ```
   Error: 401 Unauthorized
   ```
   **Solution**: Provide valid authentication token or credentials

3. **Connection Drops**:
   ```
   Warning: WebSocket connection lost
   ```
   **Solution**: Check network stability and implement reconnection logic

4. **Message Parsing Error**:
   ```
   Error: Invalid JSON in notification
   ```
   **Solution**: Verify agent sends properly formatted JSON messages

### Debug Steps

1. **Test WebSocket Endpoint**:
   ```bash
   # Using websocat (install with: cargo install websocat)
   websocat ws://localhost:8000/notifications
   ```

2. **Check Agent WebSocket Support**:
   ```bash
   curl -I http://localhost:8000/notifications
   ```

3. **Monitor Network Traffic**:
   ```bash
   # Using tcpdump to monitor WebSocket traffic
   tcpdump -i lo0 port 8000
   ```

## Performance Notes

- **Connection Overhead**: WebSocket connections have minimal overhead
- **Message Throughput**: Can handle high-frequency notifications
- **Memory Usage**: Minimal memory footprint for notification handling
- **Latency**: Real-time delivery with <100ms typical latency

## Security Considerations

- **Authentication**: Use secure tokens for WebSocket authentication
- **Encryption**: Use WSS (WebSocket Secure) for production
- **Origin Validation**: Verify allowed origins for WebSocket connections
- **Rate Limiting**: Implement client-side rate limiting

## Client Integration

The push notification listener is part of the broader client functionality:

### Related Client Commands
```bash
# Interactive client mode
uv run .

# Direct agent communication
uv run . --agent http://localhost:8003 "what is 2+3"

# Push notification monitoring
uv run . --listen
```

### Configuration
- **Default Endpoints**: Configurable agent endpoints
- **Authentication**: Token storage and management
- **Logging**: Configurable log levels and output

For more information about the client architecture and usage, see the main README in the orchestrator_client directory. 