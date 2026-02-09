"""Safety and guardrails engine for LLM input/output filtering."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class InjectionPattern:
    """A regex pattern for detecting prompt injection attempts."""

    name: str
    pattern: str
    severity: str  # "low" | "medium" | "high" | "critical"
    description: str = ""


@dataclass
class PIIMatch:
    """A detected PII occurrence."""

    type: str
    value: str
    position: tuple[int, int] = (0, 0)


@dataclass
class GuardrailPolicy:
    """Policy for content filtering."""

    name: str
    rules: list[str] = field(default_factory=list)
    block_on_violation: bool = True


@dataclass
class SafetyReport:
    """Result of a safety check."""

    is_safe: bool
    violations: list[str] = field(default_factory=list)
    severity: str = "none"
    recommendations: list[str] = field(default_factory=list)


_DEFAULT_INJECTION_PATTERNS: list[InjectionPattern] = [
    InjectionPattern(
        name="ignore_previous",
        pattern=r"ignore\s+(all\s+)?previous\s+(instructions|prompts?)",
        severity="critical",
        description="Attempts to override system instructions",
    ),
    InjectionPattern(
        name="system_prompt_leak",
        pattern=r"(show|reveal|print|output|repeat)\s+.*?(system\s+prompt|instructions|rules)",
        severity="high",
        description="Attempts to extract system prompt",
    ),
    InjectionPattern(
        name="sql_injection",
        pattern=r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b\s+.*(FROM|INTO|TABLE|SET))",
        severity="critical",
        description="SQL injection markers detected",
    ),
    InjectionPattern(
        name="code_injection",
        pattern=r"(exec|eval|import\s+os|subprocess|__import__|os\.system)\s*\(",
        severity="critical",
        description="Code execution injection attempt",
    ),
    InjectionPattern(
        name="role_override",
        pattern=r"(you\s+are\s+now|act\s+as|pretend\s+to\s+be|switch\s+to\s+.*mode)",
        severity="high",
        description="Attempts to change AI role or behavior",
    ),
    InjectionPattern(
        name="instruction_override",
        pattern=r"(disregard|forget|override)\s+(all\s+)?(previous|above|prior|your)\s*(instructions|rules|constraints)?",
        severity="critical",
        description="Attempts to override instructions",
    ),
]

_PII_PATTERNS: dict[str, str] = {
    "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "phone": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
}


class PromptInjectionDetector:
    """Detect prompt injection attempts via regex patterns."""

    def __init__(self) -> None:
        self._patterns: list[InjectionPattern] = list(_DEFAULT_INJECTION_PATTERNS)
        self._compiled: list[tuple[InjectionPattern, re.Pattern[str]]] = [
            (p, re.compile(p.pattern, re.IGNORECASE)) for p in self._patterns
        ]

    def detect(self, text: str) -> list[InjectionPattern]:
        """Return all matched injection patterns."""
        return [p for p, regex in self._compiled if regex.search(text)]

    def is_safe(self, text: str) -> bool:
        """Return True if no injection patterns detected."""
        return len(self.detect(text)) == 0

    def add_pattern(self, name: str, pattern: str, severity: str, description: str = "") -> None:
        """Add a custom injection pattern."""
        p = InjectionPattern(name=name, pattern=pattern, severity=severity, description=description)
        self._patterns.append(p)
        self._compiled.append((p, re.compile(p.pattern, re.IGNORECASE)))


class PIIDetector:
    """Detect personally identifiable information in text."""

    def detect(self, text: str) -> list[PIIMatch]:
        """Find all PII matches in text."""
        matches: list[PIIMatch] = []
        for pii_type, pattern in _PII_PATTERNS.items():
            for m in re.finditer(pattern, text):
                matches.append(
                    PIIMatch(type=pii_type, value=m.group(), position=(m.start(), m.end()))
                )
        return matches

    def redact(self, text: str) -> str:
        """Replace PII with [REDACTED_TYPE] placeholders."""
        result = text
        # Process in reverse order of specificity to avoid partial matches
        for pii_type in ["credit_card", "ssn", "email", "phone"]:
            pattern = _PII_PATTERNS[pii_type]
            result = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", result)
        return result


class ContentFilter:
    """Configurable output filtering based on policies."""

    def check_output(self, text: str, policy: GuardrailPolicy) -> SafetyReport:
        """Check text against a guardrail policy."""
        violations: list[str] = []
        recommendations: list[str] = []

        lower_text = text.lower()
        for rule in policy.rules:
            if rule.lower() in lower_text:
                violations.append(f"policy_violation:{rule}")
                recommendations.append(f"Remove or rephrase content matching rule: {rule}")

        max_severity = "none"
        if violations:
            max_severity = "high" if policy.block_on_violation else "medium"

        return SafetyReport(
            is_safe=len(violations) == 0,
            violations=violations,
            severity=max_severity,
            recommendations=recommendations,
        )


class GuardrailsEngine:
    """Orchestrate all safety checks: injection, PII, and content filtering."""

    def __init__(self) -> None:
        self._injection_detector = PromptInjectionDetector()
        self._pii_detector = PIIDetector()
        self._content_filter = ContentFilter()

    def check_input(self, text: str) -> SafetyReport:
        """Check input text for injection attempts and PII."""
        violations: list[str] = []
        recommendations: list[str] = []
        max_severity = "none"

        # Check injections
        injections = self._injection_detector.detect(text)
        for inj in injections:
            violations.append(f"injection:{inj.name}")
            recommendations.append(f"Blocked injection pattern: {inj.description}")
            if inj.severity == "critical":
                max_severity = "critical"
            elif inj.severity == "high" and max_severity not in ("critical",):
                max_severity = "high"
            elif inj.severity == "medium" and max_severity not in ("critical", "high"):
                max_severity = "medium"
            elif max_severity == "none":
                max_severity = "low"

        # Check PII
        pii_matches = self._pii_detector.detect(text)
        if pii_matches:
            pii_types = {m.type for m in pii_matches}
            for pt in pii_types:
                violations.append(f"pii_detected:{pt}")
            recommendations.append("Redact PII before processing")
            if max_severity == "none":
                max_severity = "medium"

        return SafetyReport(
            is_safe=len(violations) == 0,
            violations=violations,
            severity=max_severity,
            recommendations=recommendations,
        )

    def check_output(self, text: str, policy: GuardrailPolicy) -> SafetyReport:
        """Check output text against a content policy."""
        return self._content_filter.check_output(text, policy)

    def filter(self, text: str) -> str:
        """Return a redacted version of text (PII removed)."""
        return self._pii_detector.redact(text)
