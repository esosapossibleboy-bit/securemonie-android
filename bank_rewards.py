import secrets
from datetime import datetime
from bank_security import log_security_event

def init_rewards_columns(conn):
    cur = conn.cursor()
    for col_sql in (
        "ALTER TABLE customers ADD COLUMN cashback_kobo INTEGER DEFAULT 0",
        "ALTER TABLE customers ADD COLUMN referral_kobo INTEGER DEFAULT 0",
        "ALTER TABLE customers ADD COLUMN referral_code TEXT DEFAULT ''",
        "ALTER TABLE customers ADD COLUMN referred_by TEXT DEFAULT ''",
    ):
        try:
            cur.execute(col_sql)
            conn.commit()
        except Exception:
            if hasattr(conn, "rollback"):
                conn.rollback()
    conn.commit()

def ensure_referral_code(conn, customer_id: int) -> str:
    init_rewards_columns(conn)
    cur = conn.cursor()
    cur.execute("SELECT referral_code FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if row and row[0]:
        return row[0]
    code = "SM-" + secrets.token_hex(3).upper()
    cur.execute("UPDATE customers SET referral_code = ? WHERE id = ?", (code, customer_id))
    conn.commit()
    return code

def award_bill_cashback(conn, customer_id: int, amount_kobo: int) -> int:
    init_rewards_columns(conn)
    bonus_kobo = max(100, round(amount_kobo * 0.01))
    cur = conn.cursor()
    cur.execute("UPDATE customers SET cashback_kobo = COALESCE(cashback_kobo, 0) + ? WHERE id = ?", (bonus_kobo, customer_id))
    conn.commit()
    return bonus_kobo

def apply_referral_code(conn, customer_id: int, code: str):
    init_rewards_columns(conn)
    clean_code = code.strip().upper()
    cur = conn.cursor()
    cur.execute("SELECT referral_code, referred_by FROM customers WHERE id = ?", (customer_id,))
    me = cur.fetchone()
    if not me:
        return {"ok": False, "error": "Account not found"}
    my_code, already_used = me
    if already_used:
        return {"ok": False, "error": "You have already claimed a referral bonus"}
    if clean_code == my_code:
        return {"ok": False, "error": "You cannot use your own referral code"}

    cur.execute("SELECT id, full_name FROM customers WHERE referral_code = ?", (clean_code,))
    inviter = cur.fetchone()
    if not inviter:
        return {"ok": False, "error": "Invalid referral code"}
    inviter_id, inviter_name = inviter

    bonus_kobo = 50_000
    cur.execute("UPDATE customers SET referred_by = ?, referral_kobo = COALESCE(referral_kobo, 0) + ? WHERE id = ?", (clean_code, bonus_kobo, customer_id))
    cur.execute("UPDATE customers SET referral_kobo = COALESCE(referral_kobo, 0) + ? WHERE id = ?", (bonus_kobo, inviter_id))
    conn.commit()
    log_security_event(conn, customer_id, f"Referral Bonus Claimed ({clean_code})", "SUCCESS")
    log_security_event(conn, inviter_id, "Earned ₦500 Referral Reward", "SUCCESS")
    return {"ok": True, "inviter": inviter_name}

def redeem_rewards_to_wallet(conn, customer_id: int):
    init_rewards_columns(conn)
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(cashback_kobo, 0), COALESCE(referral_kobo, 0) FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row:
        return {"ok": False, "error": "Account not found"}
    cb_kobo, ref_kobo = row
    total_kobo = cb_kobo + ref_kobo
    if total_kobo <= 0:
        return {"ok": False, "error": "No cashback or referral rewards available to redeem"}

    ref = "RWD-" + secrets.token_hex(4).upper()
    ts = datetime.now().strftime("%d %b %Y, %H:%M")
    cur.execute("UPDATE customers SET cashback_kobo = 0, referral_kobo = 0, wallet_kobo = wallet_kobo + ? WHERE id = ?", (total_kobo, customer_id))
    cur.execute(
        "INSERT INTO ledger (reference, customer_id, title, bank_name, kind, amount_kobo, created_at) VALUES (?, ?, 'Cashback & Referral Payout', 'SecureRewards', 'CREDIT', ?, ?)",
        (ref, customer_id, total_kobo, ts),
    )
    conn.commit()
    return {"ok": True, "redeemed_ngn": total_kobo / 100, "reference": ref}
