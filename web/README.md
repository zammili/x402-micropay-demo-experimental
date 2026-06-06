# Casper x402 Web Frontend

This Next.js app is a lightweight dashboard for the Casper x402 micropayment demo.

## Features

- Casper Testnet-oriented landing page.
- `POST /api/verify` endpoint that verifies a Casper `deployHash` with `info_get_deploy`.
- In-memory replay protection using `PROOF_TTL`.

## Environment

```bash
CASPER_RPC_URL=https://rpc.testnet.casperlabs.io
PROOF_TTL=3600
```

## Run

```bash
pnpm install
pnpm dev
```
