from android_pwa import LOGO_SVG
from mobile_auth_html import AUTH_HTML
from mobile_script import MOBILE_JS
from mobile_styles import MOBILE_CSS
from mobile_tabs_html import TABS_HTML

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
        <div style="display:flex;align-items:center;gap:8px;">
            <img id="topSelfieImg" style="display:none;width:34px;height:34px;border-radius:50%;object-fit:cover;border:2px solid #f59e0b;" />
            <div id="brandLogo" class="brand">{LOGO_SVG}<span>Securemonie</span></div>
            <span id="lvlBadge" class="lvl-pill" style="display:none;">🏅 Level 1</span>
        </div>
        <div id="topActions" style="display:none;gap:8px;align-items:center;">
            <button type="button" class="btn-dark" style="width:auto;margin:0;padding:6px 10px;font-size:0.85rem;" onclick="openPanel('panelSettings')">🎧</button>
            <button type="button" class="btn-dark" style="width:auto;margin:0;padding:6px 10px;font-size:0.82rem;" onclick="lockApp()">🔒 Lock</button>
        </div>
    </div>

    <div class="wrap">
        {AUTH_HTML}
        <div id="appShell" style="display:none;">
            <div id="tabHome">
                <div class="hero">
                    <div style="display:flex;justify-content:space-between;align-items:center;font-size:0.88rem;opacity:0.95;">
                        <span id="acctHeaderText">8100000000 | Customer</span>
                        <button type="button" onclick="copyAcct()" style="width:auto;margin:0;padding:3px 9px;background:rgba(255,255,255,0.2);font-size:0.75rem;">📋 Copy</button>
                    </div>
                    <div class="bal-row">
                        <span id="balText">₦0.00</span>
                        <button type="button" onclick="toggleBal()" style="width:auto;margin:0;padding:4px 8px;background:none;font-size:1.1rem;">👁️</button>
                    </div>
                    <div style="font-size:0.78rem;opacity:0.85;">Last updated just now</div>
                    <div class="hero-actions">
                        <button type="button" class="pill-btn" onclick="openPanel('panelTopup')">+ Add Money</button>
                        <button type="button" class="pill-btn" onclick="openPanel('panelHistory')">🕒 History</button>
                    </div>
                </div>

                <div class="card">
                    <div class="sec-head" style="margin-top:0;"><span>Services</span><button type="button" class="sec-link" onclick="openTab('Services')">View All</button></div>
                    <div class="svc-grid">
                        <button type="button" class="svc-item" onclick="openPanel('panelTransfer')"><span class="svc-icon">⇄</span>Transfer</button>
                        <button type="button" class="svc-item" onclick="openBillService('MTN Airtime')"><span class="svc-icon">📞</span>Airtime</button>
                        <button type="button" class="svc-item" onclick="openBillService('Airtel Data')"><span class="svc-icon">📶</span>Data</button>
                        <button type="button" class="svc-item" onclick="openBillService('Bet9ja Wallet')"><span class="svc-icon">⚽</span>Betting</button>
                        <button type="button" class="svc-item" onclick="openPanel('panelVault')"><span class="svc-icon">🐷</span>Savings</button>
                        <button type="button" class="svc-item" onclick="openBillService('WAEC / JAMB PIN')"><span class="svc-icon">🎓</span>Education</button>
                        <button type="button" class="svc-item" onclick="getPdf()"><span class="svc-icon">📄</span>Statement</button>
                        <button type="button" class="svc-item" onclick="openTab('Services')"><span class="svc-icon">⊞</span>More</button>
                    </div>
                </div>

                <div class="card">
                    <div class="sec-head" style="margin-top:0;"><span>Rewards</span><button type="button" class="sec-link" onclick="openTab('Rewards')">See All</button></div>
                    <div class="two-col">
                        <div class="mini-box" onclick="openTab('Rewards')" style="cursor:pointer;"><div style="font-size:0.82rem;color:#94a3b8;">🪙 Cashback</div><div id="homeCashbackText" style="font-weight:800;font-size:1.05rem;margin-top:4px;color:#fbbf24;">₦0.00</div></div>
                        <div class="mini-box" onclick="openTab('Rewards')" style="cursor:pointer;"><div style="font-size:0.82rem;color:#94a3b8;">📣 Referrals</div><div id="homeReferralText" style="font-weight:800;font-size:1.05rem;margin-top:4px;color:#34d399;">₦0.00</div></div>
                    </div>
                    <div class="sec-head"><span>Your to-do list</span><button type="button" class="sec-link" onclick="openPanel('panelSettings')">See All</button></div>
                    <div class="mini-box" onclick="openPanel('panelSettings')" style="cursor:pointer;display:flex;justify-content:space-between;align-items:center;">
                        <div><div id="todoCount" style="font-size:0.78rem;color:#fbbf24;font-weight:700;">2/3</div><div id="todoTitle" style="font-weight:700;font-size:0.9rem;">Upgrade KYC Tier & Daily Limits</div></div>
                        <span>›</span>
                    </div>
                </div>

                <div class="card">
                    <div class="sec-head" style="margin-top:0;"><span>Recent transactions</span><button type="button" class="sec-link" onclick="openPanel('panelHistory')">View All</button></div>
                    <div id="recentTxBox"></div>
                    <div class="sec-head"><span>Finances</span></div>
                    <div class="mini-box" onclick="openPanel('panelVault')" style="cursor:pointer;">
                        <div style="font-size:0.8rem;color:#94a3b8;">🌱 Savings Vault</div>
                        <div style="font-weight:700;font-size:0.92rem;margin-top:4px;">Create a savings plan and get up to <span style="color:#34d399;">18.0% interest</span> per annum</div>
                    </div>
                    <div class="sec-head"><span>Spending trends</span><span style="font-size:0.78rem;color:#fbbf24;">All Time</span></div>
                    <div class="two-col">
                        <div class="mini-box"><div style="font-size:0.8rem;color:#34d399;">↓ Money in</div><div id="moneyInText" style="font-weight:800;margin-top:4px;">₦0.00</div></div>
                        <div class="mini-box"><div style="font-size:0.8rem;color:#fb7185;">↑ Money out</div><div id="moneyOutText" style="font-weight:800;margin-top:4px;">₦0.00</div></div>
                    </div>
                </div>
            </div>
            {TABS_HTML}
        </div>
    </div>

    <div id="bottomTabs" class="tab-bar" style="display:none;">
        <button id="btnHome" class="tab-btn active" onclick="openTab('Home')">🏠<br/>Home</button>
        <button id="btnCard" class="tab-btn" onclick="openTab('Card')">💳<br/>Card</button>
        <button id="btnServices" class="tab-btn" onclick="openTab('Services')">⊞<br/>Services</button>
        <button id="btnRewards" class="tab-btn" onclick="openTab('Rewards')">🏆<br/>Rewards & Me</button>
    </div>
    {MOBILE_JS}
</body>
</html>"""
