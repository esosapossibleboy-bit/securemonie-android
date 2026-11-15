WALLET_JS = """
    let hideBal = true, rawBal = 0, curAcct = "", curRefCode = "", isSendingTx = false;
    function enterApp() {
        quickUnlockBox.style.display = "none"; loginBox.style.display = "none"; signupWizard.style.display = "none"; forgotBox.style.display = "none";
        appShell.style.display = "block"; bottomTabs.style.display = "flex"; topActions.style.display = "flex"; lvlBadge.style.display = "inline-flex";
        bumpIdle(); refreshWallet();
    }
    function lockApp(msg = "") {
        clearTimeout(idle); token = ""; sessionStorage.removeItem("sm_token"); localStorage.removeItem("sm_token");
        topActions.style.display = "none"; lvlBadge.style.display = "none"; topSelfieImg.style.display = "none"; brandLogo.style.display = "flex";
        showQuickUnlock(msg);
    }
    function openTab(name) {
        for (const t of Array.of("Home", "Card", "Services", "Rewards")) {
            document.getElementById("tab" + t).style.display = t === name ? "block" : "none";
            document.getElementById("btn" + t).className = "tab-btn" + (t === name ? " active" : "");
        }
    }
    function openPanel(panelId) {
        openTab(panelId === "panelSettings" ? "Rewards" : "Services");
        const el = document.getElementById(panelId);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    function openBillService(svcName) {
        billSvc.value = svcName;
        openPanel("panelBills");
    }
    function toggleBal() { hideBal = !hideBal; renderBal(); }
    function renderBal() { balText.textContent = hideBal ? "₦ ••••••" : ("₦" + rawBal.toLocaleString("en-NG", { minimumFractionDigits:2 })); }
    function copyAcct() { navigator.clipboard?.writeText(curAcct); alert("✅ Account number copied: " + curAcct); }
    function copyRefCode() { navigator.clipboard?.writeText(curRefCode); alert("✅ Referral code copied: " + curRefCode); }
    async function refreshWallet() {
        const res = await fetch("/api/wallet", { headers:headers() });
        if (res.status === 401) return lockApp("Session expired");
        const d = await res.json();
        rawBal = d.wallet_ngn; curAcct = d.account_number; curRefCode = d.referral_code || "SM-000000";
        if (typeof d.hide_bal_default === "boolean") hideBal = d.hide_bal_default;
        saveDeviceProfile(d.full_name, d.phone, d.selfie_data);
        if (d.selfie_data) {
            topSelfieImg.src = settingsSelfieImg.src = d.selfie_data;
            topSelfieImg.style.display = settingsSelfieImg.style.display = "block";
            brandLogo.style.display = "none";
        }
        lvlBadge.textContent = `🏅 Level ${d.kyc_tier}`;
        acctHeaderText.textContent = `${d.account_number} | ${d.business_name || d.full_name}`;
        renderBal();
        const cbTxt = "₦" + (d.cashback_ngn || 0).toLocaleString("en-NG", { minimumFractionDigits:2 });
        const rfTxt = "₦" + (d.referral_ngn || 0).toLocaleString("en-NG", { minimumFractionDigits:2 });
        homeCashbackText.textContent = tabCashbackText.textContent = cbTxt;
        homeReferralText.textContent = tabReferralText.textContent = rfTxt;
        myRefCodeText.textContent = curRefCode;
        vaultText.textContent = "₦" + d.vault_ngn.toLocaleString("en-NG", { minimumFractionDigits:2 });
        moneyInText.textContent = "₦" + (d.money_in_ngn || 0).toLocaleString("en-NG", { minimumFractionDigits:2 });
        moneyOutText.textContent = "₦" + (d.money_out_ngn || 0).toLocaleString("en-NG", { minimumFractionDigits:2 });
        todoCount.textContent = d.kyc_tier >= 3 ? "3/3 Completed" : `${d.kyc_tier}/3`;
        todoTitle.textContent = d.kyc_tier >= 3 ? "Maximum Tier 3 KYC Verified" : "Upgrade KYC Level & Daily Limit";
        if (d.cac_rc_number) cacStatus.textContent = `✅ Registered Business: ${d.business_name} (${d.cac_rc_number})`;
        acctStatusText.textContent = d.account_frozen ? "❄️ ACCOUNT FROZEN (Outgoing Blocked)" : "✅ ACTIVE & PROTECTED";
        acctStatusText.style.color = d.account_frozen ? "#fb7185" : "#34d399";
        profileInfo.textContent = `${d.full_name} • Level ${d.kyc_tier} • Daily: ₦${d.daily_limit_ngn.toLocaleString()} • Single Cap: ₦${(d.single_limit_ngn || d.daily_limit_ngn).toLocaleString()}`;
        renderCardsAndTx(d);
    }
    async function claimReferral() {
        rwdMsg.className = "err"; rwdMsg.textContent = "";
        const res = await fetch("/api/rewards/claim", { method:"POST", headers:headers(), body:JSON.stringify({ code:claimRefInput.value }) });
        const d = await res.json();
        if (!res.ok) return rwdMsg.textContent = d.detail || "Invalid referral code";
        rwdMsg.className = "ok"; rwdMsg.textContent = `✅ Claimed ₦500 bonus from ${d.inviter}!`; claimRefInput.value = ""; refreshWallet();
    }
    async function redeemRewards() {
        rwdMsg.className = "err"; rwdMsg.textContent = "";
        const res = await fetch("/api/rewards/redeem", { method:"POST", headers:headers() });
        const d = await res.json();
        if (!res.ok) return rwdMsg.textContent = d.detail || "No rewards to redeem";
        rwdMsg.className = "ok"; rwdMsg.textContent = `✅ Redeemed ₦${d.redeemed_ngn.toLocaleString()} to your wallet!`; refreshWallet();
    }
    async function checkAcct() {
        recipPreview.textContent = "";
        if (toAcct.value.trim().length !== 10) return;
        const res = await fetch(`/api/lookup/${toAcct.value.trim()}?bank=${encodeURIComponent(bankSelect.value)}`, { headers:headers() });
        if (res.ok) { const d = await res.json(); recipPreview.textContent = "✅ " + d.full_name; }
        else recipPreview.textContent = "❌ Account not found";
    }
    async function doTopup() {
        topupMsg.className = "err"; topupMsg.textContent = "";
        const res = await fetch("/api/deposit", { method:"POST", headers:headers(), body:JSON.stringify({ amount:parseFloat(topupAmt.value), pin:topupPin.value, when:localTime() }) });
        const d = await res.json();
        if (!res.ok) return topupMsg.textContent = d.detail || "Failed";
        topupMsg.className = "ok"; topupMsg.textContent = "✅ Wallet funded"; topupAmt.value = topupPin.value = ""; refreshWallet();
    }
    async function doBill() {
        billMsg.className = "err"; billMsg.textContent = "";
        const res = await fetch("/api/bills", { method:"POST", headers:headers(), body:JSON.stringify({ service:billSvc.value, target:billTarget.value, amount:parseFloat(billAmt.value), pin:billPin.value, when:localTime() }) });
        const d = await res.json();
        if (!res.ok) return billMsg.textContent = d.detail || "Failed";
        billMsg.className = "ok"; billMsg.textContent = `✅ Paid + ₦${(d.cashback_ngn || 0).toFixed(2)} Cashback (${d.reference})`; billTarget.value = billAmt.value = billPin.value = ""; refreshWallet();
    }
    async function doTransfer() {
        if (isSendingTx) return;
        isSendingTx = true; sendMsg.className = "err"; sendMsg.textContent = "⏳ Sending...";
        const idemKey = "IDEM-" + Date.now() + "-" + Math.random().toString(36).slice(2, 8);
        try {
            const res = await fetch("/api/transfer", { method:"POST", headers:headers(), body:JSON.stringify({ recipient_account:toAcct.value.trim(), bank_name:bankSelect.value, amount:parseFloat(sendAmt.value), pin:sendPin.value, note:sendNote.value, when:localTime(), idem_key:idemKey }) });
            const d = await res.json();
            if (!res.ok) { sendMsg.textContent = d.detail || "Failed"; return; }
            sendMsg.className = "ok"; sendMsg.textContent = `✅ Sent to ${d.recipient} (${d.reference})`; toAcct.value = sendAmt.value = sendNote.value = sendPin.value = recipPreview.textContent = ""; refreshWallet();
        } finally { isSendingTx = false; }
    }
    async function doVault(action) {
        vaultMsg.className = "err"; vaultMsg.textContent = "";
        const res = await fetch("/api/vault", { method:"POST", headers:headers(), body:JSON.stringify({ action, amount:parseFloat(vaultAmt.value || "0"), pin:vaultPin.value, when:localTime() }) });
        const d = await res.json();
        if (!res.ok) return vaultMsg.textContent = d.detail || "Failed";
        vaultMsg.className = "ok"; vaultMsg.textContent = `✅ Done (${d.reference})`; vaultAmt.value = vaultPin.value = ""; refreshWallet();
    }
    async function submitCac() {
        cacMsg.className = "err"; cacMsg.textContent = "";
        const res = await fetch("/api/cac-register", { method:"POST", headers:headers(), body:JSON.stringify({ business_name:cacBizName.value, category:cacCat.value, pin:cacPin.value }) });
        const d = await res.json();
        if (!res.ok) return cacMsg.textContent = d.detail || "Failed";
        cacMsg.className = "ok"; cacMsg.textContent = `✅ CAC Approved! RC Number: ${d.cac_number}`; cacBizName.value = cacPin.value = ""; refreshWallet();
    }
"""
