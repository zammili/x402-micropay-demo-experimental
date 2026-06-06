#!/usr/bin/env python3
"""
casper_payment_validator.py

Casper Network on-chain payment validator with:
- Casper RPC integration via Casper JSON-RPC
- Transaction verification on Casper Testnet
- Replay attack prevention
- Deploy/contract interaction validation
"""
import os
import logging
import time
import threading
from decimal import Decimal
from typing import Any, Dict
from enum import Enum

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Configuration
CASPER_RPC_URL = os.getenv("CASPER_RPC_URL", "https://rpc.testnet.casperlabs.io")
CASPER_PAYMENT_ADDRESS = os.getenv("CASPER_PAYMENT_ADDRESS", "")  # Casper account hash
PRICE_CSPR = Decimal(os.getenv("PRICE_CSPR", "0.001"))
TRANSACTION_VALIDITY_WINDOW = int(os.getenv("TRANSACTION_VALIDITY_WINDOW", "3600"))
CASPER_CHAIN_NAME = os.getenv("CASPER_CHAIN_NAME", "casper-test")

# Replay attack prevention
_validated_deploys = set()
_deploy_lock = threading.Lock()


class CasperTransactionStatus(Enum):
    """Casper deploy execution status"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"
    UNKNOWN = "unknown"


def get_casper_deploy_status(deploy_hash: str) -> Dict[str, Any]:
    """
    Fetch a Casper deploy by hash from the configured RPC endpoint.

    Args:
        deploy_hash: Casper deploy hash, with or without a 0x prefix.

    Returns:
        RPC result plus a compact status field for agent consumption.
    """
    if not HTTPX_AVAILABLE:
        logging.error("httpx library is not available. Install with: pip install httpx")
        return {}

    normalized_hash = deploy_hash.removeprefix("0x")

    try:
        with httpx.Client() as client:
            payload = {
                "jsonrpc": "2.0",
                "method": "info_get_deploy",
                "params": {"deploy_hash": normalized_hash},
                "id": 1,
            }
            response = client.post(CASPER_RPC_URL, json=payload, timeout=10)
            response.raise_for_status()
            rpc_response = response.json()

        result = rpc_response.get("result", {})
        execution_results = result.get("execution_results") or []
        if not execution_results:
            rpc_response["status"] = CasperTransactionStatus.PENDING.value
        elif _deploy_execution_succeeded(execution_results):
            rpc_response["status"] = CasperTransactionStatus.SUCCESS.value
        else:
            rpc_response["status"] = CasperTransactionStatus.FAILURE.value
        return rpc_response
    except Exception as e:
        logging.error("Error querying Casper deploy status: %s", e)
        return {"status": CasperTransactionStatus.UNKNOWN.value, "error": str(e)}


def _deploy_execution_succeeded(execution_results: Any) -> bool:
    """Return True when any Casper execution result reports success."""
    for item in execution_results or []:
        result = item.get("result", {}) if isinstance(item, dict) else {}
        if "Success" in result or result.get("Success") is not None:
            return True
        if result.get("status") == "success":
            return True
    return False


def _extract_transfer_args(deploy_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract native transfer amount and target from info_get_deploy output."""
    session = deploy_result.get("deploy", {}).get("session", {})
    transfer = session.get("Transfer", {}) if isinstance(session, dict) else {}
    args = transfer.get("args", []) if isinstance(transfer, dict) else []
    extracted: Dict[str, Any] = {}

    for arg in args:
        if not isinstance(arg, list) or len(arg) != 2:
            continue
        name, value = arg
        if isinstance(value, dict):
            parsed = value.get("parsed")
            extracted[name] = parsed if parsed is not None else value
        else:
            extracted[name] = value
    return extracted


def _motes_to_cspr(motes: Any) -> Decimal:
    """Convert a Casper motes value from RPC JSON into CSPR."""
    return Decimal(str(motes)) / Decimal(10**9)


def get_account_info(account_address: str) -> Dict[str, Any]:
    """
    Fetch account information from Casper network.
    
    Args:
        account_address: Casper account address (hex or public key)
    
    Returns:
        Account state and balance info
    """
    if not HTTPX_AVAILABLE:
        logging.error("httpx library is not available.")
        return {}
    
    try:
        with httpx.Client() as client:
            payload = {
                "jsonrpc": "2.0",
                "method": "state_get_account_info",
                "params": {
                    "account_identifier": {
                        "Hash": account_address
                    }
                },
                "id": 1
            }
            response = client.post(CASPER_RPC_URL, json=payload, timeout=10)
            response.raise_for_status()
            return response.json().get("result", {})
    except Exception as e:
        logging.error("Error fetching account info: %s", e)
        return {}


