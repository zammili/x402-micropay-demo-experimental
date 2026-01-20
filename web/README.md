# Next.js Mini-App for x402 Micropay Demo

This is a Next.js application built with TypeScript and Tailwind CSS, serving as a client-side interface for the x402 Micropay Demo. It integrates **OnchainKit** for wallet connection and identity, and provides a serverless API endpoint for on-chain transaction verification.

## Features

*   **OnchainKit Integration:** Connects to Coinbase Smart Wallet and displays on-chain identity (Avatar, Name, Address, Balance).
*   **Server-Side Verification:** A Next.js API route (`/api/verify`) to check transaction status on-chain using Viem.
*   **Proof Caching:** Implements a time-to-live (TTL) cache for transaction proofs to reduce RPC calls and improve performance.

## Getting Started

### 1. Environment Variables

Create a `.env.local` file in the root of the `web` directory based on the provided `.env.example`.

```bash
cp .env.example .env.local
```

| Variable | Description | Required |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_ONCHAINKIT_API_KEY` | API Key from Coinbase Developer Platform for OnchainKit. | No (Recommended) |
| `PROOF_TTL` | Time-To-Live for the server-side proof cache in seconds. Default is 3600 (1 hour). | No |

### 2. Installation

Navigate to the `web` directory and install dependencies:

```bash
cd web
pnpm install
```

### 3. Running the App

```bash
pnpm run dev
```

The application will be available at `http://localhost:3000`.

## Server-Side Verification Endpoint

The endpoint `/api/verify` handles transaction proof verification.

**Endpoint:** `POST /api/verify`

**Request Body:**

```json
{
  "transactionHash": "0x..."
}
```

**Response Body (Verified):**

```json
{
  "verified": true,
  "source": "on-chain" | "cache",
  "blockNumber": "123456" // or expiresIn: 1234 (if from cache)
}
```

The server uses an in-memory cache with a default TTL of 1 hour (configurable via `PROOF_TTL`) to prevent redundant on-chain lookups for the same transaction hash.
