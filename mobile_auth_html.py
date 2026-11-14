from android_pwa import LOGO_SVG
from mobile_signup_html import SIGNUP_WIZARD_HTML

AUTH_HTML = f"""
        <div id="quickUnlockBox" style="display:none;text-align:center;padding-top:4px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <button type="button" onclick="switchToFullLogin()" style="width:auto;margin:0;background:none;color:#f8fafc;font-size:1.35rem;padding:4px 8px;">←</button>
                <span id="topPhonePill" class="phone-pill">📞 ***0000</span>
            </div>
            <div class="avatar-ring">
                <img id="unlockSelfieImg" style="display:none;width:54px;height:54px;object-fit:cover;border-radius:15px;" />
                <div id="avatarInitials" class="avatar-inner">SM</div>
            </div>
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
            <div style="margin-top:6px;"><a href="#" onclick="openForgotBox();return false;" style="color:#fbbf24;text-decoration:none;font-weight:700;font-size:0.92rem;">Forgot passcode?</a></div>
        </div>

        <form id="loginBox" class="card" autocomplete="off" onsubmit="return false;">
            <div style="text-align:center;margin-bottom:10px;">{LOGO_SVG}</div>
            <h2 style="margin:0 0 6px;text-align:center;">Sign In to Securemonie</h2>
            <input id="loginIdent" placeholder="Phone Number or Email Address" />
            <input id="loginPass" type="password" maxlength="6" inputmode="numeric" placeholder="6-Digit Login Passcode" />
            <button type="button" onclick="submitLogin()">Sign In</button>
            <button type="button" class="btn-dark" onclick="openSignupWizard()">Open a Free Securemonie Account</button>
            <div style="text-align:center;margin-top:10px;"><a href="#" onclick="openForgotBox();return false;" style="color:#fbbf24;font-size:0.88rem;text-decoration:none;font-weight:600;">Forgot 6-Digit Passcode?</a></div>
            <p id="loginMsg" class="err"></p>
        </form>

        <form id="forgotBox" class="card" style="display:none;" autocomplete="off" onsubmit="return false;">
            <h3 style="margin-top:0;">🔑 Reset 6-Digit Passcode</h3>
            <input id="fgIdent" placeholder="Registered Phone Number or Email" />
            <input id="fgPin" type="password" maxlength="4" inputmode="numeric" placeholder="Verify 4-Digit Transaction PIN" />
            <input id="fgNewPass" type="password" maxlength="6" inputmode="numeric" placeholder="New 6-Digit Login Passcode" />
            <button type="button" class="btn-gold" onclick="submitForgot()">Reset Passcode</button>
            <button type="button" class="btn-dark" onclick="switchToFullLogin()">Back to Sign In</button>
            <p id="fgMsg" class="err"></p>
        </form>
        {SIGNUP_WIZARD_HTML}
"""
