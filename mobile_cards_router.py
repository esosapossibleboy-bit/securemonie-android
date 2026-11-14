import time
from typing import Literal, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from cards_core import (
    fund_sm_card,
    issue_sm_card,
    reveal_sm_card,
    toggle_sm_card_freeze,
)
from db_adapter import get_db_connection

cards_router = APIRouter()

class CardIssueReq(BaseModel):
    currency: Literal["NGN", "USD"] = "NGN"

class CardFundReq(BaseModel):
    amount: float = Field(gt=0, le=50_000_000)
    pin: str = Field(pattern=r"^\d{4}$")
    when: Optional[str] = None

class CardPinReq(BaseModel):
    pin: str = Field(pattern=r"^\d{4}$")

def get_auth_and_db(authorization: Optional[str]):
    import mobile_server
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sign in required")
    _, tok = authorization.split(" ", 1)
    sess = mobile_server.SESSIONS.get(tok)
    if not sess or time.time() - sess["seen"] > 600:
        mobile_server.SESSIONS.pop(tok, None)
        raise HTTPException(status_code=401, detail="Session expired")
    sess["seen"] = time.time()
    return sess, get_db_connection(mobile_server.DB_PATH)

@cards_router.post("/api/cards")
def api_issue_card(req: CardIssueReq, authorization: Optional[str] = Header(None)):
    u, conn = get_auth_and_db(authorization)
    card = issue_sm_card(conn, u["id"], req.currency)
    conn.close()
    return card

@cards_router.post("/api/cards/{card_id}/fund")
def api_fund_card(card_id: int, req: CardFundReq, authorization: Optional[str] = Header(None)):
    u, conn = get_auth_and_db(authorization)
    res = fund_sm_card(conn, u["id"], card_id, req.amount, req.pin, req.when)
    conn.close()
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@cards_router.post("/api/cards/{card_id}/freeze")
def api_freeze_card(card_id: int, authorization: Optional[str] = Header(None)):
    u, conn = get_auth_and_db(authorization)
    state = toggle_sm_card_freeze(conn, u["id"], card_id)
    conn.close()
    if state is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return {"frozen": state}

@cards_router.post("/api/cards/{card_id}/reveal")
def api_reveal_card(card_id: int, req: CardPinReq, authorization: Optional[str] = Header(None)):
    u, conn = get_auth_and_db(authorization)
    res = reveal_sm_card(conn, u["id"], card_id, req.pin)
    conn.close()
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res
