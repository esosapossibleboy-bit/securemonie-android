import re
import secrets
import time
from typing import Literal, Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse, Response
from fpdf import FPDF, XPos, YPos
from pydantic import BaseModel, Field, field_validator
from android_pwa import pwa_router
from bank_core import (
    add_money,
    get_account_summary,
    init_bank_db,
    login_customer,
    lookup_recipient,
    register_customer,
    send_transfer,
    vault_action,
)
from db_adapter import get_db_connection
from mobile_ui import render_mobile_app

app = FastAPI(title="Securemonie Microfinance Bank")
DB_PATH = "securemonie.db"
SESSIONS = {}
app.include_router(pwa_router)

class RegisterReq(BaseModel):
    full_name: str = Field(min_length=2, max_length=60)
    email: str = Field(min_length=4, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    pin: str = Field(pattern=r"^\d{4}$")

    @field_validator("password")
    @classmethod
    def strong_pw(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v) or not re.search(r"[a-z]", v) or not re.search(r"\d", v):
            raise ValueError("Use 8+ chars with uppercase, lowercase, and a number")
        return v

class LoginReq(BaseModel):
    email: str
    password: str

class DepositReq(BaseModel):
    amount: float = Field(gt=0, le=50_000_000)
    pin: str = Field(pattern=r"^\d{4}$")
    when: Optional[str] = None

class TransferReq(BaseModel):
    recipient_account: str = Field(pattern=r"^\d{10}$")
    amount: float = Field(gt=0, le=10_000_000)
    pin: str = Field(pattern=r"^\d{4}$")
    note: str = Field(default="Transfer", max_length=50)
    when: Optional[str] = None

class VaultReq(BaseModel):
    action: Literal["save", "withdraw", "interest"]
    amount: float = Field(default=0, ge=0, le=50_000_000)
    pin: str = Field(pattern=r"^\d{4}$")
    when: Optional[str] = None

def auth_user(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Log in required")
    _, tok = authorization.split(" ", 1)
    sess = SESSIONS.get(tok)
    if not sess or time.time() - sess["seen"] > 600:
        SESSIONS.pop(tok, None)
        raise HTTPException(status_code=401, detail="Session expired")
    sess["seen"] = time.time()
    return sess

@app.get("/", response_class=HTMLResponse)
def home():
    return render_mobile_app()

@app.post("/api/register")
def api_reg(req: RegisterReq):
    conn = get_db_connection(DB_PATH)
    user = register_customer(conn, req.full_name, req.email, req.password, req.pin)
    conn.close()
    if not user:
        raise HTTPException(status_code=400, detail="Email already registered")
    tok = secrets.token_urlsafe(32)
    SESSIONS[tok] = {"id": user["id"], "seen": time.time()}
    return {"token": tok, **user}

@app.post("/api/login")
def api_login(req: LoginReq):
    conn = get_db_connection(DB_PATH)
    user = login_customer(conn, req.email, req.password)
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    tok = secrets.token_urlsafe(32)
    SESSIONS[tok] = {"id": user["id"], "seen": time.time()}
    return {"token": tok, **user}

@app.get("/api/wallet")
def api_wallet(authorization: Optional[str] = Header(None)):
    u = auth_user(authorization)
    conn = get_db_connection(DB_PATH)
    init_bank_db(conn)
    data = get_account_summary(conn, u["id"])
    conn.close()
    return data

@app.get("/api/lookup/{acct}")
def api_lookup(acct: str, authorization: Optional[str] = Header(None)):
    auth_user(authorization)
    conn = get_db_connection(DB_PATH)
    name = lookup_recipient(conn, acct)
    conn.close()
    if not name:
        raise HTTPException(status_code=404, detail="Not found")
    return {"full_name": name}

@app.post("/api/deposit")
def api_deposit(req: DepositReq, authorization: Optional[str] = Header(None)):
    u = auth_user(authorization)
    conn = get_db_connection(DB_PATH)
    res = add_money(conn, u["id"], req.amount, req.pin, req.when)
    conn.close()
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.post("/api/transfer")
def api_transfer(req: TransferReq, authorization: Optional[str] = Header(None)):
    u = auth_user(authorization)
    conn = get_db_connection(DB_PATH)
    res = send_transfer(conn, u["id"], req.recipient_account, req.amount, req.pin, req.note, req.when)
    conn.close()
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.post("/api/vault")
def api_vault(req: VaultReq, authorization: Optional[str] = Header(None)):
    u = auth_user(authorization)
    conn = get_db_connection(DB_PATH)
    res = vault_action(conn, u["id"], req.action, req.amount, req.pin, req.when)
    conn.close()
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.get("/api/statement/pdf")
def api_pdf(authorization: Optional[str] = Header(None)):
    u = auth_user(authorization)
    conn = get_db_connection(DB_PATH)
    d = get_account_summary(conn, u["id"])
    conn.close()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, "Securemonie Microfinance Bank - Statement", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Customer: {d['full_name']} | Acct: {d['account_number']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Wallet: NGN {d['wallet_ngn']:,.2f} | Vault: NGN {d['vault_ngn']:,.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    for t in d["transactions"]:
        sign = "+" if t["kind"] == "CREDIT" else "-"
        line = f"[{t['time']}] {t['ref']} {t['title']}: {sign}NGN {t['amount']:,.2f}".encode("latin-1", "replace").decode("latin-1")
        pdf.cell(0, 7, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    raw = pdf.output()
    return Response(content=raw.encode("latin-1") if isinstance(raw, str) else bytes(raw), media_type="application/pdf")
