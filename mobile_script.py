MOBILE_JS = """
<script>
    let token = localStorage.getItem("sm_token") || "", isReg = false, idle = null;
    const headers = () => ({ "Content-Type":"application/json", "Authorization":"Bearer " + token });
    const localTime = () => new Date().toLocaleString("en-GB", { day:"2-digit", month:"short", year:"numeric", hour:"2-digit", minute:"2-digit" });
    function bumpIdle() { clearTimeout(idle); if (token) idle = setTimeout(() => logout("🔒 Locked after 10 mins inactivity"), 600000); }
    ["click", "touchstart", "keydown"].forEach(e => window.addEventListener(e, bumpIdle, { passive:true }));
    function switchAuth() {
        isReg = !isReg; authMsg.textContent = "";
        regNameRow.style.display = isReg ? "block" : "none";
        regPinRow.style.display = isReg ? "block" : "none";
        authHeading.textContent = isReg ? "🏦 Open Securemonie Account" : "🔐 Welcome Back";
        authSubmitBtn.textContent = isReg ? "Create Account" : "Log In";
        authSwitchBtn.textContent = isReg ? "Already have an account? Log In" : "New to Securemonie? Create Account";
    }
    async function submitAuth() {
        authMsg.textContent = "";
        const body = isReg ? { full_name:regName.value, email:authEmail.value, password:authPass.value, pin:regPin.value } : { email:authEmail.value, password:authPass.value };
        const res = await fetch(isReg ? "/api/register" : "/api/login", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) });
        const d = await res.json();
        if (!res.ok) return authMsg.textContent = Array.isArray(d.detail) ? d.detail.map(x => x.msg).join(", ") : (d.detail || "Auth failed");
        token = d.token; localStorage.setItem("sm_token", token);
        regName.value = authEmail.value = authPass.value = regPin.value = "";
        enterApp();
    }
    function enterApp() {
        authBox.style.display = "none"; appShell.style.display = "block"; bottomTabs.style.display = "flex"; logoutBtn.style.display = "block";
        bumpIdle(); refreshWallet();
    }
    function logout(msg = "") {
        clearTimeout(idle); token = ""; localStorage.clear();
        appShell.style.display = "none"; bottomTabs.style.display = "none"; logoutBtn.style.display = "none"; authBox.style.display = "block";
        authMsg.textContent = typeof msg === "string" ? msg : "";
    }
    function openTab(name) {
        ["Home", "Send", "Vault", "History"].forEach(t => {
            document.getElementById("tab" + t).style.display = t === name ? "block" : "none";
            document.getElementById("btn" + t).className = "tab-btn" + (t === name ? " active" : "");
        });
    }
    async function refreshWallet() {
        const res = await fetch("/api/wallet", { headers:headers() });
        if (res.status === 401) return logout("Session expired");
        const d = await res.json();
        greetText.textContent = "Hi, " + d.full_name;
        acctText.textContent = d.account_number;
        balText.textContent = "₦" + d.wallet_ngn.toLocaleString("en-NG", { minimumFractionDigits:2 });
        vaultText.textContent = "₦" + d.vault_ngn.toLocaleString("en-NG", { minimumFractionDigits:2 });
        txList.replaceChildren(...d.transactions.map(t => {
            const row = Object.assign(document.createElement("div"), { className:"tx" });
            const left = document.createElement("div");
            left.append(Object.assign(document.createElement("div"), { textContent:t.title }), Object.assign(document.createElement("small"), { textContent:`${t.ref} • ${t.time}`, style:"color:#94a3b8;" }));
            const amt = Object.assign(document.createElement("span"), { style:`font-weight:700;color:${t.kind==="CREDIT"?"#00d285":"#fb7185"}`, textContent:`${t.kind==="CREDIT"?"+":"-"}₦${t.amount.toLocaleString("en-NG", { minimumFractionDigits:2 })}` });
            row.append(left, amt); return row;
        }));
    }
    async function checkAcct() {
        recipPreview.textContent = "";
        if (toAcct.value.trim().length !== 10) return;
        const res = await fetch(`/api/lookup/${toAcct.value.trim()}`, { headers:headers() });
        if (res.ok) { const d = await res.json(); recipPreview.textContent = "✅ " + d.full_name; }
        else recipPreview.textContent = "❌ Account not found";
    }
    async function doTopup() {
        topupMsg.className = "err"; topupMsg.textContent = "";
        const res = await fetch("/api/deposit", { method:"POST", headers:headers(), body:JSON.stringify({ amount:parseFloat(topupAmt.value), pin:topupPin.value, when:localTime() }) });
        const d = await res.json();
        if (!res.ok) return topupMsg.textContent = d.detail || "Failed";
        topupMsg.className = "ok"; topupMsg.textContent = "✅ Top-up successful"; topupAmt.value = topupPin.value = ""; refreshWallet();
    }
    async function doTransfer() {
        sendMsg.className = "err"; sendMsg.textContent = "";
        const res = await fetch("/api/transfer", { method:"POST", headers:headers(), body:JSON.stringify({ recipient_account:toAcct.value.trim(), amount:parseFloat(sendAmt.value), pin:sendPin.value, note:sendNote.value, when:localTime() }) });
        const d = await res.json();
        if (!res.ok) return sendMsg.textContent = d.detail || "Failed";
        sendMsg.className = "ok"; sendMsg.textContent = `✅ Sent (${d.reference})`; toAcct.value = sendAmt.value = sendNote.value = sendPin.value = recipPreview.textContent = ""; refreshWallet();
    }
    async function doVault(action) {
        vaultMsg.className = "err"; vaultMsg.textContent = "";
        const res = await fetch("/api/vault", { method:"POST", headers:headers(), body:JSON.stringify({ action, amount:parseFloat(vaultAmt.value || "0"), pin:vaultPin.value, when:localTime() }) });
        const d = await res.json();
        if (!res.ok) return vaultMsg.textContent = d.detail || "Failed";
        vaultMsg.className = "ok"; vaultMsg.textContent = `✅ Done (${d.reference})`; vaultAmt.value = vaultPin.value = ""; refreshWallet();
    }
    async function getPdf() {
        const res = await fetch("/api/statement/pdf", { headers:headers() });
        if (!res.ok) return;
        const url = URL.createObjectURL(await res.blob());
        const a = Object.assign(document.createElement("a"), { href:url, download:"securemonie_statement.pdf" });
        document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    }
    if (token) enterApp();
</script>
"""
