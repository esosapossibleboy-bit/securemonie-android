REWARDS_TAB_HTML = """
            <div id="tabRewards" style="display:none;">
                <div class="card">
                    <h3 style="margin-top:0;">🎁 Cashback & Referral Hub</h3>
                    <div class="two-col">
                        <div class="mini-box"><div style="font-size:0.8rem;color:#94a3b8;">🪙 Cashback Earned</div><div id="tabCashbackText" style="font-weight:800;font-size:1.1rem;color:#fbbf24;margin-top:4px;">₦0.00</div></div>
                        <div class="mini-box"><div style="font-size:0.8rem;color:#94a3b8;">📣 Referral Bonus</div><div id="tabReferralText" style="font-weight:800;font-size:1.1rem;color:#34d399;margin-top:4px;">₦0.00</div></div>
                    </div>
                    <div style="margin-top:10px;background:#0b1021;border:1px solid #2a3963;border-radius:12px;padding:10px;display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:0.85rem;">Your Invite Code: <strong id="myRefCodeText" style="color:#fbbf24;">SM-000000</strong></span>
                        <button type="button" class="btn-dark" style="width:auto;margin:0;padding:5px 10px;font-size:0.78rem;" onclick="copyRefCode()">📋 Copy</button>
                    </div>
                    <button type="button" class="btn-gold" onclick="redeemRewards()">💰 Redeem All Rewards to Wallet</button>
                    <input id="claimRefInput" placeholder="Enter Friend's Referral Code (Earn ₦500)" />
                    <button type="button" class="btn-dark" onclick="claimReferral()">Claim ₦500 Referral Bonus</button>
                    <p id="rwdMsg" class="err"></p>
                </div>

                <div id="panelSettings" class="card">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                        <img id="settingsSelfieImg" style="display:none;width:62px;height:62px;border-radius:50%;object-fit:cover;border:3px solid #f59e0b;" />
                        <div>
                            <h3 style="margin:0;">🛡️ Bank Security Center</h3>
                            <div id="profileInfo" style="font-size:0.84rem;color:#cbd5e1;line-height:1.5;margin-top:4px;"></div>
                        </div>
                    </div>

                    <div id="freezeStatusBox" style="background:#0b1021;border:1px solid #2a3963;border-radius:12px;padding:12px;margin-bottom:10px;font-size:0.86rem;">
                        Status: <strong id="acctStatusText" style="color:#34d399;">✅ ACTIVE & PROTECTED</strong>
                    </div>

                    <select id="settingType" onchange="updateSettingHint()">
                        <option value="kyc">Upgrade KYC Level (Enter 11-Digit BVN/NIN)</option>
                        <option value="limit">Set 24-Hour Daily Transfer Limit (₦)</option>
                        <option value="single_limit">Set Per-Transaction Transfer Cap (₦)</option>
                        <option value="biometrics">Enable / Disable Fingerprint & Face ID Login</option>
                        <option value="pin">Change / Unlock 4-Digit Transaction PIN</option>
                        <option value="password">Change 6-Digit Login Passcode</option>
                        <option value="freeze">Emergency Panic Freeze / Unfreeze Account</option>
                        <option value="privacy">Toggle Hide Balance on App Launch</option>
                    </select>
                    <input id="settingNewVal" placeholder="Enter 11-Digit BVN or NIN" />
                    <input id="settingPass" type="password" maxlength="6" inputmode="numeric" placeholder="Verify Current 6-Digit Passcode" />
                    <button onclick="saveSetting()">Apply Security Change</button>
                    <button type="button" class="btn-dark" onclick="logoutAllDevices()">🚫 Sign Out From All Devices</button>
                    <p id="setMsg" class="err"></p>
                </div>

                <div class="card">
                    <h3 style="margin-top:0;">📋 Recent Security Activity Log</h3>
                    <div id="secLogList" style="font-size:0.84rem;"></div>
                </div>
            </div>
"""
