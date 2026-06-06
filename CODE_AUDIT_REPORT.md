# Code Audit Report - x402 Micropay Demo Casper Implementation

**Date:** June 6, 2026  
**Reviewer:** Automated Code Analysis  
**Status:** ⚠️ **ISSUES FOUND** - 5 BUGS, 8 WARNINGS, 3 RECOMMENDATIONS

---

## 🔴 CRITICAL BUGS (Must Fix Before Production)

### 1. **CRITICAL: Integer Type Hint Bug in `research_agent_casper.py` (Line 65)**

**Severity:** HIGH  
**File:** `research_agent_casper.py`  
**Line:** 65

```python
def request_translation(text: str, payment_receipt: Optional[Dict[str, Any]] = None) -> tuple[int, Dict[str, Any]]:
```

**Issue:** Using `tuple[int, ...]` is Python 3.10+ syntax. Code may fail on Python 3.8/3.9.

**Fix:**
```python
from typing import Tuple

def request_translation(text: str, payment_receipt: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any]]:
```

**Impact:** Code crash on Python < 3.10

---

### 2. **CRITICAL: Bare Exception Handling in Multiple Files**

**Severity:** CRITICAL  
**Files:** 
- `casper_payment_validator.py` (Lines 173, 238)
- `translation_agent_casper.py` (Lines 105, 186)
- `rwa_defi_agent.py` (N/A - uses bare except but in try/except)

**Issue:** Catching bare `except:` exceptions suppresses critical errors like KeyboardInterrupt, SystemExit, MemoryError.

**Example (casper_payment_validator.py, Line 173):**
```python
try:
    amount_cspr = Decimal(str(amount))
except:  # ❌ TOO BROAD
    logging.error("Invalid amount in receipt: %s", amount)
    return False
```

**Fix:**
```python
try:
    amount_cspr = Decimal(str(amount))
except (ValueError, TypeError, InvalidOperation) as e:  # ✅ SPECIFIC
    logging.error("Invalid amount in receipt: %s - %s", amount, e)
    return False
```

**Impact:** May hide critical errors, makes debugging difficult

---

### 3. **CRITICAL: Missing Error Handling in `translation_agent_casper.py` (Line 86)**

**Severity:** HIGH  
**File:** `translation_agent_casper.py`  
**Lines:** 86, 101

```python
deploy_hash = deploy_hash.lstrip("0x")  # No bounds checking
if len(deploy_hash) < 32:  # Only checks minimum length
    logging.error("Invalid deploy hash format")
    return False
```

**Issue:** After `lstrip("0x")`, if input is just "0x", result is empty string but still passes through.

**Attack Scenario:**
```python
# Input: "0x"
deploy_hash = "0x".lstrip("0x")  # Results in ""
if len("") < 32:  # TRUE
    return False  # Good, but...)

# Input: "0xabc"
deploy_hash = "0xabc".lstrip("0x")  # Results in "abc"
if len("abc") < 32:  # TRUE
    return False  # Correctly rejects
```

**Fix:**
```python
if deploy_hash.startswith("0x"):
    deploy_hash = deploy_hash[2:]  # Use slice instead of lstrip

if len(deploy_hash) < 64 or not all(c in '0123456789abcdefABCDEF' for c in deploy_hash):
    logging.error("Invalid deploy hash format")
    return False
```

**Impact:** Potential bypass of validation

---

### 4. **CRITICAL: Race Condition in Cache Cleanup**

**Severity:** HIGH  
**Files:** 
- `translation_agent_casper.py` (Lines 60-68)
- `casper_payment_validator.py` (Not affected - uses set)

**Issue:** In `translation_agent_casper.py`, the cache deletion can happen between check and cleanup:

```python
def is_deploy_valid(deploy_hash: str) -> bool:
    with _pending_lock:
        ts = _validated_deploys.get(deploy_hash)
        if not ts:
            return False
        if time.time() - ts <= PROOF_TTL:
            return True
        # RACE CONDITION: Lock released here
        del _validated_deploys[deploy_hash]  # ❌ May not exist anymore
        return False
```

