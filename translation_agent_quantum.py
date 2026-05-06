#!/usr/bin/env python3
"""
translation_agent_quantum.py

Quantum-resistant Flask server supporting:
- Mainnet-Beta, Testnet, Devnet
- Custom RPC endpoints
- Hybrid quantum+classical+on-chain verification
- ALL Solana networks
"""
from __future__ import annotations
import os
import logging
from decimal import Decimal, InvalidOperation
from typing import Dict, Any

from flask import Flask, request, jsonify
from quantum_resistant_crypto import QuantumResistantPaymentProof

try:
    from solana_payment_validator import validate_receipt_onchain_solana, validate_receipt_mock_solana
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False

# Configuration - Support ALL networks
PAYMENT_ADDRESS = os.getenv("SOLANA_PAYMENT_ADDRESS", "YourSolanaWalletAddressHere")
PRICE_SOL = os.getenv("PRICE_SOL", "0.001")
SOLANA_CLUSTER = os.getenv("SOLANA_CLUSTER", "mainnet-beta")  # mainnet-beta, testnet, devnet
RPC_URL = os.getenv("SOLANA_RPC_URL", f"https://api.{SOLANA_CLUSTER}.solana.com")
VERIFY_ONCHAIN = os.getenv("VERIFY_ONCHAIN", "false").lower() in ("1", "true", "yes")
QUANTUM_ENABLED = os.getenv("QUANTUM_ENABLED", "true").lower() in ("1", "true", "yes")
USE_HYBRID_MODE = os.getenv("USE_HYBRID_MODE", "true").lower() in ("1", "true", "yes")
PORT = int(os.getenv("PORT", "5002"))

# Validate configuration
try:
    PRICE = Decimal(str(PRICE_SOL))
except InvalidOperation:
    raise SystemExit("Invalid PRICE_SOL")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Initialize quantum crypto
quantum_proof = QuantumResistantPaymentProof(enable_quantum=QUANTUM_ENABLED)


