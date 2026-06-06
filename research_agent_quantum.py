#!/usr/bin/env python3
"""
research_agent_quantum.py

Casper client agent that combines x402 payment receipts with a
quantum-resistant payment commitment.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import time
from decimal import Decimal
from typing import Any, Dict, Optional

import requests

from quantum_resistant_crypto import QuantumResistantPaymentProof

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:5001").rstrip("/")
TRANSLATION_TEXT = sys.argv[1] if len(sys.argv) > 1 else "Hello world"
CASPER_CHAIN_NAME = os.getenv("CASPER_CHAIN_NAME", "casper-test")
CASPER_PAYMENT_ADDRESS = os.getenv("CASPER_PAYMENT_ADDRESS", "account-hash-demo-recipient")
PRICE_CSPR = Decimal(os.getenv("PRICE_CSPR", "0.001"))
QUANTUM_ENABLED = os.getenv("QUANTUM_ENABLED", "true").lower() in ("1", "true", "yes")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def request_translation(text: str) -> Optional[Dict[str, Any]]:
    logger.info("Requesting Casper translation: %r", text)
    response = requests.post(f"{AGENT_URL}/translate", json={"text": text}, timeout=10)
    if response.status_code in (200, 402):
        return response.json()
    logger.error("Unexpected response %s: %s", response.status_code, response.text)
    return None


def generate_mock_casper_receipt(text: str, amount_cspr: Decimal, recipient: str) -> Dict[str, Any]:
    logger.info("Generating mock Casper deploy receipt (chain=%s)", CASPER_CHAIN_NAME)
    deploy_hash = "0x" + hashlib.sha256(f"{text}|{amount_cspr}|{time.time_ns()}".encode()).hexdigest()
    return {
        "deployHash": deploy_hash,
        "chainName": CASPER_CHAIN_NAME,
        "amount": str(amount_cspr),
        "toAddress": recipient,
        "blockTime": int(time.time()),
    }


def generate_quantum_proof(receipt: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    logger.info("Generating quantum-resistant Casper payment proof")
    qrp = QuantumResistantPaymentProof(enable_quantum=QUANTUM_ENABLED)
    amount_motes = int(Decimal(str(receipt["amount"])) * Decimal(10**9))
    commitment = qrp.create_payment_commitment(
        transaction_hash=receipt["deployHash"],
        amount_motes=amount_motes,
        payment_address=receipt["toAddress"],
    )
    proof = qrp.sign_payment_proof(commitment)
    proof["casperDeployHash"] = receipt["deployHash"]
    proof["chainName"] = receipt["chainName"]
    return proof


def retry_with_payment(text: str, receipt: Dict[str, Any], quantum_proof: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    payload: Dict[str, Any] = {"text": text, "payment_receipt": receipt}
    if quantum_proof:
        payload["quantum_proof"] = quantum_proof
    response = requests.post(f"{AGENT_URL}/translate", json=payload, timeout=10)
    if response.status_code in (200, 402):
        return response.json()
    logger.error("Unexpected retry response %s: %s", response.status_code, response.text)
    return None


def main() -> None:
    logger.info("Starting quantum-resistant Casper research agent")
    payment_info = request_translation(TRANSLATION_TEXT)
    if not payment_info:
        raise SystemExit(1)
    logger.info("Payment requirements: %s", json.dumps(payment_info, indent=2))

    amount = Decimal(str(payment_info.get("amount", PRICE_CSPR)))
    recipient = payment_info.get("recipient", CASPER_PAYMENT_ADDRESS)
    receipt = generate_mock_casper_receipt(TRANSLATION_TEXT, amount, recipient)
    quantum_proof = generate_quantum_proof(receipt)
    result = retry_with_payment(TRANSLATION_TEXT, receipt, quantum_proof)

    if result and "result" in result:
        logger.info("Success: %s", result["result"])
        return
    logger.error("Payment failed: %s", json.dumps(result or {}, indent=2))
    raise SystemExit(1)


if __name__ == "__main__":
    main()
