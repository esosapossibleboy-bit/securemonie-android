import hashlib
import hmac
import random
import secrets
from datetime import datetime

def hash_secret(value: str, salt: str = None) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", value.encode(), salt.encode(), 100_000)
    return f"{salt}${dk.hex()}"

def verify_secret(value: str, stored: str) -> bool:
    if not stored or "$" not in stored:
        return False
    salt, _ = stored.split("$", 1)
    return hmac.compare_digest(hash_secret(value, salt), stored)

def init_bank_db(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            account_number TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            pin_hash TEXT NOT NULL,
            wallet_kobo INTEGER DEFAULT 0,
            vault_kobo INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT NOT NULL,
            customer_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            kind TEXT NOT NULL,
            amount_kobo INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

def register_customer(conn, full_name: str, email: str, password: str, pin: str):
    init_bank_db(conn)
    cur = conn.cursor()
    while True:
        acct = "80" + "".join(str(random.randint(0, 9)) for _ in range(8))
        cur.execute("SELECT id FROM customers WHERE account_number = ?", (acct,))
        if not cur.fetchone():
            break
    try:
        cur.execute(
            "INSERT INTO customers (full_name, email, account_number, password_hash, pin_hash) VALUES (?, ?, ?, ?, ?)",
            (full_name.strip(), email.lower().strip(), acct, hash_secret(password), hash_secret(pin)),
        )
        conn.commit()
        return {"id": cur.lastrowid, "full_name": full_name.strip(), "account_number": acct}
    except Exception:
        if hasattr(conn, "rollback"):
            conn.rollback()
        return None

def login_customer(conn, email: str, password: str):
    init_bank_db(conn)
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, account_number, password_hash FROM customers WHERE email = ?", (email.lower().strip(),))
    row = cur.fetchone()
    if not row:
        return None
    cid, name, acct, pw_hash = row
    return {"id": cid, "full_name": name, "account_number": acct} if verify_secret(password, pw_hash) else None

def check_pin(cur, customer_id: int, pin: str) -> bool:
    cur.execute("SELECT pin_hash FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row:
        return False
    (pin_hash,) = row
    return verify_secret(pin, pin_hash)

def lookup_recipient(conn, account_number: str):
    cur = conn.cursor()
    cur.execute("SELECT full_name FROM customers WHERE account_number = ?", (account_number.strip(),))
    row = cur.fetchone()
    return row[0] if row else None

def add_money(conn, customer_id: int, amount_ngn: float, pin: str, when: str = None):
    kobo = round(amount_ngn * 100)
    if kobo <= 0:
        return {"ok": False, "error": "Amount must be positive"}
    cur = conn.cursor()
    if not check_pin(cur, customer_id, pin):
        return {"ok": False, "error": "Incorrect 4-digit PIN"}
    ref = "SCM-" + secrets.token_hex(4).upper()
    ts = when or datetime.now().strftime("%d %b %Y, %H:%M")
    cur.execute("UPDATE customers SET wallet_kobo = wallet_kobo + ? WHERE id = ?", (kobo, customer_id))
    cur.execute("INSERT INTO ledger (reference, customer_id, title, kind, amount_kobo, created_at) VALUES (?, ?, 'Instant Wallet Top-Up', 'CREDIT', ?, ?)", (ref, customer_id, kobo, ts))
    conn.commit()
    return {"ok": True, "reference": ref}

def send_transfer(conn, sender_id: int, recipient_acct: str, amount_ngn: float, pin: str, note: str = "Transfer", when: str = None):
    kobo = round(amount_ngn * 100)
    if kobo <= 0:
        return {"ok": False, "error": "Amount must be positive"}
    cur = conn.cursor()
    cur.execute("SELECT full_name, account_number, pin_hash, wallet_kobo FROM customers WHERE id = ?", (sender_id,))
    s = cur.fetchone()
    if not s:
        return {"ok": False, "error": "Sender not found"}
    s_name, s_acct, pin_hash, s_bal = s
    if not verify_secret(pin, pin_hash):
        return {"ok": False, "error": "Incorrect 4-digit PIN"}
    if s_acct == recipient_acct.strip():
        return {"ok": False, "error": "Cannot send to your own account"}
    if s_bal < kobo:
        return {"ok": False, "error": "Insufficient wallet balance"}

    cur.execute("SELECT id, full_name FROM customers WHERE account_number = ?", (recipient_acct.strip(),))
    r = cur.fetchone()
    if not r:
        return {"ok": False, "error": "Recipient account not found"}
    r_id, r_name = r

    ref = "SCM-" + secrets.token_hex(4).upper()
    ts = when or datetime.now().strftime("%d %b %Y, %H:%M")
    desc = note.strip() or "Transfer"
    cur.execute("UPDATE customers SET wallet_kobo = wallet_kobo - ? WHERE id = ?", (kobo, sender_id))
    cur.execute("UPDATE customers SET wallet_kobo = wallet_kobo + ? WHERE id = ?", (kobo, r_id))
    cur.execute("INSERT INTO ledger (reference, customer_id, title, kind, amount_kobo, created_at) VALUES (?, ?, ?, 'DEBIT', ?, ?)", (ref, sender_id, f"To {r_name} ({desc})", kobo, ts))
    cur.execute("INSERT INTO ledger (reference, customer_id, title, kind, amount_kobo, created_at) VALUES (?, ?, ?, 'CREDIT', ?, ?)", (ref, r_id, f"From {s_name} ({desc})", kobo, ts))
    conn.commit()
    return {"ok": True, "reference": ref, "recipient": r_name}

def vault_action(conn, customer_id: int, action: str, amount_ngn: float, pin: str, when: str = None):
    cur = conn.cursor()
    if not check_pin(cur, customer_id, pin):
        return {"ok": False, "error": "Incorrect 4-digit PIN"}
    cur.execute("SELECT wallet_kobo, vault_kobo FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row:
        return {"ok": False, "error": "Customer not found"}
    w_kobo, v_kobo = row
    ref = "SAV-" + secrets.token_hex(4).upper()
    ts = when or datetime.now().strftime("%d %b %Y, %H:%M")

    if action == "save":
        kobo = round(amount_ngn * 100)
        if kobo <= 0 or w_kobo < kobo:
            return {"ok": False, "error": "Insufficient wallet balance"}
        cur.execute("UPDATE customers SET wallet_kobo = wallet_kobo - ?, vault_kobo = vault_kobo + ? WHERE id = ?", (kobo, kobo, customer_id))
        cur.execute("INSERT INTO ledger (reference, customer_id, title, kind, amount_kobo, created_at) VALUES (?, ?, 'Save to SecureVault', 'DEBIT', ?, ?)", (ref, customer_id, kobo, ts))
    elif action == "withdraw":
        kobo = round(amount_ngn * 100)
        if kobo <= 0 or v_kobo < kobo:
            return {"ok": False, "error": "Insufficient vault balance"}
        cur.execute("UPDATE customers SET vault_kobo = vault_kobo - ?, wallet_kobo = wallet_kobo + ? WHERE id = ?", (kobo, kobo, customer_id))
        cur.execute("INSERT INTO ledger (reference, customer_id, title, kind, amount_kobo, created_at) VALUES (?, ?, 'Vault Withdrawal', 'CREDIT', ?, ?)", (ref, customer_id, kobo, ts))
    elif action == "interest":
        if v_kobo <= 0:
            return {"ok": False, "error": "Save money first to earn 15% interest"}
        gain = max(1, round(v_kobo * 0.15 * (30 / 365)))
        cur.execute("UPDATE customers SET vault_kobo = vault_kobo + ? WHERE id = ?", (gain, customer_id))
        cur.execute("INSERT INTO ledger (reference, customer_id, title, kind, amount_kobo, created_at) VALUES (?, ?, '30-Day Vault Interest (15% p.a.)', 'CREDIT', ?, ?)", (ref, customer_id, gain, ts))
    conn.commit()
    return {"ok": True, "reference": ref}

def get_account_summary(conn, customer_id: int):
    cur = conn.cursor()
    cur.execute("SELECT full_name, account_number, wallet_kobo, vault_kobo FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row:
        return None
    name, acct, w_kobo, v_kobo = row
    cur.execute("SELECT reference, title, kind, amount_kobo, created_at FROM ledger WHERE customer_id = ? ORDER BY id DESC LIMIT 30", (customer_id,))
    txs = [{"ref": r, "title": t, "kind": k, "amount": a / 100, "time": tm} for r, t, k, a, tm in cur.fetchall()]
    return {"full_name": name, "account_number": acct, "wallet_ngn": w_kobo / 100, "vault_ngn": v_kobo / 100, "transactions": txs}
