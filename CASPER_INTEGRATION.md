# Casper Network Integration Guide

This guide documents the migration of the x402 micropayment demo to **Casper Network Testnet**.

## Completed Migration Items

- `translation_agent.py` uses Casper payment metadata and validates Casper receipts.
- `research_agent.py` performs the x402 retry loop with Casper deploy receipt fields.
- `casper_payment_validator.py` supports mock validation and Casper JSON-RPC `info_get_deploy` checks.
- `casper_ai_toolkit.py` provides MCP-friendly Casper status snapshots and CSPR.click-style payment intents.
- `translation_agent_quantum.py` and `research_agent_quantum.py` bind quantum-resistant commitments to Casper deploy hashes.
- `rwa_defi_agent.py` demonstrates Casper-oriented DeFi/RWA research and protocol fee flows.

## Casper Testnet Configuration

```bash
CASPER_RPC_URL=https://rpc.testnet.casperlabs.io
CASPER_CHAIN_NAME=casper-test
CASPER_PAYMENT_ADDRESS=account-hash-...
PRICE_CSPR=0.001
VERIFY_ONCHAIN=false
TRANSACTION_VALIDITY_WINDOW=3600
```

Use `VERIFY_ONCHAIN=false` for local demos. Use `VERIFY_ONCHAIN=true` when the receipt references a real successful Casper Testnet deploy.

## Receipt Validation Flow

1. The protected service returns HTTP 402 with `paymentNetwork=casper`.
2. The client obtains a wallet-signing intent from `/cspr-click/payment-intent`.
3. The client submits/signs a native Casper transfer or Odra contract deploy.
4. The client retries with `payment_receipt.deployHash`, `chainName`, `amount`, `toAddress`, and `blockTime`.
5. The validator checks replay, chain name, deploy success, amount, recipient, and age.

## AI Toolkit Integration

### MCP-Friendly Status

`GET /mcp/casper/status` returns:

- chain name and RPC URL,
- configured contract/account hashes,
- current x402 CSPR price,
- verification mode,
- optional account data when on-chain verification is enabled.

This endpoint can be wrapped by a Casper MCP server so AI agents can query payment and smart-contract state.

### CSPR.click Intent

`GET|POST /cspr-click/payment-intent` returns a native-transfer intent with recipient, amount in CSPR/motes, chain name, memo, and receipt fields expected by the x402 retry.

## Odra Smart Contract Path

For a production Casper build, implement the payment policy as an Odra smart contract that:

- records paid service invocations,
- prevents receipt replay at contract level,
- emits events for AI/MCP observers,
- supports DeFi/RWA tier pricing or escrow rules.

The current Python validator is intentionally compatible with native transfer deploys first, while leaving the deploy/contract status endpoint ready for Odra contract hashes.

## DeFi/RWA Scenarios

- RWA research agent pays for commodity, FX, and carbon-credit oracle data.
- DeFi fee agent calculates protocol fees and routes CSPR micropayments.
- Future Odra contracts can enforce fee splits, liquidity-provider settlement, and RWA data freshness.

## Demo Video Script

1. Show the Casper Testnet `.env` values.
2. Start `python translation_agent.py`.
3. Call `/translate` without payment and show the HTTP 402 Casper metadata.
4. Run `python research_agent.py "Casper x402 demo"` and show successful retry.
5. Open `/mcp/casper/status` and `/cspr-click/payment-intent`.
6. Run `python rwa_defi_agent.py`.
7. Run the quantum service/client pair to highlight quantum-resistant commitments.
