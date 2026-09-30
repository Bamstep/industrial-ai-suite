"""
src/core/security.py
JWT Authentication and Role-Based Access Control (RBAC).
Uses standard hashlib PBKDF2-HMAC-SHA256 for cross-platform stability.
Roles:
- inspector: View blueprints, record measurements, trigger QMS dispatch.
- quality_engineer: Ingest multi-page PDFs, adjust tolerances, run SPC calculations.
- lead_auditor: Full access, sign off AS9102 Form 1-3 packages.
"""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

SECRET_KEY = "AERO_INDUSTRIAL_AI_GD_T_METROLOGY_SECRET_KEY_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def hash_password(password: str, salt: Optional[str] = None) -> str:
    if not salt:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${dk.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        salt, expected_hex = stored_hash.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(dk.hex(), expected_hex)
    except Exception:
        return False


USERS_DB = {
    "inspector01": {
        "username": "inspector01",
        "hashed_password": hash_password("inspect123"),
        "roles": ["inspector"],
    },
    "engineer01": {
        "username": "engineer01",
        "hashed_password": hash_password("eng123"),
        "roles": ["inspector", "quality_engineer"],
    },
    "auditor01": {
        "username": "auditor01",
        "hashed_password": hash_password("audit123"),
        "roles": ["inspector", "quality_engineer", "lead_auditor"],
    },
}


class TokenData(BaseModel):
    username: Optional[str] = None
    roles: List[str] = []


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        roles: List[str] = payload.get("roles", [])
        if username is None:
            raise credentials_exception
        return TokenData(username=username, roles=roles)
    except JWTError:
        raise credentials_exception


def require_role(required_role: str):
    def role_checker(current_user: TokenData = Depends(get_current_user)):
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{required_role}' authorization role",
            )
        return current_user
    return role_checker
