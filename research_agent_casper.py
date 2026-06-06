#!/usr/bin/env python3
"""
research_agent_casper.py

Casper Network-native research agent that initiates translation requests
and handles 402 Payment Required responses by submitting Casper transactions.
"""
from __future__ import annotations
import os
import sys
import time
import logging
from decimal import Decimal
from typing import Dict, Any, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Configuration
TRANSLATE_URL = os.getenv("TRANSLATE_URL", "http://localhost:5001/translate")
CASPER_RPC_URL = os.getenv("CASPER_RPC_URL", "https://rpc.testnet.casperlabs.io")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def simulate_casper_payment(amount_cspr: Decimal, to_address: str) -> Dict[str, Any]:
    """
    Simulate or prepare a Casper Network payment via deploy.
    
    In a real implementation, this would:
    1. Create a Casper deploy
    2. Sign with user's private key
    3. Submit to Casper RPC
    
    Args:
        amount_cspr: Amount to transfer in CSPR
        to_address: Recipient account hash
    
    Returns:
        Dict with deploy information including deployHash
    """
    if DRY_RUN:
        # Mock deploy hash (64 hex chars)
        mock_deploy_hash = "a" * 64
        logging.info("[DRY RUN] Simulated Casper payment deploy: %s", mock_deploy_hash)
        return {
            "deployHash": mock_deploy_hash,
            "amount": str(amount_cspr),
            "toAddress": to_address,
            "chainName": "casper-test",
            "timestamp": int(time.time())
        }
    else:
        # TODO: Implement real Casper deploy signing and submission
        logging.warning("Real Casper payment not yet implemented. Use DRY_RUN=true")
        return {}


def request_translation(text: str, payment_receipt: Optional[Dict[str, Any]] = None) -> tuple[int, Dict[str, Any]]:
    """
    Request translation from the translation agent.
    
    Args:
        text: Text to translate
        payment_receipt: Optional Casper deploy receipt for payment verification
    
    Returns:
        Tuple of (status_code, response_data)
    """
    if not REQUESTS_AVAILABLE:
        logging.error("requests library not available")
        return 500, {}
    
    try:
        payload = {"text": text}
        if payment_receipt:
            payload["payment_receipt"] = payment_receipt
        
        response = requests.post(TRANSLATE_URL, json=payload, timeout=10)
        return response.status_code, response.json()
    except requests.RequestException as e:
        logging.error("Request failed: %s", e)
        return 500, {}


def handle_payment_required(price_cspr: Decimal, payment_address: str, text: str, retry_count: int = 0) -> Optional[str]:
    """
    Handle 402 Payment Required response.
    
    Flow:
    1. Receive 402 with payment metadata
    2. Create and sign Casper deploy
    3. Submit payment
    4. Retry translation request with receipt
    
    Args:
        price_cspr: Price in CSPR from 402 response
        payment_address: Recipient account hash
        text: Original text to translate
        retry_count: Current retry attempt
    
    Returns:
        Translation result if successful, None otherwise
    """
    if retry_count >= MAX_RETRIES:
        logging.error("Max retries exceeded")
        return None
    
    logging.info("Handling 402 Payment Required (attempt %d/%d)", retry_count + 1, MAX_RETRIES)
    
    # Step 1: Prepare Casper payment
    payment = simulate_casper_payment(price_cspr, payment_address)
    
    if not payment:
        logging.error("Failed to prepare payment")
        return None
    
    deploy_hash = payment.get("deployHash")
    logging.info("Payment prepared with deploy: %s", deploy_hash)
    
    # Step 2: Wait for payment confirmation (mock delay)
    if not DRY_RUN:
        logging.info("Waiting for Casper deploy confirmation...")
        time.sleep(RETRY_DELAY)
    else:
        logging.info("[DRY RUN] Simulating payment confirmation delay...")
        time.sleep(1)
    
    # Step 3: Retry translation with payment receipt
    logging.info("Retrying translation with payment receipt...")
    status, response = request_translation(text, payment_receipt=payment)
    
    if status == 200:
        translation = response.get("result", "")
        logging.info("✅ Translation succeeded: %s", translation)
        return translation
    elif status == 402:
        # Still not paid (shouldn't happen in normal flow)
        logging.warning("Still receiving 402. Retrying...")
        return handle_payment_required(price_cspr, payment_address, text, retry_count + 1)
    else:
        logging.error("Unexpected status code: %d", status)
        return None


def translate_text(text: str) -> Optional[str]:
    """
    Main translation workflow with automatic payment handling.
    
    Args:
        text: Text to translate
    
    Returns:
        Translation result or None if failed
    """
    logging.info("Requesting translation: '%s'", text)
    
    # Step 1: Initial request (likely to receive 402)
    status, response = request_translation(text)
    
    if status == 200:
        # No payment required
        translation = response.get("result", "")
        logging.info("✅ Translation (no payment): %s", translation)
        return translation
    
    elif status == 402:
        # Payment required
        logging.info("Payment required. Processing...")
        
        # Extract payment metadata
        price_cspr = Decimal(response.get("price", "0"))
        payment_address = response.get("payment_address", "")
        
        if not payment_address:
            logging.error("No payment address provided in 402 response")
            return None
        
        # Handle payment and retry
        return handle_payment_required(price_cspr, payment_address, text)
    
    else:
        logging.error("Unexpected status code: %d - %s", status, response)
        return None


def run_test_suite():
    """Run a series of test translations"""
    test_texts = [
        "Hello world",
        "Casper Network adalah blockchain third-generation",
        "Machine-to-machine payments are now possible"
    ]
    
    logging.info("=" * 60)
    logging.info("Starting Research Agent Test Suite")
    logging.info("Translation URL: %s", TRANSLATE_URL)
    logging.info("Dry Run Mode: %s", DRY_RUN)
    logging.info("=" * 60)
    
    results = []
    
    for i, text in enumerate(test_texts, 1):
        logging.info("\n[Test %d/%d] Translating: '%s'", i, len(test_texts), text)
        result = translate_text(text)
        results.append({
            "text": text,
            "translation": result,
            "success": result is not None
        })
        
        if i < len(test_texts):
            time.sleep(2)  # Delay between requests
    
    # Summary
    logging.info("\n" + "=" * 60)
    logging.info("Test Suite Summary:")
    successful = sum(1 for r in results if r["success"])
    logging.info("Successful: %d/%d", successful, len(results))
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        logging.info("%s %s", status, result["text"])
    
    logging.info("=" * 60)


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Translate single text provided as argument
        text = " ".join(sys.argv[1:])
        result = translate_text(text)
        sys.exit(0 if result else 1)
    else:
        # Run test suite
        run_test_suite()


if __name__ == "__main__":
    main()
