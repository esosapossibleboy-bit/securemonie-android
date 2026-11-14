import random
from bank_security import (
    check_login_lockout,
    init_security_tables,
    log_security_event,
    record_login_attempt,
    record_pin_attempt,
)
from bank_settings import (
    TIER_LIMITS_NGN,
    check_pin,
    hash_secret,
    register_cac_business,
    update_security_settings,
    verify_secret,
)

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
            cac_rc_number TEXT DEFAULT '',
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
    for col in ("business_name", "business_category", "cac_rc_number", "address", "id_type", "pep_status", "revenue_source", "selfie_data"):
        try:
            cur.execute(f"ALTER TABLE customers ADD COLUMN {col} TEXT DEFAULT ''")
            conn.commit()
        except Exception:
            if hasattr(conn, "rollback"):
                conn.rollback()

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
    init_security_tables(conn)

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
                password_hash, pin_hash, kyc_tier, daily_limit_kobo, single_limit_kobo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                full_name.strip(), phone.strip(), email.lower().strip(), acct_kind,
                business_name.strip(), business_category.strip(), address.strip(),
                id_type.strip(), pep_status.strip(), revenue_source.strip(), selfie_data.strip(),
                acct, hash_secret(password), hash_secret(pin), tier, limit_kobo, limit_kobo,
            ),
        )
        conn.commit()
        cid = cur.lastrowid
        log_security_event(conn, cid, f"Account Opened (Tier {tier})", "SUCCESS")
        return {"id": cid, "full_name": full_name.strip(), "account_number": acct, "kyc_tier": tier}
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
    lock_err = check_login_lockout(conn, cid)
    if lock_err:
        return {"locked": lock_err}
    if verify_secret(password, pw_hash):
        record_login_attempt(conn, cid, True)
        return {"id": cid, "full_name": name, "account_number": acct}
    record_login_attempt(conn, cid, False)
    return None

def reset_forgotten_passcode(conn, identifier: str, transaction_pin: str, new_passcode: str):
    init_bank_db(conn)
    ident = identifier.lower().strip()
    cur = conn.cursor()
    cur.execute("SELECT id, pin_hash FROM customers WHERE email = ? OR phone = ?", (ident, ident))
    row = cur.fetchone()
    if not row:
        return {"ok": False, "error": "Account not found for that phone or email"}
    cid, pin_hash = row
    if not verify_secret(transaction_pin, pin_hash):
        record_pin_attempt(conn, cid, False)
        return {"ok": False, "error": "Incorrect 4-digit Transaction PIN"}
    cur.execute("UPDATE customers SET password_hash = ?, failed_logins = 0, locked_until = 0 WHERE id = ?", (hash_secret(new_passcode), cid))
    conn.commit()
    log_security_event(conn, cid, "Login Passcode Reset via PIN", "SUCCESS")
    return {"ok": True}
