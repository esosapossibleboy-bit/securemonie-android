import random
import secrets
from datetime import datetime
from bank_accounts import check_pin

USD_RATE = 1600.0

def init_cards_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sm_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            brand TEXT NOT NULL,
            currency TEXT NOT NULL,
            card_number TEXT UNIQUE NOT NULL,
            expiry TEXT NOT NULL,
            cvv TEXT NOT NULL,
            balance_cents INTEGER DEFAULT 0,
            frozen INTEGER DEFAULT 0
        )
    """)
    conn.commit()

def issue_sm_card(conn, customer_id: int, currency: str = "NGN"):
    init_cards_table(conn)
    cur = currency.upper().strip()
    brand = "Securemonie Verve (NGN)" if cur == "NGN" else "Securemonie Visa (USD)"
    prefix = "5061" if cur == "NGN" else "4532"
    cursor = conn.cursor()
    while True:
        num = prefix + "".join(str(random.randint(0, 9)) for _ in range(12))
        cursor.execute("SELECT id FROM sm_cards WHERE card_number = ?", (num,))
        if not cursor.fetchone():
            break
    cvv = "".join(str(random.randint(0, 9)) for _ in range(3))
    cursor.execute(
        "INSERT INTO sm_cards (customer_id, brand, currency, card_number, expiry, cvv) VALUES (?, ?, ?, ?, '11/29', ?)",
        (customer_id, brand, cur, num, cvv),
    )
    conn.commit()
    return {"id": cursor.lastrowid, "brand": brand, "last4": num[-4:]}

def get_sm_cards(conn, customer_id: int):
    init_cards_table(conn)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, brand, currency, card_number, expiry, balance_cents, frozen FROM sm_cards WHERE customer_id = ? ORDER BY id DESC",
        (customer_id,),
    )
    return [
        {
            "id": cid,
            "brand": brand,
            "currency": cur,
            "masked": f"{num[:4]} •••• •••• {num[-4:]}",
            "expiry": exp,
            "balance": bal / 100,
            "frozen": bool(frz),
        }
        for cid, brand, cur, num, exp, bal, frz in cursor.fetchall()
    ]

def fund_sm_card(conn, customer_id: int, card_id: int, amount_ngn: float, pin: str, when: str = None):
    init_cards_table(conn)
    kobo = round(amount_ngn * 100)
    if kobo <= 0:
        return {"ok": False, "error": "Amount must be positive"}
    cursor = conn.cursor()
    if not check_pin(cursor, customer_id, pin):
        return {"ok": False, "error": "Incorrect 4-digit PIN"}

    cursor.execute("SELECT wallet_kobo FROM customers WHERE id = ?", (customer_id,))
    u = cursor.fetchone()
    if not u:
        return {"ok": False, "error": "Customer not found"}
    (wallet_kobo,) = u
    if wallet_kobo < kobo:
        return {"ok": False, "error": "Insufficient wallet balance"}

    cursor.execute("SELECT brand, currency, frozen FROM sm_cards WHERE id = ? AND customer_id = ?", (card_id, customer_id))
    c = cursor.fetchone()
    if not c:
        return {"ok": False, "error": "Card not found"}
    brand, cur, frozen = c
    if frozen:
        return {"ok": False, "error": "Unfreeze card before funding"}

    add_cents = kobo if cur == "NGN" else round((amount_ngn / USD_RATE) * 100)
    ref = "CRD-" + secrets.token_hex(4).upper()
    ts = when or datetime.now().strftime("%d %b %Y, %H:%M")
    cursor.execute("UPDATE customers SET wallet_kobo = wallet_kobo - ? WHERE id = ?", (kobo, customer_id))
    cursor.execute("UPDATE sm_cards SET balance_cents = balance_cents + ? WHERE id = ?", (add_cents, card_id))
    cursor.execute(
        "INSERT INTO ledger (reference, customer_id, title, bank_name, kind, amount_kobo, created_at) VALUES (?, ?, ?, 'Virtual Card', 'DEBIT', ?, ?)",
        (ref, customer_id, f"Fund {brand}", kobo, ts),
    )
    conn.commit()
    return {"ok": True, "reference": ref}

def toggle_sm_card_freeze(conn, customer_id: int, card_id: int):
    init_cards_table(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT frozen FROM sm_cards WHERE id = ? AND customer_id = ?", (card_id, customer_id))
    row = cursor.fetchone()
    if not row:
        return None
    (cur_frozen,) = row
    new_val = 0 if cur_frozen else 1
    cursor.execute("UPDATE sm_cards SET frozen = ? WHERE id = ? AND customer_id = ?", (new_val, card_id, customer_id))
    conn.commit()
    return bool(new_val)

def reveal_sm_card(conn, customer_id: int, card_id: int, pin: str):
    init_cards_table(conn)
    cursor = conn.cursor()
    if not check_pin(cursor, customer_id, pin):
        return {"ok": False, "error": "Incorrect 4-digit PIN"}
    cursor.execute("SELECT card_number, expiry, cvv FROM sm_cards WHERE id = ? AND customer_id = ?", (card_id, customer_id))
    row = cursor.fetchone()
    if not row:
        return {"ok": False, "error": "Card not found"}
    num, exp, cvv = row
    return {"ok": True, "card_number": " ".join(num[i:i+4] for i in range(0, 16, 4)), "expiry": exp, "cvv": cvv}
