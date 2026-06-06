#!/usr/bin/env python3
"""
research_agent.py

Client agent for the Casper x402 micropayment loop. It requests a translation,
reads the HTTP 402 Casper payment requirements, obtains a CSPR.click-style
payment intent, and retries with a Casper deploy receipt.
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

AGENT_URL = os.getenv("AGENT_URL", os.getenv("TRANSLATE_URL", "http://localhost:5001")).rstrip("/")
TRANSLATION_TEXT = sys.argv[1] if len(sys.argv) > 1 else "Hello world"
CASPER_CHAIN_NAME = os.getenv("CASPER_CHAIN_NAME", "casper-test")
CASPER_PAYMENT_ADDRESS = os.getenv("CASPER_PAYMENT_ADDRESS", "account-hash-demo-recipient")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def request_translation(text: str) -> Optional[Dict[str, Any]]:
    """Request translation without payment and return the 402 metadata or result."""
    logger.info("Requesting translation: %r", text)
    response = requests.post(f"{AGENT_URL}/translate", json={"text": text}, timeout=10)
    if response.status_code in (200, 402):
        return response.json()
    logger.error("Unexpected response %s: %s", response.status_code, response.text)
    return None


def request_cspr_click_intent(memo: str) -> Dict[str, Any]:
    """Fetch the service's CSPR.click-style wallet signing intent."""
    response = requests.post(
        f"{AGENT_URL}/cspr-click/payment-intent",
        json={"memo": memo},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def generate_mock_casper_deploy_hash(text: str, amount: str, recipient: str) -> str:
    """Generate a deterministic mock deploy hash for local demos."""
    seed = f"{text}|{amount}|{recipient}|{time.time_ns()}".encode("utf-8")
    return "0x" + hashlib.sha256(seed).hexdigest()


def submit_casper_payment(payment_requirements: Dict[str, Any], text: str) -> Dict[str, Any]:
    """
    Create a Casper payment receipt.

    In DRY_RUN mode this creates a mock receipt. In production, replace this
    function with Casper SDK / Odra contract interaction or CSPR.click signing.
    """
    amount = str(payment_requirements.get("amount", "0.001"))
    recipient = payment_requirements.get("recipient") or CASPER_PAYMENT_ADDRESS
    chain_name = payment_requirements.get("chainName") or CASPER_CHAIN_NAME

    intent = request_cspr_click_intent(f"x402 translation: {text[:48]}")
    logger.info("CSPR.click payment intent: %s", json.dumps(intent, indent=2))

    if DRY_RUN:
        logger.info("DRY_RUN=true: generating mock Casper deploy receipt")
        deploy_hash = generate_mock_casper_deploy_hash(text, amount, recipient)
    else:
        logger.warning("Real Casper submission is not wired in this demo; using mock deploy hash placeholder")
        deploy_hash = generate_mock_casper_deploy_hash(text, amount, recipient)

    return {
        "deployHash": deploy_hash,
        "chainName": chain_name,
        "amount": str(Decimal(amount)),
        "toAddress": recipient,
        "blockTime": int(time.time()),
        "source": "cspr.click-intent" if not DRY_RUN else "mock-cspr-click-intent",
    }


def retry_with_payment(text: str, receipt: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Retry translation with Casper payment proof."""
    response = requests.post(
        f"{AGENT_URL}/translate",
        json={"text": text, "payment_receipt": receipt},
        timeout=10,
    )
    if response.status_code in (200, 402):
        return response.json()
    logger.error("Unexpected retry response %s: %s", response.status_code, response.text)
    return None


def main() -> None:
    logger.info("Starting Casper research agent (chain=%s, dry_run=%s)", CASPER_CHAIN_NAME, DRY_RUN)
    payment_info = request_translation(TRANSLATION_TEXT)
    if not payment_info:
        raise SystemExit(1)

    if "result" in payment_info:
        logger.info("Translation succeeded without payment: %s", payment_info["result"])
        return

    logger.info("Payment requirements: %s", json.dumps(payment_info, indent=2))
    receipt = submit_casper_payment(payment_info, TRANSLATION_TEXT)
    logger.info("Submitting Casper receipt: %s", json.dumps(receipt, indent=2))

    result = retry_with_payment(TRANSLATION_TEXT, receipt)
    if result and "result" in result:
        logger.info("Translation result: %s", result["result"])
        logger.info("Verification: %s", result.get("verification"))
        return

    logger.error("Payment retry failed: %s", json.dumps(result or {}, indent=2))
    raise SystemExit(1)


if __name__ == "__main__":
    main()
