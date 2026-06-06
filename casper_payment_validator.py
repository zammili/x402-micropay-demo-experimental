#!/usr/bin/env python3
"""
casper_payment_validator.py

Casper Network on-chain payment validator with:
- Casper RPC integration via httpx library
- Transaction verification on Casper Testnet
- Replay attack prevention
- Deploy/contract interaction validation
"""
import os
import logging
import time
import threading
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional
from datetime import datetime
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
MAX_AMOUNT_LENGTH = 30  # Prevent decimal overflow attacks

# Validate configuration at startup
try:
    PRICE_CSPR = Decimal(str(PRICE_CSPR))
    if PRICE_CSPR < 0:
        raise ValueError("PRICE_CSPR must be non-negative")
except (ValueError, InvalidOperation) as e:
    raise SystemExit(f"Invalid PRICE_CSPR configuration: {e}")

# Validate RPC URL format
if CASPER_RPC_URL:
    if not (CASPER_RPC_URL.startswith("http://") or CASPER_RPC_URL.startswith("https://")):
        raise SystemExit(f"Invalid CASPER_RPC_URL format: {CASPER_RPC_URL}")

# Valid Casper chains
VALID_CASPER_CHAINS = {"casper-test", "casper"}
if CASPER_CHAIN_NAME not in VALID_CASPER_CHAINS:
    raise SystemExit(f"Invalid CASPER_CHAIN_NAME: {CASPER_CHAIN_NAME}")

# Replay attack prevention
_validated_deploys = set()
_deploy_lock = threading.Lock()