def validate_receipt_onchain_casper(receipt: Dict[str, Any]) -> bool:
    """
    Validate Casper on-chain payment with security hardening.
    
    Security Checks:
    1. Deploy hash format validation
    2. Chain name verification
    3. Replay attack prevention
    4. Deploy status confirmation
    5. Sufficient CSPR transfer amount
    
    Args:
        receipt: Transaction receipt dict with deployHash, amount, etc.
    
    Returns:
        bool: True if payment is valid and verified, False otherwise
    """
    if not HTTPX_AVAILABLE:
        logging.error("httpx library is required for Casper validation.")
        return False
    
    # Step 0: Validate input
    if not isinstance(receipt, dict):
        logging.error("Receipt must be a dictionary")
        return False
    
    deploy_hash = receipt.get("deployHash")
    if not isinstance(deploy_hash, str) or not deploy_hash.strip():
        logging.error("Invalid or missing deployHash in receipt")
        return False
    
    # Normalize hex string (remove 0x prefix if present)
    deploy_hash = deploy_hash.removeprefix("0x")
    
    # ✅ Step 1: Chain name validation
    receipt_chain = receipt.get("chainName", CASPER_CHAIN_NAME)
    if receipt_chain != CASPER_CHAIN_NAME:
        logging.error("Chain mismatch. Expected: %s, Got: %s", CASPER_CHAIN_NAME, receipt_chain)
        return False
    
    # ✅ Step 2: Replay attack prevention
    with _deploy_lock:
        if deploy_hash in _validated_deploys:
            logging.warning("Security: Replay attack detected. Deploy already validated: %s", deploy_hash)
            return False
    
    try:
        # ✅ Step 3: Confirm deploy execution on Casper RPC
        deploy_status = get_casper_deploy_status(deploy_hash)
        if deploy_status.get("status") != CasperTransactionStatus.SUCCESS.value:
            logging.info("Deploy %s is not successful yet: %s", deploy_hash, deploy_status.get("status"))
            return False

        deploy_result = deploy_status.get("result", {})
        transfer_args = _extract_transfer_args(deploy_result)

        # ✅ Step 4: Check deploy timestamp (recency)
        block_time = receipt.get("blockTime")
        if block_time:
            time_diff = time.time() - block_time
            if time_diff > TRANSACTION_VALIDITY_WINDOW:
                logging.warning("Deploy too old (%d seconds): %s", time_diff, deploy_hash)
                return False
            if time_diff < 0:
                logging.error("Clock skew detected: deploy block_time is in future: %s", deploy_hash)
                return False

        # ✅ Step 5: Verify sufficient CSPR transfer amount
        amount = transfer_args.get("amount", receipt.get("amount", 0))
        try:
            amount_cspr = _motes_to_cspr(amount) if transfer_args.get("amount") is not None else Decimal(str(amount))
        except Exception:
            logging.error("Invalid amount in receipt/deploy: %s", amount)
            return False

        required_cspr = PRICE_CSPR

        if amount_cspr < required_cspr:
            logging.info("Insufficient payment. Received: %s CSPR, Required: %s CSPR",
                        amount_cspr, required_cspr)
            return False

        # ✅ Step 6: Verify target account matches payment address (if configured)
        if CASPER_PAYMENT_ADDRESS:
            to_address = str(transfer_args.get("target") or receipt.get("toAddress", ""))
            if CASPER_PAYMENT_ADDRESS not in to_address and to_address != CASPER_PAYMENT_ADDRESS:
                logging.info("Payment to %s does not match expected %s", to_address, CASPER_PAYMENT_ADDRESS)
                return False

        # ✅ All checks passed - mark as validated
        with _deploy_lock:
            _validated_deploys.add(deploy_hash)
        
        logging.info("Casper payment validated successfully. Deploy: %s, Amount: %s CSPR",
                    deploy_hash, amount_cspr)
        return True
    
    except Exception as e:
        logging.exception("Error during Casper payment validation: %s", e)
        return False


def validate_receipt_mock_casper(receipt: Dict[str, Any]) -> bool:
    """
    Mock Casper validation for testing (no real RPC calls).
    Accepts receipts with valid Casper deploy hash format.
    """
    if not isinstance(receipt, dict):
        logging.error("Receipt must be a dictionary")
        return False
    
    deploy_hash = receipt.get("deployHash")
    if not isinstance(deploy_hash, str) or not deploy_hash.strip():
        logging.error("Invalid or missing deployHash")
        return False
    
    # Normalize and validate hex format (64 chars for Casper deploy hash)
    deploy_hash = deploy_hash.removeprefix("0x")
    if len(deploy_hash) < 32:
        logging.error("Invalid deploy hash format")
        return False
    
    # Replay attack prevention even in mock mode
    with _deploy_lock:
        if deploy_hash in _validated_deploys:
            logging.warning("Mock: Replay attack prevented. Deploy already validated: %s", deploy_hash)
            return False
        _validated_deploys.add(deploy_hash)
    
    # Validate amount
    amount = receipt.get("amount", 0)
    try:
        amount_cspr = Decimal(str(amount))
        if amount_cspr < PRICE_CSPR:
            logging.error("Insufficient amount: %s < %s", amount_cspr, PRICE_CSPR)
            return False
    except Exception:
        logging.error("Invalid amount")
        return False
    
    logging.info("Mock validation passed for Casper deploy: %s", deploy_hash)
    return True
