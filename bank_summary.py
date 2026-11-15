from bank_accounts import init_bank_db
from bank_beneficiaries import get_beneficiaries
from bank_rewards import ensure_referral_code, init_rewards_columns
from bank_security import get_security_logs

def get_account_summary(conn, customer_id: int):
    init_bank_db(conn)
    init_rewards_columns(conn)
    ref_code = ensure_referral_code(conn, customer_id)
    cur = conn.cursor()
    cur.execute(
        """SELECT full_name, phone, email, account_type, business_name, cac_rc_number, id_type,
           selfie_data, account_number, kyc_tier, daily_limit_kobo, single_limit_kobo,
           account_frozen, hide_bal_default, wallet_kobo, vault_kobo,
           COALESCE(cashback_kobo, 0), COALESCE(referral_kobo, 0), COALESCE(referred_by, '')
           FROM customers WHERE id = ?""",
        (customer_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    (
        name, phone, email, acct_type, biz_name, cac_rc, id_type,
        selfie, acct_num, tier, limit_kobo, single_kobo,
        frozen, hide_bal, w_kobo, v_kobo, cb_kobo, ref_kobo, ref_by,
    ) = row
    cur.execute("SELECT reference, title, bank_name, kind, amount_kobo, created_at FROM ledger WHERE customer_id = ? ORDER BY id DESC LIMIT 30", (customer_id,))
    rows = cur.fetchall()
    txs = [{"ref": r, "title": t, "bank": b, "kind": k, "amount": a / 100, "time": tm} for r, t, b, k, a, tm in rows]
    money_in = sum(a for _, _, _, k, a, _ in rows if k == "CREDIT") / 100
    money_out = sum(a for _, _, _, k, a, _ in rows if k == "DEBIT") / 100
    return {
        "full_name": name,
        "phone": phone,
        "email": email,
        "account_type": acct_type,
        "business_name": biz_name,
        "cac_rc_number": cac_rc,
        "id_type": id_type,
        "selfie_data": selfie,
        "account_number": acct_num,
        "kyc_tier": tier,
        "daily_limit_ngn": limit_kobo / 100,
        "single_limit_ngn": (single_kobo or limit_kobo) / 100,
        "account_frozen": bool(frozen),
        "hide_bal_default": bool(hide_bal),
        "wallet_ngn": w_kobo / 100,
        "vault_ngn": v_kobo / 100,
        "cashback_ngn": cb_kobo / 100,
        "referral_ngn": ref_kobo / 100,
        "referral_code": ref_code,
        "referred_by": ref_by,
        "money_in_ngn": money_in,
        "money_out_ngn": money_out,
        "beneficiaries": get_beneficiaries(conn, customer_id),
        "security_logs": get_security_logs(conn, customer_id),
        "transactions": txs,
    }
