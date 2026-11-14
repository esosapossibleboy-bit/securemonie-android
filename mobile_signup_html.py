SIGNUP_WIZARD_HTML = """
        <form id="signupWizard" class="card" style="display:none;" autocomplete="off" onsubmit="return false;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span id="wizBadge" class="badge">STEP 1 OF 4</span>
                <button type="button" class="btn-dark" style="width:auto;margin:0;padding:5px 10px;font-size:0.8rem;" onclick="backToLogin()">Back to Sign In</button>
            </div>

            <div id="wizStep1">
                <h3 style="margin:6px 0;">1. Account Type & Phone OTP</h3>
                <select id="regType" onchange="toggleBizFields()">
                    <option value="Personal">Personal Banking Account</option>
                    <option value="Business">Business / Merchant Account</option>
                </select>
                <input id="regPhone" type="tel" maxlength="11" inputmode="numeric" placeholder="BVN-Linked Phone Number (080...)" />
                <button type="button" class="btn-gold" onclick="sendOtp()">Send 6-Digit SMS OTP</button>
                <div id="otpHint" class="ok"></div>
                <input id="regOtp" type="text" maxlength="6" inputmode="numeric" placeholder="Enter 6-Digit OTP Code" />
                <button type="button" onclick="goStep(2)">Verify & Continue →</button>
            </div>

            <div id="wizStep2" style="display:none;">
                <h3 style="margin:6px 0;">2. Identity, KYC & Live Selfie</h3>
                <input id="regName" placeholder="Legal Full Name (as on BVN/NIN)" />
                <input id="regEmail" type="email" placeholder="Email Address" />
                <select id="regIdType">
                    <option value="NIN Slip">NIN Slip</option>
                    <option value="Voters Card">Voter's Card</option>
                    <option value="International Passport">International Passport</option>
                    <option value="Drivers License">Driver's License</option>
                </select>
                <input id="regBvn" type="text" maxlength="11" inputmode="numeric" placeholder="11-Digit BVN (Optional for Tier 1)" />
                <input id="regNin" type="text" maxlength="11" inputmode="numeric" placeholder="11-Digit NIN (Optional for Tier 1)" />
                <input id="regAddress" placeholder="Residential / Proof of Address" />

                <div style="background:#0b1021;border:1px dashed #4f46e5;border-radius:14px;padding:12px;margin-top:10px;text-align:center;">
                    <div style="font-weight:700;font-size:0.88rem;color:#fbbf24;margin-bottom:6px;">📸 Live Face Selfie Verification (Required)</div>
                    <video id="selfieVideo" autoplay playsinline muted style="display:none;width:120px;height:120px;object-fit:cover;border-radius:50%;border:3px solid #f59e0b;margin:0 auto 8px;"></video>
                    <img id="selfiePreview" style="display:none;width:120px;height:120px;object-fit:cover;border-radius:50%;border:3px solid #34d399;margin:0 auto 8px;" />
                    <canvas id="selfieCanvas" width="160" height="160" style="display:none;"></canvas>
                    <div style="display:flex;gap:8px;justify-content:center;">
                        <button type="button" class="btn-dark" style="margin:0;padding:8px 10px;font-size:0.82rem;" onclick="startCamera()">Open Camera</button>
                        <button type="button" id="snapBtn" class="btn-gold" style="display:none;margin:0;padding:8px 10px;font-size:0.82rem;" onclick="takeSelfie()">Capture Selfie</button>
                    </div>
                    <label style="display:block;margin-top:8px;font-size:0.78rem;color:#94a3b8;cursor:pointer;">
                        Or take selfie with phone camera:
                        <input id="selfieFileInput" type="file" accept="image/*" capture="user" onchange="handleSelfieFile(event)" style="margin-top:4px;padding:6px;font-size:0.78rem;" />
                    </label>
                </div>

                <div style="display:flex;gap:8px;">
                    <button type="button" class="btn-dark" onclick="goStep(1)">← Back</button>
                    <button type="button" onclick="goStep(3)">Next Step →</button>
                </div>
            </div>

            <div id="wizStep3" style="display:none;">
                <h3 style="margin:6px 0;">3. Profile & Compliance Details</h3>
                <div id="bizOnlyFields" style="display:none;">
                    <input id="regBizName" placeholder="Registered Business / Shop Name" />
                    <select id="regBizCat">
                        <option value="Retail & Supermarket">Retail & Supermarket</option>
                        <option value="POS & Agency Banking">POS & Agency Banking</option>
                        <option value="Food & Hospitality">Food & Hospitality</option>
                        <option value="Tech & Digital Services">Tech & Digital Services</option>
                    </select>
                </div>
                <select id="regPep">
                    <option value="No">Politically Exposed Person (PEP): No</option>
                    <option value="Yes">Politically Exposed Person (PEP): Yes</option>
                </select>
                <select id="regRevenue">
                    <option value="Salary / Employment">Source of Revenue: Salary / Employment</option>
                    <option value="Business / Trading Sales">Source of Revenue: Business / Trading Sales</option>
                    <option value="Freelance / Consulting">Source of Revenue: Freelance / Consulting</option>
                </select>
                <div style="display:flex;gap:8px;">
                    <button type="button" class="btn-dark" onclick="goStep(2)">← Back</button>
                    <button type="button" onclick="goStep(4)">Next Step →</button>
                </div>
            </div>

            <div id="wizStep4" style="display:none;">
                <h3 style="margin:6px 0;">4. Security Passcodes & Attestation</h3>
                <input id="regPass" type="password" maxlength="6" inputmode="numeric" placeholder="Create 6-Digit Login Passcode" />
                <input id="regPin" type="password" maxlength="4" inputmode="numeric" placeholder="Create 4-Digit Transaction PIN" />
                <label style="display:flex;align-items:flex-start;gap:10px;margin-top:12px;font-size:0.86rem;color:#cbd5e1;cursor:pointer;">
                    <input id="regAttest" type="checkbox" style="width:20px;height:20px;margin:2px 0 0;" />
                    <span>I Attest that all identity, address, and compliance details provided are true and accurate.</span>
                </label>
                <div style="display:flex;gap:8px;">
                    <button type="button" class="btn-dark" onclick="goStep(3)">← Back</button>
                    <button type="button" class="btn-gold" onclick="submitSignup()">Complete Registration</button>
                </div>
            </div>
            <p id="signupMsg" class="err"></p>
        </form>
"""