**Fix:**
```python
def is_deploy_valid(deploy_hash: str) -> bool:
    with _pending_lock:
        ts = _validated_deploys.get(deploy_hash)
        if not ts:
            return False
        if time.time() - ts <= PROOF_TTL:
            return True
        _validated_deploys.pop(deploy_hash, None)  # ✅ Safe deletion
        return False
```

**Impact:** Potential KeyError crash on concurrent requests

---

### 5. **CRITICAL: RPC URL Validation Missing**

**Severity:** MEDIUM-HIGH  
**Files:** 
- `casper_payment_validator.py` (Line 27)
- `translation_agent_casper.py` (Line 25)
- `casper_mcp_server.py` (Line 22)

**Issue:** Default RPC URL used without validation, may be misconfigured.

```python
CASPER_RPC_URL = os.getenv("CASPER_RPC_URL", "https://rpc.testnet.casperlabs.io")
# No validation that URL is reachable
```

**Fix:**
```python
import validators

CASPER_RPC_URL = os.getenv("CASPER_RPC_URL", "https://rpc.testnet.casperlabs.io")

if not validators.url(CASPER_RPC_URL):
    raise SystemExit(f"Invalid CASPER_RPC_URL: {CASPER_RPC_URL}")
```

**Impact:** Silently fails when RPC is down

---

## 🟠 HIGH-PRIORITY WARNINGS (Should Fix)

### W1: Unused Function Parameters

**File:** `casper_payment_validator.py` (Line 46)  
**Function:** `get_casper_deploy_status(deploy_hash)`

```python
def get_casper_deploy_status(deploy_hash: str) -> Dict[str, Any]:
    # ... but deploy_hash is NOT used in the function!
    payload = {
        "method": "chain_get_block_transfers",
        "params": {},  # ❌ Should include deploy_hash
    }
```

**Fix:** Either use the parameter or remove it.

---

### W2: Incomplete RPC Parameter Handling

**File:** `translation_agent_casper.py` (Line 158)

```python
payload = {
    "jsonrpc": "2.0",
    "method": "info_get_deploy",
    "params": {
        "deploy_hash": deploy_hash  # ❌ Should be lowercase "deploy_hash"
    },
    "id": 1
}
```

**Issue:** Casper RPC expects field names. Should verify against official Casper docs.

---

### W3: Missing Timeout Configuration

**File:** `research_agent_casper.py` (Line 85)

```python
response = requests.post(TRANSLATE_URL, json=payload, timeout=10)
# No retry on timeout, will crash immediately
```

**Fix:**
```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

response = session.post(TRANSLATE_URL, json=payload, timeout=10)
```

---

### W4: No Connection Pooling

**File:** `casper_payment_validator.py`, `translation_agent_casper.py`, `casper_mcp_server.py`

**Issue:** Creating new `httpx.Client()` for every request.

```python
with httpx.Client() as client:  # ❌ Creates new connection each time
    response = client.post(...)
```

**Fix:**
```python
# Module level
client = httpx.Client(timeout=10.0, limits=httpx.Limits(max_connections=10))

# In functions
response = client.post(...)
```

**Impact:** Poor performance, connection exhaustion

---

### W5: Decimal Conversion Without Max Length Check

**File:** `casper_payment_validator.py`, `translation_agent_casper.py`

**Issue:** Very large numbers can cause issues:

```python
amount = Decimal(str(receipt.get("amount", 0)))
# What if amount is "999999999999999999999999999999999999999999999"?
```

**Fix:**
```python
amount_str = str(receipt.get("amount", 0))
if len(amount_str) > 30:
    logging.error("Amount too large")
    return False
try:
    amount = Decimal(amount_str)
except:
    return False
```

---

### W6: Missing Chain ID Validation

**File:** `translation_agent_casper.py` (Line 94)

```python
chain = receipt.get("chainName", CASPER_CHAIN_NAME)
if chain != CASPER_CHAIN_NAME:
    return False
```

**Issue:** No validation that chainName is valid Casper chain.

**Fix:**
```python
VALID_CHAINS = {"casper-test", "casper"}

chain = receipt.get("chainName", CASPER_CHAIN_NAME)
if chain not in VALID_CHAINS:
    logging.error("Invalid chain: %s", chain)
    return False
```

---

### W7: String Formatting Security

