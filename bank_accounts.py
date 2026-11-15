import secrets
from bank_db_setup import (
    TIER_LIMITS_NGN,
    generate_account_number,
    hash_secret,
    init_bank_db,
    verify_secret,
)
from bank_security import (
    check_login_lockout,
    log_security_event,
    record_login_attempt,
    record_pin_attempt,
    verify_device_or_2fa,
)

def register_customer(
    conn, full_name: str, phone: str, email: str, account_type: str,
    password: str, pin: str, bvn: str = "", nin: str = "", id_type: str = "NIN Slip",
    business_name: str = "", business_category: str = "", address: str = "",
    pep_status: str = "No", revenue_source: str = "Salary / Trade", selfie_data: str = "",
    device_id: str = "",
):
    init_bank_db(conn)
    cur = conn.cursor()
    cur.execute("SELECT id FROM customers WHERE phone = ? OR email = ?", (phone.strip(), email.strip().lower()))
    if cur.fetchone():
        return None
    acct = generate_account_number(cur)
    has_bvn = len(bvn.strip()) == 11
    has_nin = len(nin.strip()) == 11
    tier = 3 if (has_bvn and has_nin) else (2 if (has_bvn or has_nin) else 1)
    limit_kobo = TIER_LIMITS_NGN[tier] * 100
    cur.execute(
        """INSERT INTO customers (full_name, phone, email, account_type, business_name, business_category,
           bvn, nin, id_type, address, pep_status, revenue_source, selfie_data, account_number,
           password_hash, pin_hash, kyc_tier, daily_limit_kobo, trusted_device)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (full_name.strip(), phone.strip(), email.strip().lower(), account_type,
         business_name.strip(), business_category.strip(), bvn.strip(), nin.strip(),
         id_type, address.strip(), pep_status, revenue_source, selfie_data, acct,
         hash_secret(password), hash_secret(pin), tier, limit_kobo, device_id.strip()),
    )
    cid = cur.lastrowid
    conn.commit()
    log_security_event(conn, cid, "Account Opened & Trusted Device Registered", "SUCCESS")
    return {"id": cid, "full_name": full_name.strip(), "account_number": acct, "kyc_tier": tier}

def login_customer(conn, identifier: str, password: str, device_id: str = "", otp_code: str = ""):
    init_bank_db(conn)
    cur = conn.cursor()
    ident = identifier.strip().lower()
    cur.execute("SELECT id, full_name, account_number, password_hash, kyc_tier FROM customers WHERE phone = ? OR email = ?", (ident, ident))
    row = cur.fetchone()
    if not row:
        return None
    cid, name, acct, pw_hash, tier = row
    lock_msg = check_login_lockout(conn, cid)
    if lock_msg:
        return {"locked": lock_msg}
    if not verify_secret(password, pw_hash):
        record_login_attempt(conn, cid, False)
        return None
    dev_err = verify_device_or_2fa(conn, cid, device_id, otp_verified=bool(otp_code.strip()))
    if dev_err == "2FA_REQUIRED":
        return {"two_factor_required": True, "id": cid}
    record_login_attempt(conn, cid, True)
    return {"id": cid, "full_name": name, "account_number": acct, "kyc_tier": tier}

def check_pin(cur, customer_id: int, pin: str) -> bool:
    cur.execute("SELECT pin_hash, failed_pins FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row:
        return False
    pin_hash, fails = row
    if fails and fails >= 3:
        return False
    ok = verify_secret(pin, pin_hash)
    record_pin_attempt(cur.connection, customer_id, ok)
    return ok

def emergency_lock_by_phone(conn, identifier: str, pin: str):
    init_bank_db(conn)
    cur = conn.cursor()
    ident = identifier.strip().lower()
    cur.execute("SELECT id, pin_hash FROM customers WHERE phone = ? OR email = ?", (ident, ident))
    row = cur.fetchone()
    if not row or not verify_secret(pin, row[1]):
        return {"ok": False, "error": "Invalid phone/email or 4-digit PIN"}
    cid = row[0]
    cur.execute("UPDATE customers SET account_frozen = 1 WHERE id = ?", (cid,))
    cur.execute("UPDATE virtual_cards SET frozen = 1 WHERE customer_id = ?", (cid,))
    conn.commit()
    log_security_event(conn, cid, "EMERGENCY REMOTE LOCK: Account & Cards Frozen", "ALERT")
    return {"ok": True, "customer_id": cid}

def reset_forgotten_passcode(conn, identifier: str, pin: str, new_passcode: str):
    init_bank_db(conn)
    cur = conn.cursor()
    ident = identifier.strip().lower()
    cur.execute("SELECT id, pin_hash FROM customers WHERE phone = ? OR email = ?", (ident, ident))
    row = cur.fetchone()
    if not row or not verify_secret(pin, row[1]):
        return {"ok": False, "error": "Invalid phone/email or 4-digit PIN"}
    cid = row[0]
    cur.execute("UPDATE customers SET password_hash = ?, failed_logins = 0, locked_until = 0 WHERE id = ?", (hash_secret(new_passcode), cid))
    conn.commit()
    log_security_event(conn, cid, "Passcode Reset via PIN", "ALERT")
    return {"ok": True}

def register_cac_business(conn, customer_id: int, business_name: str, category: str, pin: str):
    cur = conn.cursor()
    if not check_pin(cur, customer_id, pin):
        return {"ok": False, "error": "Incorrect or locked 4-digit PIN"}
    rc = "BN-" + str(1000000 + secrets.randbelow(8999999))
    cur.execute("UPDATE customers SET account_type = 'Business', business_name = ?, business_category = ?, cac_rc_number = ? WHERE id = ?", (business_name.strip(), category, rc, customer_id))
    conn.commit()
    log_security_event(conn, customer_id, f"CAC Registered ({rc})", "SUCCESS")
    return {"ok": True, "cac_number": rc}

def update_security_settings(conn, customer_id: int, setting: str, current_password: str, new_value: str):
    cur = conn.cursor()
    cur.execute("SELECT password_hash, account_frozen, hide_bal_default FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    if not row or not verify_secret(current_password, row[0]):
        return {"ok": False, "error": "Current 6-digit passcode is wrong"}
    _, is_frozen, is_hidden = row
    if setting == "kyc" and len(new_value.strip()) == 11 and new_value.strip().isdigit():
        cur.execute("UPDATE customers SET kyc_tier = 3, daily_limit_kobo = ?, bvn = ? WHERE id = ?", (TIER_LIMITS_NGN[3] * 100, new_value.strip(), customer_id))
    elif setting == "limit" and new_value.isdigit() and 10_000 <= int(new_value) <= 5_000_000:
        cur.execute("UPDATE customers SET daily_limit_kobo = ? WHERE id = ?", (int(new_value) * 100, customer_id))
    elif setting == "single_limit" and new_value.isdigit() and 5_000 <= int(new_value) <= 5_000_000:
        cur.execute("UPDATE customers SET single_limit_kobo = ? WHERE id = ?", (int(new_value) * 100, customer_id))
    elif setting == "pin" and len(new_value) == 4 and new_value.isdigit():
        cur.execute("UPDATE customers SET pin_hash = ?, failed_pins = 0 WHERE id = ?", (hash_secret(new_value), customer_id))
    elif setting == "password" and len(new_value) == 6 and new_value.isdigit():
        cur.execute("UPDATE customers SET password_hash = ? WHERE id = ?", (hash_secret(new_value), customer_id))
    elif setting == "freeze":
        new_state = 0 if is_frozen else 1
        cur.execute("UPDATE customers SET account_frozen = ? WHERE id = ?", (new_state, customer_id))
    elif setting == "privacy":
        cur.execute("UPDATE customers SET hide_bal_default = ? WHERE id = ?", (0 if is_hidden else 1, customer_id))
    elif setting == "biometrics":
        pass
    else:
        return {"ok": False, "error": "Invalid setting value"}
    conn.commit()
    log_security_event(conn, customer_id, f"Updated Security Setting: {setting.upper()}", "SUCCESS")
    return {"ok": True}
