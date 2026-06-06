#!/usr/bin/env python3
"""
Casper AI Toolkit helpers for x402 agents.

These pure-Python helpers provide MCP-friendly Casper state snapshots and
CSPR.click payment intents without forcing a specific MCP or wallet SDK runtime.
"""
from __future__ import annotations

import os
from decimal import Decimal
from typing import Any, Dict, Optional

from casper_payment_validator import CASPER_CHAIN_NAME, CASPER_RPC_URL, get_account_info


def cspr_to_motes(amount_cspr: Decimal) -> int:
    """Convert CSPR to motes, Casper's smallest denomination."""
    return int(amount_cspr * Decimal(10**9))


def build_casper_mcp_status(
    *,
    contract_hash: Optional[str],
    account_hash: str,
    price_cspr: Decimal,
    verify_onchain: bool,
) -> Dict[str, Any]:
    """Build a JSON state snapshot that Casper MCP tools can expose to agents."""
    account_info = get_account_info(account_hash) if verify_onchain and account_hash else {}
    return {
        "mcpVersion": "casper-x402-demo/0.1",
        "network": "casper",
        "chainName": CASPER_CHAIN_NAME,
        "rpcUrl": CASPER_RPC_URL,
        "contractHash": contract_hash or os.getenv("CASPER_CONTRACT_HASH", "not-deployed"),
        "accountHash": account_hash,
        "price": {
            "cspr": str(price_cspr),
            "motes": str(cspr_to_motes(price_cspr)),
        },
        "verificationMode": "onchain" if verify_onchain else "mock",
        "accountInfo": account_info,
        "tools": [
            "query_casper_deploy_status",
            "query_casper_account_info",
            "create_cspr_click_payment_intent",
        ],
    }


def build_cspr_click_payment_intent(
    *,
    amount_cspr: Decimal,
    recipient: str,
    chain_name: str,
    memo: str,
) -> Dict[str, Any]:
    """Build a wallet-signing intent compatible with CSPR.click agent workflows."""
    return {
        "provider": "cspr.click",
        "intentType": "native-transfer",
        "network": "casper",
        "chainName": chain_name,
        "recipient": recipient,
        "amount": {
            "cspr": str(amount_cspr),
            "motes": str(cspr_to_motes(amount_cspr)),
        },
        "memo": memo,
        "returnReceiptFields": ["deployHash", "chainName", "amount", "toAddress", "blockTime"],
    }
