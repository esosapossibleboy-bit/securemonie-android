from android_pwa import LOGO_SVG

AUTH_HTML = f"""
        <div id="quickUnlockBox" style="display:none;text-align:center;padding-top:4px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <button type="button" onclick="switchToFullLogin()" style="width:auto;margin:0;background:none;color:#f8fafc;font-size:1.35rem;padding:4px 8px;">←</button>
                <span id="topPhonePill" class="phone-pill">📞 ***0000</span>
            </div>
            <div class="avatar-ring"><div id="avatarInitials" class="avatar-inner">SM</div></div>
            <div style="margin:6px 0;"><span id="midPhonePill" class="phone-pill">📞 ***0000</span></div>
            <h2 style="margin:10px 0 4px;">Welcome back!</h2>
            <div style="color:#94a3b8;font-size:0.92rem;">Enter your 6 digit passcode</div>
            <div class="pin-strip" id="passcodeCells">
                <div class="pin-cell active"></div><div class="pin-cell"></div><div class="pin-cell"></div>
                <div class="pin-cell"></div><div class="pin-cell"></div><div class="pin-cell"></div>
            </div>
            <div class="keypad">
                <button type="button" class="key-btn" onclick="pressDigit('1')">1</button>
                <button type="button" class="key-btn" onclick="pressDigit('2')">2</button>
                <button type="button" class="key-btn" onclick="pressDigit('3')">3</button>
                <button type="button" class="key-btn" onclick="pressDigit('4')">4</button>
                <button type="button" class="key-btn" onclick="pressDigit('5')">5</button>
                <button type="button" class="key-btn" onclick="pressDigit('6')">6</button>
                <button type="button" class="key-btn" onclick="pressDigit('7')">7</button>
                <button type="button" class="key-btn" onclick="pressDigit('8')">8</button>
                <button type="button" class="key-btn" onclick="pressDigit('9')">9</button>
                <button type="button" class="key-btn" onclick="delDigit()">⌫</button>
                <button type="button" class="key-btn" onclick="pressDigit('0')">0</button>
                <button type="button" class="key-btn key-submit" onclick="submitKeypad()">→</button>
            </div>
            <p id="keypadMsg" class="err"></p>
            <div style="margin-top:6px;"><a href="#" onclick="switchToFullLogin();return false;" style="color:#fbbf24;text-decoration:none;font-weight:700;font-size:0.92rem;">Forgot passcode?</a></div>
        </div>

        <form id="authBox" class="card" autocomplete="off" onsubmit="return false;">
            <div style="text-align:center;margin-bottom:10px;">{LOGO_SVG}</div>
            <h2 id="authHeading" style="margin:0 0 6px;text-align:center;">Sign In to Securemonie</h2>
            <div id="regFields" style="display:none;">
                <input id="regName" placeholder="Legal Full Name (as on BVN/NIN)" />
                <input id="regPhone" type="tel" maxlength="11" inputmode="numeric" placeholder="Nigerian Phone Number (080...)" />
                <select id="regType"><option value="Personal">Personal Banking Account</option><option value="Business">Business / POS Account</option></select>
            </div>
            <input id="authIdent" placeholder="Phone Number or Email Address" />
            <input id="authPass" type="password" maxlength="6" inputmode="numeric" placeholder="6-Digit Login Passcode" />
            <div id="regPinFields" style="display:none;">
                <input id="regPin" type="password" inputmode="numeric" maxlength="4" placeholder="Create 4-Digit Transaction PIN" />
                <input id="regBvn" type="text" inputmode="numeric" maxlength="11" placeholder="Optional 11-Digit BVN/NIN (Instant Tier 2)" />
            </div>
            <button id="authSubmitBtn" type="button" onclick="submitAuth()">Sign In</button>
            <button id="authSwitchBtn" type="button" class="btn-dark" onclick="switchAuth()">Open a Free Securemonie Account</button>
            <p id="authMsg" class="err"></p>
        </form>
"""
