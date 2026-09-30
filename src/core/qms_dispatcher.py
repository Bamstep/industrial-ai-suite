"""
src/core/qms_dispatcher.py
Dispatches inspection results, AS9102 compliance events, and SPC out-of-control
alerts to upstream Manufacturing Execution Systems (MES) and Quality Management Systems (QMS).
"""
import json
import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger("QMSDispatcher")


@dataclass
class QMSInspectionEvent:
    event_id: str
    part_number: str
    serial_number: str
    overall_status: str              # PASS / FAIL / MARGINAL
    total_characteristics: int
    non_conformances: int
    spc_cpk: float
    is_spc_capable: bool
    characteristics_summary: List[Dict[str, Any]]


class QMSDispatcher:
    def __init__(self, endpoint_url: Optional[str] = None, api_key: Optional[str] = None, timeout: float = 5.0):
        self.endpoint_url = endpoint_url or "http://127.0.0.1:8000/api/v1/mock-qms/webhook"
        self.api_key = api_key or "AERO-QMS-SECRET-TOKEN"
        self.timeout = timeout

    def dispatch_inspection_record(self, event: QMSInspectionEvent) -> Dict[str, Any]:
        """Sends payload to upstream QMS webhook."""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "User-Agent": "Industrial-CAD-GDT-InspectionEngine/1.0",
        }
        payload = asdict(event)

        try:
            response = requests.post(self.endpoint_url, json=payload, headers=headers, timeout=self.timeout)
            return {
                "status_code": response.status_code,
                "dispatched": response.status_code in [200, 201, 202],
                "response_body": response.text,
            }
        except requests.RequestException as e:
            logger.warning(f"QMS Dispatch failed: {e}")
            return {
                "status_code": 503,
                "dispatched": False,
                "error": str(e),
            }
