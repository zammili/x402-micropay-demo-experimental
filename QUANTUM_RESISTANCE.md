# Quantum-Resistant Casper Payments

The quantum extension binds a post-quantum/hybrid cryptographic commitment to a **Casper deploy hash**, CSPR amount in **motes**, recipient account hash, and timestamp.

## Components

- `quantum_resistant_crypto.py` — creates and verifies hybrid/PQ payment proofs.
- `translation_agent_quantum.py` — Casper x402 service with optional quantum proof verification.
- `research_agent_quantum.py` — Casper client that creates a mock Casper receipt and quantum proof for local demos.

## Algorithms

- ML-KEM-768 when `liboqs` is available.
- Classical fallback using secure random keys and HMAC-style signatures.
- SHA-256 + BLAKE2b double hashing for payment commitments.

## Run Locally

```bash
pip install -r requirements-quantum.txt
python translation_agent_quantum.py
AGENT_URL=http://localhost:5002 python research_agent_quantum.py "Quantum-safe Casper x402"
```

## Casper Commitment Fields

```json
{
  "deployHash": "0x...",
  "amountMotes": "1000000",
  "paymentAddress": "account-hash-...",
  "chainName": "casper-test"
}
```

The on-chain receipt is still validated by `casper_payment_validator.py`; the quantum proof adds a cryptographic commitment layer over the same Casper payment evidence.