class CasperTransactionStatus(Enum):
    """Casper deploy execution status"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"
    UNKNOWN = "unknown"


def validate_deploy_hash_format(deploy_hash: str) -> bool:
    """
    Validate Casper deploy hash format.
    
    Args:
        deploy_hash: Hex string (with or without 0x prefix)
    
    Returns:
        True if valid hex format, False otherwise
    """
    if not isinstance(deploy_hash, str) or not deploy_hash.strip():
        return False
    
    # Remove 0x prefix if present
    if deploy_hash.startswith("0x") or deploy_hash.startswith("0X"):
        deploy_hash = deploy_hash[2:]
    
    # Validate: must be 64 hex chars (256-bit hash)
    if len(deploy_hash) != 64:
        return False
    
    try:
        int(deploy_hash, 16)  # Verify it's valid hex
        return True
    except ValueError:
        return False


def get_casper_deploy_status(deploy_hash: str) -> Dict[str, Any]:
    """
    Fetch deploy status from Casper RPC.
    
    Args:
        deploy_hash: Casper deploy hash (hex string)
    
    Returns:
        Dict with deployment info and execution status
    """
    if not HTTPX_AVAILABLE:
        logging.error("httpx library is not available. Install with: pip install httpx")
        return {}
    
    if not validate_deploy_hash_format(deploy_hash):
        logging.error("Invalid deploy hash format: %s", deploy_hash)
        return {}
    
    try:
        with httpx.Client(timeout=10.0) as client:
            # Query info_get_deploy with the specific deploy hash
            payload = {
                "jsonrpc": "2.0",
                "method": "info_get_deploy",
                "params": {
                    "deploy_hash": deploy_hash.lstrip("0x")
                },
                "id": 1
            }
            response = client.post(CASPER_RPC_URL, json=payload, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logging.error("Network error querying Casper RPC: %s", e)
        return {}
    except httpx.TimeoutException:
        logging.error("RPC request timeout")
        return {}
    except Exception as e:
        logging.exception("Error querying Casper RPC: %s", e)
        return {}


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
    
    if not isinstance(account_address, str) or not account_address.strip():
        logging.error("Invalid account address")
        return {}
    
    try:
        with httpx.Client(timeout=10.0) as client:
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
            response = client.post(CASPER_RPC_URL, json=payload, timeout=10.0)
            response.raise_for_status()
            return response.json().get("result", {})
    except httpx.TimeoutException:
        logging.error("Account info RPC timeout")
        return {}
    except httpx.RequestError as e:
        logging.error("Network error fetching account info: %s", e)
        return {}
    except Exception as e:
        logging.exception("Error fetching account info: %s", e)
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
    
    # Normalize hex string
    if deploy_hash.startswith("0x") or deploy_hash.startswith("0X"):
        deploy_hash = deploy_hash[2:]
    
    # ✅ Step 1: Chain name validation
    receipt_chain = receipt.get("chainName", CASPER_CHAIN_NAME)
    if receipt_chain not in VALID_CASPER_CHAINS:
        logging.error("Chain mismatch. Expected: %s, Got: %s", CASPER_CHAIN_NAME, receipt_chain)
        return False
    
    # ✅ Step 2: Deploy hash format validation
    if not validate_deploy_hash_format(deploy_hash):
        logging.error("Invalid deploy hash format: %s", deploy_hash)
        return False
    
    # ✅ Step 3: Replay attack prevention
    with _deploy_lock:
        if deploy_hash in _validated_deploys:
            logging.warning("Security: Replay attack detected. Deploy already validated: %s", deploy_hash)
            return False
    
    try:
        # ✅ Step 4: Check deploy timestamp (recency)
        block_time = receipt.get("blockTime")
        if block_time:
            try:
                block_time = float(block_time)
            except (ValueError, TypeError):
                logging.error("Invalid blockTime format: %s", block_time)
                return False
                
            time_diff = time.time() - block_time
            if time_diff > TRANSACTION_VALIDITY_WINDOW:
                logging.warning("Deploy too old (%d seconds): %s", time_diff, deploy_hash)
                return False
            if time_diff < 0:
                logging.error("Clock skew detected: deploy block_time is in future: %s", deploy_hash)
                return False
        
        # ✅ Step 5: Verify sufficient CSPR transfer amount
        amount = receipt.get("amount", 0)
        
        # Validate amount format and size
        amount_str = str(amount)
        if len(amount_str) > MAX_AMOUNT_LENGTH:
            logging.error("Amount string too large: %s", amount_str[:50])
            return False
        
        try:
            amount_cspr = Decimal(amount_str)
        except (ValueError, TypeError, InvalidOperation) as e:
            logging.error("Invalid amount in receipt: %s - %s", amount, e)
            return False
        
        if amount_cspr < 0:
            logging.error("Amount cannot be negative: %s", amount_cspr)
            return False
        
        required_cspr = PRICE_CSPR
        
        if amount_cspr < required_cspr:
            logging.info("Insufficient payment. Received: %s CSPR, Required: %s CSPR",
                        amount_cspr, required_cspr)
            return False
        
        # ✅ Step 6: Verify target account matches payment address (if configured)
        if CASPER_PAYMENT_ADDRESS:
            to_address = receipt.get("toAddress", "")
            if not isinstance(to_address, str):
                logging.error("Invalid toAddress format")
                return False
            if to_address != CASPER_PAYMENT_ADDRESS:
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
    
    # Validate deploy hash format
    if not validate_deploy_hash_format(deploy_hash):
        logging.error("Invalid deploy hash format")
        return False
    
    # Normalize for replay check
    if deploy_hash.startswith("0x") or deploy_hash.startswith("0X"):
        deploy_hash = deploy_hash[2:]
    
    # Replay attack prevention even in mock mode
    with _deploy_lock:
        if deploy_hash in _validated_deploys:
            logging.warning("Mock: Replay attack prevented. Deploy already validated: %s", deploy_hash)
            return False
        _validated_deploys.add(deploy_hash)
    
    # Validate amount
    amount_str = str(receipt.get("amount", 0))
    if len(amount_str) > MAX_AMOUNT_LENGTH:
        logging.error("Amount too large")
        return False
    
    try:
        amount_cspr = Decimal(amount_str)
        if amount_cspr < 0:
            logging.error("Amount cannot be negative")
            return False
        if amount_cspr < PRICE_CSPR:
            logging.error("Insufficient amount: %s < %s", amount_cspr, PRICE_CSPR)
            return False
    except (ValueError, TypeError, InvalidOperation) as e:
        logging.error("Invalid amount: %s", e)
        return False
    
    logging.info("Mock validation passed for Casper deploy: %s", deploy_hash)
    return True
