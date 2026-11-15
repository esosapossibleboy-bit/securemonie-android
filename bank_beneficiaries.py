from datetime import datetime

def init_beneficiaries_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS beneficiaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            recipient_name TEXT NOT NULL,
            account_number TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

def save_beneficiary(conn, customer_id: int, recipient_name: str, account_number: str, bank_name: str):
    init_beneficiaries_table(conn)
    acct = account_number.strip()
    bank = bank_name.strip()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM beneficiaries WHERE customer_id = ? AND account_number = ? AND bank_name = ?",
        (customer_id, acct, bank),
    )
    if cur.fetchone():
        return {"ok": True, "already_saved": True}

    ts = datetime.now().strftime("%d %b %Y")
    cur.execute(
        "INSERT INTO beneficiaries (customer_id, recipient_name, account_number, bank_name, created_at) VALUES (?, ?, ?, ?, ?)",
        (customer_id, recipient_name.strip(), acct, bank, ts),
    )
    conn.commit()
    return {"ok": True}

def get_beneficiaries(conn, customer_id: int) -> list[dict]:
    init_beneficiaries_table(conn)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, recipient_name, account_number, bank_name FROM beneficiaries WHERE customer_id = ? ORDER BY id DESC LIMIT 12",
        (customer_id,),
    )
    return [
        {"id": bid, "name": name, "account_number": acct, "bank_name": bank}
        for bid, name, acct, bank in cur.fetchall()
    ]

def delete_beneficiary(conn, customer_id: int, beneficiary_id: int) -> bool:
    init_beneficiaries_table(conn)
    cur = conn.cursor()
    cur.execute("DELETE FROM beneficiaries WHERE id = ? AND customer_id = ?", (beneficiary_id, customer_id))
    conn.commit()
    return cur.rowcount > 0

