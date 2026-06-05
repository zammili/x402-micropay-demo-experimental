# Casper Network Integration Guide

This document provides a comprehensive guide for integrating Casper Network into the x402 Micropay Demo for the Casper Agentic Buildathon 2026.

## 🎯 Goals

1. **Migrate from Solana → Casper Network** for on-chain payment verification
2. **Leverage Casper AI Toolkit** for enhanced agent capabilities
3. **Expand DeFi/RWA Use Cases** with Casper smart contracts
4. **Optimize for Buildathon Success** with production-ready code

## 📋 Implementation Roadmap

### Phase 1: Core Casper Integration (MVP) ✅

- [x] `casper_payment_validator.py` — On-chain payment verification
- [x] Update `translation_agent.py` to support Casper receipts
- [x] Update `research_agent.py` to generate Casper deploy hashes
- [x] Environment configuration for Casper Testnet
- [x] Mock validation for local development

**Status:** Complete. The validator is ready for testing on Casper Testnet.

### Phase 2: AI Toolkit Integration (In Progress)

#### 2.1 MCP (Model Context Protocol) Servers

**Goal:** Expose Casper smart contract state to AI agents

```python
# Example: Casper MCP Server for contract state queries
from mcp import Server

server = Server()

@server.tool()
def query_smart_contract_balance(contract_hash: str, account: str) -> dict:
    """Query balance in a Casper smart contract"""
    # Implementation: Call Casper RPC to fetch contract storage
    pass

@server.tool()
def list_active_contracts() -> list:
    """List all active contracts on Casper Network"""
    pass
```

**Next Steps:**
- Define MCP interface for contract queries
- Implement Casper RPC bindings
- Test with research agent

#### 2.2 CSPR.click AI Agent Skill Integration

**Goal:** Enable wallet management and transaction signing via CSPR.click API

```python
# Example: Integrate CSPR.click for transaction signing
import cspr_click_sdk

def sign_and_submit_payment(amount: int, to_account: str) -> str:
    """
    Use CSPR.click to sign and submit a payment
    
    Args:
        amount: Amount in motes (1 CSPR = 10^9 motes)
        to_account: Recipient account hash
    
    Returns:
        Deploy hash
    """
    # Implementation
    pass
```

**Next Steps:**
- Obtain CSPR.click API credentials
- Integrate signing functionality
- Test payment flow

### Phase 3: DeFi/RWA Use Cases

#### 3.1 RWA Data Research Agent

**Goal:** Create an agent that researches Real-World Asset (RWA) data on Casper

```python
# research_agent_rwa.py
class RWAResearchAgent:
    """Agent for querying and analyzing RWA data on Casper"""
    
    def query_asset_data(self, asset_id: str) -> dict:
        """Query RWA data from on-chain contract"""
        pass
    
    def pay_for_analysis(self, analysis_result: dict) -> str:
        """Submit payment for research"""
        pass
```

**DeFi Scenarios:**
- Query asset pricing (Oracle integration)
- Validate tokenized asset ownership
- Pay for real-time market analysis

#### 3.2 DeFi Protocol Fee Automation

**Goal:** Use micropayments for protocol fees and liquidity provision

```python
# defi_agent.py
class DeFiAgent:
    """Agent for automated DeFi operations"""
    
    def calculate_protocol_fee(self, transaction_value: int) -> int:
        """Calculate fee for DeFi transaction"""
        pass
    
    def pay_liquidity_provider(self, amount: int, provider: str) -> str:
        """Pay liquidity providers via 402 mechanism"""
        pass
```

**Next Steps:**
- Deploy test Casper contracts for DeFi operations
- Implement fee calculation logic
- Test payment routing

### Phase 4: Production Optimization

- [ ] Performance benchmarking on Casper Mainnet
- [ ] Enhanced error handling and recovery
- [ ] Rate limiting and quota management
- [ ] Comprehensive logging and monitoring
- [ ] Security audit (if applicable for buildathon)

## 🔧 Setup Instructions

### 1. Environment Configuration

Create `.env.casper` based on `.env.example`:

```bash
# Casper Network
CASPER_RPC_URL=https://rpc.testnet.casperlabs.io
CASPER_PAYMENT_ADDRESS=account-hash-1234567890abcdef...
PRICE_CSPR=0.001
CASPER_CHAIN_NAME=casper-test
VERIFY_ONCHAIN=false  # Set to true for Testnet verification

# Translation Agent
PAYMENT_ADDRESS=account-hash-...  # Casper account hash (if using Casper)
PRICE_ETH=0.001  # Not used for Casper mode
VERIFY_ONCHAIN=false
PORT=5001

# Research Agent
TRANSLATE_URL=http://localhost:5001/translate
PRIVATE_KEY=... # For signing transactions (handle securely)
DRY_RUN=false  # Set to true to preview without submitting
```

