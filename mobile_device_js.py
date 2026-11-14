DEVICE_JS = """
    let token = sessionStorage.getItem("sm_token") || "", keypadBuf = "", generatedOtp = "", login2faCode = "", capturedSelfie = "", camStream = null, idle = null;
    function getDeviceId() {
        let id = localStorage.getItem("sm_device_id");
        if (!id) { id = "DEV-" + Math.random().toString(36).slice(2) + Date.now().toString(36); localStorage.setItem("sm_device_id", id); }
        return id;
    }
    const headers = () => ({ "Content-Type":"application/json", "Authorization":"Bearer " + token });
    const localTime = () => new Date().toLocaleString("en-GB", { day:"2-digit", month:"short", year:"numeric", hour:"2-digit", minute:"2-digit" });
    function bumpIdle() {
        clearTimeout(idle);
        if (token) idle = setTimeout(() => lockApp("🔒 Auto-locked after 3 mins inactivity"), 180000);
    }
    window.addEventListener("click", bumpIdle, { passive:true });
    window.addEventListener("touchstart", bumpIdle, { passive:true });
    window.addEventListener("keydown", bumpIdle, { passive:true });
    document.addEventListener("visibilitychange", () => {
        if (document.hidden && token) lockApp("🔒 Locked for your security");
    });
    function getInitials(name) {
        const clean = (name || "SM").trim().replace(/\\s+/g, " ");
        const spaceIdx = clean.indexOf(" ");
        if (spaceIdx > 0) return (clean.charAt(0) + clean.charAt(spaceIdx + 1)).toUpperCase();
        return clean.slice(0, 2).toUpperCase();
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
    async function unlockWithBiometrics() {
        keypadMsg.textContent = "";
        const savedPass = localStorage.getItem("sm_bio_pass");
        if (!savedPass || !window.PublicKeyCredential) return keypadMsg.textContent = "Enable Biometrics inside Security Settings first.";
        try {
            const challenge = new Uint8Array(16); crypto.getRandomValues(challenge);
            await navigator.credentials.get({ publicKey: { challenge, timeout: 30000, userVerification: "required" } });
            keypadBuf = savedPass;
            submitKeypad();
        } catch (e) { keypadMsg.textContent = "Fingerprint / Face ID cancelled. Enter 6-digit passcode."; }
    }
"""
