#!/usr/bin/env python3
"""
research_agent_quantum.py

Client agent that:
- Requests translations
- Handles 402 Payment Required responses
- Generates quantum-resistant payment proofs
- Supports ALL Solana networks (testnet, mainnet, devnet)
"""
import os
import sys
import json
import logging
import requests
from decimal import Decimal

from quantum_resistant_crypto import QuantumResistantPaymentProof

# Configuration
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:5002")
TRANSLATION_TEXT = sys.argv[1] if len(sys.argv) > 1 else "Hello world"
SOLANA_CLUSTER = os.getenv("SOLANA_CLUSTER", "testnet")
QUANTUM_ENABLED = os.getenv("QUANTUM_ENABLED", "true").lower() in ("1", "true", "yes")
USE_HYBRID_MODE = os.getenv("USE_HYBRID_MODE", "true").lower() in ("1", "true", "yes")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def request_translation(text: str) -> dict:
    """
    Step 1: Request translation without payment.
    Expect 402 response with payment requirements.
    """
    logger.info("📝 Requesting translation: '%s'", text)
    
    try:
        response = requests.post(
            f"{AGENT_URL}/translate",
            json={"text": text},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Translation succeeded without payment (mock mode?)")
            return response.json()
        
        if response.status_code == 402:
            logger.info("⏳ Received 402 Payment Required")
            return response.json()
        
        logger.error("❌ Unexpected response: %s", response.status_code)
        return None
    
    except Exception as e:
        logger.exception("Error requesting translation: %s", e)
        return None


def generate_quantum_proof() -> dict:
    """
    Step 2: Generate quantum-resistant payment proof.
    """
    logger.info("🔐 Generating quantum-resistant payment proof...")
    
    try:
        qrp = QuantumResistantPaymentProof(enable_quantum=QUANTUM_ENABLED)
        
        # Create mock payment commitment
        commitment = qrp.create_payment_commitment(
            transaction_hash="5vbX7T2X3Y4Z5a6B7c8D9E0F1G2H3I4J5K6L7M8N9O0P1Q2R3S4T5U",
            amount_lamports=1_000_000,
            payment_address="YourTestnetSolanaAddressHere"
        )
        
        # Sign the commitment
        proof = qrp.sign_payment_proof(commitment)
        
        logger.info(
            "✅ Quantum proof generated (Algo: %s, Hybrid: %s)",
            proof.get("algorithm"),
            proof.get("hybrid_mode")
        )
        
        return proof
    
    except Exception as e:
        logger.exception("Error generating quantum proof: %s", e)
        return None


def generate_mock_solana_receipt() -> dict:
    """
    Step 2 (Alt): Generate mock Solana on-chain receipt.
    For testing without real transactions.
    """
    logger.info("📋 Generating mock Solana receipt (cluster: %s)...", SOLANA_CLUSTER)
    
    return {
        "transactionHash": "5vbX7T2X3Y4Z5a6B7c8D9E0F1G2H3I4J5K6L7M8N9O0P1Q2R3S4T5U",
        "blockNumber": 123456789,
        "status": 1,
        "cluster": SOLANA_CLUSTER,
        "amount_lamports": 1_000_000
    }


def retry_with_payment(text: str, use_quantum: bool = True) -> dict:
    """
    Step 3: Retry translation with payment proof.
    """
    logger.info("💳 Retrying with payment proof (Quantum: %s)...", use_quantum)
    
    payload = {"text": text}
    
    if use_quantum:
        # Use quantum-resistant proof
        quantum_proof = generate_quantum_proof()
        if quantum_proof:
            payload["quantum_proof"] = quantum_proof
    else:
        # Use on-chain mock receipt
        payment_receipt = generate_mock_solana_receipt()
        payload["payment_receipt"] = payment_receipt
    
    try:
        response = requests.post(
            f"{AGENT_URL}/translate",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Translation succeeded with payment!")
            return response.json()
        
        if response.status_code == 402:
            logger.warning("⚠️  Still receiving 402 (payment still invalid)")
            return response.json()
        
        logger.error("❌ Error: %s", response.status_code)
        return None
    
    except Exception as e:
        logger.exception("Error retrying with payment: %s", e)
        return None


def main():
    """
    Main workflow:
    1. Request translation (expect 402)
    2. Generate payment proof (quantum or on-chain)
    3. Retry with payment
    4. Profit!
    """
    logger.info("🚀 Starting research agent (Network: %s)", SOLANA_CLUSTER)
    logger.info("="*60)
    
    # Step 1: Request without payment
    payment_info = request_translation(TRANSLATION_TEXT)
    if not payment_info:
        logger.error("Failed to request translation")
        return
    
    logger.info("Payment requirements: %s", json.dumps(payment_info, indent=2))
    
    # Step 2: Generate payment proof
    result = retry_with_payment(
        TRANSLATION_TEXT,
        use_quantum=QUANTUM_ENABLED
    )
    
    if result:
        logger.info("="*60)
        logger.info("🎉 SUCCESS!")
        logger.info("Result: %s", result.get("result", "N/A"))
        logger.info("Verification: %s", result.get("verification", "N/A"))
        logger.info("Network: %s", result.get("network", "N/A"))
    else:
        logger.error("Failed to get translation with payment")


if __name__ == "__main__":
    main()
