WALLET_JS = """
    let hideBal = false, rawBal = 0, curAcct = "";
    function enterApp() {
        quickUnlockBox.style.display = "none"; loginBox.style.display = "none"; signupWizard.style.display = "none";
        appShell.style.display = "block"; bottomTabs.style.display = "flex"; logoutBtn.style.display = "block";
        bumpIdle(); refreshWallet();
    }
    function lockApp(msg = "") {
        clearTimeout(idle); token = ""; localStorage.removeItem("sm_token");
        showQuickUnlock(msg);
    }
    function openTab(name) {
        ["Home", "Send", "Vault", "Cards", "History", "Settings"].forEach(t => {
            document.getElementById("tab" + t).style.display = t === name ? "block" : "none";
            document.getElementById("btn" + t).className = "tab-btn" + (t === name ? " active" : "");
        });
    }
    function toggleBal() { hideBal = !hideBal; renderBal(); }
    function renderBal() { balText.textContent = hideBal ? "₦ ••••••" : ("₦" + rawBal.toLocaleString("en-NG", { minimumFractionDigits:2 })); }
    function copyAcct() { navigator.clipboard?.writeText(curAcct); homeMsg.className = "ok"; homeMsg.textContent = "✅ Account number copied!"; }
    async function refreshWallet() {
        const res = await fetch("/api/wallet", { headers:headers() });
        if (res.status === 401) return lockApp("Session expired");
        const d = await res.json();
        rawBal = d.wallet_ngn; curAcct = d.account_number; saveDeviceProfile(d.full_name, d.phone, d.selfie_data);
        if (d.selfie_data) {
            homeSelfieImg.src = settingsSelfieImg.src = d.selfie_data;
            homeSelfieImg.style.display = settingsSelfieImg.style.display = "block";
        }
        greetText.textContent = `${d.business_name || d.full_name} (${d.account_type})`; tierBadge.textContent = `TIER ${d.kyc_tier}`; acctText.textContent = d.account_number;
        renderBal();
        vaultText.textContent = "₦" + d.vault_ngn.toLocaleString("en-NG", { minimumFractionDigits:2 });
        profileInfo.textContent = `${d.full_name} • ${d.phone} • ${d.email} • ID: ${d.id_type} • Tier ${d.kyc_tier} (Daily Limit: ₦${d.daily_limit_ngn.toLocaleString()})`;
        renderCardsAndTx(d);
    }
    async function checkAcct() {
        recipPreview.textContent = "";
        if (toAcct.value.trim().length !== 10) return;
        const res = await fetch(`/api/lookup/${toAcct.value.trim()}?bank=${encodeURIComponent(bankSelect.value)}`, { headers:headers() });
        if (res.ok) { const d = await res.json(); recipPreview.textContent = "✅ " + d.full_name; }
        else recipPreview.textContent = "❌ Account not found";
    }
    async function doTopup() {
        homeMsg.className = "err"; homeMsg.textContent = "";
        const res = await fetch("/api/deposit", { method:"POST", headers:headers(), body:JSON.stringify({ amount:parseFloat(topupAmt.value), pin:topupPin.value, when:localTime() }) });
        const d = await res.json();
        if (!res.ok) return homeMsg.textContent = d.detail || "Failed";
        homeMsg.className = "ok"; homeMsg.textContent = "✅ Wallet funded"; topupAmt.value = topupPin.value = ""; refreshWallet();
    }
    async function doBill() {
        homeMsg.className = "err"; homeMsg.textContent = "";
        const res = await fetch("/api/bills", { method:"POST", headers:headers(), body:JSON.stringify({ service:billSvc.value, target:billTarget.value, amount:parseFloat(billAmt.value), pin:billPin.value, when:localTime() }) });
        const d = await res.json();
        if (!res.ok) return homeMsg.textContent = d.detail || "Failed";
        homeMsg.className = "ok"; homeMsg.textContent = `✅ Paid (${d.reference})`; billTarget.value = billAmt.value = billPin.value = ""; refreshWallet();
    }
    async function doTransfer() {
        sendMsg.className = "err"; sendMsg.textContent = "";
        const res = await fetch("/api/transfer", { method:"POST", headers:headers(), body:JSON.stringify({ recipient_account:toAcct.value.trim(), bank_name:bankSelect.value, amount:parseFloat(sendAmt.value), pin:sendPin.value, note:sendNote.value, when:localTime() }) });
        const d = await res.json();
        if (!res.ok) return sendMsg.textContent = d.detail || "Failed";
        sendMsg.className = "ok"; sendMsg.textContent = `✅ Sent to ${d.recipient} (${d.reference})`; toAcct.value = sendAmt.value = sendNote.value = sendPin.value = recipPreview.textContent = ""; refreshWallet();
    }
    async function doVault(action) {
        vaultMsg.className = "err"; vaultMsg.textContent = "";
        const res = await fetch("/api/vault", { method:"POST", headers:headers(), body:JSON.stringify({ action, amount:parseFloat(vaultAmt.value || "0"), pin:vaultPin.value, when:localTime() }) });
        const d = await res.json();
        if (!res.ok) return vaultMsg.textContent = d.detail || "Failed";
        vaultMsg.className = "ok"; vaultMsg.textContent = `✅ Done (${d.reference})`; vaultAmt.value = vaultPin.value = ""; refreshWallet();
    }
"""
