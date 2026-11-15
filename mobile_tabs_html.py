from mobile_rewards_html import REWARDS_TAB_HTML

TABS_HTML = f"""
            <div id="tabCard" style="display:none;">
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <h3 style="margin:0;">💳 Virtual Debit Cards</h3>
                        <button class="btn-gold" style="width:auto;margin:0;padding:8px 12px;font-size:0.82rem;" onclick="issueCard()">+ New Card</button>
                    </div>
                    <select id="cardCur"><option value="NGN">Verve Naira Card (₦)</option><option value="USD">Visa Dollar Card ($)</option></select>
                    <p id="cardMsg" class="err"></p>
                    <div id="cardsList"></div>
                </div>
            </div>

            <div id="tabServices" style="display:none;">
                <div id="panelTopup" class="card">
                    <h3 style="margin-top:0;">💳 Add Money to Wallet</h3>
                    <input id="topupAmt" type="number" inputmode="decimal" placeholder="Amount (₦)" />
                    <input id="topupPin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter 4-Digit PIN" />
                    <button class="btn-gold" onclick="doTopup()">+ Fund Wallet Now</button>
                    <p id="topupMsg" class="err"></p>
                </div>

                <div id="panelTransfer" class="card">
                    <h3 style="margin-top:0;">⇄ Bank Transfer</h3>
                    <div id="beneficiariesBar" style="display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;margin-bottom:4px;"></div>
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
                    <input id="sendPin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter 4-Digit PIN" />
                    <button onclick="doTransfer()">Send Money</button>
                    <p id="sendMsg" class="err"></p>
                </div>

                <div id="panelBills" class="card">
                    <h3 style="margin-top:0;">📱 Airtime, Data & Bills</h3>
                    <select id="billSvc"><option value="MTN Airtime">MTN Airtime</option><option value="Airtel Data">Airtel Data</option><option value="Bet9ja Wallet">Bet9ja Wallet</option><option value="WAEC / JAMB PIN">WAEC / JAMB PIN</option><option value="IKEDC Prepaid">IKEDC Electricity</option></select>
                    <input id="billTarget" placeholder="Phone Number, User ID or Meter" />
                    <input id="billAmt" type="number" inputmode="decimal" placeholder="Amount (₦)" />
                    <input id="billPin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter 4-Digit PIN" />
                    <button class="btn-dark" onclick="doBill()">Pay Now</button>
                    <p id="billMsg" class="err"></p>
                </div>

                <div id="panelVault" class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <h3 style="margin:0;">🌱 Savings Vault (18.0% p.a.)</h3>
                        <button type="button" class="btn-dark" style="width:auto;margin:0;padding:5px 10px;font-size:0.76rem;" onclick="setVaultGoal()">🎯 Set Goal</button>
                    </div>
                    <div style="font-size:1.5rem;font-weight:800;color:#fbbf24;margin:8px 0 4px;">Vault Balance: <span id="vaultText">₦0.00</span></div>
                    <div id="vaultGoalLabel" style="font-size:0.8rem;color:#94a3b8;margin-bottom:6px;">Goal: ₦100,000 (0%)</div>
                    <div style="background:#0b1021;border-radius:999px;height:10px;overflow:hidden;margin-bottom:10px;">
                        <div id="vaultGoalBar" style="background:linear-gradient(90deg,#f59e0b,#34d399);height:100%;width:0%;transition:width 0.3s;"></div>
                    </div>
                    <input id="vaultAmt" type="number" inputmode="decimal" placeholder="Amount (₦)" />
                    <input id="vaultPin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter 4-Digit PIN" />
                    <button class="btn-gold" onclick="doVault('save')">Save to Vault</button>
                    <button class="btn-dark" onclick="doVault('withdraw')">Withdraw to Wallet</button>
                    <button class="btn-dark" onclick="doVault('interest')">✨ Simulate 30-Day Interest</button>
                    <p id="vaultMsg" class="err"></p>
                </div>

                <div id="panelCac" class="card">
                    <h3 style="margin-top:0;">🏢 CAC Business Name Registration</h3>
                    <div id="cacStatus" style="font-size:0.86rem;color:#cbd5e1;margin-bottom:6px;">Register your business name directly with CAC from Securemonie.</div>
                    <input id="cacBizName" placeholder="Proposed Business Name" />
                    <select id="cacCat"><option value="General Trading & Retail">General Trading & Retail</option><option value="POS & Financial Agency">POS & Financial Agency</option><option value="Food, Logistics & Services">Food, Logistics & Services</option></select>
                    <input id="cacPin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter 4-Digit Transaction PIN" />
                    <button class="btn-gold" onclick="submitCac()">Register Business with CAC</button>
                    <p id="cacMsg" class="err"></p>
                </div>

                <div id="panelHistory" class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <h3 style="margin:0;">🧾 Full Transaction History</h3>
                        <button class="btn-gold" style="width:auto;margin:0;padding:7px 12px;font-size:0.8rem;" onclick="getPdf()">📄 PDF</button>
                    </div>
                    <div style="display:flex;gap:8px;margin-top:8px;">
                        <input id="txSearchInput" placeholder="🔍 Search name or ref..." oninput="filterTxHistory()" style="margin:0;" />
                        <select id="txKindFilter" onchange="filterTxHistory()" style="margin:0;width:115px;">
                            <option value="ALL">All</option>
                            <option value="CREDIT">Money In</option>
                            <option value="DEBIT">Money Out</option>
                        </select>
                    </div>
                    <div id="txList" style="margin-top:10px;"></div>
                </div>
            </div>
            {REWARDS_TAB_HTML}
"""
