"""SAGE Capability Warehouse Auto-Promotion Engine.

Executes Stage 4 (Warehouse Promote) of the canonical 5x4 Big Jump Wave frame:
- Receives wave reconvergence receipts and validated evidence packages.
- Enforces exact 40-character commit SHA binding and fail-closed evidence validation.
- Promotes reusable capability items, patterns, and evidence into the Capability Warehouse.
- Synchronizes promoted capabilities with SAGEOperationalCapabilityRegistry.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.capability_registry import SAGECapability, SAGEOperationalCapabilityRegistry


class PromotionStatus(str, Enum):
    """Promotion status of a warehouse item."""
    PROMOTED = "PROMOTED"
    RECONCILED = "RECONCILED"
    SUPERSEDED = "SUPERSEDED"
    REJECTED_UNVERIFIED = "REJECTED_UNVERIFIED"


class WarehouseItem(BaseModel):
    """Schema representing an item stored in the capability warehouse."""
    item_id: str
    capability_id: str
    name: str
    description: str
    wave_id: str
    exact_commit_sha: str
    promotion_status: PromotionStatus = PromotionStatus.PROMOTED
    reusable_patterns: List[str] = Field(default_factory=list)
    evidence_references: List[str] = Field(default_factory=list)
    test_references: List[str] = Field(default_factory=list)
    promoted_at: float = Field(default_factory=time.time)


class WarehousePromotionReceipt(BaseModel):
    """Cryptographic evidence receipt for a wave capability promotion event."""
    receipt_id: str
    wave_id: str
    exact_git_head: str
    promoted_items_count: int
    promoted_capability_ids: List[str]
    reconvergence_verdict: str
    rolls_royce_passed: bool
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""

    def compute_hash(self) -> str:
        caps_str = ",".join(sorted(self.promoted_capability_ids))
        payload = (
            f"{self.receipt_id}:{self.wave_id}:{self.exact_git_head}:{self.promoted_items_count}:"
            f"{caps_str}:{self.reconvergence_verdict}:{self.rolls_royce_passed}:{self.timestamp}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CapabilityWarehouseEngine:
    """Engine managing capability promotion into the canonical SAGE Warehouse."""

    def __init__(
        self,
        storage_path: str = "evidence_capture/capability_warehouse_registry.json",
        op_registry_path: Optional[str] = None,
    ):
        self.storage_path = storage_path
        self.items: Dict[str, WarehouseItem] = {}
        if op_registry_path:
            self.op_registry = SAGEOperationalCapabilityRegistry(storage_path=op_registry_path)
        else:
            self.op_registry = SAGEOperationalCapabilityRegistry()
        self.load()

    def load(self) -> None:
        """Loads warehouse items from disk if available."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item_data in data:
                        item = WarehouseItem(**item_data)
                        self.items[item.item_id] = item
            except Exception as exc:
                print(f"[*] Warning loading warehouse items: {exc}")

    def save(self) -> None:
        """Persists warehouse items to disk."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        serialized = [item.model_dump() for item in self.items.values()]
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2)

    def promote_wave_capabilities(
        self,
        wave_id: str,
        exact_git_head: str,
        items_to_promote: List[Dict[str, Any]],
        reconvergence_verdict: str = "PASS",
        rolls_royce_passed: bool = True,
    ) -> WarehousePromotionReceipt:
        """Promotes validated wave capability items into the warehouse.

        Enforces exact 40-character HEAD commit SHA binding and test/evidence proof requirements.
        Fails closed if commit SHA is invalid or evidence references are missing.
        """
        sha_pattern = re.compile(r"^[0-9a-fA-F]{40}$")
        if not sha_pattern.match(exact_git_head):
            raise ValueError(f"Invalid exact git HEAD commit SHA: {exact_git_head}")

        if reconvergence_verdict != "PASS" or not rolls_royce_passed:
            raise ValueError("Cannot promote capabilities from an unverified or failed wave.")

        promoted_ids: List[str] = []

        for item_def in items_to_promote:
            cap_id = item_def.get("capability_id")
            name = item_def.get("name")
            desc = item_def.get("description", "")
            evidence_refs = item_def.get("evidence_references", [])
            test_refs = item_def.get("test_references", [])
            reusable_patterns = item_def.get("reusable_patterns", [])

            if not cap_id or not name:
                raise ValueError("Capability item must contain capability_id and name.")

            # Fail-closed check: evidence and test proof required
            if not evidence_refs or not test_refs:
                raise ValueError(
                    f"Capability {cap_id} missing evidence or test references. Fail-closed on promotion."
                )

            item_id = f"wh_{cap_id.lower().replace('-', '_')}"
            wh_item = WarehouseItem(
                item_id=item_id,
                capability_id=cap_id,
                name=name,
                description=desc,
                wave_id=wave_id,
                exact_commit_sha=exact_git_head,
                promotion_status=PromotionStatus.PROMOTED,
                reusable_patterns=reusable_patterns,
                evidence_references=evidence_refs,
                test_references=test_refs,
            )

            self.items[wh_item.item_id] = wh_item
            promoted_ids.append(cap_id)

            # Synchronize with SAGEOperationalCapabilityRegistry
            op_cap = SAGECapability(
                capability_id=cap_id,
                name=name,
                description=desc,
                implementation_status="IMPLEMENTED",
                validation_status="VALIDATED",
                evidence_references=evidence_refs,
                test_references=test_refs,
                archive_promotion_status="PROMOTED",
            )
            self.op_registry.add_capability(op_cap)

        self.save()

        receipt = WarehousePromotionReceipt(
            receipt_id=f"wh_rec_{hashlib.sha256(f'{wave_id}:{exact_git_head}'.encode('utf-8')).hexdigest()[:12]}",
            wave_id=wave_id,
            exact_git_head=exact_git_head,
            promoted_items_count=len(promoted_ids),
            promoted_capability_ids=promoted_ids,
            reconvergence_verdict=reconvergence_verdict,
            rolls_royce_passed=rolls_royce_passed,
        )
        receipt.receipt_hash = receipt.compute_hash()
        return receipt

    def get_item(self, item_id: str) -> Optional[WarehouseItem]:
        """Lookup item by item_id."""
        return self.items.get(item_id)

    def list_items(self) -> List[WarehouseItem]:
        """Returns list of all warehouse items."""
        return list(self.items.values())
