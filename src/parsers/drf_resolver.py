"""
src/parsers/drf_resolver.py
Resolves ASME Y14.5 Datum Reference Frames (DRF), material boundary
modifiers (MMC, LMC, RFS), and dynamic bonus tolerance calculations.
"""
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class DatumModifier:
    datum_label: str             # e.g., 'A', 'B', 'A-B'
    material_boundary: str       # 'RFS', 'MMC', 'LMC'
    precedence: str              # 'PRIMARY', 'SECONDARY', 'TERTIARY'


@dataclass
class ResolvedDRF:
    characteristic_symbol: str
    tolerance_zone_shape: str     # 'DIAMETRAL' or 'PLANAR'
    specified_tolerance: float
    material_condition: str      # 'RFS', 'MMC', 'LMC'
    datums: List[DatumModifier]
    bonus_tolerance: float = 0.0
    total_allowable_tolerance: float = 0.0


class DatumReferenceFrameResolver:
    MOD_MAP = {
        "(M)": "MMC",
        "M": "MMC",
        "(L)": "LMC",
        "L": "LMC",
        "(S)": "RFS",
        "S": "RFS",
    }

    def resolve(
        self,
        fcf_cells: List[str],
        feature_actual_size: Optional[float] = None,
        feature_mmc_size: Optional[float] = None,
        is_internal_feature: bool = False,
    ) -> ResolvedDRF:
        """
        Parses multi-cell FCF list, e.g. ["POS", "%%C 0.05 (M)", "A", "B (M)", "C"]
        """
        if not fcf_cells:
            raise ValueError("Empty Feature Control Frame")

        char_symbol = fcf_cells[0].upper().strip()
        tol_cell = fcf_cells[1] if len(fcf_cells) > 1 else "0.0"

        # Tolerance zone shape
        is_dia = any(d in tol_cell for d in ["%%C", "%C", "Ø", "ø"])
        shape = "DIAMETRAL" if is_dia else "PLANAR"

        # Material condition modifier on tolerance
        mat_cond = "RFS"
        for code, m_name in self.MOD_MAP.items():
            if code in tol_cell:
                mat_cond = m_name
                break

        # Extract numeric tolerance
        tol_matches = re.findall(r"\d+(?:\.\d+)?", tol_cell.replace("%%C", "").replace("%C", "").replace("Ø", ""))
        specified_tol = float(tol_matches[0]) if tol_matches else 0.05

        # Parse datum sequence
        precedence_labels = ["PRIMARY", "SECONDARY", "TERTIARY"]
        datum_modifiers: List[DatumModifier] = []

        raw_datums = fcf_cells[2:] if len(fcf_cells) > 2 else []
        for idx, d_text in enumerate(raw_datums):
            d_clean = d_text.strip()
            if not d_clean or d_clean.upper() == "NONE":
                continue

            # Check for modifier
            d_mod = "RFS"
            for code, m_name in self.MOD_MAP.items():
                if code in d_clean:
                    d_mod = m_name
                    d_clean = d_clean.replace(code, "").strip()
                    break

            prec = precedence_labels[idx] if idx < len(precedence_labels) else f"PRECEDENCE_{idx+1}"
            datum_modifiers.append(DatumModifier(datum_label=d_clean, material_boundary=d_mod, precedence=prec))

        # Dynamic Bonus Tolerance Calculation
        bonus = 0.0
        if mat_cond == "MMC" and feature_actual_size is not None and feature_mmc_size is not None:
            if is_internal_feature:
                # Hole: Departure from MMC (MMC is minimum size)
                bonus = max(0.0, feature_actual_size - feature_mmc_size)
            else:
                # Shaft: Departure from MMC (MMC is maximum size)
                bonus = max(0.0, feature_mmc_size - feature_actual_size)

        total_tol = round(specified_tol + bonus, 4)

        return ResolvedDRF(
            characteristic_symbol=char_symbol,
            tolerance_zone_shape=shape,
            specified_tolerance=specified_tol,
            material_condition=mat_cond,
            datums=datum_modifiers,
            bonus_tolerance=round(bonus, 4),
            total_allowable_tolerance=total_tol,
        )
