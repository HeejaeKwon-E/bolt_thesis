from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from bolt_thesis.paths import SYSTEM_C_CONFIG_PATH


class RegexDictionaryExtractor:
    """Deterministic regex/dictionary baseline for the four study attributes."""

    def __init__(self, config_path: str | Path = SYSTEM_C_CONFIG_PATH) -> None:
        self.config = json.loads(Path(config_path).read_text(encoding="utf-8"))
        allowed = self.config["allowed_values"]

        self.allowed_diameters = set(allowed["diameter_mm"])
        self.allowed_lengths = set(allowed["length_mm"])
        self.allowed_grades = set(allowed["strength_grade"])

    @staticmethod
    def _normalize(text: str) -> str:
        # Unicode multiplication/dashes are intentionally normalized only for
        # regex matching. The original input is preserved in result files.
        return (
            text.strip()
            .replace("×", "x")
            .replace("✕", "x")
            .replace("—", "-")
            .replace("–", "-")
        )

    @staticmethod
    def _unique_allowed(values: list[int | str], allowed: set[int | str]):
        unique = []
        for value in values:
            if value in allowed and value not in unique:
                unique.append(value)
        return unique[0] if len(unique) == 1 else None

    def extract(self, text: str) -> dict[str, Any]:
        normalized = self._normalize(text)
        lower = normalized.lower()

        # Size-pair patterns are evaluated first because they define both
        # diameter and length with the strongest deterministic evidence.
        diameter, length = self._extract_size_pair(normalized)

        if diameter is None:
            diameter = self._extract_diameter(normalized)
        if length is None:
            length = self._extract_length(normalized)

        return {
            "diameter_mm": diameter,
            "length_mm": length,
            "strength_grade": self._extract_strength(lower),
            "surface_treatment": self._extract_surface(lower),
        }

    def _extract_size_pair(self, text: str) -> tuple[int | None, int | None]:
        patterns = [
            # M12x80, M12 * 80, M12-80, M16/60mm
            r"(?<![A-Za-z0-9])M\s*(\d{1,3})\s*(?:x|\*|/|-)\s*(\d{1,3})(?:\s*mm)?(?!\d)",
            # Explicit diameter symbols followed by a length:
            # 8파이 30, 12Ø x 30, 16Φ-60L, 20Ø80L
            r"(?<!\d)(\d{1,3})\s*(?:파이|Φ|Ø)\s*(?:x|\*|/|-|\s)?\s*(\d{1,3})\s*(?:L|롱|mm)?(?!\d)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if not match:
                continue
            d = int(match.group(1))
            l = int(match.group(2))
            if d in self.allowed_diameters and l in self.allowed_lengths:
                return d, l

        return None, None

    def _extract_diameter(self, text: str) -> int | None:
        candidates: list[int] = []

        patterns = [
            # M12, including standalone M-size.
            r"(?<![A-Za-z0-9])M\s*(\d{1,3})(?!\d)",
            # 20파이 / 20Φ / 20Ø
            r"(?<!\d)(\d{1,3})\s*(?:파이|Φ|Ø)",
            r"(?:Φ|Ø)\s*(\d{1,3})(?!\d)",
            # 직경 20, 직경=20, diameter 20, dia 20
            r"(?:직경|diameter|dia)\s*(?:=|:)?\s*(\d{1,3})(?:\s*(?:mm|미리))?",
            # English: 16mm dia
            r"(?<!\d)(\d{1,3})\s*mm\s*dia\b",
            # Korean colloquial diameter form: 16미리.
            # Diameter and length domains do not overlap in this study.
            r"(?<!\d)(\d{1,3})\s*미리\b",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                candidates.append(int(match.group(1)))

        return self._unique_allowed(candidates, self.allowed_diameters)

    def _extract_length(self, text: str) -> int | None:
        candidates: list[int] = []

        patterns = [
            # L80 / L=80
            r"(?<![A-Za-z0-9])L\s*(?:=|:)?\s*(\d{1,3})(?!\d)",
            # 80L
            r"(?<![\d.])(\d{1,3})\s*L(?!\d)",
            # 100롱
            r"(?<!\d)(\d{1,3})\s*롱\b",
            # 길이 80, 길이=80, length=80, len 80
            r"(?:길이|length|len)\s*(?:는|가|=|:)?\s*(\d{1,3})(?:\s*(?:mm|짜리))?",
            # 120mm long
            r"(?<!\d)(\d{1,3})\s*mm\s*long\b",
            # Generic xx mm. Because diameter-domain values do not overlap with
            # length-domain values, allowed-value filtering resolves examples
            # such as '직경 8mm, 길이 50mm' deterministically.
            r"(?<![\d.])(\d{1,3})\s*mm\b",
            # '길이 100짜리'
            r"길이\s*(\d{1,3})\s*짜리\b",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                candidates.append(int(match.group(1)))

        return self._unique_allowed(candidates, self.allowed_lengths)

    def _extract_strength(self, lower: str) -> str | None:
        # Property grades are decimals in the closed study domain, so an exact
        # grade token is sufficient and avoids inventing values.
        values = re.findall(r"(?<![\d.])(8\.8|10\.9|12\.9)(?!\d)", lower)
        unique = []
        for value in values:
            if value in self.allowed_grades and value not in unique:
                unique.append(value)
        return unique[0] if len(unique) == 1 else None

    def _extract_surface(self, lower: str) -> str | None:
        # Explicit statements that the information is unavailable take
        # precedence over lexical aliases such as the word 'coating'.
        for phrase in self.config["surface_missing_phrases"]:
            if phrase.lower() in lower:
                return None

        matched: list[str] = []
        aliases = self.config["surface_aliases"]

        for canonical, values in aliases.items():
            for alias in values:
                alias_lower = alias.lower()

                # Short 'zn' requires token boundaries to avoid accidental
                # substring matches.
                if alias_lower == "zn":
                    found = re.search(r"(?<![a-z])zn(?![a-z])", lower)
                else:
                    found = alias_lower in lower

                if found and canonical not in matched:
                    matched.append(canonical)

        return matched[0] if len(matched) == 1 else None
