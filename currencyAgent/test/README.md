# Currency Agent Test Suite

This directory contains tests for the Currency Agent, which provides real-time currency exchange rates and financial data analysis.

## Prerequisites

Before running tests, ensure you have:

1. **Dependencies Installed**:
   ```bash
   cd currencyAgent
   uv sync
   ```

2. **API Keys** (if required):
   - Some currency APIs may require API keys
   - Check the main agent configuration for specific requirements

## Test Files Overview

### 💰 Core Functionality Tests

#### `test_client.py`
- **Purpose**: Comprehensive currency agent functionality test
- **What it tests**: Currency exchange operations and financial data
- **Run**: `uv run python test/test_client.py`
- **Features tested**:
  - Currency conversion rates
  - Multi-currency support
  - Real-time exchange data
  - Financial calculations
  - Error handling for invalid currencies

## Running Tests

### Quick Test
```bash
# From currencyAgent directory
uv run python test/test_client.py
```

### With Currency Agent Running
```bash
# Terminal 1: Start Currency Agent
cd currencyAgent
uv run app

# Terminal 2: Run tests
cd currencyAgent
uv run python test/test_client.py
```

## Test Dependencies

### Required Services
- **Currency Agent**: Should be running on `localhost:8002` for integration tests
- **Internet Connection**: Required for real-time currency data

### External APIs
- Tests may use public currency exchange APIs
- Rate limiting may apply to external API calls

## Expected Outputs

### Successful Test Examples

**Currency Conversion**:
```
💰 Testing currency conversion: USD to EUR
📊 Result: 1 USD = 0.85 EUR
```

**Multi-Currency Support**:
```
✅ Supported currencies: USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY
```

## Troubleshooting

### Common Issues

1. **Network Connection**:
   ```
   Error: Unable to fetch exchange rates
   ```
   **Solution**: Check internet connection and API availability

2. **Invalid Currency**:
   ```
   Error: Currency code 'XYZ' not supported
   ```
   **Solution**: Use valid ISO currency codes (USD, EUR, GBP, etc.)

3. **Rate Limiting**:
   ```
   Error: API rate limit exceeded
   ```
   **Solution**: Wait before retrying or use different API endpoints

### Debug Steps

1. **Check Currency Agent Status**:
   ```bash
   curl http://localhost:8002/.well-known/agent.json
   ```

2. **Test API Endpoints**:
   ```bash
   curl "https://api.exchangerate-api.com/v4/latest/USD"
   ```

## Test Coverage

- ✅ **Currency Conversion**: USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY
- ✅ **Real-time Rates**: Live exchange rate fetching
- ✅ **Error Handling**: Invalid currencies, network failures
- ✅ **Financial Calculations**: Multi-currency operations
- ✅ **Agent Integration**: A2A protocol communication

## Performance Notes

- **API Calls**: Tests make real API calls which may be slow
- **Rate Limiting**: External APIs may have usage limits
- **Caching**: Some exchange rates may be cached for performance

For more information about the Currency Agent, see the main README in the currencyAgent directory. 