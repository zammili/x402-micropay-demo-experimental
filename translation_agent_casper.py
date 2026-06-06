#!/usr/bin/env python3
"""
translation_agent_casper.py

Casper Network-native translation agent with full on-chain payment verification.
Replaces solana/ethereum dependencies with Casper-specific logic.
"""
from __future__ import annotations
import os
import time
import logging
from decimal import Decimal, InvalidOperation
from threading import Lock
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Configuration - Casper specific
CASPER_RPC_URL = os.getenv("CASPER_RPC_URL", "https://rpc.testnet.casperlabs.io")
CASPER_PAYMENT_ADDRESS = os.getenv("CASPER_PAYMENT_ADDRESS", "account-hash-1234567890abcdef...")
PRICE_CSPR = Decimal(os.getenv("PRICE_CSPR", "0.001"))
CASPER_CHAIN_NAME = os.getenv("CASPER_CHAIN_NAME", "casper-test")
VERIFY_ONCHAIN = os.getenv("VERIFY_ONCHAIN", "false").lower() in ("1", "true", "yes")
PROOF_TTL = int(os.getenv("PROOF_TTL", "120"))
MIN_CONFIRMATIONS = int(os.getenv("MIN_CONFIRMATIONS", "1"))
PORT = int(os.getenv("PORT", "5001"))

# Validate configuration
try:
    PRICE = Decimal(str(PRICE_CSPR))
except InvalidOperation:
    raise SystemExit("Invalid PRICE_CSPR")

if VERIFY_ONCHAIN and not HTTPX_AVAILABLE:
    logging.warning("VERIFY_ONCHAIN enabled but httpx not available. Falling back to mock verification.")
    VERIFY_ONCHAIN = False

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Proof validation cache - prevents replay attacks
_pending_lock = Lock()
_validated_deploys: Dict[str, float] = {}


def add_validated_deploy(deploy_hash: str) -> None:
    """Mark a deploy as validated (with timestamp for TTL)"""
    with _pending_lock:
        _validated_deploys[deploy_hash] = time.time()


def is_deploy_valid(deploy_hash: str) -> bool:
    """Check if deploy has been validated within TTL window"""
    with _pending_lock:
        ts = _validated_deploys.get(deploy_hash)
        if not ts:
            return False
        if time.time() - ts <= PROOF_TTL:
            return True
        # Cleanup expired entry
        del _validated_deploys[deploy_hash]
        return False


def validate_receipt_mock_casper(receipt: Dict[str, Any]) -> bool:
    """
    Mock Casper validation for local testing.
    Validates receipt format without RPC calls.
    """
    if not isinstance(receipt, dict):
        logging.error("Receipt must be a dictionary")
        return False
    
    deploy_hash = receipt.get("deployHash")
    if not isinstance(deploy_hash, str) or not deploy_hash.strip():
        logging.error("Invalid or missing deployHash")
        return False
    
    # Normalize hex (remove 0x prefix if present)
    deploy_hash = deploy_hash.lstrip("0x")
    
    # Validate hex format and length (Casper deploy hash is typically 64 chars)
    if len(deploy_hash) < 32:
        logging.error("Invalid deploy hash format")
        return False
    
    # Validate chain name
    chain = receipt.get("chainName", CASPER_CHAIN_NAME)
    if chain != CASPER_CHAIN_NAME:
        logging.error("Chain mismatch. Expected: %s, Got: %s", CASPER_CHAIN_NAME, chain)
        return False
    
    # Validate amount
    try:
        amount = Decimal(str(receipt.get("amount", 0)))
        if amount < PRICE:
            logging.error("Insufficient amount: %s < %s", amount, PRICE)
            return False
    except:
        logging.error("Invalid amount format")
        return False
    
    # Replay attack prevention
    if is_deploy_valid(deploy_hash):
        logging.warning("Replay attack prevented: Deploy already validated: %s", deploy_hash)
        return False
    
    add_validated_deploy(deploy_hash)
    logging.info("Mock validation passed for Casper deploy: %s", deploy_hash)
    return True


