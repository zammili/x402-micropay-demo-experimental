#!/usr/bin/env python3
"""
translation_agent.py

Casper Network x402 translation service.

The service returns HTTP 402 with Casper payment requirements when a request is
missing a valid receipt. Clients retry with a Casper deploy receipt under the
`payment_receipt` JSON key. Local development uses the mock Casper validator;
set VERIFY_ONCHAIN=true to verify deploys against Casper Testnet RPC.
"""
from __future__ import annotations

import logging
import os
from decimal import Decimal, InvalidOperation
from typing import Any, Dict

from flask import Flask, jsonify, request

from casper_ai_toolkit import build_casper_mcp_status, build_cspr_click_payment_intent
from casper_payment_validator import (
    CASPER_CHAIN_NAME,
    CASPER_PAYMENT_ADDRESS,
    CASPER_RPC_URL,
    PRICE_CSPR,
    get_casper_deploy_status,
    validate_receipt_mock_casper,
    validate_receipt_onchain_casper,
)

# Config
VERIFY_ONCHAIN = os.getenv("VERIFY_ONCHAIN", "false").lower() in ("1", "true", "yes")
PORT = int(os.getenv("PORT", "5001"))
PAYMENT_ADDRESS = os.getenv("CASPER_PAYMENT_ADDRESS", CASPER_PAYMENT_ADDRESS)
PRICE_CSPR_ENV = os.getenv("PRICE_CSPR", str(PRICE_CSPR))

try:
    PRICE = Decimal(str(PRICE_CSPR_ENV))
except InvalidOperation as exc:
    raise SystemExit("Invalid PRICE_CSPR") from exc

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def build_payment_requirements() -> Dict[str, Any]:
    """Return x402-compatible Casper payment metadata for agents."""
    return {
        "x402Version": "0.1",
        "error": "Payment required",
        "paymentNetwork": "casper",
        "chainName": CASPER_CHAIN_NAME,
        "rpcUrl": CASPER_RPC_URL,
        "amount": str(PRICE),
        "currency": "CSPR",
        "amountMotes": str(int(PRICE * Decimal(10**9))),
        "recipient": PAYMENT_ADDRESS,
        "receiptSchema": {
            "deployHash": "0x-prefixed Casper deploy hash",
            "chainName": CASPER_CHAIN_NAME,
            "amount": "CSPR amount as a decimal string",
            "toAddress": PAYMENT_ADDRESS,
            "blockTime": "Unix timestamp from the accepted block",
        },
        "aiToolkit": {
            "mcpStatusEndpoint": "/mcp/casper/status",
            "csprClickIntentEndpoint": "/cspr-click/payment-intent",
        },
    }


def validate_casper_receipt(receipt: Dict[str, Any]) -> bool:
    """Validate a Casper payment receipt using mock or Testnet RPC mode."""
    if VERIFY_ONCHAIN:
        return validate_receipt_onchain_casper(receipt)
    return validate_receipt_mock_casper(receipt)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "ok": True,
            "network": "casper",
            "verify_onchain": VERIFY_ONCHAIN,
            "payment_address": PAYMENT_ADDRESS,
            "price_cspr": str(PRICE),
            "chain_name": CASPER_CHAIN_NAME,
            "rpc_url": CASPER_RPC_URL,
        }
    )


@app.route("/mcp/casper/status", methods=["GET"])
def casper_mcp_status():
    """Expose Casper contract/payment state in an MCP-friendly JSON shape."""
    contract_hash = request.args.get("contractHash")
    account_hash = request.args.get("accountHash", PAYMENT_ADDRESS)
    return jsonify(
        build_casper_mcp_status(
            contract_hash=contract_hash,
            account_hash=account_hash,
            price_cspr=PRICE,
            verify_onchain=VERIFY_ONCHAIN,
        )
    )


@app.route("/cspr-click/payment-intent", methods=["GET", "POST"])
def cspr_click_payment_intent():
    """Return a CSPR.click-compatible intent for wallet signing workflows."""
    data = request.get_json(silent=True) or {}
    memo = data.get("memo") or request.args.get("memo") or "x402 translation micropayment"
    return jsonify(
        build_cspr_click_payment_intent(
            amount_cspr=PRICE,
            recipient=PAYMENT_ADDRESS,
            chain_name=CASPER_CHAIN_NAME,
            memo=memo,
        )
    )


@app.route("/casper/deploy/<deploy_hash>", methods=["GET"])
def casper_deploy(deploy_hash: str):
    """Expose deploy status for agents and demo tooling."""
    return jsonify(get_casper_deploy_status(deploy_hash))


@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json(silent=True) or {}
    text_to_translate = data.get("text", "")
    receipt = data.get("payment_receipt")

    if receipt:
        logging.info("Received Casper payment_receipt in request")
        if validate_casper_receipt(receipt):
            return jsonify(
                {
                    "result": f"[Casper-paid translation] {text_to_translate[::-1]}",
                    "verification": "casper-onchain" if VERIFY_ONCHAIN else "casper-mock",
                    "network": "casper",
                    "chainName": CASPER_CHAIN_NAME,
                }
            )
        return jsonify({**build_payment_requirements(), "error": "Invalid Casper payment receipt"}), 402

    return jsonify(build_payment_requirements()), 402


if __name__ == "__main__":
    logging.info("Starting Casper x402 Translation Agent on port %s", PORT)
    logging.info("Payment: %s CSPR to %s on %s", PRICE, PAYMENT_ADDRESS, CASPER_CHAIN_NAME)
    app.run(host="0.0.0.0", port=PORT)
