"""API key vault.

Implements §1.5: the only component that can resolve `vault_key_ref` to the
raw secret is the internal key broker. The secret never appears in any
DAI-visible response, timeline event, decision log entry, or error.
"""
from __future__ import annotations

import secrets as secrets_mod
import uuid
from datetime import datetime, timezone
from threading import RLock
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .errors import make_error


class VaultEntryView(BaseModel):
    """DAI- and API-visible vault entry. `secret_value` is never included."""

    vault_key_ref: str
    owner_scope: str
    rotates_at: Optional[datetime]
    last_rotated_at: datetime
    usage_counter: int
    revoked: bool = False


class VaultEntryDraft(BaseModel):
    """Admin registration payload. `secret_value` is consumed and never echoed."""

    secret_value: str
    owner_scope: str = "user"
    rotates_at: Optional[datetime] = None


class _VaultEntry:
    """Internal vault record. Not a Pydantic model so it cannot be accidentally
    serialised into an API response."""

    __slots__ = (
        "vault_key_ref",
        "secret_value",
        "owner_scope",
        "rotates_at",
        "last_rotated_at",
        "usage_counter",
        "revoked",
    )

    def __init__(
        self,
        *,
        secret_value: str,
        owner_scope: str,
        rotates_at: Optional[datetime],
    ) -> None:
        self.vault_key_ref = f"vault_{uuid.uuid4().hex[:16]}"
        self.secret_value = secret_value
        self.owner_scope = owner_scope
        self.rotates_at = rotates_at
        self.last_rotated_at = datetime.now(timezone.utc)
        self.usage_counter = 0
        self.revoked = False

    def to_view(self) -> VaultEntryView:
        return VaultEntryView(
            vault_key_ref=self.vault_key_ref,
            owner_scope=self.owner_scope,
            rotates_at=self.rotates_at,
            last_rotated_at=self.last_rotated_at,
            usage_counter=self.usage_counter,
            revoked=self.revoked,
        )


class Vault:
    """In-memory key vault."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: Dict[str, _VaultEntry] = {}

    def register(self, draft: VaultEntryDraft) -> VaultEntryView:
        with self._lock:
            entry = _VaultEntry(
                secret_value=draft.secret_value,
                owner_scope=draft.owner_scope,
                rotates_at=draft.rotates_at,
            )
            self._entries[entry.vault_key_ref] = entry
            return entry.to_view()

    def rotate(self, vault_key_ref: str, *, new_secret: Optional[str] = None) -> VaultEntryView:
        """Rotate a secret without changing its `vault_key_ref` (§1.5)."""
        with self._lock:
            entry = self._entries.get(vault_key_ref)
            if entry is None:
                raise make_error("ErrVaultRefUnknown", f"Unknown vault ref: {vault_key_ref}")
            if entry.revoked:
                raise make_error("ErrVaultRevoked", f"Vault entry revoked: {vault_key_ref}")
            entry.secret_value = new_secret if new_secret is not None else secrets_mod.token_urlsafe(32)
            entry.last_rotated_at = datetime.now(timezone.utc)
            return entry.to_view()

    def revoke(self, vault_key_ref: str) -> VaultEntryView:
        with self._lock:
            entry = self._entries.get(vault_key_ref)
            if entry is None:
                raise make_error("ErrVaultRefUnknown", f"Unknown vault ref: {vault_key_ref}")
            entry.revoked = True
            return entry.to_view()

    def list(self) -> List[VaultEntryView]:
        with self._lock:
            return [e.to_view() for e in self._entries.values()]

    def view(self, vault_key_ref: str) -> VaultEntryView:
        with self._lock:
            entry = self._entries.get(vault_key_ref)
            if entry is None:
                raise make_error("ErrVaultRefUnknown", f"Unknown vault ref: {vault_key_ref}")
            return entry.to_view()

    def exists(self, vault_key_ref: str) -> bool:
        with self._lock:
            return vault_key_ref in self._entries

    def _resolve_for_broker(self, vault_key_ref: str) -> str:
        """Return the raw secret, incrementing the usage counter.

        Callers must ensure the secret is used exactly once in an outbound
        call and never retained, logged, or echoed. This method is
        underscore-prefixed and should only be called from KeyBroker.
        """
        with self._lock:
            entry = self._entries.get(vault_key_ref)
            if entry is None:
                raise make_error("ErrVaultRefUnknown", f"Unknown vault ref: {vault_key_ref}")
            if entry.revoked:
                raise make_error("ErrVaultRevoked", f"Vault entry revoked: {vault_key_ref}")
            entry.usage_counter += 1
            return entry.secret_value


class KeyBroker:
    """Single authorised boundary between the Vault and outbound calls.

    Brokers never return a secret to callers; they take a closure that uses
    the secret and returns a value. This makes key leakage structurally
    hard: no code path yields the raw string back up the stack.
    """

    def __init__(self, vault: Vault) -> None:
        self._vault = vault

    def call_with_secret(self, vault_key_ref: Optional[str], fn):
        """Invoke `fn(secret)` and return its result. If no ref is provided,
        `fn` receives None. The secret is not retained after `fn` returns."""
        if vault_key_ref is None:
            return fn(None)
        secret = self._vault._resolve_for_broker(vault_key_ref)
        try:
            return fn(secret)
        finally:
            secret = None  # noqa: F841
