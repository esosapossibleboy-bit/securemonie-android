import secrets
import time
from typing import Literal, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from bank_core import (
    get_account_summary,
    login_customer,
    register_customer,
    update_security_settings,
)
from db_adapter import get_db_connection

auth_router = APIRouter()

class RegisterReq(BaseModel):
    full_name: str = Field(min_length=2, max_length=60)
    phone: str = Field(pattern=r"^0[789][01]\d{8}$")
    email: str = Field(min_length=4, max_length=120)
    account_type: Literal["Personal", "Business"] = "Personal"
    password: str = Field(pattern=r"^\d{6}$")
    pin: str = Field(pattern=r"^\d{4}$")
    bvn: str = Field(default="", max_length=11)
    nin: str = Field(default="", max_length=11)
    id_type: str = Field(default="NIN Slip", max_length=40)
    business_name: str = Field(default="", max_length=80)
    business_category: str = Field(default="", max_length=60)
    address: str = Field(default="", max_length=120)
    pep_status: str = Field(default="No", max_length=10)
    revenue_source: str = Field(default="Salary / Trade", max_length=60)
    selfie_data: str = Field(min_length=20, max_length=120_000)

class LoginReq(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)
    password: str = Field(pattern=r"^\d{6}$")

class SettingReq(BaseModel):
    setting: Literal["kyc", "limit", "pin", "password"]
    new_value: str = Field(min_length=1, max_length=64)
    password: str = Field(pattern=r"^\d{6}$")

def get_db():
    import mobile_server
    return get_db_connection(mobile_server.DB_PATH)

def auth_user(authorization: Optional[str]):
    import mobile_server
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sign in required")
    _, tok = authorization.split(" ", 1)
    sess = mobile_server.SESSIONS.get(tok)
    if not sess or time.time() - sess["seen"] > 600:
        mobile_server.SESSIONS.pop(tok, None)
        raise HTTPException(status_code=401, detail="Session expired")
    sess["seen"] = time.time()
    return sess

@auth_router.post("/api/register")
def api_reg(req: RegisterReq):
    import mobile_server
    conn = get_db()
    user = register_customer(
        conn, req.full_name, req.phone, req.email, req.account_type, req.password, req.pin,
        req.bvn, req.nin, req.id_type, req.business_name, req.business_category,
        req.address, req.pep_status, req.revenue_source, req.selfie_data,
    )
    conn.close()
    if not user:
        raise HTTPException(status_code=400, detail="Phone or Email already registered")
    tok = secrets.token_urlsafe(32)
    mobile_server.SESSIONS[tok] = {"id": user["id"], "seen": time.time()}
    return {"token": tok, "phone": req.phone, "selfie_data": req.selfie_data, **user}

@auth_router.post("/api/login")
def api_login(req: LoginReq):
    import mobile_server
    conn = get_db()
    user = login_customer(conn, req.identifier, req.password)
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Wrong 6-digit passcode")
    summary = get_account_summary(conn, user["id"])
    conn.close()
    tok = secrets.token_urlsafe(32)
    mobile_server.SESSIONS[tok] = {"id": user["id"], "seen": time.time()}
    return {"token": tok, "phone": summary["phone"], "selfie_data": summary["selfie_data"], **user}

@auth_router.post("/api/settings")
def api_settings(req: SettingReq, authorization: Optional[str] = Header(None)):
    u = auth_user(authorization)
    conn = get_db()
    res = update_security_settings(conn, u["id"], req.setting, req.password, req.new_value)
    conn.close()
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res
