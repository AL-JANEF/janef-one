from __future__ import annotations

import fnmatch
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def _now_epoch() -> float:
    return datetime.now(timezone.utc).timestamp()


class ActionClass(str, Enum):
    READ_ONLY = "read_only"
    REVERSIBLE_LOCAL_WRITE = "reversible_local_write"
    EXTERNAL_WRITE = "external_write"
    DESTRUCTIVE = "destructive"
    PRODUCTION = "production"
    CREDENTIAL = "credential"
    FINANCIAL = "financial"
    PUBLICATION = "publication"


@dataclass(frozen=True, slots=True)
class ActionRequest:
    """A request to gate a consequential action.

    `explicit_authorization` and `target_verified` are trusted host/runtime
    inputs. They record that the *host* has confirmed authorization and
    verified the exact target, not that some skill or prompt merely asserts
    it. They must never be set from untrusted skill content, retrieved
    prompts/documents, tool output, or any candidate package — only from the
    trusted caller that constructs the request.
    """

    action: str
    action_class: ActionClass
    target: str = ""
    explicit_authorization: bool = False
    target_verified: bool = False
    reason: str = ""
    request_id: str = field(default_factory=lambda: secrets.token_hex(8))

    def __post_init__(self) -> None:
        if not self.action.strip():
            raise ValueError("action is required")


@dataclass(frozen=True, slots=True)
class AuthorizationGrant:
    grant_id: str
    action_classes: frozenset[ActionClass]
    target_patterns: tuple[str, ...]
    expires_at: float
    single_use: bool = True

    def __post_init__(self) -> None:
        if not self.grant_id:
            raise ValueError("grant_id is required")
        if not self.action_classes:
            raise ValueError("grant must cover at least one action class")
        if not self.target_patterns:
            raise ValueError("grant must include target patterns")

    @property
    def expired(self) -> bool:
        return _now_epoch() >= self.expires_at


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    reason: str
    grant_id: str | None = None


class AuthorizationGate:
    """Fail-closed gate for consequential side effects.

    Explicit authorization on the request is accepted only when the target has
    also been verified. Reusable grants are scoped by action class, target glob,
    expiry, and optional single-use semantics.
    """

    ALWAYS_GATED = {
        ActionClass.EXTERNAL_WRITE,
        ActionClass.DESTRUCTIVE,
        ActionClass.PRODUCTION,
        ActionClass.CREDENTIAL,
        ActionClass.FINANCIAL,
        ActionClass.PUBLICATION,
    }

    def __init__(self, grants: tuple[AuthorizationGrant, ...] = ()) -> None:
        self._grants: dict[str, AuthorizationGrant] = {grant.grant_id: grant for grant in grants}
        if len(self._grants) != len(grants):
            raise ValueError("duplicate authorization grant IDs")
        self._consumed: set[str] = set()

    def add_grant(self, grant: AuthorizationGrant) -> None:
        if grant.grant_id in self._grants:
            raise ValueError(f"duplicate authorization grant: {grant.grant_id}")
        self._grants[grant.grant_id] = grant

    def _matching_grant(self, request: ActionRequest) -> AuthorizationGrant | None:
        if not request.target:
            return None
        for grant in self._grants.values():
            if grant.grant_id in self._consumed or grant.expired:
                continue
            if request.action_class not in grant.action_classes:
                continue
            if any(fnmatch.fnmatchcase(request.target, pattern) for pattern in grant.target_patterns):
                return grant
        return None

    def decide(self, request: ActionRequest) -> AuthorizationDecision:
        if request.action_class not in self.ALWAYS_GATED:
            return AuthorizationDecision(True, "non-consequential action allowed by default")

        if not request.target_verified:
            return AuthorizationDecision(False, "consequential action target is not verified")
        if not request.target.strip():
            return AuthorizationDecision(False, "consequential action requires an explicit target")

        if request.explicit_authorization:
            return AuthorizationDecision(True, "explicit authorization and verified target present")

        grant = self._matching_grant(request)
        if grant is None:
            return AuthorizationDecision(False, "explicit authorization or matching scoped grant is required")
        if grant.single_use:
            self._consumed.add(grant.grant_id)
        return AuthorizationDecision(True, "matched scoped authorization grant", grant.grant_id)
