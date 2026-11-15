import hashlib
import hmac
import secrets
from bank_security import init_security_tables

TIER_LIMITS_NGN = {1: 50_000, 2: 500_000, 3: 5_000_000}

def hash_secret(secret: str, salt: str = None) -> str:
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${dk}"

def verify_secret(secret: str, stored: str) -> bool:
    if "$" not in stored:
        return False
    salt, _ = stored.split("$", 1)
    return hmac.compare_digest(hash_secret(secret, salt), stored)

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
            bvn TEXT DEFAULT '',
            nin TEXT DEFAULT '',
            id_type TEXT DEFAULT 'NIN Slip',
            address TEXT DEFAULT '',
            pep_status TEXT DEFAULT 'No',
            revenue_source TEXT DEFAULT 'Salary / Trade',
            selfie_data TEXT DEFAULT '',
            account_number TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            pin_hash TEXT NOT NULL,
            kyc_tier INTEGER NOT NULL DEFAULT 1,
            daily_limit_kobo INTEGER NOT NULL DEFAULT 5000000,
            wallet_kobo INTEGER NOT NULL DEFAULT 0,
            vault_kobo INTEGER NOT NULL DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            kind TEXT NOT NULL,
            amount_kobo INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ledger_customer ON ledger(customer_id, id DESC)")
    conn.commit()
    init_security_tables(conn)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_seclogs_customer ON security_logs(customer_id, id DESC)")
    conn.commit()

def generate_account_number(cur) -> str:
    while True:
        acct = "81" + "".join(str(secrets.randbelow(10)) for _ in range(8))
        cur.execute("SELECT id FROM customers WHERE account_number = ?", (acct,))
        if not cur.fetchone():
            return acct
