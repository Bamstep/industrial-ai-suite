"""
src/core/dimension_parser.py
Parses ASME Y14.5 linear, diametral, and depth dimensions and their tolerance limits.
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ParsedDimension:
    dimension_id: str
    raw_text: str
    nominal: float
    upper_tolerance: float
    lower_tolerance: float
    upper_limit: float
    lower_limit: float
    is_diameter: bool
    is_reference: bool
    unit: str
    bounding_box: Optional[Tuple[int, int, int, int]] = None  # (x, y, w, h)


class DimensionParser:
    # 1. Bilateral unequal/equal: Ø320.00 +0.05/-0.00 or 620.00 +/- 0.15
    PAT_PLUS_MINUS = re.compile(
        r"(?P<dia>[Øø]?)?\s*(?P<nominal>\d+(?:\.\d+)?)\s*(?:\+/-|±)\s*(?P<tol>\d+(?:\.\d+)?)"
    )
    PAT_LIMITS_DEVIATION = re.compile(
        r"(?P<dia>[Øø]?)?\s*(?P<nominal>\d+(?:\.\d+)?)\s*\+(?P<upper>\d+(?:\.\d+)?)\s*/\s*-(?P<lower>\d+(?:\.\d+)?)"
    )
    # 2. Direct Limits: 25.15 / 24.85
    PAT_DIRECT_LIMITS = re.compile(
        r"(?P<dia>[Øø]?)?\s*(?P<high>\d+(?:\.\d+)?)\s*(?:/|-)\s*(?P<low>\d+(?:\.\d+)?)"
    )
    # 3. Basic Dimension [120.00] or Reference (120.00)
    PAT_BASIC_OR_REF = re.compile(
        r"(?:\[|\()(?P<dia>[Øø]?)?\s*(?P<nominal>\d+(?:\.\d+)?)(?:\]|\))"
    )

    def parse(
        self,
        raw_text: str,
        dim_id: str = "DIM-01",
        default_tolerance: float = 0.1,
        unit: str = "mm",
        bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[ParsedDimension]:
        cleaned = raw_text.strip()

        # Bilateral symmetrical (+/-)
        m = self.PAT_PLUS_MINUS.search(cleaned)
        if m:
            nom = float(m.group("nominal"))
            tol = float(m.group("tol"))
            is_dia = bool(m.group("dia"))
            return ParsedDimension(
                dimension_id=dim_id,
                raw_text=raw_text,
                nominal=nom,
                upper_tolerance=tol,
                lower_tolerance=-tol,
                upper_limit=round(nom + tol, 4),
                lower_limit=round(nom - tol, 4),
                is_diameter=is_dia,
                is_reference=False,
                unit=unit,
                bounding_box=bbox,
            )

        # Unequal deviation (+upper / -lower)
        m = self.PAT_LIMITS_DEVIATION.search(cleaned)
        if m:
            nom = float(m.group("nominal"))
            upper = float(m.group("upper"))
            lower = float(m.group("lower"))
            is_dia = bool(m.group("dia"))
            return ParsedDimension(
                dimension_id=dim_id,
                raw_text=raw_text,
                nominal=nom,
                upper_tolerance=upper,
                lower_tolerance=-lower,
                upper_limit=round(nom + upper, 4),
                lower_limit=round(nom - lower, 4),
                is_diameter=is_dia,
                is_reference=False,
                unit=unit,
                bounding_box=bbox,
            )

        # Direct High/Low Limits
        m = self.PAT_DIRECT_LIMITS.search(cleaned)
        if m:
            high = float(m.group("high"))
            low = float(m.group("low"))
            if high < low:
                high, low = low, high
            nom = round((high + low) / 2.0, 4)
            dev = round((high - low) / 2.0, 4)
            is_dia = bool(m.group("dia"))
            return ParsedDimension(
                dimension_id=dim_id,
                raw_text=raw_text,
                nominal=nom,
                upper_tolerance=dev,
                lower_tolerance=-dev,
                upper_limit=high,
                lower_limit=low,
                is_diameter=is_dia,
                is_reference=False,
                unit=unit,
                bounding_box=bbox,
            )

        # Basic / Reference Dimension
        m = self.PAT_BASIC_OR_REF.search(cleaned)
        if m:
            nom = float(m.group("nominal"))
            is_dia = bool(m.group("dia"))
            is_ref = "(" in cleaned
            return ParsedDimension(
                dimension_id=dim_id,
                raw_text=raw_text,
                nominal=nom,
                upper_tolerance=0.0 if not is_ref else default_tolerance,
                lower_tolerance=0.0 if not is_ref else -default_tolerance,
                upper_limit=nom,
                lower_limit=nom,
                is_diameter=is_dia,
                is_reference=is_ref,
                unit=unit,
                bounding_box=bbox,
            )

        return None
