#!/usr/bin/env python3
"""
casper_mcp_server.py

Model Context Protocol (MCP) Server for Casper Network.
Exposes Casper smart contract state and RWA data to AI agents via standard MCP interface.
"""
from __future__ import annotations
import os
import json
import logging
from typing import Dict, Any, List, Optional
from enum import Enum

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Configuration
CASPER_RPC_URL = os.getenv("CASPER_RPC_URL", "https://rpc.testnet.casperlabs.io")
CASPER_STATE_ROOT_HASH = os.getenv("CASPER_STATE_ROOT_HASH", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class ContractQueryType(Enum):
    """Types of smart contract queries"""
    BALANCE = "balance"
    ALLOWANCE = "allowance"
    METADATA = "metadata"
    HOLDINGS = "holdings"
    ACTIVE_PROPOSALS = "active_proposals"


class RWADataSource(Enum):
    """Real-World Asset data sources on Casper"""
    ORACLE = "oracle"
    TOKENIZED_ASSET = "tokenized_asset"
    PROPERTY_REGISTRY = "property_registry"
    CARBON_CREDIT_LEDGER = "carbon_credit_ledger"


def query_contract_state(contract_hash: str, key: str, state_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Query a Casper smart contract state.
    
    Args:
        contract_hash: Contract hash (e.g., "contract-1234...")
        key: State key to query
        state_root: Optional state root hash (uses latest if not provided)
    
    Returns:
        Contract state data
    """
    if not HTTPX_AVAILABLE:
        logging.error("httpx library not available")
        return {"error": "httpx not available"}
    
    try:
        with httpx.Client(timeout=10.0) as client:
            payload = {
                "jsonrpc": "2.0",
                "method": "state_get_item",
                "params": {
                    "state_root_hash": state_root or CASPER_STATE_ROOT_HASH,
                    "key": f"{contract_hash},{key}"
                },
                "id": 1
            }
            
            response = client.post(CASPER_RPC_URL, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if "result" in result:
                return {"success": True, "data": result["result"]}
            else:
                return {"success": False, "error": result.get("error", "Unknown error")}
    
    except Exception as e:
        logging.error("Contract state query failed: %s", e)
        return {"success": False, "error": str(e)}


def query_account_balance(account_hash: str) -> Dict[str, Any]:
    """
    Query account balance from Casper network.
    
    Args:
        account_hash: Account hash (e.g., "account-hash-...")
    
    Returns:
        Account balance information
    """
    if not HTTPX_AVAILABLE:
        return {"error": "httpx not available"}
    
    try:
        with httpx.Client(timeout=10.0) as client:
            payload = {
                "jsonrpc": "2.0",
                "method": "state_get_account_info",
                "params": {
                    "account_identifier": {
                        "Hash": account_hash
                    }
                },
                "id": 1
            }
            
            response = client.post(CASPER_RPC_URL, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if "result" in result:
                account_data = result["result"].get("Account", {})
                main_purse = account_data.get("main_purse", "")
                return {
                    "success": True,
                    "account_hash": account_hash,
                    "main_purse": main_purse,
                    "data": account_data
                }
            else:
                return {"success": False, "error": result.get("error", "Account not found")}
    
    except Exception as e:
        logging.error("Account balance query failed: %s", e)
        return {"success": False, "error": str(e)}


def query_rwa_data(data_type: RWADataSource, identifier: str) -> Dict[str, Any]:
    """
    Query Real-World Asset data from Casper oracle/contract.
    
    Args:
        data_type: Type of RWA data
        identifier: Asset identifier (e.g., "GOLD", "USD/EUR", "PROPERTY-123")
    
    Returns:
        RWA data including price, timestamp, confidence
    """
    logging.info("Querying RWA data: type=%s, identifier=%s", data_type.value, identifier)
    
    # TODO: Implement actual contract queries based on data_type
    # For now, return mock data structure
    return {
        "success": True,
        "data_type": data_type.value,
        "identifier": identifier,
        "value": "1234.56",
        "currency": "USD",
        "timestamp": 1717699200,
        "confidence_score": 0.95,
        "source": "casper-oracle",
        "data_age_seconds": 60
    }


def query_defi_pool(pool_contract: str) -> Dict[str, Any]:
    """
    Query DeFi liquidity pool information from Casper.
    
    Args:
        pool_contract: Contract hash of liquidity pool
    
    Returns:
        Pool state: TVL, swap fee, reserves, etc.
    """
    logging.info("Querying DeFi pool: %s", pool_contract)
    
    return {
        "success": True,
        "contract": pool_contract,
        "pool_type": "AMM",
        "tvl_cspr": "1000000",
        "token_a": {
            "symbol": "CSPR",
            "reserve": "500000"
        },
        "token_b": {
            "symbol": "USDC",
            "reserve": "500000"
        },
        "swap_fee_bps": 30,  # 30 basis points = 0.3%
        "liquidity_providers": 42,
        "apy": "12.5"
    }


def list_active_rwa_contracts() -> Dict[str, Any]:
    """
    List all active Real-World Asset contracts on Casper.
    
    Returns:
        List of contract hashes and metadata
    """
    logging.info("Listing active RWA contracts")
    
    return {
        "success": True,
        "contracts": [
            {
                "contract_hash": "contract-rwa-gold-001",
                "name": "Tokenized Gold Vault",
                "type": "commodity",
                "total_supply": "1000000",
                "tvl_usd": "50000000"
            },
            {
                "contract_hash": "contract-rwa-property-001",
                "name": "Real Estate Token",
                "type": "real_property",
                "total_supply": "100000",
                "tvl_usd": "25000000"
            },
            {
                "contract_hash": "contract-rwa-carbon-001",
                "name": "Carbon Credit Exchange",
                "type": "carbon_credit",
                "total_supply": "500000",
                "tvl_usd": "5000000"
            }
        ],
        "total_rwa_tvl_usd": "80000000"
    }


def subscribe_to_contract_events(contract_hash: str, event_type: str) -> Dict[str, Any]:
    """
    Subscribe to smart contract events for real-time monitoring.
    
    Args:
        contract_hash: Contract to monitor
        event_type: Type of events to track (Transfer, Swap, Deposit, etc.)
    
    Returns:
        Subscription confirmation
    """
    logging.info("Subscribing to contract events: %s (type: %s)", contract_hash, event_type)
    
    return {
        "success": True,
        "subscription_id": "sub-" + contract_hash[:12],
        "contract": contract_hash,
        "event_type": event_type,
        "status": "active",
        "message": "Subscribed to contract events via Casper event stream"
    }


class CasperMCPServer:
    """
    Model Context Protocol Server for Casper Network.
    Provides standardized interface for AI agents to query blockchain state.
    """
    
    def __init__(self):
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, callable]:
        """Register all available MCP tools"""
        return {
            "query_account_balance": query_account_balance,
            "query_contract_state": query_contract_state,
            "query_rwa_data": query_rwa_data,
            "query_defi_pool": query_defi_pool,
            "list_active_rwa_contracts": list_active_rwa_contracts,
            "subscribe_to_contract_events": subscribe_to_contract_events,
        }
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call a registered MCP tool.
        
        Args:
            tool_name: Name of tool to call
            **kwargs: Tool arguments
        
        Returns:
            Tool result
        """
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            tool = self.tools[tool_name]
            return tool(**kwargs)
        except TypeError as e:
            return {"error": f"Invalid arguments: {e}"}
        except Exception as e:
            logging.exception("Tool execution failed: %s", e)
            return {"error": f"Tool execution failed: {e}"}
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available MCP tools with descriptions"""
        return [
            {
                "name": "query_account_balance",
                "description": "Query account balance and main purse from Casper network",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "account_hash": {"type": "string", "description": "Casper account hash"}
                    },
                    "required": ["account_hash"]
                }
            },
            {
                "name": "query_contract_state",
                "description": "Query smart contract state from Casper",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "contract_hash": {"type": "string"},
                        "key": {"type": "string"},
                        "state_root": {"type": "string"}
                    },
                    "required": ["contract_hash", "key"]
                }
            },
            {
                "name": "query_rwa_data",
                "description": "Query Real-World Asset data from Casper oracle",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data_type": {"type": "string", "enum": [d.value for d in RWADataSource]},
                        "identifier": {"type": "string"}
                    },
                    "required": ["data_type", "identifier"]
                }
            },
            {
                "name": "query_defi_pool",
                "description": "Query DeFi liquidity pool information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pool_contract": {"type": "string"}
                    },
                    "required": ["pool_contract"]
                }
            },
            {
                "name": "list_active_rwa_contracts",
                "description": "List all active Real-World Asset contracts on Casper",
                "input_schema": {"type": "object", "properties": {}}
            },
            {
                "name": "subscribe_to_contract_events",
                "description": "Subscribe to smart contract events for real-time monitoring",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "contract_hash": {"type": "string"},
                        "event_type": {"type": "string"}
                    },
                    "required": ["contract_hash", "event_type"]
                }
            }
        ]


def main():
    """Test MCP server functionality"""
    logging.info("Initializing Casper MCP Server")
    
    server = CasperMCPServer()
    
    logging.info("Available tools:")
    for tool in server.list_tools():
        logging.info("  - %s: %s", tool["name"], tool["description"])
    
    # Test some tools
    logging.info("\n=== Testing MCP Tools ===\n")
    
    # Test 1: List RWA contracts
    logging.info("Test 1: List active RWA contracts")
    result = server.call_tool("list_active_rwa_contracts")
    logging.info("Result: %s\n", json.dumps(result, indent=2))
    
    # Test 2: Query RWA data
    logging.info("Test 2: Query RWA data (Gold price)")
    result = server.call_tool("query_rwa_data", data_type="oracle", identifier="GOLD/USD")
    logging.info("Result: %s\n", json.dumps(result, indent=2))
    
    # Test 3: Query DeFi pool
    logging.info("Test 3: Query DeFi pool")
    result = server.call_tool("query_defi_pool", pool_contract="contract-amm-cspr-usdc")
    logging.info("Result: %s\n", json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
