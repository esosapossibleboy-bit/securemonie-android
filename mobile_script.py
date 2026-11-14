from mobile_auth_js import AUTH_JS
from mobile_wallet_js import WALLET_JS

EXTRAS_JS = """
    function renderCardsAndTx(d) {
        cardsList.replaceChildren(...(d.cards || []).map(c => {
            const box = Object.assign(document.createElement("div"), { style:"background:#0b1021;border:1px solid #2a3963;border-radius:14px;padding:14px;margin-top:10px;" });
            const sym = c.currency === "NGN" ? "₦" : "$";
            box.append(
                Object.assign(document.createElement("div"), { textContent:`${c.brand} ${c.frozen ? "❄️ FROZEN" : "✅"}`, style:"font-weight:700;color:#fbbf24;" }),
                Object.assign(document.createElement("div"), { textContent:`${c.masked} • Exp ${c.expiry}`, style:"margin:6px 0;font-family:monospace;" }),
                Object.assign(document.createElement("div"), { textContent:`Balance: ${sym}${c.balance.toFixed(2)}` }),
                Object.assign(document.createElement("button"), { className:"btn-gold", style:"padding:9px;margin-top:8px;", textContent:"+ Fund Card (₦)", onclick:()=>fundCard(c.id) }),
                Object.assign(document.createElement("button"), { className:"btn-dark", style:"padding:9px;margin-top:6px;", textContent:"👁️ Reveal Number & CVV", onclick:()=>revealCard(c.id) }),
                Object.assign(document.createElement("button"), { className:"btn-dark", style:"padding:9px;margin-top:6px;", textContent:c.frozen ? "🔥 Unfreeze Card" : "❄️ Freeze Card", onclick:()=>freezeCard(c.id) })
            );
            return box;
        }));
        txList.replaceChildren(...d.transactions.map(t => {
            const row = Object.assign(document.createElement("div"), { className:"tx" });
            const left = document.createElement("div");
            left.append(Object.assign(document.createElement("div"), { textContent:t.title }), Object.assign(document.createElement("small"), { textContent:`${t.bank} • ${t.ref} • ${t.time}`, style:"color:#94a3b8;" }));
            const amt = Object.assign(document.createElement("span"), { style:`font-weight:700;color:${t.kind==="CREDIT"?"#34d399":"#fb7185"}`, textContent:`${t.kind==="CREDIT"?"+":"-"}₦${t.amount.toLocaleString("en-NG", { minimumFractionDigits:2 })}` });
            row.append(left, amt); return row;
        }));
    }
    async function issueCard() {
        const res = await fetch("/api/cards", { method:"POST", headers:headers(), body:JSON.stringify({ currency:cardCur.value }) });
        if (res.ok) refreshWallet();
    }
    async function fundCard(id) {
        const amt = prompt("Enter Naira (₦) amount to fund card:"), pin = amt ? prompt("Enter 4-Digit Transaction PIN:") : "";
        if (!amt || !pin) return;
        const res = await fetch(`/api/cards/${id}/fund`, { method:"POST", headers:headers(), body:JSON.stringify({ amount:parseFloat(amt), pin, when:localTime() }) });
        const d = await res.json();
        if (!res.ok) return cardMsg.textContent = d.detail || "Failed";
        cardMsg.className = "ok"; cardMsg.textContent = `✅ Card funded (${d.reference})`; refreshWallet();
    }
    async function freezeCard(id) {
        const res = await fetch(`/api/cards/${id}/freeze`, { method:"POST", headers:headers() });
        if (res.ok) refreshWallet();
    }
    async function revealCard(id) {
        const pin = prompt("Enter 4-Digit Transaction PIN:");
        if (!pin) return;
        const res = await fetch(`/api/cards/${id}/reveal`, { method:"POST", headers:headers(), body:JSON.stringify({ pin }) });
        const d = await res.json();
        if (!res.ok) return alert(d.detail || "Invalid PIN");
        alert(`Card Number: ${d.card_number}\\nExpiry: ${d.expiry}\\nCVV: ${d.cvv}`);
    }
    function updateSettingHint() {
        const map = { kyc:"Enter 11-Digit BVN or NIN", limit:"Enter New Daily Limit in Naira (e.g. 50000)", pin:"Enter New 4-Digit PIN", password:"Enter New 6-Digit Login Passcode" };
        settingNewVal.placeholder = map[settingType.value] || "";
    }
    async function saveSetting() {
        setMsg.className = "err"; setMsg.textContent = "";
        const res = await fetch("/api/settings", { method:"POST", headers:headers(), body:JSON.stringify({ setting:settingType.value, new_value:settingNewVal.value, password:settingPass.value }) });
        const d = await res.json();
        if (!res.ok) return setMsg.textContent = d.detail || "Update failed";
        setMsg.className = "ok"; setMsg.textContent = "✅ Security setting updated!"; settingNewVal.value = settingPass.value = ""; refreshWallet();
    }
    async function getPdf() {
        const res = await fetch("/api/statement/pdf", { headers:headers() });
        if (!res.ok) return;
        const url = URL.createObjectURL(await res.blob());
        const a = Object.assign(document.createElement("a"), { href:url, download:"securemonie_statement.pdf" });
        document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    }
    if (token) enterApp();
    else if (localStorage.getItem("sm_phone")) showQuickUnlock();
"""

MOBILE_JS = f"<script>\n{AUTH_JS}\n{WALLET_JS}\n{EXTRAS_JS}\n</script>"
