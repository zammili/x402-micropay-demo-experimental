#!/usr/bin/env python3
"""
solana_payment_validator.py

Hardened Solana on-chain payment validator with:
- Replay attack prevention
- Transaction timestamp validation
- Legitimate transfer instruction verification
- Network/cluster validation
- Lamport amount verification
"""
import os
import logging
import time
import threading
from decimal import Decimal
from typing import Dict, Any
from datetime import datetime

try:
    from solana.rpc.api import Client
    from solders.signature import Signature
    from solders.pubkey import Pubkey
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False

# Configuration
PAYMENT_ADDRESS_STR = os.getenv("SOLANA_PAYMENT_ADDRESS", "YourSolanaWalletAddressHere")
PRICE_SOL = Decimal(os.getenv("PRICE_SOL", "0.001"))
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
EXPECTED_CLUSTER = os.getenv("SOLANA_CLUSTER", "mainnet-beta")
TRANSACTION_VALIDITY_WINDOW = int(os.getenv("TRANSACTION_VALIDITY_WINDOW", "3600"))

# System Program ID constant
SYSTEM_PROGRAM_ID = "11111111111111111111111111111111"

# Replay attack prevention
_validated_transactions = set()
_tx_lock = threading.Lock()


def validate_receipt_onchain_solana(receipt: Dict[str, Any]) -> bool:
    """
    Validate Solana on-chain payment with security hardening.
    
    Security Checks:
    1. Network/cluster correctness
    2. Transaction existence and success
    3. Replay attack prevention
    4. Transaction recency
    5. Legitimate System Program transfer instruction
    6. Sufficient balance received
    
    Args:
        receipt: Transaction receipt dict with transactionHash, cluster, etc.
    
    Returns:
        bool: True if payment is valid and verified, False otherwise
    """
    if not SOLANA_AVAILABLE:
        logging.error("Solana/solders libraries are not available.")
        return False

    # Step 0: Validate input
    if not isinstance(receipt, dict):
        logging.error("Receipt must be a dictionary")
        return False

    txh = receipt.get("transactionHash")
    if not isinstance(txh, str) or not txh.strip():
        logging.error("Invalid or missing transactionHash in receipt")
        return False

    # ✅ Step 1: Network validation
    receipt_cluster = receipt.get("cluster", EXPECTED_CLUSTER)
    if receipt_cluster != EXPECTED_CLUSTER:
        logging.error("Network mismatch. Expected: %s, Got: %s", EXPECTED_CLUSTER, receipt_cluster)
        return False

    # ✅ Step 2: Replay attack prevention
    with _tx_lock:
        if txh in _validated_transactions:
            logging.warning("Security: Replay attack detected. Transaction already validated: %s", txh)
            return False

    try:
        client = Client(RPC_URL)

        # Convert transaction hash string to Solana Signature
        try:
            sig = Signature.from_string(txh)
        except Exception as e:
            logging.error("Invalid transaction hash format: %s - %s", txh, e)
            return False

        # Fetch transaction
        tx_response = client.get_transaction(sig, max_supported_transaction_version=0)

        if tx_response is None or tx_response.value is None:
            logging.info("Transaction not found or not yet confirmed: %s", txh)
            return False

        meta = tx_response.value.transaction.meta

        # ✅ Step 3: Verify transaction succeeded
        if meta.err is not None:
            logging.info("Transaction failed on-chain: %s - Error: %s", txh, meta.err)
            return False

        # ✅ Step 4: Timestamp validation
        if meta.block_time is None:
            logging.warning("Transaction not yet finalized: %s", txh)
            return False

        time_diff = time.time() - meta.block_time
        if time_diff > TRANSACTION_VALIDITY_WINDOW:
            logging.warning("Transaction too old (%d seconds): %s", time_diff, txh)
            return False

        if time_diff < 0:
            logging.error("Clock skew detected: transaction block_time is in future: %s", txh)
            return False

        # Get account keys and payment address
        transaction_message = tx_response.value.transaction.transaction.message
        account_keys = (transaction_message.static_account_keys 
                       if hasattr(transaction_message, 'static_account_keys') 
                       else transaction_message.account_keys)

        try:
            payment_pubkey = Pubkey.from_string(PAYMENT_ADDRESS_STR)
        except Exception:
            logging.error("Invalid SOLANA_PAYMENT_ADDRESS configuration")
            return False

        # Find payment address index
        target_index = -1
        for i, key in enumerate(account_keys):
            if key == payment_pubkey:
                target_index = i
                break

        if target_index == -1:
            logging.info("Payment address not involved in transaction: %s", txh)
            return False

        # ✅ Step 5: Verify legitimate transfer instruction to payment address
        instructions = transaction_message.instructions
        transfer_found = False

        for instruction in instructions:
            program_id_index = instruction.program_id_index
            if program_id_index >= len(account_keys):
                continue

            program_id = account_keys[program_id_index]
            if str(program_id) != SYSTEM_PROGRAM_ID:
                continue

            # System Program Transfer instruction has data[0] == 2
            if len(instruction.data) < 1 or instruction.data[0] != 2:
                continue

            # Transfer instruction should have at least 2 accounts (from, to)
            if len(instruction.accounts) < 2:
                continue

            to_account_index = instruction.accounts[1]
            if to_account_index == target_index:
                transfer_found = True
                break

        if not transfer_found:
            logging.warning("No legitimate transfer instruction found to payment address: %s", txh)
            return False

        # ✅ Step 6: Verify sufficient balance received
        pre_balance = meta.pre_balances[target_index]
        post_balance = meta.post_balances[target_index]
        balance_change = post_balance - pre_balance

        required_lamports = int(PRICE_SOL * Decimal(10**9))

        if balance_change < required_lamports:
            logging.info("Insufficient payment. Received: %d lamports, Required: %d lamports",
                         balance_change, required_lamports)
            return False

        # �� All checks passed - mark as validated
        with _tx_lock:
            _validated_transactions.add(txh)

        logging.info("Payment validated successfully. TX: %s, Amount: %d lamports, Time: %s",
                     txh, balance_change, datetime.fromtimestamp(meta.block_time))
        return True

    except Exception as e:
        logging.exception("Error during Solana payment validation: %s", e)
        return False


def validate_receipt_mock_solana(receipt: Dict[str, Any]) -> bool:
    """
    Mock Solana validation for testing (no real RPC calls).
    Accepts receipts with valid Solana transaction hash format.
    """
    if not isinstance(receipt, dict):
        logging.error("Receipt must be a dictionary")
        return False

    txh = receipt.get("transactionHash")
    if not isinstance(txh, str) or not txh.strip():
        logging.error("Invalid or missing transactionHash")
        return False

    # Check if it's a valid Solana base58 transaction hash (58 chars typically)
    if len(txh) < 40:
        logging.error("Invalid transaction hash format")
        return False

    # Replay attack prevention even in mock mode
    with _tx_lock:
        if txh in _validated_transactions:
            logging.warning("Mock: Replay attack prevented. Transaction already validated: %s", txh)
            return False
        _validated_transactions.add(txh)

    logging.info("Mock validation passed for transaction: %s", txh)
    return True
