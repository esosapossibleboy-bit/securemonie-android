import hashlib
import hmac
import random
import secrets
from bank_security import init_security_tables, log_security_event, record_pin_attempt

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

def check_pin(cur, customer_id: int, pin: str) -> bool:
    cur.execute("SELECT pin_hash, failed_pins FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row:
        return False
    pin_hash, failed_pins = row
    if failed_pins and failed_pins >= 3:
        return False
    ok = verify_secret(pin, pin_hash)
    record_pin_attempt(cur.connection, customer_id, ok)
    return ok

def register_cac_business(conn, customer_id: int, business_name: str, category: str, pin: str):
    cur = conn.cursor()
    if not check_pin(cur, customer_id, pin):
        return {"ok": False, "error": "Incorrect or locked 4-digit Transaction PIN"}
    bn_code = "BN-" + "".join(str(random.randint(0, 9)) for _ in range(7))
    cur.execute(
        "UPDATE customers SET account_type = 'Business', business_name = ?, business_category = ?, cac_rc_number = ? WHERE id = ?",
        (business_name.strip(), category.strip(), bn_code, customer_id),
    )
    conn.commit()
    log_security_event(conn, customer_id, f"CAC Business Registered ({bn_code})", "SUCCESS")
    return {"ok": True, "cac_number": bn_code}

def update_security_settings(conn, customer_id: int, setting: str, password: str, new_value: str):
    init_security_tables(conn)
    cur = conn.cursor()
    cur.execute("SELECT password_hash, kyc_tier, account_frozen, hide_bal_default FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row:
        return {"ok": False, "error": "Account not found"}
    pw_hash, tier, frozen, hide_bal = row
    if not verify_secret(password, pw_hash):
        return {"ok": False, "error": "Incorrect 6-digit passcode"}

    if setting == "pin":
        if len(new_value.strip()) != 4 or not new_value.strip().isdigit():
            return {"ok": False, "error": "New Transaction PIN must be 4 digits"}
        cur.execute("UPDATE customers SET pin_hash = ?, failed_pins = 0 WHERE id = ?", (hash_secret(new_value), customer_id))
        log_security_event(conn, customer_id, "Transaction PIN Changed & Unlocked", "SUCCESS")
    elif setting == "password":
        if len(new_value.strip()) != 6 or not new_value.strip().isdigit():
            return {"ok": False, "error": "New Login Passcode must be 6 digits"}
        cur.execute("UPDATE customers SET password_hash = ? WHERE id = ?", (hash_secret(new_value), customer_id))
        log_security_event(conn, customer_id, "6-Digit Login Passcode Changed", "SUCCESS")
    elif setting == "kyc":
        if len(new_value.strip()) != 11 or not new_value.strip().isdigit():
            return {"ok": False, "error": "Enter a valid 11-digit BVN or NIN"}
        next_tier = min(3, tier + 1)
        new_limit = int(TIER_LIMITS_NGN[next_tier] * 100)
        cur.execute("UPDATE customers SET kyc_tier = ?, daily_limit_kobo = ?, single_limit_kobo = ? WHERE id = ?", (next_tier, new_limit, new_limit, customer_id))
        log_security_event(conn, customer_id, f"KYC Upgraded to Level {next_tier}", "SUCCESS")
    elif setting == "limit":
        limit_ngn = float(new_value)
        max_allowed = TIER_LIMITS_NGN.get(tier, 50_000.0)
        if limit_ngn <= 0 or limit_ngn > max_allowed:
            return {"ok": False, "error": f"Level {tier} limit must be between ₦1 and ₦{max_allowed:,.0f}"}
        cur.execute("UPDATE customers SET daily_limit_kobo = ? WHERE id = ?", (int(limit_ngn * 100), customer_id))
        log_security_event(conn, customer_id, f"Daily Limit Set to ₦{limit_ngn:,.0f}", "SUCCESS")
    elif setting == "single_limit":
        limit_ngn = float(new_value)
        max_allowed = TIER_LIMITS_NGN.get(tier, 50_000.0)
        if limit_ngn <= 0 or limit_ngn > max_allowed:
            return {"ok": False, "error": f"Single cap must be between ₦1 and ₦{max_allowed:,.0f}"}
        cur.execute("UPDATE customers SET single_limit_kobo = ? WHERE id = ?", (int(limit_ngn * 100), customer_id))
        log_security_event(conn, customer_id, f"Per-Transfer Cap Set to ₦{limit_ngn:,.0f}", "SUCCESS")
    elif setting == "freeze":
        new_state = 0 if frozen else 1
        cur.execute("UPDATE customers SET account_frozen = ? WHERE id = ?", (new_state, customer_id))
        log_security_event(conn, customer_id, "Emergency Account Freeze Enabled" if new_state else "Account Unfrozen", "ALERT" if new_state else "SUCCESS")
    elif setting == "privacy":
        new_priv = 0 if hide_bal else 1
        cur.execute("UPDATE customers SET hide_bal_default = ? WHERE id = ?", (new_priv, customer_id))
        log_security_event(conn, customer_id, "Balance Privacy Updated", "SUCCESS")
    conn.commit()
    return {"ok": True}
