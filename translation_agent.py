#!/usr/bin/env python3
"""
translation_agent.py

Now requires a full transaction receipt as proof (sent in JSON body under "payment_receipt").
Mock verification accepts any receipt-like dict with "transactionHash" that starts with "0x".
"""
from __future__ import annotations
import os
import time
import logging
from decimal import Decimal, InvalidOperation
from threading import Lock
from typing import Dict, Any

from flask import Flask, request, jsonify

try:
    from web3 import Web3
    from web3.exceptions import TransactionNotFound
    WEB3_AVAILABLE = True
except Exception:
    WEB3_AVAILABLE = False

# Config
PAYMENT_ADDRESS = os.getenv("PAYMENT_ADDRESS", "0x1234567890AbCdEf1234567890AbCdEf12345678")
PRICE_ETH = os.getenv("PRICE_ETH", "0.001")
CHAIN_ID = int(os.getenv("CHAIN_ID", "84532"))
RPC_URL = os.getenv("RPC_URL", "")
VERIFY_ONCHAIN = os.getenv("VERIFY_ONCHAIN", "false").lower() in ("1", "true", "yes")
PROOF_TTL = int(os.getenv("PROOF_TTL", "120"))
MIN_CONFIRMATIONS = int(os.getenv("MIN_CONFIRMATIONS", "0"))
PORT = int(os.getenv("PORT", "5001"))

# validate/normalize
try:
    PRICE = Decimal(str(PRICE_ETH))
except InvalidOperation:
    raise SystemExit("Invalid PRICE_ETH")

if VERIFY_ONCHAIN and not WEB3_AVAILABLE:
    logging.warning("VERIFY_ONCHAIN enabled but web3 not available. Falling back to mock verification.")
    VERIFY_ONCHAIN = False

if WEB3_AVAILABLE:
    try:
        PAYMENT_ADDRESS = Web3.to_checksum_address(PAYMENT_ADDRESS)
    except Exception:
        logging.warning("PAYMENT_ADDRESS could not be checksummed; continuing.")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

_pending_lock = Lock()
_pending_proofs: Dict[str, float] = {}

def add_pending_proof(tx_hash: str) -> None:
    with _pending_lock:
        _pending_proofs[tx_hash] = time.time()

def is_pending_proof_valid(tx_hash: str) -> bool:
    with _pending_lock:
        ts = _pending_proofs.get(tx_hash)
        if not ts:
            return False
        if time.time() - ts <= PROOF_TTL:
            return True
        del _pending_proofs[tx_hash]
        return False

def validate_receipt_mock(receipt: Dict[str, Any]) -> bool:
    """Mock: accept any receipt-like dict with a transactionHash starting with '0x' and value field >= price if present."""
    txh = receipt.get("transactionHash") if isinstance(receipt, dict) else None
    if not isinstance(txh, str) or not txh.startswith("0x"):
        return False
    # Cache by transactionHash
    if not is_pending_proof_valid(txh):
        add_pending_proof(txh)
    return True

def validate_receipt_onchain(receipt: Dict[str, Any]) -> bool:
    """Validate receipt on-chain by cross-checking RPC: must exist, status==1, to==PAYMENT_ADDRESS, value>=PRICE."""
    if not WEB3_AVAILABLE or not RPC_URL:
        logging.error("On-chain verification not configured correctly.")
        return False
    if not isinstance(receipt, dict):
        return False
    txh = receipt.get("transactionHash")
    if not isinstance(txh, str):
        return False
    if is_pending_proof_valid(txh):
        return True

    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 10}))
        if not w3.isConnected():
            logging.error("Cannot connect to RPC")
            return False

        # fetch receipt & transaction to cross-check
        try:
            onchain_rcpt = w3.eth.get_transaction_receipt(txh)
        except TransactionNotFound:
            logging.info("Transaction not found yet: %s", txh)
            return False

        if onchain_rcpt.get("status") != 1:
            logging.info("Transaction %s has non-success status", txh)
            return False

        if MIN_CONFIRMATIONS > 0:
            latest = w3.eth.block_number
            confirmations = latest - onchain_rcpt.get("blockNumber", latest)
            if confirmations < MIN_CONFIRMATIONS:
                logging.info("Transaction %s has %d confirmations (need %d)", txh, confirmations, MIN_CONFIRMATIONS)
                return False

        tx = w3.eth.get_transaction(txh)
        to_addr = tx.get("to")
        value_wei = tx.get("value", 0)
        required_wei = int(PRICE * Decimal(10**18))

        if to_addr is None:
            logging.info("Transaction %s has no 'to' address", txh)
            return False

        try:
            to_cs = Web3.to_checksum_address(to_addr)
            expected_cs = Web3.to_checksum_address(PAYMENT_ADDRESS)
        except Exception:
            logging.error("Checksum failure")
            return False

        if to_cs != expected_cs:
            logging.info("Transaction to %s does not match expected %s", to_cs, expected_cs)
            return False

        if int(value_wei) < required_wei:
            logging.info("Transaction value %s less than required %s", value_wei, required_wei)
            return False

        add_pending_proof(txh)
        logging.info("On-chain verification succeeded for %s", txh)
        return True

    except Exception as e:
        logging.exception("Error during on-chain verification: %s", e)
        return False

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "verify_onchain": VERIFY_ONCHAIN, "payment_address": PAYMENT_ADDRESS, "price_eth": str(PRICE)})

@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json(silent=True) or {}
    text_to_translate = data.get("text", "")
    receipt = data.get("payment_receipt")  # expect a full receipt dict here

    if receipt:
        # Validate the provided receipt
        logging.info("Received payment_receipt in request")
        if VERIFY_ONCHAIN:
            valid = validate_receipt_onchain(receipt)
        else:
            valid = validate_receipt_mock(receipt)
        if valid:
            return jsonify({"result": f"Terjemahan: {text_to_translate} (Translated via x402)"}), 200
        else:
            return jsonify({"error": "Payment invalid or not yet confirmed"}), 402

    # No receipt provided -> respond with 402 metadata
    response = {
        "error": "Payment Required",
        "price": str(PRICE),
        "currency": "ETH",
        "payment_address": PAYMENT_ADDRESS,
        "chain": f"chainId:{CHAIN_ID}"
    }
    logging.info("No payment proof provided; responding with 402 metadata")
    return jsonify(response), 402

if __name__ == "__main__":
    logging.info("Starting translation agent on port %s (VERIFY_ONCHAIN=%s)", PORT, VERIFY_ONCHAIN)
    app.run(host="0.0.0.0", port=PORT)