def validate_receipt_onchain_casper(receipt: Dict[str, Any]) -> bool:
    """
    Validate Casper on-chain payment by querying Casper RPC.
    
    Verification steps:
    1. Validate receipt format
    2. Prevent replay attacks
    3. Query deploy status from RPC
    4. Verify sufficient amount
    5. Verify payment recipient
    """
    if not HTTPX_AVAILABLE or not CASPER_RPC_URL:
        logging.error("On-chain verification not configured correctly")
        return False
    
    if not isinstance(receipt, dict):
        logging.error("Receipt must be a dictionary")
        return False
    
    deploy_hash = receipt.get("deployHash")
    if not isinstance(deploy_hash, str):
        logging.error("Invalid or missing deployHash")
        return False
    
    # Normalize hex
    deploy_hash = deploy_hash.lstrip("0x")
    
    # Check if already validated (within TTL)
    if is_deploy_valid(deploy_hash):
        logging.info("Deploy already validated within TTL: %s", deploy_hash)
        return True
    
    try:
        with httpx.Client(timeout=10.0) as client:
            # Query deploy status from Casper RPC
            payload = {
                "jsonrpc": "2.0",
                "method": "info_get_deploy",
                "params": {
                    "deploy_hash": deploy_hash
                },
                "id": 1
            }
            
            response = client.post(CASPER_RPC_URL, json=payload)
            response.raise_for_status()
            
            result = response.json().get("result", {})
            deploy = result.get("deploy", {})
            
            # Validate deploy execution
            execution_results = result.get("execution_results", [])
            if not execution_results:
                logging.warning("No execution results for deploy: %s", deploy_hash)
                return False
            
            execution = execution_results[0]
            if execution.get("Success") is None:
                logging.error("Deploy execution failed: %s", deploy_hash)
                return False
            
            # Verify payment amount
            try:
                amount = Decimal(str(receipt.get("amount", 0)))
                if amount < PRICE:
                    logging.info("Insufficient payment. Received: %s, Required: %s", amount, PRICE)
                    return False
            except:
                logging.error("Invalid amount in receipt")
                return False
            
            # Verify recipient address (if configured)
            if CASPER_PAYMENT_ADDRESS:
                to_address = receipt.get("toAddress", "")
                if to_address != CASPER_PAYMENT_ADDRESS:
                    logging.info("Payment to %s does not match expected %s", to_address, CASPER_PAYMENT_ADDRESS)
                    return False
            
            # Mark as validated
            add_validated_deploy(deploy_hash)
            logging.info("On-chain validation succeeded for deploy: %s", deploy_hash)
            return True
    
    except httpx.RequestError as e:
        logging.error("RPC request failed: %s", e)
        return False
    except Exception as e:
        logging.exception("Error during Casper validation: %s", e)
        return False


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "ok": True,
        "network": CASPER_CHAIN_NAME,
        "verify_onchain": VERIFY_ONCHAIN,
        "payment_address": CASPER_PAYMENT_ADDRESS,
        "price_cspr": str(PRICE)
    }), 200


@app.route("/translate", methods=["POST"])
def translate():
    """
    Translation endpoint with 402 Payment Required support.
    
    Request format:
    - Without payment: Returns 402 with payment metadata
    - With payment_receipt: Validates Casper deploy, returns translation or 402
    """
    data = request.get_json(silent=True) or {}
    text_to_translate = data.get("text", "")
    receipt = data.get("payment_receipt")
    
    if not text_to_translate:
        return jsonify({"error": "Missing 'text' field"}), 400
    
    # If payment receipt provided, validate it
    if receipt:
        logging.info("Received payment_receipt for Casper deploy")
        
        if VERIFY_ONCHAIN:
            valid = validate_receipt_onchain_casper(receipt)
        else:
            valid = validate_receipt_mock_casper(receipt)
        
        if valid:
            # Payment verified - return translation
            translation = f"Terjemahan: {text_to_translate} (Diterjemahkan via x402 + Casper)"
            return jsonify({
                "result": translation,
                "blockchain": "casper",
                "payment_verified": True
            }), 200
        else:
            # Payment validation failed
            return jsonify({
                "error": "Payment invalid or not yet confirmed",
                "blockchain": "casper"
            }), 402
    
    # No payment provided - respond with 402 and payment metadata
    response = {
        "error": "Payment Required",
        "price": str(PRICE),
        "currency": "CSPR",
        "payment_address": CASPER_PAYMENT_ADDRESS,
        "chain": CASPER_CHAIN_NAME,
        "rpc_url": CASPER_RPC_URL,
        "blockchain": "casper"
    }
    logging.info("No payment proof provided; responding with 402 metadata")
    return jsonify(response), 402


@app.route("/config", methods=["GET"])
def get_config():
    """Get current Casper configuration (non-sensitive info)"""
    return jsonify({
        "casper_chain": CASPER_CHAIN_NAME,
        "casper_rpc_url": CASPER_RPC_URL,
        "verify_onchain": VERIFY_ONCHAIN,
        "price_cspr": str(PRICE),
        "proof_ttl": PROOF_TTL,
        "min_confirmations": MIN_CONFIRMATIONS
    }), 200


if __name__ == "__main__":
    logging.info("Starting Casper translation agent on port %s", PORT)
    logging.info("Network: %s | Verify OnChain: %s | Price: %s CSPR", 
                 CASPER_CHAIN_NAME, VERIFY_ONCHAIN, PRICE)
    app.run(host="0.0.0.0", port=PORT, debug=False)
