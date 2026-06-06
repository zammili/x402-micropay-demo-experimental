# x402 Micropay Demo — Casper Network Edition

This repository demonstrates an Agentic AI micropayment loop using HTTP `402 Payment Required`, **Casper Network Testnet** payment receipts, Casper AI Toolkit-style agent endpoints, DeFi/RWA research scenarios, and optional quantum-resistant payment commitments.

## What Changed for Casper

- **Primary payment network:** Casper Network (`casper-test` by default), not Solana.
- **Validator:** `casper_payment_validator.py` verifies Casper deploy receipts, prevents replay, checks chain name, confirms deploy status with `info_get_deploy`, and validates CSPR amount/recipient data.
- **Agents:** `translation_agent.py`, `research_agent.py`, `translation_agent_quantum.py`, and `research_agent_quantum.py` now use Casper receipt fields.
- **AI Toolkit integration:** `casper_ai_toolkit.py` exposes MCP-friendly state snapshots and CSPR.click-style payment intents.
- **DeFi/RWA:** `rwa_defi_agent.py` demonstrates RWA oracle research and DeFi protocol fee micropayment patterns.

## Casper x402 Receipt Format

Clients retry a protected request with a Casper deploy receipt in `payment_receipt`:

```json
{
  "text": "Hello world",
  "payment_receipt": {
    "deployHash": "0x...",
    "chainName": "casper-test",
    "amount": "0.001",
    "toAddress": "account-hash-...",
    "blockTime": 1780680000
  }
}
```

## Environment Variables

```bash
CASPER_RPC_URL=https://rpc.testnet.casperlabs.io
CASPER_PAYMENT_ADDRESS=account-hash-...
PRICE_CSPR=0.001
CASPER_CHAIN_NAME=casper-test
VERIFY_ONCHAIN=false
TRANSACTION_VALIDITY_WINDOW=3600
PORT=5001
```

Set `VERIFY_ONCHAIN=true` only after you have a real Casper Testnet deploy receipt and a configured recipient account.

## Quick Start

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the Casper translation service:

   ```bash
   python translation_agent.py
   ```

3. In another terminal, run the Casper research/payment agent:

   ```bash
   python research_agent.py "Text to translate"
   ```

4. Optional quantum-resistant flow:

   ```bash
   pip install -r requirements-quantum.txt
   python translation_agent_quantum.py
   AGENT_URL=http://localhost:5002 python research_agent_quantum.py "Quantum-safe Casper payment"
   ```

## Agent and API Endpoints

- `POST /translate` — returns 402 Casper payment metadata, then accepts a Casper receipt.
- `GET /health` — service health, chain, price, and verification mode.
- `GET /mcp/casper/status` — MCP-friendly Casper state for AI agents.
- `GET|POST /cspr-click/payment-intent` — CSPR.click-style native transfer signing intent.
- `GET /casper/deploy/<deploy_hash>` — Casper deploy status via `info_get_deploy`.

## DeFi/RWA Use Cases

Run the scenario demo:

```bash
python rwa_defi_agent.py
```

The demo covers:

- RWA research requests for commodities, FX rates, and carbon credits.
- Casper oracle-style data lookup patterns.
- DeFi swap fee calculation.
- x402-style CSPR fee payments to protocol/liquidity-provider accounts.

## Demo Video Checklist

A clear demo video should show:

1. Casper Testnet configuration and recipient account.
2. `translation_agent.py` returning HTTP 402 payment requirements.
3. `research_agent.py` obtaining a CSPR.click payment intent and retrying with a Casper deploy receipt.
4. `/mcp/casper/status` exposing Casper state to an AI agent.
5. `rwa_defi_agent.py` demonstrating DeFi/RWA scenarios.
6. `translation_agent_quantum.py` and `research_agent_quantum.py` showing quantum-resistant proof metadata.

## Project Structure

```text
x402-micropay-demo-experimental/
├── translation_agent.py            # Casper x402 Flask service
├── research_agent.py               # Casper payment client agent
├── casper_payment_validator.py     # Casper RPC + mock validators
├── casper_ai_toolkit.py            # MCP-friendly state + CSPR.click intents
├── translation_agent_quantum.py    # Casper + quantum-resistant service
├── research_agent_quantum.py       # Casper + quantum-resistant client
├── quantum_resistant_crypto.py     # Hybrid/PQ payment commitments
├── rwa_defi_agent.py               # DeFi/RWA scenario agent
├── solana_payment_validator.py     # Legacy reference only
├── requirements.txt
└── requirements-quantum.txt
```

## References

- Casper Network documentation: https://docs.casper.network
- Casper JSON-RPC: https://docs.casper.network/developers/json-rpc
- Odra framework: https://odra.dev
- x402 concept: HTTP `402 Payment Required`

## License

MIT License
