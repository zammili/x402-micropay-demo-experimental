# x402 Micropay Demo (AI Agent Economy) — Casper Network Edition

This project demonstrates a machine-to-machine micropayment loop using HTTP `402 Payment Required` and **Casper Network** payments, with AI-powered agents for translation and research tasks.

## 🎯 Overview

- **`translation_agent.py`** — Flask server providing translation services, requires payment via 402 Payment Required (Casper Network or mock).
- **`research_agent.py`** — Client agent that requests translations and automatically pays when receiving 402 status.
- **`casper_payment_validator.py`** — Casper Network on-chain payment validation with replay attack prevention.

## 🌐 Casper Network Integration

This project has been adapted to run on **Casper Network** (Testnet by default). Key components:

### Payment Receipt Format (Casper)

The research agent sends a full Casper deploy receipt in the retry request JSON under the `payment_receipt` key:

```json
{
  "text": "Hello world",
  "payment_receipt": {
    "deployHash": "0x...",
    "chainName": "casper-test",
    "amount": 1000000000,
    "blockTime": 1717699200,
    "toAddress": "account-hash-..."
  }
}
```

### Environment Variables (Casper Mode)

```bash
# Casper RPC endpoint
CASPER_RPC_URL=https://rpc.testnet.casperlabs.io

# Payment recipient address (Casper account hash)
CASPER_PAYMENT_ADDRESS=account-hash-...

# Price in CSPR (Casper tokens)
PRICE_CSPR=0.001

# Chain identifier
CASPER_CHAIN_NAME=casper-test
```

## 🚀 Quick Start (Local, Mock Mode)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the translation agent:**
   ```bash
   python translation_agent.py
   ```

3. **In another terminal, run the research agent:**
   ```bash
   python research_agent.py "Text to translate"
   ```

## 🧪 Testing & Validation

### Run Unit Tests

```bash
pytest -q
```

### Test with Docker Compose

```bash
# Copy environment template
cp .env.example .env

# Start services
docker-compose up --build
```

### Casper Testnet Integration

For on-chain verification on Casper Testnet:

1. Set `VERIFY_ONCHAIN=true` in `.env`
2. Configure `CASPER_RPC_URL` pointing to Casper Testnet
3. Set `CASPER_PAYMENT_ADDRESS` to your Casper account hash
4. Set `PRICE_CSPR` to desired amount

## 🔐 Security

- **Replay Attack Prevention:** Both mock and on-chain validators prevent transaction replay
- **Network Validation:** Ensures transactions are on the correct Casper chain
- **Timestamp Validation:** Verifies transaction recency (configurable window)
- **Amount Verification:** Validates sufficient payment received
- **Private Key Safety:** Never commit `.env.local` or private keys to version control

### Best Practices

- Keep `VERIFY_ONCHAIN=false` while developing to avoid accidental on-chain transactions
- Use test networks (Casper Testnet) before mainnet
- Store private keys securely (e.g., AWS Secrets Manager, HashiCorp Vault)
- Implement rate limiting on `/translate` endpoint for production

## 📚 Architecture

### Agent Components

1. **Translation Agent** (`translation_agent.py`)
   - Flask HTTP server
   - Listens on `/translate` POST endpoint
   - Validates payment receipts before processing
   - Responds with 402 Payment Required if no valid receipt

2. **Research Agent** (`research_agent.py`)
   - HTTP client that initiates translation requests
   - Captures 402 responses with payment metadata
   - Initiates Casper payment transaction
   - Retries with payment receipt

3. **Payment Validators**
   - `casper_payment_validator.py` — Casper Network on-chain verification
   - `solana_payment_validator.py` — Legacy Solana support (optional)
   - Mock validators for local testing

### Smart Contract Integration (Future)

For advanced use cases, deploy Casper smart contracts to:
- Automate payment splitting
- Implement tiered pricing based on RWA data
- Enable escrow-like functionality for complex transactions

## 🤖 AI Toolkit Integration (Roadmap)

- **MCP Servers:** Expose Casper smart contract state to AI agents
- **CSPR.click AI Agent Skill:** Leverage wallet management and transaction signing
- **DeFi/RWA Agents:** Research agents can query on-chain RWA data via Casper

## 🛠️ Development

### Project Structure

```
x402-micropay-demo-experimental/
├── translation_agent.py          # Translation service (Flask)
├── research_agent.py             # Research/payment client
├── casper_payment_validator.py   # Casper Network validator
├── solana_payment_validator.py   # Legacy Solana validator
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Local deployment
├── .env.example                  # Template environment variables
└── web/                          # Optional Next.js frontend
```

### Adding New Agents

1. Create agent file (e.g., `your_agent.py`)
2. Import payment validator: `from casper_payment_validator import validate_receipt_onchain_casper`
3. Implement payment retry logic with receipt submission

## 📖 References

- [Casper Network Documentation](https://docs.casper.network)
- [Casper RPC JSON-RPC Specification](https://docs.casper.network/developers/json-rpc)
- [Casper Python SDK](https://github.com/casper-network/casper-python-sdk)
- [HTTP 402 Payment Required RFC](https://tools.ietf.org/html/rfc7231#section-6.5.2)

## 📄 LICENSE

MIT License

Copyright (c) 2026 zammili

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

## 🤝 Contributing

See `CONTRIBUTING.md` for guidelines on submitting issues and pull requests.

### For Casper Agentic Buildathon 2026

This project is optimized for the Casper Agentic Buildathon. Contributions focusing on:
- Enhanced DeFi/RWA use cases
- AI agent improvements
- Casper smart contract integration
- Performance optimizations

...are especially welcomed!
