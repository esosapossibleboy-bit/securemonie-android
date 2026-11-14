from mobile_script import MOBILE_JS

MOBILE_CSS = """
<style>
    * { box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; -webkit-tap-highlight-color: transparent; }
    body { margin: 0; background: #090f18; color: #f8fafc; padding-bottom: 80px; }
    .app-bar { background: #0d1624; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1b283b; position: sticky; top: 0; z-index: 10; }
    .brand { font-size: 1.2rem; font-weight: 800; color: #00d285; letter-spacing: 0.3px; }
    .wrap { max-width: 520px; margin: 0 auto; padding: 16px; }
    .card { background: #111c2d; border: 1px solid #1e2d44; border-radius: 18px; padding: 18px; margin-bottom: 14px; }
    .hero { background: linear-gradient(135deg, #00b875, #008252); color: #fff; border-radius: 20px; padding: 22px; margin-bottom: 16px; box-shadow: 0 10px 25px rgba(0, 184, 117, 0.2); }
    .bal { font-size: 2.1rem; font-weight: 800; margin: 6px 0; }
    input, button { width: 100%; padding: 14px; margin-top: 10px; border-radius: 12px; border: 1px solid #263954; font-size: 1rem; }
    input { background: #090f18; color: #f8fafc; }
    button { background: #00d285; color: #041d13; font-weight: 700; border: none; cursor: pointer; }
    .btn-dark { background: #1c2b42; color: #e2e8f0; }
    .tab-bar { position: fixed; bottom: 0; left: 0; right: 0; background: #0d1624; border-top: 1px solid #1b283b; display: flex; justify-content: space-around; padding: 8px 0; z-index: 20; }
    .tab-btn { background: none; border: none; color: #94a3b8; font-size: 0.8rem; font-weight: 600; margin: 0; padding: 6px; width: auto; }
    .tab-btn.active { color: #00d285; }
    .tx { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #1b283b; gap: 10px; }
    .err { color: #fb7185; font-size: 0.9rem; min-height: 20px; margin-top: 8px; }
    .ok { color: #00d285; font-size: 0.9rem; min-height: 20px; margin-top: 8px; }
</style>
"""

def render_mobile_app() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <meta name="theme-color" content="#00b875" />
    <meta name="mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-title" content="Securemonie" />
    <link rel="manifest" href="/manifest.json" />
    <link rel="icon" type="image/png" href="/icon-192.png" />
    <link rel="apple-touch-icon" href="/icon-192.png" />
    <title>Securemonie</title>{MOBILE_CSS}
    <script>if ("serviceWorker" in navigator) {{ window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js")); }}</script>
</head>
<body>
    <div class="app-bar">
        <span class="brand">🛡️ Securemonie</span>
        <button id="logoutBtn" class="btn-dark" style="display:none;width:auto;margin:0;padding:7px 14px;font-size:0.85rem;" onclick="logout()">Lock / Out</button>
    </div>

    <div class="wrap">
        <form id="authBox" class="card" autocomplete="off" onsubmit="return false;">
            <h2 id="authHeading" style="margin-top:0;">🔐 Welcome Back</h2>
            <div id="regNameRow" style="display:none;"><input id="regName" placeholder="Full Name" /></div>
            <input id="authEmail" type="email" placeholder="Email Address" />
            <input id="authPass" type="password" placeholder="Password" />
            <div id="regPinRow" style="display:none;"><input id="regPin" type="password" inputmode="numeric" maxlength="4" placeholder="Create 4-Digit Transaction PIN" /></div>
            <button id="authSubmitBtn" type="button" onclick="submitAuth()">Log In</button>
            <button id="authSwitchBtn" type="button" class="btn-dark" onclick="switchAuth()">New to Securemonie? Create Account</button>
            <p id="authMsg" class="err"></p>
        </form>

        <div id="appShell" style="display:none;">
            <div id="tabHome">
                <div class="hero">
                    <div id="greetText" style="font-weight:600;opacity:0.95;"></div>
                    <div id="balText" class="bal">₦0.00</div>
                    <div style="font-size:0.9rem;opacity:0.95;">Account No: <strong id="acctText"></strong></div>
                </div>
                <div class="card">
                    <h3 style="margin-top:0;">💳 Add Money to Wallet</h3>
                    <input id="topupAmt" type="number" inputmode="decimal" placeholder="Amount (₦)" />
                    <input id="topupPin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter 4-Digit PIN" />
                    <button onclick="doTopup()">+ Add Money</button>
                    <p id="topupMsg" class="err"></p>
                </div>
            </div>

            <div id="tabSend" style="display:none;">
                <div class="card">
                    <h3 style="margin-top:0;">💸 Send Money</h3>
                    <input id="toAcct" maxlength="10" inputmode="numeric" placeholder="10-Digit Account Number (80...)" oninput="checkAcct()" />
                    <div id="recipPreview" class="ok"></div>
                    <input id="sendAmt" type="number" inputmode="decimal" placeholder="Amount (₦)" />
                    <input id="sendNote" maxlength="50" placeholder="Note (Optional)" />
                    <input id="sendPin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter 4-Digit PIN" />
                    <button onclick="doTransfer()">Send Instantly</button>
                    <p id="sendMsg" class="err"></p>
                </div>
            </div>

            <div id="tabVault" style="display:none;">
                <div class="card">
                    <h3 style="margin-top:0;">🌱 SecureVault (15% p.a.)</h3>
                    <div style="font-size:1.6rem;font-weight:800;color:#00d285;margin-bottom:8px;">Saved: <span id="vaultText">₦0.00</span></div>
                    <input id="vaultAmt" type="number" inputmode="decimal" placeholder="Amount (₦)" />
                    <input id="vaultPin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter 4-Digit PIN" />
                    <button onclick="doVault('save')">Save to Vault</button>
                    <button class="btn-dark" onclick="doVault('withdraw')">Withdraw to Wallet</button>
                    <button class="btn-dark" onclick="doVault('interest')">✨ Simulate 30-Day Interest</button>
                    <p id="vaultMsg" class="err"></p>
                </div>
            </div>

            <div id="tabHistory" style="display:none;">
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <h3 style="margin:0;">🧾 Activity</h3>
                        <button class="btn-dark" style="width:auto;margin:0;padding:8px 12px;font-size:0.85rem;" onclick="getPdf()">📄 PDF Receipt</button>
                    </div>
                    <div id="txList" style="margin-top:10px;"></div>
                </div>
            </div>
        </div>
    </div>

    <div id="bottomTabs" class="tab-bar" style="display:none;">
        <button id="btnHome" class="tab-btn active" onclick="openTab('Home')">🏠<br/>Home</button>
        <button id="btnSend" class="tab-btn" onclick="openTab('Send')">💸<br/>Send</button>
        <button id="btnVault" class="tab-btn" onclick="openTab('Vault')">🌱<br/>Vault</button>
        <button id="btnHistory" class="tab-btn" onclick="openTab('History')">🧾<br/>History</button>
    </div>
    {MOBILE_JS}
</body>
</html>"""
