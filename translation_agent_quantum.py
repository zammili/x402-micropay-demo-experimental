#!/usr/bin/env python3
"""
translation_agent_quantum.py

Quantum-resistant Casper variant of the x402 translation agent. It validates a
Casper payment receipt and, when supplied, verifies a post-quantum/hybrid proof
that commits to the same Casper deploy hash.
"""
from __future__ import annotations

import logging
import os
from decimal import Decimal, InvalidOperation
from typing import Any, Dict

from flask import Flask, jsonify, request

from casper_payment_validator import (
    CASPER_CHAIN_NAME,
    CASPER_PAYMENT_ADDRESS,
    CASPER_RPC_URL,
    PRICE_CSPR,
    validate_receipt_mock_casper,
    validate_receipt_onchain_casper,
)
from quantum_resistant_crypto import QuantumResistantPaymentProof

VERIFY_ONCHAIN = os.getenv("VERIFY_ONCHAIN", "false").lower() in ("1", "true", "yes")
PORT = int(os.getenv("PORT", "5002"))
PAYMENT_ADDRESS = os.getenv("CASPER_PAYMENT_ADDRESS", CASPER_PAYMENT_ADDRESS)
PRICE_CSPR_ENV = os.getenv("PRICE_CSPR", str(PRICE_CSPR))
QUANTUM_ENABLED = os.getenv("QUANTUM_ENABLED", "true").lower() in ("1", "true", "yes")
USE_HYBRID_MODE = os.getenv("USE_HYBRID_MODE", "true").lower() in ("1", "true", "yes")

try:
    PRICE = Decimal(str(PRICE_CSPR_ENV))
except InvalidOperation as exc:
    raise SystemExit("Invalid PRICE_CSPR") from exc

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
quantum_proof = QuantumResistantPaymentProof(enable_quantum=QUANTUM_ENABLED)


def payment_metadata() -> Dict[str, Any]:
    return {
        "error": "Payment Required",
        "paymentNetwork": "casper",
        "chainName": CASPER_CHAIN_NAME,
        "rpcUrl": CASPER_RPC_URL,
        "price_cspr": str(PRICE),
        "currency": "CSPR",
        "payment_address": PAYMENT_ADDRESS,
        "verification_methods": ["casper-onchain", "casper-mock", "quantum-resistant"],
        "payment_methods": [
            "payment_receipt (Casper deploy receipt)",
            "quantum_proof (ML-KEM/hybrid commitment to Casper deploy)",
        ],
    }


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "ok": True,
            "network": "casper",
            "chainName": CASPER_CHAIN_NAME,
            "verify_onchain": VERIFY_ONCHAIN,
            "quantum_enabled": QUANTUM_ENABLED,
            "hybrid_mode": USE_HYBRID_MODE,
        }
    )


@app.route("/quantum/commitment", methods=["POST"])
def create_commitment():
    data = request.get_json(silent=True) or {}
    deploy_hash = data.get("deployHash")
    amount_motes = data.get("amountMotes")
    address = data.get("paymentAddress", PAYMENT_ADDRESS)

    if not all([deploy_hash, amount_motes, address]):
        return jsonify({"error": "Missing deployHash, amountMotes, or paymentAddress"}), 400

    commitment = quantum_proof.create_payment_commitment(
        transaction_hash=deploy_hash,
        amount_motes=int(amount_motes),
        payment_address=address,
    )
    return jsonify({"commitment": commitment, "algorithm": "SHA-256+BLAKE2b", "quantum_safe": True})


@app.route("/quantum/sign", methods=["POST"])
def sign_proof():
    data = request.get_json(silent=True) or {}
    commitment = data.get("commitment")
    if not commitment:
        return jsonify({"error": "Missing commitment"}), 400
    return jsonify(quantum_proof.sign_payment_proof(commitment))


@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json(silent=True) or {}
    text_to_translate = data.get("text", "")
    payment_receipt = data.get("payment_receipt")
    quantum_proof_data = data.get("quantum_proof")

    if quantum_proof_data:
        logging.info("Quantum proof provided. Verifying...")
        if not quantum_proof.verify_payment_proof(quantum_proof_data):
            return jsonify({"error": "Quantum proof verification failed", **payment_metadata()}), 402
        if quantum_proof.is_proof_replayed(quantum_proof_data):
            return jsonify({"error": "Replay attack detected", **payment_metadata()}), 402

    if payment_receipt:
        receipt_chain = payment_receipt.get("chainName", CASPER_CHAIN_NAME)
        if receipt_chain != CASPER_CHAIN_NAME:
            return jsonify({"error": f"Network mismatch. Expected {CASPER_CHAIN_NAME}, got {receipt_chain}"}), 402

        valid = validate_receipt_onchain_casper(payment_receipt) if VERIFY_ONCHAIN else validate_receipt_mock_casper(payment_receipt)
        if valid:
            return jsonify(
                {
                    "result": f"Terjemahan: {text_to_translate} (via Casper x402 quantum)",
                    "verification": "casper-onchain+quantum" if quantum_proof_data else "casper-payment",
                    "network": "casper",
                    "chainName": CASPER_CHAIN_NAME,
                }
            )
        return jsonify({"error": "Payment invalid or not yet confirmed", **payment_metadata()}), 402

    return jsonify(payment_metadata()), 402


if __name__ == "__main__":
    logging.info(
        "Starting quantum-resistant Casper translation agent on port %s (Quantum: %s, Hybrid: %s)",
        PORT,
        QUANTUM_ENABLED,
        USE_HYBRID_MODE,
    )
    app.run(host="0.0.0.0", port=PORT, debug=False)
