import secrets
from datetime import datetime
from bank_accounts import (
    TIER_LIMITS_NGN,
    check_pin,
    hash_secret,
    init_bank_db,
    login_customer,
    register_cac_business,
    register_customer,
    reset_forgotten_passcode,
    update_security_settings,
    verify_secret,
)
from bank_rewards import award_bill_cashback
from bank_security import verify_transaction_guard
from bank_summary import get_account_summary

def lookup_recipient(conn, account_number: str, bank_name: str = "Securemonie MFB"):
    acct = account_number.strip()
    if bank_name == "Securemonie MFB":
        cur = conn.cursor()
        cur.execute("SELECT full_name FROM customers WHERE account_number = ?", (acct,))
        row = cur.fetchone()
        if not row:
            return None
        (full_name,) = row
        return full_name
    if len(acct) == 10 and acct.isdigit():
        return f"Verified {bank_name} Customer"
    return None

def add_money(conn, customer_id: int, amount_ngn: float, pin: str, when: str = None):
    kobo = round(amount_ngn * 100)
    if kobo <= 0:
        return {"ok": False, "error": "Amount must be positive"}
    cur = conn.cursor()
    if not check_pin(cur, customer_id, pin):
        return {"ok": False, "error": "Incorrect or locked 4-digit PIN"}
    ref = "SCM-" + secrets.token_hex(5).upper()
    ts = when or datetime.now().strftime("%d %b %Y, %H:%M")
    cur.execute("UPDATE customers SET wallet_kobo = wallet_kobo + ? WHERE id = ?", (kobo, customer_id))
    cur.execute("INSERT INTO ledger (reference, customer_id, title, bank_name, kind, amount_kobo, created_at) VALUES (?, ?, 'Instant Wallet Funding', 'Securemonie MFB', 'CREDIT', ?, ?)", (ref, customer_id, kobo, ts))
    conn.commit()
    return {"ok": True, "reference": ref}

def send_transfer(conn, sender_id: int, recipient_acct: str, bank_name: str, amount_ngn: float, pin: str, note: str = "Transfer", when: str = None):
    kobo = round(amount_ngn * 100)
    if kobo <= 0:
        return {"ok": False, "error": "Amount must be positive"}
    guard_err = verify_transaction_guard(conn, sender_id, kobo)
    if guard_err:
        return {"ok": False, "error": guard_err}

    cur = conn.cursor()
    if not check_pin(cur, sender_id, pin):
        return {"ok": False, "error": "Incorrect or locked 4-digit PIN"}

    cur.execute("SELECT full_name, account_number, wallet_kobo FROM customers WHERE id = ?", (sender_id,))
    s = cur.fetchone()
    if not s:
        return {"ok": False, "error": "Sender not found"}
    s_name, s_acct, s_bal = s
    if s_bal < kobo:
        return {"ok": False, "error": "Insufficient wallet balance"}

    ref = "SCM-" + secrets.token_hex(5).upper()
    ts = when or datetime.now().strftime("%d %b %Y, %H:%M")
    desc = note.strip() or "Transfer"

    if bank_name == "Securemonie MFB":
        if s_acct == recipient_acct.strip():
            return {"ok": False, "error": "Cannot transfer to your own account"}
        cur.execute("SELECT id, full_name FROM customers WHERE account_number = ?", (recipient_acct.strip(),))
        r = cur.fetchone()
        if not r:
            return {"ok": False, "error": "Securemonie account not found"}
        r_id, r_name = r
        cur.execute("UPDATE customers SET wallet_kobo = wallet_kobo - ? WHERE id = ?", (kobo, sender_id))
        cur.execute("UPDATE customers SET wallet_kobo = wallet_kobo + ? WHERE id = ?", (kobo, r_id))
        cur.execute("INSERT INTO ledger (reference, customer_id, title, bank_name, kind, amount_kobo, created_at) VALUES (?, ?, ?, ?, 'DEBIT', ?, ?)", (ref, sender_id, f"To {r_name} ({desc})", bank_name, kobo, ts))
        cur.execute("INSERT INTO ledger (reference, customer_id, title, bank_name, kind, amount_kobo, created_at) VALUES (?, ?, ?, ?, 'CREDIT', ?, ?)", (ref, r_id, f"From {s_name} ({desc})", bank_name, kobo, ts))
        conn.commit()
        return {"ok": True, "reference": ref, "recipient": r_name}

    cur.execute("UPDATE customers SET wallet_kobo = wallet_kobo - ? WHERE id = ?", (kobo, sender_id))
    cur.execute("INSERT INTO ledger (reference, customer_id, title, bank_name, kind, amount_kobo, created_at) VALUES (?, ?, ?, ?, 'DEBIT', ?, ?)", (ref, sender_id, f"NIP Transfer to {recipient_acct} ({desc})", bank_name, kobo, ts))
    conn.commit()
    return {"ok": True, "reference": ref, "recipient": f"{bank_name} ({recipient_acct})"}

