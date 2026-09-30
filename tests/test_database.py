"""
tests/test_database.py
Verifies inspection record persistence and query flow.
"""
import json
from src.core.database import SessionLocal, InspectionRecord, init_db

def test_inspection_record_crud():
    init_db()
    db = SessionLocal()
    
    # Create record
    rec = InspectionRecord(
        part_number="FLANGE-7075-T6",
        serial_number="SN-TEST-9999",
        total_characteristics=4,
        status="PASS",
        cp=11.11,
        cpk=9.97,
        operator="inspector01",
        characteristics_json=json.dumps([{"char": 1, "status": "PASS"}])
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    
    assert rec.id is not None
    assert rec.part_number == "FLANGE-7075-T6"
    assert rec.cpk == 9.97

    # Query record back
    fetched = db.query(InspectionRecord).filter(InspectionRecord.serial_number == "SN-TEST-9999").first()
    assert fetched is not None
    assert fetched.operator == "inspector01"
    
    # Cleanup
    db.delete(fetched)
    db.commit()
    db.close()
