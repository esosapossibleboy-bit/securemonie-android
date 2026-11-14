import hashlib
import hmac
import random
import secrets

TIER_LIMITS_NGN = {1: 50_000.0, 2: 200_000.0, 3: 5_000_000.0}

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
            phone TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            account_type TEXT NOT NULL DEFAULT 'Personal',
            business_name TEXT DEFAULT '',
            business_category TEXT DEFAULT '',
            address TEXT DEFAULT '',
            id_type TEXT DEFAULT 'NIN Slip',
            pep_status TEXT DEFAULT 'No',
            revenue_source TEXT DEFAULT 'Salary / Trade',
            selfie_data TEXT DEFAULT '',
            account_number TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            pin_hash TEXT NOT NULL,
            kyc_tier INTEGER DEFAULT 1,
            daily_limit_kobo INTEGER DEFAULT 5000000,
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
            bank_name TEXT NOT NULL DEFAULT 'Securemonie MFB',
            kind TEXT NOT NULL,
            amount_kobo INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

def register_customer(
    conn,
    full_name: str,
    phone: str,
    email: str,
    account_type: str,
    password: str,
    pin: str,
    bvn: str = "",
    nin: str = "",
    id_type: str = "NIN Slip",
    business_name: str = "",
    business_category: str = "",
    address: str = "",
    pep_status: str = "No",
    revenue_source: str = "Salary / Trade",
    selfie_data: str = "",
):
    init_bank_db(conn)
    cur = conn.cursor()
    while True:
        acct = "81" + "".join(str(random.randint(0, 9)) for _ in range(8))
        cur.execute("SELECT id FROM customers WHERE account_number = ?", (acct,))
        if not cur.fetchone():
            break

    has_bvn = len(bvn.strip()) == 11 and bvn.strip().isdigit()
    has_nin = len(nin.strip()) == 11 and nin.strip().isdigit()
    tier = 3 if (has_bvn and has_nin and address.strip()) else (2 if (has_bvn or has_nin) else 1)
    limit_kobo = int(TIER_LIMITS_NGN[tier] * 100)
    acct_kind = "Business" if account_type.strip().lower() == "business" else "Personal"

    try:
        cur.execute(
            """
            INSERT INTO customers (
                full_name, phone, email, account_type, business_name, business_category,
                address, id_type, pep_status, revenue_source, selfie_data, account_number,
                password_hash, pin_hash, kyc_tier, daily_limit_kobo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                full_name.strip(), phone.strip(), email.lower().strip(), acct_kind,
                business_name.strip(), business_category.strip(), address.strip(),
                id_type.strip(), pep_status.strip(), revenue_source.strip(), selfie_data.strip(),
                acct, hash_secret(password), hash_secret(pin), tier, limit_kobo,
            ),
        )
        conn.commit()
        return {"id": cur.lastrowid, "full_name": full_name.strip(), "account_number": acct, "kyc_tier": tier}
    except Exception:
        if hasattr(conn, "rollback"):
            conn.rollback()
        return None

def login_customer(conn, identifier: str, password: str):
    init_bank_db(conn)
    ident = identifier.lower().strip()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, full_name, account_number, password_hash FROM customers WHERE email = ? OR phone = ?",
        (ident, ident),
    )
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

def update_security_settings(conn, customer_id: int, setting: str, password: str, new_value: str):
    cur = conn.cursor()
    cur.execute("SELECT password_hash, kyc_tier FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row:
        return {"ok": False, "error": "Account not found"}
    pw_hash, tier = row
    if not verify_secret(password, pw_hash):
        return {"ok": False, "error": "Incorrect 6-digit passcode"}

    if setting == "pin":
        cur.execute("UPDATE customers SET pin_hash = ? WHERE id = ?", (hash_secret(new_value), customer_id))
    elif setting == "password":
        cur.execute("UPDATE customers SET password_hash = ? WHERE id = ?", (hash_secret(new_value), customer_id))
    elif setting == "kyc":
        if len(new_value.strip()) != 11 or not new_value.strip().isdigit():
            return {"ok": False, "error": "Enter a valid 11-digit BVN or NIN"}
        next_tier = min(3, tier + 1)
        new_limit = int(TIER_LIMITS_NGN[next_tier] * 100)
        cur.execute("UPDATE customers SET kyc_tier = ?, daily_limit_kobo = ? WHERE id = ?", (next_tier, new_limit, customer_id))
    elif setting == "limit":
        limit_ngn = float(new_value)
        max_allowed = TIER_LIMITS_NGN.get(tier, 50_000.0)
        if limit_ngn <= 0 or limit_ngn > max_allowed:
            return {"ok": False, "error": f"Tier {tier} limit must be between ₦1 and ₦{max_allowed:,.0f}"}
        cur.execute("UPDATE customers SET daily_limit_kobo = ? WHERE id = ?", (int(limit_ngn * 100), customer_id))
    conn.commit()
    return {"ok": True}
