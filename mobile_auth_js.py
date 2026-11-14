from mobile_device_js import DEVICE_JS

AUTH_CORE_JS = """
    function showQuickUnlock(msg = "") {
        const phone = localStorage.getItem("sm_phone"), name = localStorage.getItem("sm_name"), selfie = localStorage.getItem("sm_selfie");
        if (!phone) return switchToFullLogin(msg);
        loginBox.style.display = "none"; signupWizard.style.display = "none"; forgotBox.style.display = "none"; emergencyBox.style.display = "none";
        appShell.style.display = "none"; bottomTabs.style.display = "none";
        quickUnlockBox.style.display = "block";
        bioUnlockBtn.style.display = localStorage.getItem("sm_bio_pass") ? "block" : "none";
        if (selfie) { unlockSelfieImg.src = selfie; unlockSelfieImg.style.display = "block"; avatarInitials.style.display = "none"; }
        else { unlockSelfieImg.style.display = "none"; avatarInitials.style.display = "flex"; avatarInitials.textContent = getInitials(name); }
        const masked = "📞 ***" + phone.slice(-4);
        topPhonePill.textContent = masked; midPhonePill.textContent = masked;
        keypadBuf = ""; renderKeypadCells(); keypadMsg.textContent = typeof msg === "string" ? msg : "";
    }
    function switchToFullLogin(msg = "") {
        stopCamera(); quickUnlockBox.style.display = "none"; signupWizard.style.display = "none"; forgotBox.style.display = "none"; emergencyBox.style.display = "none";
        appShell.style.display = "none"; bottomTabs.style.display = "none";
        loginBox.style.display = "block"; loginMsg.textContent = typeof msg === "string" ? msg : "";
    }
    function openEmergencyBox() {
        quickUnlockBox.style.display = "none"; loginBox.style.display = "none"; signupWizard.style.display = "none"; forgotBox.style.display = "none";
        emergencyBox.style.display = "block"; emMsg.textContent = "";
    }
    async function submitEmergencyLock() {
        emMsg.className = "err"; emMsg.textContent = "";
        const res = await fetch("/api/emergency-lock", {
            method:"POST", headers:{"Content-Type":"application/json"},
            body:JSON.stringify({ identifier:emIdent.value.trim(), pin:emPin.value })
        });
        const d = await res.json();
        if (!res.ok) return emMsg.textContent = Array.isArray(d.detail) ? d.detail.map(x => x.msg).join(", ") : (d.detail || "Lock failed");
        emMsg.className = "ok"; emMsg.textContent = "🚨 SUCCESS: Account & all Virtual Cards are now FROZEN!";
        emIdent.value = emPin.value = "";
    }
    function openForgotBox() {
        quickUnlockBox.style.display = "none"; loginBox.style.display = "none"; signupWizard.style.display = "none"; emergencyBox.style.display = "none";
        forgotBox.style.display = "block"; fgMsg.textContent = "";
        fgIdent.value = localStorage.getItem("sm_phone") || "";
    }
    async function submitForgot() {
        fgMsg.className = "err"; fgMsg.textContent = "";
        const res = await fetch("/api/forgot-passcode", {
            method:"POST", headers:{"Content-Type":"application/json"},
            body:JSON.stringify({ identifier:fgIdent.value.trim(), pin:fgPin.value, new_passcode:fgNewPass.value })
        });
        const d = await res.json();
        if (!res.ok) return fgMsg.textContent = Array.isArray(d.detail) ? d.detail.map(x => x.msg).join(", ") : (d.detail || "Reset failed");
        fgMsg.className = "ok"; fgMsg.textContent = "✅ Passcode reset! Sign in with your new 6-digit passcode.";
        fgPin.value = fgNewPass.value = "";
        setTimeout(() => { forgotBox.style.display = "none"; switchToFullLogin("✅ Passcode updated—enter your new 6-digit passcode."); }, 1200);
    }
    function openSignupWizard() {
        loginBox.style.display = "none"; quickUnlockBox.style.display = "none"; forgotBox.style.display = "none"; emergencyBox.style.display = "none";
        signupWizard.style.display = "block"; signupMsg.textContent = ""; goStep(1);
    }
    function backToLogin() { switchToFullLogin(); }
    function toggleBizFields() { bizOnlyFields.style.display = regType.value === "Business" ? "block" : "none"; }
    function sendOtp() {
        signupMsg.textContent = "";
        if (!/^0\\d{10}$/.test(regPhone.value.trim())) return signupMsg.textContent = "Enter a valid 11-digit Nigerian phone number (e.g. 08012345678)";
        generatedOtp = String(Math.floor(100000 + Math.random() * 900000));
        otpHint.textContent = `📩 Demo SMS OTP sent to ${regPhone.value.trim()}: ${generatedOtp}`;
    }
    function goStep(step) {
        signupMsg.textContent = "";
        if (step === 2 && (!generatedOtp || regOtp.value.trim() !== generatedOtp)) {
            return signupMsg.textContent = "Please click Send SMS OTP and enter the 6-digit code first";
        }
        if (step === 3) {
            if (!regName.value.trim() || !regEmail.value.includes("@")) return signupMsg.textContent = "Enter your Legal Full Name and Email Address";
            if (!capturedSelfie) return signupMsg.textContent = "Please click Open Front Camera and Take a Selfie before continuing";
        }
        stopCamera();
        for (let n = 1; n <= 4; n++) {
            document.getElementById("wizStep" + n).style.display = n === step ? "block" : "none";
        }
        wizBadge.textContent = `STEP ${step} OF 4`;
        toggleBizFields();
    }
    async function submitSignup() {
        signupMsg.textContent = "";
        if (!regAttest.checked) return signupMsg.textContent = "Please check the I Attest box to finalize registration";
        const payload = {
            full_name: regName.value.trim(), phone: regPhone.value.trim(), email: regEmail.value.trim(),
            account_type: regType.value, password: regPass.value, pin: regPin.value,
            bvn: regBvn.value.trim(), nin: regNin.value.trim(), id_type: regIdType.value,
            business_name: regBizName.value.trim(), business_category: regBizCat.value,
            address: regAddress.value.trim(), pep_status: regPep.value, revenue_source: regRevenue.value,
            selfie_data: capturedSelfie, device_id: getDeviceId()
        };
        const res = await fetch("/api/register", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload) });
        const d = await res.json();
        if (!res.ok) return signupMsg.textContent = Array.isArray(d.detail) ? d.detail.map(x => x.msg).join(", ") : (d.detail || "Registration failed");
        token = d.token; sessionStorage.setItem("sm_token", token); saveDeviceProfile(d.full_name, d.phone, d.selfie_data);
        enterApp();
    }
    function renderKeypadCells() {
        const cells = passcodeCells.children;
        for (let i = 0; i < 6; i++) {
            cells.item(i).textContent = i < keypadBuf.length ? "•" : "";
            cells.item(i).className = "pin-cell" + (i === keypadBuf.length ? " active" : "");
        }
    }
    function pressDigit(d) {
        if (keypadBuf.length >= 6) return;
        keypadBuf += d; renderKeypadCells();
        if (keypadBuf.length === 6) submitKeypad();
    }
    function delDigit() { keypadBuf = keypadBuf.slice(0, -1); renderKeypadCells(); }
    async function submitKeypad() {
        if (keypadBuf.length !== 6) return keypadMsg.textContent = "Enter all 6 digits";
        keypadMsg.textContent = "";
        const res = await fetch("/api/login", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({ identifier:localStorage.getItem("sm_phone"), password:keypadBuf, device_id:getDeviceId() }) });
        const d = await res.json();
        keypadBuf = ""; renderKeypadCells();
        if (!res.ok) return keypadMsg.textContent = d.detail || "Incorrect 6-digit passcode";
        token = d.token; sessionStorage.setItem("sm_token", token); saveDeviceProfile(d.full_name, d.phone, d.selfie_data);
        enterApp();
    }
    async function submitLogin() {
        loginMsg.textContent = "";
        if (twoFaRow.style.display === "block" && loginOtp.value.trim() !== login2faCode) {
            return loginMsg.textContent = "Enter the 6-digit 2FA verification code shown above";
        }
        const res = await fetch("/api/login", {
            method:"POST", headers:{"Content-Type":"application/json"},
            body:JSON.stringify({ identifier:loginIdent.value, password:loginPass.value, device_id:getDeviceId(), otp_code:loginOtp.value.trim() })
        });
        const d = await res.json();
        if (!res.ok) {
            if (d.detail === "2FA_REQUIRED") {
                login2faCode = String(Math.floor(100000 + Math.random() * 900000));
                twoFaRow.style.display = "block";
                twoFaHint.textContent = `📩 Demo 2FA Security Code: ${login2faCode}`;
                return;
            }
            return loginMsg.textContent = Array.isArray(d.detail) ? d.detail.map(x => x.msg).join(", ") : (d.detail || "Sign in failed");
        }
        token = d.token; sessionStorage.setItem("sm_token", token); saveDeviceProfile(d.full_name, d.phone, d.selfie_data);
        loginIdent.value = loginPass.value = loginOtp.value = ""; twoFaRow.style.display = "none";
        enterApp();
    }
"""

AUTH_JS = f"{DEVICE_JS}\n{AUTH_CORE_JS}"
