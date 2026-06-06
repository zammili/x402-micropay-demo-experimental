# Casper Testnet Testing Guide

Panduan komprehensif untuk menguji implementasi x402 Micropay Demo di Casper Testnet.

## 📋 Prerequisites

### 1. Setup Environment

```bash
# Clone repository (jika belum)
git clone https://github.com/zammili/x402-micropay-demo-experimental.git
cd x402-micropay-demo-experimental

# Create Casper-specific environment
cp .env.casper.example .env.casper

# Install Python dependencies
pip install flask httpx requests
```

### 2. Get Casper Testnet Account

- Buka [Casper Testnet Faucet](https://testnet.cspr.live/tools/faucet)
- Request testnet CSPR tokens
- Catat account hash Anda (format: `account-hash-1234...`)

### 3. Update Configuration

Edit `.env.casper`:

```bash
# Set your Casper account
CASPER_PAYMENT_ADDRESS=account-hash-<your-account-hash>

# Testnet RPC (default sudah benar)
CASPER_RPC_URL=https://rpc.testnet.casperlabs.io

# Mulai dengan mock mode
VERIFY_ONCHAIN=false
DRY_RUN=true
```

## 🧪 Phase 1: Mock Testing (Local)

### Test 1.1: Translation Agent Startup

```bash
# Terminal 1: Start translation agent (mock mode)
VERIFY_ONCHAIN=false PORT=5001 python translation_agent_casper.py
```

**Expected Output:**
```
2026-06-06 10:00:00 INFO Starting Casper translation agent on port 5001
2026-06-06 10:00:00 INFO Network: casper-test | Verify OnChain: False | Price: 0.001 CSPR
```

### Test 1.2: Research Agent Without Payment

```bash
# Terminal 2: Request translation (no payment)
python research_agent_casper.py "Hello world"
```

**Expected Behavior:**
- Agent receives 402 Payment Required
- Extracts payment metadata
- Simulates Casper payment
- Retries with payment receipt
- Receives translation

**Expected Output:**
```
2026-06-06 10:01:00 INFO Requesting translation: 'Hello world'
2026-06-06 10:01:00 INFO Payment required. Processing...
2026-06-06 10:01:00 INFO [DRY RUN] Simulated Casper payment deploy: aaaa...
2026-06-06 10:01:01 INFO Retrying translation with payment receipt...
2026-06-06 10:01:01 INFO ✅ Translation (no payment): Terjemahan: Hello world (Diterjemahkan via x402 + Casper)
```

### Test 1.3: Replay Attack Prevention

```bash
# Terminal 2: Submit same payment twice
python research_agent_casper.py "Test replay"
python research_agent_casper.py "Test replay"  # Should fail
```

**Expected Behavior:**
- First request: Success (200)
- Second request: Rejected (402) - deploy hash sudah di-cache

### Test 1.4: Health Check Endpoint

```bash
curl http://localhost:5001/health
```

**Expected Response:**
```json
{
  "ok": true,
  "network": "casper-test",
  "verify_onchain": false,
  "payment_address": "account-hash-...",
  "price_cspr": "0.001"
}
```

### Test 1.5: Configuration Endpoint

```bash
curl http://localhost:5001/config
```

## 🌐 Phase 2: Casper Testnet Integration

### Test 2.1: Enable On-Chain Verification

```bash
# Update .env.casper
VERIFY_ONCHAIN=true
DRY_RUN=false

# Start agent
python translation_agent_casper.py
```

### Test 2.2: Generate Real Casper Deploy

Implementasi di `research_agent_casper.py` untuk menggunakan Casper SDK:

```python
# TODO: Implement using casper-python-sdk
# Contoh flow:
# 1. Import Casper SDK
# 2. Create deploy untuk transfer CSPR
# 3. Sign dengan private key
# 4. Submit ke RPC
# 5. Poll untuk konfirmasi
```

**Manual Testing (jika SDK belum tersedia):**

```bash
# Gunakan Casper CLI untuk generate deploy
casper-client put-deploy \
  --node-address http://rpc.testnet.casperlabs.io:7777 \
  --secret-key <path-to-secret-key> \
  --session-path <path-to-wasm> \
  --payment-amount 5000000000
```

### Test 2.3: Verify On-Chain Payment

```bash
# Check deploy status
curl -X POST http://rpc.testnet.casperlabs.io:7777 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "info_get_deploy",
    "params": {"deploy_hash": "0x<deploy-hash>"},
    "id": 1
  }'
```

## 🤖 Phase 3: MCP Server Testing

### Test 3.1: Initialize MCP Server

```bash
# Terminal 3: Start MCP server
python casper_mcp_server.py
```

**Expected Output:**
```
2026-06-06 10:02:00 INFO Initializing Casper MCP Server
2026-06-06 10:02:00 INFO Available tools:
  - query_account_balance: Query account balance and main purse from Casper network
  - query_contract_state: Query smart contract state from Casper
  - query_rwa_data: Query Real-World Asset data from Casper oracle
  - query_defi_pool: Query DeFi liquidity pool information
  - list_active_rwa_contracts: List all active Real-World Asset contracts on Casper
  - subscribe_to_contract_events: Subscribe to smart contract events for real-time monitoring
```

### Test 3.2: Query Account Balance

```python
# Python client
from casper_mcp_server import CasperMCPServer

server = CasperMCPServer()
result = server.call_tool("query_account_balance", 
                         account_hash="account-hash-...")
print(result)
```

### Test 3.3: List RWA Contracts

```python
result = server.call_tool("list_active_rwa_contracts")
print(result)
```

## 💰 Phase 4: RWA/DeFi Agent Testing

### Test 4.1: DeFi Fee Calculation

```bash
python rwa_defi_agent.py
```

**Expected Output:**
```
2026-06-06 10:03:00 INFO RWA/DeFi Agent for x402 Micropay Demo
2026-06-06 10:03:00 INFO === DeFi Swap Simulation ===
2026-06-06 10:03:00 INFO [DRY RUN] Would pay protocol fee: 0.003000 CSPR
2026-06-06 10:03:01 INFO === RWA Research Simulation ===
2026-06-06 10:03:01 INFO Querying RWA data: type=commodity_price, identifier=GOLD/USD
2026-06-06 10:03:01 INFO Research data retrieved: GOLD/USD = 1234.56
```

### Test 4.2: Real DeFi Integration

```bash
# Enable real payment
DRY_RUN=false python rwa_defi_agent.py
```

## ✅ Test Checklist

### Mock Mode (Phase 1)
- [ ] Translation agent starts successfully
- [ ] Health endpoint responds correctly
- [ ] Research agent receives 402 payment required
- [ ] Payment simulation succeeds
- [ ] Replay attack prevention works
- [ ] Translation with payment succeeds
- [ ] Config endpoint shows correct settings

### Testnet Mode (Phase 2)
- [ ] On-chain verification enabled
- [ ] Casper RPC connection successful
- [ ] Deploy can be submitted to testnet
- [ ] Deploy status can be queried
- [ ] Payment validation succeeds on-chain
- [ ] Insufficient payment rejected correctly

### MCP Server (Phase 3)
- [ ] MCP server initializes
- [ ] All tools registered successfully
- [ ] Account balance queries work
- [ ] RWA contract listing works
- [ ] DeFi pool queries return correct data

### RWA/DeFi (Phase 4)
- [ ] RWA data queries return correct format
- [ ] Fee calculation accurate
- [ ] DeFi operations can be simulated
- [ ] Payment routing works correctly

## 🐛 Troubleshooting

### Issue: "httpx not available"

```bash
pip install httpx
```

### Issue: "Connection refused" on RPC

```bash
# Verify RPC URL is correct
CASPER_RPC_URL=https://rpc.testnet.casperlabs.io python translation_agent_casper.py

# Check network connectivity
curl https://rpc.testnet.casperlabs.io
```

### Issue: "Invalid account hash"

```bash
# Verify format
echo "account-hash-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd" | wc -c
# Should be 85 characters (including "account-hash-" prefix)
```

### Issue: Deploy not found

```bash
# Wait for finality (30-60 seconds on testnet)
# Check deploy hash format (should be 64 hex chars)
# Verify deploy was actually submitted to testnet
```

## 📊 Performance Benchmarks

Target metrics untuk Casper Testnet:

| Metric | Target | Status |
|--------|--------|--------|
| Payment latency | < 60s | 🔄 Testing |
| Deploy confirmation | 30-45s | 🔄 Testing |
| MCP query response | < 1s | 🔄 Testing |
| Replay attack prevention | 100% | ✅ Verified |
| RWA data freshness | < 5min | 🔄 Testing |

## 🚀 Next Steps

### Short-term (Week 1-2)
1. ✅ Complete Phase 1 mock testing
2. 🔄 Integrate Casper Python SDK
3. 🔄 Deploy to Testnet and verify
4. 🔄 Test MCP server with agents

### Medium-term (Week 3-4)
1. Develop Casper smart contracts untuk DeFi/RWA
2. Implement CSPR.click integration
3. Enhanced error handling dan recovery
4. Performance optimization

### Long-term (Week 5+)
1. Mainnet compatibility testing
2. Security audit
3. Production deployment
4. Advanced features (staking, governance)

## 📚 References

- [Casper Testnet Faucet](https://testnet.cspr.live/tools/faucet)
- [Casper RPC Documentation](https://docs.casper.network/developers/json-rpc)
- [Casper Python SDK](https://github.com/casper-network/casper-python-sdk)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io)

## 💬 Support

Untuk pertanyaan atau issues:
- Buka issue di GitHub repository
- Konsultasi dokumentasi Casper
- Bergabung dengan Casper Discord community

---

**Last Updated:** June 2026  
**For:** Casper Agentic Buildathon 2026
