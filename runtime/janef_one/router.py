from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Route:
    primary: str
    modules: tuple[str, ...]
    domains: tuple[str, ...] = ()
    confidence: float = 0.0
    needs_freshness: bool = False
    needs_authorization_gate: bool = False
    risk: int = 0


_KEYWORDS: dict[str, tuple[str, ...]] = {
    "coding": (
        "code", "repo", "repository", "bug", "test", "build", "deploy", "python", "typescript",
        "javascript", "git", "api", "refactor", "compile", "برمجة", "كود", "مستودع", "اختبار", "نشر",
    ),
    "research": (
        "research", "latest", "current", "compare", "source", "market", "news", "verify", "study",
        "بحث", "احدث", "أحدث", "حالي", "قارن", "مصدر", "سوق", "اخبار", "أخبار", "تحقق", "دراسة",
    ),
    "artifact": (
        "pdf", "spreadsheet", "excel", "slide", "pptx", "document", "docx", "presentation", "csv",
        "ملف", "اكسل", "إكسل", "عرض", "بوربوينت", "وثيقة", "جدول",
    ),
    "browser": (
        "browser", "website", "web app", "click", "login", "setting", "navigate", "form",
        "متصفح", "موقع", "تسجيل الدخول", "اضغط", "إعدادات", "نموذج",
    ),
    "memory": (
        "remember", "previous", "last time", "context", "memory", "recall",
        "تذكر", "السابق", "المرة الماضية", "سياق", "ذاكرة",
    ),
    "security": (
        "security", "vulnerability", "credential", "secret", "delete", "production", "permission", "threat",
        "امن", "أمن", "ثغرة", "اعتماد", "سر", "حذف", "انتاج", "إنتاج", "صلاحية", "تهديد",
    ),
}

_MODULES: dict[str, tuple[str, ...]] = {
    "coding": ("coding-engine", "critic-verifier"),
    "research": ("research-engine", "source-trust", "critic-verifier"),
    "artifact": ("artifact-engine", "critic-verifier"),
    "browser": ("browser-computer-engine", "security-authorization", "critic-verifier"),
    "memory": ("memory-context-engine", "critic-verifier"),
    "security": ("security-authorization", "critic-verifier"),
    "analysis": ("analysis-decision-engine", "critic-verifier"),
}

_FRESHNESS = (
    "latest", "current", "today", "news", "price", "version", "recent",
    "أحدث", "احدث", "حالي", "اليوم", "أخبار", "اخبار", "سعر", "نسخة", "مؤخر",
)
_AUTHORIZATION = (
    "delete", "publish", "send", "deploy", "production", "transfer", "overwrite", "revoke", "pay", "purchase",
    "حذف", "انشر", "نشر", "ارسل", "أرسل", "انتاج", "إنتاج", "تحويل", "استبدال", "سحب", "ادفع", "شراء",
)
_HIGH_RISK = (
    "production", "credential", "secret", "delete", "transfer", "pay", "purchase", "revoke",
    "إنتاج", "انتاج", "سر", "حذف", "تحويل", "ادفع", "شراء", "سحب صلاحية",
)


def _contains(text: str, phrase: str) -> bool:
    if re.search(r"[\u0600-\u06ff]", phrase):
        return phrase in text
    if " " in phrase or not phrase.isascii():
        return phrase in text
    return re.search(rf"(?<![a-z0-9_]){re.escape(phrase)}(?![a-z0-9_])", text) is not None


def _negated(text: str, phrase: str) -> bool:
    if not _contains(text, phrase):
        return False
    escaped = re.escape(phrase)
    patterns = (
        rf"\b(?:do not|don't|never|without)\s+(?:\w+\s+){{0,2}}{escaped}",
        rf"(?:لا|لاتقم|بدون)\s+(?:\S+\s+){{0,2}}{escaped}",
    )
    return any(re.search(pattern, text, re.I) for pattern in patterns)


def route_intent(text: str) -> Route:
    if not text.strip():
        return Route("analysis", _MODULES["analysis"], ("analysis",), 0.0)
    lowered = text.casefold()
    scored: list[tuple[int, str]] = []
    for domain, words in _KEYWORDS.items():
        score = sum(1 for word in words if _contains(lowered, word.casefold()))
        if score:
            scored.append((score, domain))
    scored.sort(key=lambda item: (-item[0], item[1]))
    primary = scored[0][1] if scored else "analysis"
    domains = tuple(domain for _, domain in scored) or ("analysis",)
    total_hits = sum(score for score, _ in scored)
    confidence = (scored[0][0] / max(1, total_hits)) if scored else 0.35

    module_order: list[str] = []
    for domain in domains[:3]:
        for module in _MODULES[domain]:
            if module not in module_order:
                module_order.append(module)
    if not module_order:
        module_order.extend(_MODULES["analysis"])

    freshness = any(_contains(lowered, word.casefold()) for word in _FRESHNESS)
    auth = any(_contains(lowered, word.casefold()) and not _negated(lowered, word.casefold()) for word in _AUTHORIZATION)
    risk_hits = sum(1 for word in _HIGH_RISK if _contains(lowered, word.casefold()) and not _negated(lowered, word.casefold()))
    risk = min(100, risk_hits * 25 + (20 if "security" in domains else 0))
    return Route(
        primary=primary,
        modules=tuple(module_order),
        domains=domains,
        confidence=round(confidence, 3),
        needs_freshness=freshness,
        needs_authorization_gate=auth,
        risk=risk,
    )