### 2. Install Casper Dependencies

```bash
pip install casper-sdk httpx
```

### 3. Deploy to Testnet

```bash
# Start translation agent
CASPER_RPC_URL=https://rpc.testnet.casperlabs.io \
CASPER_PAYMENT_ADDRESS=account-hash-... \
PRICE_CSPR=0.001 \
python translation_agent.py

# In another terminal, run research agent
TRANSLATE_URL=http://localhost:5001/translate \
python research_agent.py "Test translation"
```

## 🧪 Testing Scenarios

### Scenario 1: Mock Mode (No On-Chain Calls)

```bash
# All environment defaults
# VERIFY_ONCHAIN=false (default)
python translation_agent.py
python research_agent.py "Hello"
# Expected: 200 OK with translation, no blockchain interaction
```

### Scenario 2: Testnet Verification

```bash
# Set RPC and verification
CASPER_RPC_URL=https://rpc.testnet.casperlabs.io \
VERIFY_ONCHAIN=true \
CASPER_PAYMENT_ADDRESS=account-hash-... \
python translation_agent.py

# Submit with valid Casper deploy receipt
python research_agent.py "Hello" --submit-casper-deploy <deploy-hash>
```

### Scenario 3: Rate Limiting & Quotas

```python
# TODO: Implement quota tracking
# - Per-account payment limits
# - Daily usage limits
# - Burst protection
```

## 🔐 Security Considerations

### Private Key Management

**DON'T:**
```python
# ❌ Never hardcode private keys
PRIVATE_KEY = "00abcd..."

# ❌ Never commit .env.local with real keys
git add .env.local
```

**DO:**
```python
# ✅ Use environment variables
PRIVATE_KEY = os.getenv("CASPER_PRIVATE_KEY")

# ✅ Use secure vaults
import aws_secrets_manager
key = aws_secrets_manager.get_secret("casper-key")

# ✅ Use hardware wallets
from ledger_sdk import LedgerWallet
wallet = LedgerWallet()
```

### Transaction Validation

- Always verify payment amount matches expected price
- Check recipient address explicitly
- Validate chain ID (mainnet vs testnet)
- Implement timeout for pending transactions
- Log all payment attempts for audit

## 📊 Metrics & Monitoring

**Key Metrics to Track:**

1. **Payment Success Rate:** % of successful micropayments
2. **Average Payment Time:** Time from request to confirmation
3. **Cost per Transaction:** CSPR gas costs
4. **Agent Uptime:** Translation agent availability
5. **Error Rates:** Failed validations or transactions

**Recommended Tools:**
- Prometheus for metrics collection
- Grafana for visualization
- ELK stack for logging (Elasticsearch, Logstash, Kibana)

## 📚 Resources

- [Casper Network Docs](https://docs.casper.network)
- [Casper JSON-RPC API](https://docs.casper.network/developers/json-rpc)
- [Casper Python SDK](https://github.com/casper-network/casper-python-sdk)
- [Odra Framework](https://github.com/odradev/odra)
- [HTTP 402 RFC 7231](https://tools.ietf.org/html/rfc7231#section-6.5.2)

## 🎓 Learning Path

1. **Week 1:** Understand Casper Network basics, RPC API
2. **Week 2:** Implement `casper_payment_validator.py`, test locally
3. **Week 3:** Deploy to Testnet, test payment flow
4. **Week 4:** Integrate MCP servers, build DeFi use cases
5. **Week 5:** Optimize performance, prepare for Buildathon

## 🤝 Contributing

Contributions are welcome! Focus areas:

- [ ] DeFi/RWA use case implementations
- [ ] Performance optimizations
- [ ] Enhanced error handling
- [ ] Comprehensive test coverage
- [ ] Documentation improvements

Submit issues and PRs to discuss improvements!

## ❓ FAQ

**Q: Can I use this with Casper Mainnet?**
A: Yes! Update `CASPER_RPC_URL` to mainnet endpoint. Be cautious with real funds.

**Q: What's the payment latency?**
A: ~30-60 seconds for Casper finality. Configure `TRANSACTION_VALIDITY_WINDOW` as needed.

**Q: Can I use multiple payment validators simultaneously?**
A: Yes, implement a router in the agent to select validator based on chain config.

**Q: How do I handle failed payments?**
A: Research agent retries up to 3 times (configurable). Add exponential backoff.

---

**Last Updated:** June 2026  
**For:** Casper Agentic Buildathon 2026
