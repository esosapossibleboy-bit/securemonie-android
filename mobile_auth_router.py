import secrets
import time
from typing import Literal, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from bank_accounts import emergency_lock_by_phone
from bank_core import (
    get_account_summary,
    login_customer,
    register_cac_business,
    register_customer,
    reset_forgotten_passcode,
    update_security_settings,
)
from bank_security import log_security_event
from db_adapter import get_db_connection

auth_router = APIRouter()

class RegisterReq(BaseModel):
    full_name: str = Field(min_length=2, max_length=60)
    phone: str = Field(pattern=r"^0\d{10}$")
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
    device_id: str = Field(default="", max_length=80)

class LoginReq(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)
    password: str = Field(pattern=r"^\d{6}$")
    device_id: str = Field(default="", max_length=80)
    otp_code: str = Field(default="", max_length=6)

class ForgotPasscodeReq(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)
    pin: str = Field(pattern=r"^\d{4}$")
    new_passcode: str = Field(pattern=r"^\d{6}$")

class EmergencyLockReq(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)
    pin: str = Field(pattern=r"^\d{4}$")

class CacReq(BaseModel):
    business_name: str = Field(min_length=2, max_length=80)
    category: str = Field(min_length=2, max_length=60)
    pin: str = Field(pattern=r"^\d{4}$")

class SettingReq(BaseModel):
    setting: Literal["kyc", "limit", "single_limit", "pin", "password", "freeze", "privacy", "biometrics"]
    new_value: str = Field(default="toggle", max_length=64)
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
    if not sess or time.time() - sess["seen"] > 180:
        mobile_server.SESSIONS.pop(tok, None)
        raise HTTPException(status_code=401, detail="Session expired after 3 minutes")
    sess["seen"] = time.time()
    return sess

@auth_router.post("/api/register")
def api_reg(req: RegisterReq):
    import mobile_server
    conn = get_db()
    user = register_customer(
        conn, req.full_name, req.phone, req.email, req.account_type, req.password, req.pin,
        req.bvn, req.nin, req.id_type, req.business_name, req.business_category,
        req.address, req.pep_status, req.revenue_source, req.selfie_data, req.device_id,
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
    user = login_customer(conn, req.identifier, req.password, req.device_id, req.otp_code)
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Wrong 6-digit passcode")
    if "locked" in user:
        conn.close()
        raise HTTPException(status_code=423, detail=user["locked"])
    if user.get("two_factor_required"):
        conn.close()
        raise HTTPException(status_code=403, detail="2FA_REQUIRED")
    summary = get_account_summary(conn, user["id"])
    conn.close()
    tok = secrets.token_urlsafe(32)
    mobile_server.SESSIONS[tok] = {"id": user["id"], "seen": time.time()}
    return {"token": tok, "phone": summary["phone"], "selfie_data": summary["selfie_data"], **user}

@auth_router.post("/api/emergency-lock")
def api_emergency_lock(req: EmergencyLockReq):
    import mobile_server
    conn = get_db()
    res = emergency_lock_by_phone(conn, req.identifier, req.pin)
    conn.close()
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["error"])
    uid = res["customer_id"]
    for t in [k for k, v in mobile_server.SESSIONS.items() if v["id"] == uid]:
        mobile_server.SESSIONS.pop(t, None)
    return {"status": "account_and_cards_frozen"}

@auth_router.post("/api/forgot-passcode")
def api_forgot(req: ForgotPasscodeReq):
    conn = get_db()
    res = reset_forgotten_passcode(conn, req.identifier, req.pin, req.new_passcode)
    conn.close()
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return {"status": "passcode_reset"}

@auth_router.post("/api/cac-register")
def api_cac(req: CacReq, authorization: Optional[str] = Header(None)):
    u = auth_user(authorization)
    conn = get_db()
    res = register_cac_business(conn, u["id"], req.business_name, req.category, req.pin)
    conn.close()
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@auth_router.post("/api/settings")
def api_settings(req: SettingReq, authorization: Optional[str] = Header(None)):
    u = auth_user(authorization)
    conn = get_db()
    res = update_security_settings(conn, u["id"], req.setting, req.password, req.new_value)
    conn.close()
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@auth_router.post("/api/logout-all")
def api_logout_all(authorization: Optional[str] = Header(None)):
    import mobile_server
    u = auth_user(authorization)
    uid = u["id"]
    for t in [k for k, v in mobile_server.SESSIONS.items() if v["id"] == uid]:
        mobile_server.SESSIONS.pop(t, None)
    conn = get_db()
    log_security_event(conn, uid, "Signed Out From All Devices", "ALERT")
    conn.close()
    return {"status": "all_sessions_revoked"}
