from typing import Literal, Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse, Response
from fpdf import FPDF, XPos, YPos
from pydantic import BaseModel, Field
from android_pwa import pwa_router
from bank_core import (
    add_money,
    get_account_summary,
    init_bank_db,
    lookup_recipient,
    pay_bill_or_airtime,
    send_transfer,
    vault_action,
)
from cards_core import get_sm_cards
from db_adapter import get_db_connection
from mobile_auth_router import auth_router, auth_user
from mobile_cards_router import cards_router
from mobile_ui import render_mobile_app

app = FastAPI(title="Securemonie Microfinance Bank")
DB_PATH = "securemonie.db"
SESSIONS = {}
app.include_router(pwa_router)
app.include_router(auth_router)
app.include_router(cards_router)

class DepositReq(BaseModel):
    amount: float = Field(gt=0, le=50_000_000)
    pin: str = Field(pattern=r"^\d{4}$")
    when: Optional[str] = None

class BillReq(BaseModel):
    service: str = Field(min_length=2, max_length=40)
    target: str = Field(min_length=4, max_length=30)
    amount: float = Field(gt=0, le=1_000_000)
    pin: str = Field(pattern=r"^\d{4}$")
    when: Optional[str] = None

class TransferReq(BaseModel):
    recipient_account: str = Field(pattern=r"^\d{10}$")
    bank_name: str = Field(default="Securemonie MFB", min_length=2, max_length=40)
    amount: float = Field(gt=0, le=10_000_000)
    pin: str = Field(pattern=r"^\d{4}$")
    note: str = Field(default="Transfer", max_length=50)
    when: Optional[str] = None

class VaultReq(BaseModel):
    action: Literal["save", "withdraw", "interest"]
    amount: float = Field(default=0, ge=0, le=50_000_000)
    pin: str = Field(pattern=r"^\d{4}$")
    when: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
def home():
    return render_mobile_app()

@app.get("/api/wallet")
def api_wallet(authorization: Optional[str] = Header(None)):
    u = auth_user(authorization)
    conn = get_db_connection(DB_PATH)
    init_bank_db(conn)
    data = get_account_summary(conn, u["id"])
    data["cards"] = get_sm_cards(conn, u["id"])
    conn.close()
    return data

@app.get("/api/lookup/{acct}")
def api_lookup(acct: str, bank: str = "Securemonie MFB", authorization: Optional[str] = Header(None)):
    auth_user(authorization)
    conn = get_db_connection(DB_PATH)
    name = lookup_recipient(conn, acct, bank)
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

@app.post("/api/bills")
def api_bills(req: BillReq, authorization: Optional[str] = Header(None)):
    u = auth_user(authorization)
    conn = get_db_connection(DB_PATH)
    res = pay_bill_or_airtime(conn, u["id"], req.service, req.target, req.amount, req.pin, req.when)
    conn.close()
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.post("/api/transfer")
def api_transfer(req: TransferReq, authorization: Optional[str] = Header(None)):
    u = auth_user(authorization)
    conn = get_db_connection(DB_PATH)
    res = send_transfer(conn, u["id"], req.recipient_account, req.bank_name, req.amount, req.pin, req.note, req.when)
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
    pdf.cell(0, 10, "Securemonie Microfinance Bank - Official Statement", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"{d['full_name']} ({d['account_type']} - Tier {d['kyc_tier']}) | Acct: {d['account_number']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Wallet: NGN {d['wallet_ngn']:,.2f} | Target Vault: NGN {d['vault_ngn']:,.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    for t in d["transactions"]:
        sign = "+" if t["kind"] == "CREDIT" else "-"
        line = f"[{t['time']}] {t['ref']} ({t['bank']}) {t['title']}: {sign}NGN {t['amount']:,.2f}".encode("latin-1", "replace").decode("latin-1")
        pdf.cell(0, 7, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    raw = pdf.output()
    return Response(content=raw.encode("latin-1") if isinstance(raw, str) else bytes(raw), media_type="application/pdf")
