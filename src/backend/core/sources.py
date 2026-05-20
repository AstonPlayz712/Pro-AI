"""Source registry and source types.

A Source is any callable thing DAI might use. Secrets are never stored here;
only an opaque `vault_key_ref` pointing into the API-key vault.

Spec references: §1.1 (Source record), §1.2 (Source kinds).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .errors import make_error


class SourceKind(str, Enum):
    LOCAL_FILE = "Local.File"
    LOCAL_DIR = "Local.Dir"
    LOCAL_PROCESS = "Local.Process"
    DEVICE_SENSOR = "Device.Sensor"
    DEVICE_ACTUATOR = "Device.Actuator"
    NETWORK_HTTP = "Network.HTTP"
    NETWORK_WEBSOCKET = "Network.WebSocket"
    MODEL_LLM = "Model.LLM"
    MODEL_VISION = "Model.Vision"
    MODEL_EMBEDDING = "Model.Embedding"
    MODEL_SPEECH = "Model.Speech"
    SERVICE_SEARCH = "Service.Search"
    SERVICE_STORAGE = "Service.Storage"
    SERVICE_COMPUTE = "Service.Compute"


class PulsePolicy(str, Enum):
    OFF = "off"
    ON_HEALTH_CHANGE = "on_health_change"
    ON_CONTENT_CHANGE = "on_content_change"
    CONTINUOUS = "continuous"


class EndpointDescriptor(BaseModel):
    """Transport-level description. Never leaks in DAI-visible responses."""

    url: Optional[str] = None
    device_handle: Optional[str] = None
    local_path: Optional[str] = None
    protocol: Optional[str] = None


class QuotaDescriptor(BaseModel):
    max_calls_per_minute: Optional[int] = None
    max_tokens_per_call: Optional[int] = None
    max_cost_per_call: Optional[int] = None


class Source(BaseModel):
    """Internal Source record — full fidelity, including `auth_ref`."""

    source_id: str = Field(default_factory=lambda: f"src_{uuid.uuid4().hex[:12]}")
    kind: str
    label: str
    description: str = ""
    capabilities: List[str] = Field(default_factory=list)
    auth_ref: Optional[str] = None
    endpoint: EndpointDescriptor = Field(default_factory=EndpointDescriptor)
    quota: QuotaDescriptor = Field(default_factory=QuotaDescriptor)
    health: str = "UNKNOWN"
    tags: List[str] = Field(default_factory=list)
    scope_class: str = "user"
    pulse_policy: PulsePolicy = PulsePolicy.ON_HEALTH_CHANGE
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: Optional[datetime] = None
    version: int = 0


class SourceDraft(BaseModel):
    """API-side draft used when registering a new Source."""

    kind: str
    label: str
    description: str = ""
    capabilities: List[str] = Field(default_factory=list)
    vault_key_ref: Optional[str] = None
    endpoint: EndpointDescriptor = Field(default_factory=EndpointDescriptor)
    quota: QuotaDescriptor = Field(default_factory=QuotaDescriptor)
    tags: List[str] = Field(default_factory=list)
    scope_class: str = "user"
    pulse_policy: PulsePolicy = PulsePolicy.ON_HEALTH_CHANGE


class SourceView(BaseModel):
    """DAI-visible Source projection — `auth_ref` reduced to `{present: bool}`."""

    source_id: str
    kind: str
    label: str
    description: str
    capabilities: List[str]
    auth_ref: Dict[str, bool]
    endpoint: EndpointDescriptor
    quota: QuotaDescriptor
    health: str
    tags: List[str]
    scope_class: str
    pulse_policy: PulsePolicy
    registered_at: datetime
    last_used_at: Optional[datetime]
    version: int


def source_to_view(src: Source) -> SourceView:
    return SourceView(
        source_id=src.source_id,
        kind=src.kind,
        label=src.label,
        description=src.description,
        capabilities=list(src.capabilities),
        auth_ref={"present": src.auth_ref is not None},
        endpoint=src.endpoint,
        quota=src.quota,
        health=src.health,
        tags=list(src.tags),
        scope_class=src.scope_class,
        pulse_policy=src.pulse_policy,
        registered_at=src.registered_at,
        last_used_at=src.last_used_at,
        version=src.version,
    )


class SourceSelector(BaseModel):
    """Selector used by permission queries and enumerate requests."""

    ids: Optional[List[str]] = None
    kinds: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class SourceRegistry:
    """In-memory registry of Sources.

    Thread-safe via RLock; every mutation bumps the Source version so the
    context fabric can emit pulses on change.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._sources: Dict[str, Source] = {}

    def register(self, draft: SourceDraft, *, vault_key_ref: Optional[str] = None) -> Source:
        with self._lock:
            for existing in self._sources.values():
                if existing.label == draft.label and existing.kind == draft.kind:
                    raise make_error(
                        "ErrSourceDuplicate",
                        f"Source with label={draft.label!r} and kind={draft.kind!r} already exists",
                        details={"existing_id": existing.source_id},
                    )
            src = Source(
                kind=draft.kind,
                label=draft.label,
                description=draft.description,
                capabilities=list(draft.capabilities),
                auth_ref=vault_key_ref if vault_key_ref is not None else draft.vault_key_ref,
                endpoint=draft.endpoint,
                quota=draft.quota,
                tags=list(draft.tags),
                scope_class=draft.scope_class,
                pulse_policy=draft.pulse_policy,
            )
            self._sources[src.source_id] = src
            return src

    def get(self, source_id: str) -> Source:
        with self._lock:
            src = self._sources.get(source_id)
            if src is None:
                raise make_error("ErrSourceUnknown", f"No such source: {source_id}")
            return src

    def get_optional(self, source_id: str) -> Optional[Source]:
        with self._lock:
            return self._sources.get(source_id)

    def list(
        self,
        *,
        kind: Optional[str] = None,
        tag: Optional[str] = None,
        health: Optional[str] = None,
    ) -> List[Source]:
        with self._lock:
            results: List[Source] = []
            for src in self._sources.values():
                if kind and src.kind != kind:
                    continue
                if tag and tag not in src.tags:
                    continue
                if health and src.health != health:
                    continue
                results.append(src)
            return results

    def select(self, selector: SourceSelector) -> List[Source]:
        with self._lock:
            results: List[Source] = []
            for src in self._sources.values():
                if selector.ids and src.source_id not in selector.ids:
                    continue
                if selector.kinds and src.kind not in selector.kinds:
                    continue
                if selector.tags and not any(t in src.tags for t in selector.tags):
                    continue
                results.append(src)
            return results

    def set_health(self, source_id: str, health: str) -> Source:
        with self._lock:
            src = self.get(source_id)
            if src.health == health:
                return src
            src.health = health
            src.version += 1
            return src

    def touch(self, source_id: str) -> None:
        with self._lock:
            src = self._sources.get(source_id)
            if src is not None:
                src.last_used_at = datetime.now(timezone.utc)

    def rebind_auth(self, source_id: str, vault_key_ref: Optional[str]) -> Source:
        with self._lock:
            src = self.get(source_id)
            src.auth_ref = vault_key_ref
            src.version += 1
            return src

    def __iter__(self):
        with self._lock:
            return iter(list(self._sources.values()))

    def __len__(self) -> int:
        with self._lock:
            return len(self._sources)