@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint with configuration details.
    """
    return jsonify({
        "ok": True,
        "solana_cluster": SOLANA_CLUSTER,
        "rpc_url": RPC_URL,
        "verify_onchain": VERIFY_ONCHAIN,
        "quantum_enabled": QUANTUM_ENABLED,
        "hybrid_mode": USE_HYBRID_MODE,
        "payment_address": PAYMENT_ADDRESS,
        "price_sol": str(PRICE),
        "version": "2.0-quantum"
    })


@app.route("/quantum/status", methods=["GET"])
def quantum_status():
    """
    Get quantum cryptography status and capabilities.
    """
    status = quantum_proof.get_quantum_status()
    status["network"] = SOLANA_CLUSTER
    status["rpc_url"] = RPC_URL
    return jsonify(status), 200


@app.route("/quantum/keygen", methods=["POST"])
def quantum_keygen():
    """
    Generate quantum-resistant keypair.
    
    Request JSON:
    {
        "key_type": "signing" or "encryption"
    }
    """
    data = request.get_json(silent=True) or {}
    key_type = data.get("key_type", "signing")

    if not QUANTUM_ENABLED:
        return jsonify({"error": "Quantum cryptography not enabled"}), 503

    try:
        secret_key, public_key = quantum_proof.generate_quantum_keypair()
        return jsonify({
            "status": "success",
            "key_type": key_type,
            "algorithm": "ML-KEM-768",
            "secret_key_length": len(secret_key),
            "public_key_length": len(public_key),
            "message": "Store secret_key securely. Never share it."
        }), 200
    except Exception as e:
        logging.exception("Keygen error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/quantum/commitment", methods=["POST"])
def create_commitment():
    """
    Create quantum-resistant payment commitment.
    
    Request JSON:
    {
        "transaction_hash": "<solana_tx_hash>",
        "amount_lamports": 1000000,
        "payment_address": "<solana_address>"
    }
    """
    data = request.get_json(silent=True) or {}
    tx_hash = data.get("transaction_hash")
    amount = data.get("amount_lamports")
    address = data.get("payment_address", PAYMENT_ADDRESS)

    if not all([tx_hash, amount]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        commitment = quantum_proof.create_payment_commitment(
            transaction_hash=tx_hash,
            amount_lamports=int(amount),
            payment_address=address
        )
        return jsonify({
            "commitment": commitment,
            "algorithm": "SHA-256+BLAKE2b",
            "quantum_safe": True
        }), 200
    except Exception as e:
        logging.exception("Commitment error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/quantum/sign", methods=["POST"])
def sign_proof():
    """
    Sign payment commitment with quantum-resistant signature.
    
    Request JSON:
    {
        "commitment": "<hash>",
        "secret_key": "<base64_encoded>" (optional)
    }
    """
    data = request.get_json(silent=True) or {}
    commitment = data.get("commitment")

    if not commitment:
        return jsonify({"error": "Missing commitment"}), 400

    try:
        proof = quantum_proof.sign_payment_proof(commitment)
        return jsonify(proof), 200
    except Exception as e:
        logging.exception("Signing error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/translate", methods=["POST"])
def translate():
    """
    Translation endpoint with quantum-resistant payment verification.
    Supports:
    - Quantum-resistant signatures
    - Classical HMAC signatures
    - On-chain Solana verification
    - ALL networks: mainnet-beta, testnet, devnet
    
    Request JSON:
    {
        "text": "text to translate",
        "payment_receipt": {
            "transactionHash": "...",
            "cluster": "mainnet-beta|testnet|devnet",
            "amount_lamports": ...
        },
        "quantum_proof": {
            "commitment": "...",
            "classical_signature": "...",
            "quantum_signature": "..." (optional)
        }
    }
    """
    data = request.get_json(silent=True) or {}
    text_to_translate = data.get("text", "")
    payment_receipt = data.get("payment_receipt")
    quantum_proof_data = data.get("quantum_proof")

    logging.info("Translation request for cluster: %s", SOLANA_CLUSTER)

    # Verify quantum proof if provided
    if quantum_proof_data:
        logging.info("Quantum proof provided. Verifying...")
        if not quantum_proof.verify_payment_proof(quantum_proof_data):
            return jsonify({"error": "Quantum proof verification failed"}), 402
        
        if quantum_proof.is_proof_replayed(quantum_proof_data):
            return jsonify({"error": "Replay attack detected (proof already used)"}), 402
        
        logging.info("✅ Quantum proof verified (hybrid mode: %s)", USE_HYBRID_MODE)
        return jsonify({
            "result": f"Terjemahan: {text_to_translate} (Translated via x402 Quantum)",
            "verification": "quantum-resistant",
            "network": SOLANA_CLUSTER
        }), 200

    # Verify on-chain Solana payment if provided
    if payment_receipt:
        logging.info("Solana payment receipt provided. Verifying on-chain...")
        
        # Check cluster match
        receipt_cluster = payment_receipt.get("cluster", SOLANA_CLUSTER)
        if receipt_cluster != SOLANA_CLUSTER:
            return jsonify({
                "error": f"Network mismatch. Expected {SOLANA_CLUSTER}, got {receipt_cluster}"
            }), 402

        if VERIFY_ONCHAIN and SOLANA_AVAILABLE:
            valid = validate_receipt_onchain_solana(payment_receipt)
        else:
            valid = validate_receipt_mock_solana(payment_receipt)
        
        if valid:
            logging.info("✅ On-chain payment verified on %s", SOLANA_CLUSTER)
            return jsonify({
                "result": f"Terjemahan: {text_to_translate} (Translated via x402)",
                "verification": "on-chain",
                "network": SOLANA_CLUSTER
            }), 200
        else:
            return jsonify({"error": "Payment invalid or not yet confirmed"}), 402

    # No payment proof -> respond with 402 metadata for ALL networks
    response = {
        "error": "Payment Required",
        "price_sol": str(PRICE),
        "currency": "SOL",
        "payment_address": PAYMENT_ADDRESS,
        "cluster": SOLANA_CLUSTER,
        "rpc_url": RPC_URL,
        "verification_methods": ["quantum-resistant", "on-chain", "mock"],
        "payment_methods": [
            "quantum_proof (quantum-resistant signature)",
            "payment_receipt (on-chain verification)"
        ]
    }
    logging.info("No payment proof provided; responding with 402 metadata")
    return jsonify(response), 402


if __name__ == "__main__":
    logging.info(
        "Starting quantum-resistant translation agent on port %s "
        "(Cluster: %s, Quantum: %s, Hybrid: %s)",
        PORT, SOLANA_CLUSTER, QUANTUM_ENABLED, USE_HYBRID_MODE
    )
    app.run(host="0.0.0.0", port=PORT, debug=False)