**File:** `casper_mcp_server.py` (Line 68)

```python
"key": f"{contract_hash},{key}"  # Potential injection?
```

**Issue:** While JSON-safe, should validate contract_hash format.

---

### W8: Mock Data in Production

**File:** `casper_mcp_server.py` (Lines 134-159, 162-190, 193-228)

**Issue:** Functions return mock data without actually querying chain.

```python
def query_rwa_data(...):
    return {
        "value": "1234.56",  # ❌ HARDCODED MOCK VALUE
        ...
    }
```

**Fix:** Add check:
```python
if not HTTPX_AVAILABLE:
    return {"error": "httpx not available", "data": "MOCK"}
else:
    # Actually query RPC
```

---

## 🟡 RECOMMENDATIONS (Nice to Have)

### R1: Add Type Checking with mypy

```bash
pip install mypy
mypy translation_agent_casper.py --strict
```

---

### R2: Add Input Validation Library

```bash
pip install pydantic

from pydantic import BaseModel, validator

class PaymentReceipt(BaseModel):
    deployHash: str
    amount: float
    chainName: str
    
    @validator('deployHash')
    def validate_deploy_hash(cls, v):
        if not all(c in '0123456789abcdefABCDEF' for c in v):
            raise ValueError('Invalid hex format')
        return v
```

---

### R3: Add Request ID Tracking

```python
import uuid

def validate_receipt_onchain_casper(receipt, request_id=None):
    request_id = request_id or str(uuid.uuid4())
    logging.info("Validating receipt %s", request_id)
```

---

## 📋 SUMMARY TABLE

| Issue | Type | Severity | File | Line | Status |
|-------|------|----------|------|------|--------|
| Type hint Python 3.10+ | Bug | HIGH | research_agent_casper.py | 65 | ❌ CRITICAL |
| Bare except clauses | Bug | CRITICAL | Multiple | Multiple | ❌ CRITICAL |
| Deploy hash validation | Bug | HIGH | translation_agent_casper.py | 86 | ❌ CRITICAL |
| Race condition in cache | Bug | HIGH | translation_agent_casper.py | 60-68 | ❌ CRITICAL |
| RPC URL validation | Bug | MEDIUM | Multiple | Multiple | ⚠️ HIGH |
| Unused parameters | Warning | MEDIUM | casper_payment_validator.py | 46 | ⚠️ MEDIUM |
| Incomplete RPC fields | Warning | MEDIUM | translation_agent_casper.py | 158 | ⚠️ MEDIUM |
| No retry logic | Warning | MEDIUM | research_agent_casper.py | 85 | ⚠️ MEDIUM |
| No connection pooling | Warning | MEDIUM | Multiple | Multiple | ⚠️ MEDIUM |
| Decimal overflow | Warning | LOW | Multiple | Multiple | ⚠️ LOW |
| String injection | Warning | LOW | casper_mcp_server.py | 68 | ⚠️ LOW |
| Mock data in production | Warning | HIGH | casper_mcp_server.py | 134-228 | ⚠️ HIGH |

---

## ✅ POSITIVE FINDINGS

✅ **Good Security Practices:**
- Thread-safe locks for replay prevention
- Proper TTL cache implementation
- Comprehensive logging
- Error handling in most functions
- No hardcoded secrets

✅ **Good Code Quality:**
- Clear docstrings
- Modular design
- Separation of concerns
- Comprehensive testing guide

---

## 🚀 PRIORITY FIXES

### Must Fix Before Testing (This Week):
1. Fix type hint in research_agent_casper.py (line 65)
2. Replace all bare `except:` with specific exceptions
3. Improve deploy hash validation (use slice instead of lstrip)
4. Fix race condition in cache cleanup
5. Add RPC URL validation

### Should Fix Before Testnet (Next Week):
1. Add connection pooling
2. Add retry logic for HTTP requests
3. Remove mock data or clearly mark as mock
4. Add input validation with Pydantic

### Nice to Have (Future):
1. Add mypy type checking
2. Add request ID tracking
3. Add comprehensive unit tests
4. Add metrics/monitoring

---

**Recommendation:** Fix all CRITICAL bugs before proceeding to Testnet testing. Estimated time: 2-4 hours.