def pay_bill_or_airtime(conn, customer_id: int, service: str, target: str, amount_ngn: float, pin: str, when: str = None):
    kobo = round(amount_ngn * 100)
    if kobo <= 0:
        return {"ok": False, "error": "Amount must be positive"}
    guard_err = verify_transaction_guard(conn, customer_id, kobo)
    if guard_err:
        return {"ok": False, "error": guard_err}

    cur = conn.cursor()
    if not check_pin(cur, customer_id, pin):
        return {"ok": False, "error": "Incorrect or locked 4-digit PIN"}
    cur.execute("SELECT wallet_kobo FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row:
        return {"ok": False, "error": "Customer not found"}
    (wallet_kobo,) = row
    if wallet_kobo < kobo:
        return {"ok": False, "error": "Insufficient wallet balance"}
    ref = "BILL-" + secrets.token_hex(4).upper()
    ts = when or datetime.now().strftime("%d %b %Y, %H:%M")
    cur.execute("UPDATE customers SET wallet_kobo = wallet_kobo - ? WHERE id = ?", (kobo, customer_id))
    cur.execute("INSERT INTO ledger (reference, customer_id, title, bank_name, kind, amount_kobo, created_at) VALUES (?, ?, ?, 'Bill Payment', 'DEBIT', ?, ?)", (ref, customer_id, f"{service} ({target.strip()})", kobo, ts))
    conn.commit()
    cb_kobo = award_bill_cashback(conn, customer_id, kobo)
    return {"ok": True, "reference": ref, "cashback_ngn": cb_kobo / 100}

def vault_action(conn, customer_id: int, action: str, amount_ngn: float, pin: str, when: str = None):
    cur = conn.cursor()
    if not check_pin(cur, customer_id, pin):
        return {"ok": False, "error": "Incorrect or locked 4-digit PIN"}
    cur.execute("SELECT wallet_kobo, vault_kobo, account_frozen FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row:
        return {"ok": False, "error": "Customer not found"}
    w_kobo, v_kobo, frozen = row
    if frozen and action == "withdraw":
        return {"ok": False, "error": "Account is frozen. Unfreeze it in Security Settings first."}

    ref = "SAV-" + secrets.token_hex(4).upper()
    ts = when or datetime.now().strftime("%d %b %Y, %H:%M")

    if action == "save":
        kobo = round(amount_ngn * 100)
        if kobo <= 0 or w_kobo < kobo:
            return {"ok": False, "error": "Insufficient wallet balance"}
        cur.execute("UPDATE customers SET wallet_kobo = wallet_kobo - ?, vault_kobo = vault_kobo + ? WHERE id = ?", (kobo, kobo, customer_id))
        cur.execute("INSERT INTO ledger (reference, customer_id, title, bank_name, kind, amount_kobo, created_at) VALUES (?, ?, 'Save to Target Vault', 'SecureVault', 'DEBIT', ?, ?)", (ref, customer_id, kobo, ts))
    elif action == "withdraw":
        kobo = round(amount_ngn * 100)
        if kobo <= 0 or v_kobo < kobo:
            return {"ok": False, "error": "Insufficient vault balance"}
        cur.execute("UPDATE customers SET vault_kobo = vault_kobo - ?, wallet_kobo = wallet_kobo + ? WHERE id = ?", (kobo, kobo, customer_id))
        cur.execute("INSERT INTO ledger (reference, customer_id, title, bank_name, kind, amount_kobo, created_at) VALUES (?, ?, 'Vault Withdrawal', 'SecureVault', 'CREDIT', ?, ?)", (ref, customer_id, kobo, ts))
    elif action == "interest":
        if v_kobo <= 0:
            return {"ok": False, "error": "Save money first to earn 18% interest"}
        gain = max(1, round(v_kobo * 0.18 * (30 / 365)))
        cur.execute("UPDATE customers SET vault_kobo = vault_kobo + ? WHERE id = ?", (gain, customer_id))
        cur.execute("INSERT INTO ledger (reference, customer_id, title, bank_name, kind, amount_kobo, created_at) VALUES (?, ?, '30-Day Vault Interest (18.0% p.a.)', 'SecureVault', 'CREDIT', ?, ?)", (ref, customer_id, gain, ts))
    conn.commit()
    return {"ok": True, "reference": ref}
