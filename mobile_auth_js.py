AUTH_JS = """
    let token = localStorage.getItem("sm_token") || "", keypadBuf = "", generatedOtp = "", capturedSelfie = "", camStream = null, idle = null;
    const headers = () => ({ "Content-Type":"application/json", "Authorization":"Bearer " + token });
    const localTime = () => new Date().toLocaleString("en-GB", { day:"2-digit", month:"short", year:"numeric", hour:"2-digit", minute:"2-digit" });
    function bumpIdle() { clearTimeout(idle); if (token) idle = setTimeout(() => lockApp("🔒 Auto-locked after 10 mins inactivity"), 600000); }
    ["click", "touchstart", "keydown"].forEach(e => window.addEventListener(e, bumpIdle, { passive:true }));
    function getInitials(name) {
        const p = (name || "SM").trim().split(/\\s+/);
        return (p[0][0] + (p[1] ? p[1][0] : (p[0][1] || ""))).toUpperCase();
    }
    function saveDeviceProfile(name, phone, selfie) {
        if (name) localStorage.setItem("sm_name", name);
        if (phone) localStorage.setItem("sm_phone", phone);
        if (selfie) localStorage.setItem("sm_selfie", selfie);
    }
    function stopCamera() { if (camStream) { camStream.getTracks().forEach(t => t.stop()); camStream = null; } }
    async function startCamera() {
        signupMsg.textContent = "";
        try {
            stopCamera();
            camStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
            selfiePreview.style.display = "none";
            selfieVideo.srcObject = camStream;
            selfieVideo.style.display = "block";
            snapBtn.style.display = "inline-block";
            camBtn.textContent = "Restart Camera";
        } catch (e) { signupMsg.textContent = "Please allow front camera access in your browser settings to take a selfie."; }
    }
    function takeSelfie() {
        const ctx = selfieCanvas.getContext("2d");
        ctx.drawImage(selfieVideo, 0, 0, 160, 160);
        capturedSelfie = selfieCanvas.toDataURL("image/jpeg", 0.75);
        selfiePreview.src = capturedSelfie;
        selfiePreview.style.display = "block";
        selfieVideo.style.display = "none";
        snapBtn.style.display = "none";
        camBtn.textContent = "Retake Selfie";
        stopCamera();
    }
    function showQuickUnlock(msg = "") {
        const phone = localStorage.getItem("sm_phone"), name = localStorage.getItem("sm_name"), selfie = localStorage.getItem("sm_selfie");
        if (!phone) return switchToFullLogin(msg);
        loginBox.style.display = "none"; signupWizard.style.display = "none"; appShell.style.display = "none"; bottomTabs.style.display = "none"; logoutBtn.style.display = "none";
        quickUnlockBox.style.display = "block";
        if (selfie) { unlockSelfieImg.src = selfie; unlockSelfieImg.style.display = "block"; avatarInitials.style.display = "none"; }
        else { unlockSelfieImg.style.display = "none"; avatarInitials.style.display = "flex"; avatarInitials.textContent = getInitials(name); }
        const masked = "📞 ***" + phone.slice(-4);
        topPhonePill.textContent = masked; midPhonePill.textContent = masked;
        keypadBuf = ""; renderKeypadCells(); keypadMsg.textContent = typeof msg === "string" ? msg : "";
    }
    function switchToFullLogin(msg = "") {
        stopCamera(); quickUnlockBox.style.display = "none"; signupWizard.style.display = "none"; appShell.style.display = "none"; bottomTabs.style.display = "none"; logoutBtn.style.display = "none";
        loginBox.style.display = "block"; loginMsg.textContent = typeof msg === "string" ? msg : "";
    }
    function openSignupWizard() {
        loginBox.style.display = "none"; quickUnlockBox.style.display = "none"; signupWizard.style.display = "block";
        signupMsg.textContent = ""; goStep(1);
    }
    function backToLogin() { switchToFullLogin(); }
    function toggleBizFields() { bizOnlyFields.style.display = regType.value === "Business" ? "block" : "none"; }
    function sendOtp() {
        signupMsg.textContent = "";
        if (!/^0[789][01]\\d{8}$/.test(regPhone.value.trim())) return signupMsg.textContent = "Enter a valid 11-digit Nigerian phone number (e.g. 08012345678)";
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
        const steps =;
        steps.forEach(n => document.getElementById("wizStep" + n).style.display = n === step ? "block" : "none");
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
            selfie_data: capturedSelfie
        };
        const res = await fetch("/api/register", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload) });
        const d = await res.json();
        if (!res.ok) return signupMsg.textContent = Array.isArray(d.detail) ? d.detail.map(x => x.msg).join(", ") : (d.detail || "Registration failed");
        token = d.token; localStorage.setItem("sm_token", token); saveDeviceProfile(d.full_name, d.phone, d.selfie_data);
        enterApp();
    }
    function renderKeypadCells() {
        const cells = passcodeCells.children;
        for (let i = 0; i < 6; i++) {
            cells[i].textContent = i < keypadBuf.length ? "•" : "";
            cells[i].className = "pin-cell" + (i === keypadBuf.length ? " active" : "");
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
        const res = await fetch("/api/login", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({ identifier:localStorage.getItem("sm_phone"), password:keypadBuf }) });
        const d = await res.json();
        keypadBuf = ""; renderKeypadCells();
        if (!res.ok) return keypadMsg.textContent = d.detail || "Incorrect 6-digit passcode";
        token = d.token; localStorage.setItem("sm_token", token); saveDeviceProfile(d.full_name, d.phone, d.selfie_data);
        enterApp();
    }
    async function submitLogin() {
        loginMsg.textContent = "";
        const res = await fetch("/api/login", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({ identifier:loginIdent.value, password:loginPass.value }) });
        const d = await res.json();
        if (!res.ok) return loginMsg.textContent = Array.isArray(d.detail) ? d.detail.map(x => x.msg).join(", ") : (d.detail || "Sign in failed");
        token = d.token; localStorage.setItem("sm_token", token); saveDeviceProfile(d.full_name, d.phone, d.selfie_data);
        loginIdent.value = loginPass.value = "";
        enterApp();
    }
"""
