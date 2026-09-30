"""
gdt_parser.py
--------------
Interprets segmented Feature Control Frame compartments and compiles them
into ASME Y14.5 structured schemas and AS9102 inspection characteristic rows.
"""

import re
from typing import List, Optional
from src.core.schema import (
    FeatureControlFrame,
    ToleranceCategory,
    MaterialCondition,
    DatumReference,
    InspectionCharacteristicItem
)
from src.core.fcf_detector import DetectedFCF


class GDTCalloutParser:
    CHARACTERISTIC_MAP = {
        "FLAT": ("flatness", ToleranceCategory.FORM),
        "⏢": ("flatness", ToleranceCategory.FORM),
        "POS": ("position", ToleranceCategory.LOCATION),
        "⌖": ("position", ToleranceCategory.LOCATION),
        "//": ("parallelism", ToleranceCategory.ORIENTATION),
        "∥": ("parallelism", ToleranceCategory.ORIENTATION),
        "PERP": ("perpendicularity", ToleranceCategory.ORIENTATION),
        "⟂": ("perpendicularity", ToleranceCategory.ORIENTATION),
        "RUNOUT": ("circular_runout", ToleranceCategory.RUNOUT),
    }

    def parse_tolerance_compartment(self, text: str):
        """Parses tolerance string, e.g. '%%C 0.05 (M)' or '0.02'."""
        clean = text.strip()
        is_diameter = "%%C" in clean or "Ø" in clean or "DIA" in clean
        
        # Check material condition
        mod = MaterialCondition.NONE
        if "(M)" in clean or "Ⓜ" in clean or "MMC" in clean:
            mod = MaterialCondition.MMC
        elif "(L)" in clean or "Ⓛ" in clean or "LMC" in clean:
            mod = MaterialCondition.LMC

        # Extract numeric value
        match = re.search(r"(\d+\.?\d*)", clean)
        tol_val = float(match.group(1)) if match else 0.0

        return is_diameter, tol_val, mod

    def parse_datum_compartment(self, text: str) -> Optional[DatumReference]:
        clean = text.strip()
        if not clean:
            return None
        
        # Extract letter (e.g. 'A', 'B', 'C')
        letter_match = re.search(r"([A-Z])", clean)
        if not letter_match:
            return None
        
        label = letter_match.group(1)
        mod = MaterialCondition.NONE
        if "(M)" in clean or "Ⓜ" in clean:
            mod = MaterialCondition.MMC
        elif "(L)" in clean or "Ⓛ" in clean:
            mod = MaterialCondition.LMC

        return DatumReference(label=label, material_condition=mod)

    def parse_fcf(self, fcf: DetectedFCF, raw_cell_texts: List[str]) -> FeatureControlFrame:
        """Compiles extracted text list into a structured FeatureControlFrame."""
        sym_text = raw_cell_texts[0].strip().upper() if len(raw_cell_texts) > 0 else "FLAT"
        char_name, category = self.CHARACTERISTIC_MAP.get(sym_text, ("position", ToleranceCategory.LOCATION))

        tol_text = raw_cell_texts[1] if len(raw_cell_texts) > 1 else "0.0"
        is_dia, tol_val, tol_mod = self.parse_tolerance_compartment(tol_text)

        datum_refs = []
        for i in range(2, len(raw_cell_texts)):
            d_ref = self.parse_datum_compartment(raw_cell_texts[i])
            if d_ref:
                datum_refs.append(d_ref)

        return FeatureControlFrame(
            characteristic=char_name,
            category=category,
            is_diameter_zone=is_dia,
            tolerance_value=tol_val,
            material_modifier=tol_mod,
            primary_datum=datum_refs[0] if len(datum_refs) > 0 else None,
            secondary_datum=datum_refs[1] if len(datum_refs) > 1 else None,
            tertiary_datum=datum_refs[2] if len(datum_refs) > 2 else None,
            bounding_box=list(fcf.bounding_box)
        )

    def generate_inspection_table(
        self,
        fcfs: List[FeatureControlFrame]
    ) -> List[InspectionCharacteristicItem]:
        """Generates standard AS9102 inspection report entries."""
        items = []
        for idx, f in enumerate(fcfs, start=1):
            datums_str = " | ".join(
                [d.label for d in [f.primary_datum, f.secondary_datum, f.tertiary_datum] if d]
            ) or "NONE"
            
            callout = f"| {f.characteristic.upper()} | {'Ø' if f.is_diameter_zone else ''}{f.tolerance_value} {f.material_modifier.value} | {datums_str} |"
            
            items.append(
                InspectionCharacteristicItem(
                    char_index=idx,
                    char_type="GDT_FCF",
                    description=f"{f.characteristic.title()} Tolerance ({f.category.value})",
                    lower_spec_limit=0.0,
                    upper_spec_limit=f.tolerance_value,
                    gdt_callout=callout,
                    datums=datums_str,
                    status="PENDING"
                )
            )
        return items
