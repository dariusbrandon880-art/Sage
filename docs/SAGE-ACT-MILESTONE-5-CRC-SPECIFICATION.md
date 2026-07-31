# SAGE-ACT MILESTONE 5: CRYPTOGRAPHIC SESSION RECEIPT CHAIN (SAGE-CRC) SPECIFICATION

## 1. Executive Summary
The **SAGE Cryptographic Session Receipt Chain (SAGE-CRC)** is an experimental, non-mutating capability designed to secure sequential stateless recovery blocks. By linking successive execution and rehydration traces into a cryptographic hash chain, SAGE-CRC prevents out-of-order execution states, replay attacks, and trace tampering during stateless context recovery.

---

## 2. Architectural Layer & Boundaries
SAGE-CRC operates strictly under the **Experimental Layer** of the SAGE Three-Layer Architecture Schema.
* **Allowed Boundary:** `sage/experimental/act/` and `tests/experimental/`.
* **Protected Boundary:** `sage/runtime/`, `sage/core/`, `sage/acr/`, and `sage/agents/` are kept entirely unmodified and locked.
* **One-Way Import Law:** SAGE-CRC may ingest configuration parameters and payload structures but core production layers are completely blocked from calling or depending on SAGE-CRC interfaces.

---

## 3. Data Model & Block Structure
Each receipt block in the SAGE-CRC chain contains nine mandatory fields:

| Attribute | Data Type | Pattern / Constraints | Purpose |
|---|---|---|---|
| `receipt_id` | `str` | `^receipt_crc_[a-fA-F0-9]{32}$` | Unique identifier of this specific receipt block. |
| `session_id` | `str` | `^session_[a-fA-F0-9]{8}$` | Identifies the execution session containing the trace. |
| `sequence_number` | `int` | `Non-negative, sequential (0, 1, 2, ...)` | Sequential index of the block. Genesis block is `0`. |
| `previous_hash` | `str` | `^[a-fA-F0-9]{64}$` | Hash of the previous block in the chain. Genesis block uses 64 zeros. |
| `payload_hash` | `str` | `^[a-fA-F0-9]{64}$` | The SHA-256 hash of the transaction or CMAPS payload. |
| `timestamp` | `str` | `ISO 8601 UTC format` | Accurate, monotonically increasing UTC timestamp. |
| `signer_identity` | `str` | `^agent_[a-zA-Z0-9_]{3,64}$` | Identity of the agent signing the block. |
| `signature` | `str` | Hexadecimal string | Deterministic mock signature verifying block authenticity. |
| `current_hash` | `str` | `^[a-fA-F0-9]{64}$` | SHA-256 digest of block contents (all fields canonicalized). |

---

## 4. Chaining Mechanics & Hashing
The cryptographic link is established by digesting canonicalized representations of the block fields combined with the previous hash:

$$H_{i} = \text{SHA256}(\text{canonicalize}(\text{receipt\_id} \parallel \text{session\_id} \parallel \text{sequence\_number} \parallel \text{previous\_hash} \parallel \text{payload\_hash} \parallel \text{timestamp} \parallel \text{signer\_identity}))$$

### 4.1 Genesis Block
For the initial block in any session ($i = 0$):
* `previous_hash` is initialized to sixty-four zeros: `"0" * 64`.
* `sequence_number` is strictly `0`.

---

## 5. Validation Rules
The `CryptographicSessionReceiptChain` validator enforces five strict verification checks:

1. **Genesis Rule:** The first block must have a sequence number of `0` and a `previous_hash` of 64 zeros.
2. **Chain Link Rule:** For any block $i > 0$, the `previous_hash` must exactly match the `current_hash` of block $i-1$.
3. **Monotonicity Rule:** Sequence numbers must increase by exactly 1 ($S_i = S_{i-1} + 1$).
4. **Temporal Monotonicity Rule:** Timestamps must be strictly non-decreasing ($T_i \ge T_{i-1}$).
5. **Hash Validity Rule:** Recalculated hash must exactly match the block's `current_hash`.
6. **Signature Rule:** Blocks must possess a valid cryptographic signature mapping back to the authorized `signer_identity`.

Any rule violation triggers a fail-closed response, throwing a `ValueError` to block further trace integration.
