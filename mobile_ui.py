from android_pwa import LOGO_SVG
from mobile_script import MOBILE_JS
from mobile_styles import MOBILE_CSS

def render_mobile_app() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <meta name="theme-color" content="#4f46e5" />
    <meta name="mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-title" content="Securemonie" />
    <link rel="manifest" href="/manifest.json" />
    <link rel="icon" type="image/png" href="/icon-192.png" />
    <link rel="apple-touch-icon" href="/icon-192.png" />
    <title>Securemonie Microfinance Bank</title>{MOBILE_CSS}
    <script>if ("serviceWorker" in navigator) {{ window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js")); }}</script>
</head>
<body>
    <div class="app-bar">
        <div class="brand">{LOGO_SVG}<span>Securemonie</span></div>
        <button id="logoutBtn" class="btn-dark" style="display:none;width:auto;margin:0;padding:7px 12px;font-size:0.82rem;" onclick="logout()">Lock App</button>
    </div>

    <div class="wrap">
        <form id="authBox" class="card" autocomplete="off" onsubmit="return false;">
            <div style="text-align:center;margin-bottom:10px;">{LOGO_SVG}</div>
            <h2 id="authHeading" style="margin:0 0 6px;text-align:center;">Sign In to Securemonie</h2>
            <div id="regFields" style="display:none;">
                <input id="regName" placeholder="Legal Full Name (as on BVN/NIN)" />
                <input id="regPhone" type="tel" maxlength="11" inputmode="numeric" placeholder="Nigerian Phone Number (080...)" />
                <select id="regType"><option value="Personal">Personal Banking Account</option><option value="Business">Business / POS Account</option></select>
            </div>
            <input id="authIdent" placeholder="Phone Number or Email Address" />
            <input id="authPass" type="password" placeholder="Password (8+ chars, A-z, 0-9)" />
            <div id="regPinFields" style="display:none;">
                <input id="regPin" type="password" inputmode="numeric" maxlength="4" placeholder="Create 4-Digit Transaction PIN" />
                <input id="regBvn" type="text" inputmode="numeric" maxlength="11" placeholder="Optional 11-Digit BVN/NIN (Instant Tier 2)" />
            </div>
            <button id="authSubmitBtn" type="button" onclick="submitAuth()">Sign In</button>
            <button id="authSwitchBtn" type="button" class="btn-dark" onclick="switchAuth()">Open a Free Securemonie Account</button>
            <p id="authMsg" class="err"></p>
        </form>

        <div id="appShell" style="display:none;">
            <div id="tabHome">
                <div class="hero">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span id="greetText" style="font-weight:700;"></span>
                        <span id="tierBadge" class="badge">TIER 1</span>
                    </div>
                    <div class="bal">
                        <span id="balText">₦0.00</span>
                        <button type="button" onclick="toggleBal()" style="width:auto;margin:0;padding:4px 10px;background:rgba(255,255,255,0.18);font-size:0.85rem;">👁️</button>
                    </div>
                    <div style="display:flex;justify-content:space-between;align-items:center;font-size:0.88rem;">
                        <span>Acct: <strong id="acctText"></strong></span>
                        <button type="button" onclick="copyAcct()" style="width:auto;margin:0;padding:4px 10px;background:#f59e0b;color:#111827;font-size:0.78rem;">Copy</button>
                    </div>
                </div>

                <div class="card">
                    <h3 style="margin-top:0;">💳 Fund Wallet & Pay Bills</h3>
                    <input id="topupAmt" type="number" inputmode="decimal" placeholder="Top-Up Amount (₦)" />
                    <input id="topupPin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter 4-Digit PIN" />
                    <button class="btn-gold" onclick="doTopup()">+ Add Money Instantly</button>
                    <hr style="border-color:#222f52;margin:14px 0;" />
                    <select id="billSvc"><option value="MTN Airtime">MTN Airtime</option><option value="Airtel Data">Airtel Data</option><option value="Glo Airtime">Glo Airtime</option><option value="IKEDC Prepaid">IKEDC Electricity</option></select>
                    <input id="billTarget" placeholder="Phone Number or Meter Number" />
                    <input id="billAmt" type="number" inputmode="decimal" placeholder="Bill Amount (₦)" />
                    <input id="billPin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter 4-Digit PIN" />
                    <button class="btn-dark" onclick="doBill()">Pay Airtime / Bill</button>
                    <p id="homeMsg" class="err"></p>
                </div>
            </div>

            <div id="tabSend" style="display:none;">
                <div class="card">
                    <h3 style="margin-top:0;">💸 Transfer Money</h3>
                    <select id="bankSelect" onchange="checkAcct()">
                        <option value="Securemonie MFB">Securemonie MFB (Instant & Free)</option>
                        <option value="GTBank">GTBank</option><option value="Access Bank">Access Bank</option>
                        <option value="Zenith Bank">Zenith Bank</option><option value="UBA">UBA</option>
                        <option value="FirstBank">FirstBank</option><option value="OPay">OPay</option>
                    </select>
                    <input id="toAcct" maxlength="10" inputmode="numeric" placeholder="10-Digit Account Number" oninput="checkAcct()" />
                    <div id="recipPreview" class="ok"></div>
                    <input id="sendAmt" type="number" inputmode="decimal" placeholder="Amount (₦)" />
                    <input id="sendNote" maxlength="50" placeholder="Narration (Optional)" />
                    <input id="sendPin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter 4-Digit Transaction PIN" />
                    <button onclick="doTransfer()">Send Money</button>
                    <p id="sendMsg" class="err"></p>
                </div>
            </div>

            <div id="tabVault" style="display:none;">
                <div class="card">
                    <h3 style="margin-top:0;">🌱 Target Savings Vault (15% p.a.)</h3>
                    <div style="font-size:1.6rem;font-weight:800;color:#fbbf24;margin-bottom:8px;">Saved: <span id="vaultText">₦0.00</span></div>
                    <input id="vaultAmt" type="number" inputmode="decimal" placeholder="Amount (₦)" />
                    <input id="vaultPin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter 4-Digit PIN" />
                    <button class="btn-gold" onclick="doVault('save')">Save to Target Vault</button>
                    <button class="btn-dark" onclick="doVault('withdraw')">Withdraw to Main Wallet</button>
                    <button class="btn-dark" onclick="doVault('interest')">✨ Simulate 30-Day Interest</button>
                    <p id="vaultMsg" class="err"></p>
                </div>
            </div>

            <div id="tabHistory" style="display:none;">
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <h3 style="margin:0;">🧾 Bank Statement</h3>
                        <button class="btn-gold" style="width:auto;margin:0;padding:8px 12px;font-size:0.82rem;" onclick="getPdf()">📄 Download PDF</button>
                    </div>
                    <div id="txList" style="margin-top:10px;"></div>
                </div>
            </div>

            <div id="tabSettings" style="display:none;">
                <div class="card">
                    <h3 style="margin-top:0;">⚙️ Account & Security Settings</h3>
                    <div id="profileInfo" style="font-size:0.9rem;color:#cbd5e1;line-height:1.6;margin-bottom:10px;"></div>
                    <select id="settingType" onchange="updateSettingHint()">
                        <option value="kyc">Upgrade KYC Tier (Enter 11-Digit BVN/NIN)</option>
                        <option value="limit">Set Custom Daily Transfer Limit (₦)</option>
                        <option value="pin">Change 4-Digit Transaction PIN</option>
                        <option value="password">Change Account Password</option>
                    </select>
                    <input id="settingNewVal" placeholder="Enter 11-Digit BVN or NIN" />
                    <input id="settingPass" type="password" placeholder="Verify Account Password" />
                    <button onclick="saveSetting()">Save Security Setting</button>
                    <p id="setMsg" class="err"></p>
                </div>
            </div>
        </div>
    </div>

    <div id="bottomTabs" class="tab-bar" style="display:none;">
        <button id="btnHome" class="tab-btn active" onclick="openTab('Home')">🏠<br/>Home</button>
        <button id="btnSend" class="tab-btn" onclick="openTab('Send')">💸<br/>Transfer</button>
        <button id="btnVault" class="tab-btn" onclick="openTab('Vault')">🌱<br/>Savings</button>
        <button id="btnHistory" class="tab-btn" onclick="openTab('History')">🧾<br/>History</button>
        <button id="btnSettings" class="tab-btn" onclick="openTab('Settings')">⚙️<br/>Settings</button>
    </div>
    {MOBILE_JS}
</body>
</html>"""
