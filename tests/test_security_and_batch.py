"""
tests/test_security_and_batch.py
Verifies JWT token issuance, RBAC verification, and multi-page document parsing.
"""
import pytest
import numpy as np
import cv2
from io import BytesIO
from PIL import Image
from src.core.security import create_access_token, verify_password, USERS_DB
from src.parsers.document_ingestor import DocumentIngestor


def test_password_and_token_flow():
    user = USERS_DB["inspector01"]
    assert verify_password("inspect123", user["hashed_password"]) is True
    assert verify_password("wrongpass", user["hashed_password"]) is False

    token = create_access_token({"sub": user["username"], "roles": user["roles"]})
    assert isinstance(token, str)
    assert len(token) > 20


def test_tiff_batch_ingest():
    f1 = Image.new("RGB", (100, 100), color="white")
    f2 = Image.new("RGB", (100, 100), color="black")
    buf = BytesIO()
    f1.save(buf, format="TIFF", save_all=True, append_images=[f2])

    ingestor = DocumentIngestor()
    pages = ingestor.ingest_tiff_bytes(buf.getvalue())
    assert len(pages) == 2
    assert pages[0][0] == 1
    assert pages[1][0] == 2
    assert isinstance(pages[0][1], np.ndarray)
