import time
from datetime import datetime

def init_security_tables(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            event TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    for col_sql in (
        "ALTER TABLE customers ADD COLUMN failed_logins INTEGER DEFAULT 0",
        "ALTER TABLE customers ADD COLUMN locked_until INTEGER DEFAULT 0",
        "ALTER TABLE customers ADD COLUMN failed_pins INTEGER DEFAULT 0",
        "ALTER TABLE customers ADD COLUMN account_frozen INTEGER DEFAULT 0",
        "ALTER TABLE customers ADD COLUMN single_limit_kobo INTEGER DEFAULT 5000000",
        "ALTER TABLE customers ADD COLUMN hide_bal_default INTEGER DEFAULT 1",
        "ALTER TABLE customers ADD COLUMN trusted_device TEXT DEFAULT ''",
        "ALTER TABLE customers ADD COLUMN biometrics_enabled INTEGER DEFAULT 0",
    ):
        try:
            cur.execute(col_sql)
            conn.commit()
        except Exception:
            if hasattr(conn, "rollback"):
                conn.rollback()
    conn.commit()

def log_security_event(conn, customer_id: int, event: str, status: str = "OK"):
    init_security_tables(conn)
    cur = conn.cursor()
    ts = datetime.now().strftime("%d %b %Y, %H:%M")
    cur.execute(
        "INSERT INTO security_logs (customer_id, event, status, created_at) VALUES (?, ?, ?, ?)",
        (customer_id, event, status, ts),
    )
    conn.commit()

def get_security_logs(conn, customer_id: int):
    init_security_tables(conn)
    cur = conn.cursor()
    cur.execute(
        "SELECT event, status, created_at FROM security_logs WHERE customer_id = ? ORDER BY id DESC LIMIT 15",
        (customer_id,),
    )
    return [{"event": e, "status": s, "time": t} for e, s, t in cur.fetchall()]

def check_login_lockout(conn, customer_id: int):
    init_security_tables(conn)
    cur = conn.cursor()
    cur.execute("SELECT locked_until FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row:
        return None
    (locked_until,) = row
    now = int(time.time())
    if locked_until and locked_until > now:
        mins = max(1, (locked_until - now + 59) // 60)
        return f"Account temporarily locked after 5 failed attempts. Try again in {mins} min(s)."
    return None

def record_login_attempt(conn, customer_id: int, success: bool):
    init_security_tables(conn)
    cur = conn.cursor()
    if success:
        cur.execute("UPDATE customers SET failed_logins = 0, locked_until = 0 WHERE id = ?", (customer_id,))
        conn.commit()
        log_security_event(conn, customer_id, "App Sign-In", "SUCCESS")
        return
    cur.execute("SELECT failed_logins FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    (prev,) = row if row else (0,)
    fails = (prev or 0) + 1
    lock_ts = int(time.time()) + 900 if fails >= 5 else 0
    cur.execute(
        "UPDATE customers SET failed_logins = ?, locked_until = ? WHERE id = ?",
        (fails, lock_ts, customer_id),
    )
    conn.commit()
    log_security_event(conn, customer_id, f"Failed Passcode Attempt ({fails}/5)", "ALERT")

def verify_device_or_2fa(conn, customer_id: int, device_id: str, otp_verified: bool = False):
    init_security_tables(conn)
    cur = conn.cursor()
    cur.execute("SELECT trusted_device FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row:
        return "Account not found"
    (saved_dev,) = row
    dev = (device_id or "").strip()
    if not saved_dev:
        if dev:
            cur.execute("UPDATE customers SET trusted_device = ? WHERE id = ?", (dev, customer_id))
            conn.commit()
        return None
    if dev and dev == saved_dev:
        return None
    if otp_verified:
        if dev:
            cur.execute("UPDATE customers SET trusted_device = ? WHERE id = ?", (dev, customer_id))
            conn.commit()
        log_security_event(conn, customer_id, "New Device Authorized via 2FA", "SUCCESS")
        return None
    log_security_event(conn, customer_id, "Blocked Unrecognized Device Login (2FA Required)", "ALERT")
    return "2FA_REQUIRED"

def verify_transaction_guard(conn, customer_id: int, amount_kobo: int):
    init_security_tables(conn)
    cur = conn.cursor()
    cur.execute(
        "SELECT account_frozen, failed_pins, single_limit_kobo, daily_limit_kobo FROM customers WHERE id = ?",
        (customer_id,),
    )
    row = cur.fetchone()
    if not row:
        return "Account not found"
    frozen, failed_pins, single_kobo, daily_kobo = row
    if frozen:
        return "Account is frozen. Unfreeze it in Security Settings to transact."
    if failed_pins and failed_pins >= 3:
        return "Transaction PIN locked after 3 wrong tries. Reset PIN in Security Settings."
    if single_kobo is not None and amount_kobo > single_kobo:
        return f"Exceeds your ₦{single_kobo / 100:,.0f} per-transaction limit"

    now_minute = datetime.now().strftime("%d %b %Y, %H:%M")
    cur.execute(
        "SELECT COUNT(*) FROM ledger WHERE customer_id = ? AND kind = 'DEBIT' AND created_at = ?",
        (customer_id, now_minute),
    )
    (same_min_txs,) = cur.fetchone() or (0,)
    if same_min_txs >= 3:
        log_security_event(conn, customer_id, "Velocity Fraud Guard Triggered (3+ tx/min)", "ALERT")
        return "Security pause: Too many rapid outgoing transfers in 1 minute. Wait 60 seconds."

    today_prefix = datetime.now().strftime("%d %b %Y")
    cur.execute(
        "SELECT COALESCE(SUM(amount_kobo), 0) FROM ledger WHERE customer_id = ? AND kind = 'DEBIT' AND created_at LIKE ?",
        (customer_id, f"{today_prefix}%"),
    )
    (spent_today,) = cur.fetchone() or (0,)
    if spent_today + amount_kobo > daily_kobo:
        rem = max(0, (daily_kobo - spent_today) / 100)
        return f"Exceeds daily limit. Remaining limit today: ₦{rem:,.2f}"
    return None

def record_pin_attempt(conn, customer_id: int, success: bool):
    init_security_tables(conn)
    cur = conn.cursor()
    if success:
        cur.execute("UPDATE customers SET failed_pins = 0 WHERE id = ?", (customer_id,))
        conn.commit()
        return
    cur.execute("SELECT failed_pins FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    (prev,) = row if row else (0,)
    fails = (prev or 0) + 1
    cur.execute("UPDATE customers SET failed_pins = ? WHERE id = ?", (fails, customer_id))
    conn.commit()
    log_security_event(conn, customer_id, f"Wrong Transaction PIN ({fails}/3)", "ALERT")
