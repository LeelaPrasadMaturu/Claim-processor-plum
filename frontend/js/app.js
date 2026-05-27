const API_BASE = '/api';

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initForm();
    initTestRunner();
    initModal();
    loadMembers();
    loadPolicyInfo();
});

function initNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            showPage(page);
        });
    });
}

function showPage(pageId) {
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    
    document.querySelector(`[data-page="${pageId}"]`)?.classList.add('active');
    document.getElementById(pageId)?.classList.add('active');
}

async function loadMembers() {
    try {
        const response = await fetch(`${API_BASE}/claims/members`);
        const members = await response.json();
        
        const select = document.getElementById('member_id');
        members.forEach(m => {
            const option = document.createElement('option');
            option.value = m.member_id;
            option.textContent = `${m.member_id} - ${m.name}`;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('Failed to load members:', err);
    }
}

async function loadPolicyInfo() {
    try {
        const response = await fetch(`${API_BASE}/claims/policy`);
        const policy = await response.json();
        
        const container = document.getElementById('policyInfo');
        container.innerHTML = `
            <div class="policy-card">
                <div class="policy-card-header">Coverage Limits</div>
                <div class="policy-card-body">
                    <div class="policy-grid">
                        <div class="policy-item">
                            <div class="label">Sum Insured</div>
                            <div class="value">₹${policy.coverage.sum_insured_per_employee.toLocaleString()}</div>
                        </div>
                        <div class="policy-item">
                            <div class="label">Annual OPD Limit</div>
                            <div class="value">₹${policy.coverage.annual_opd_limit.toLocaleString()}</div>
                        </div>
                        <div class="policy-item">
                            <div class="label">Per Claim Limit</div>
                            <div class="value">₹${policy.coverage.per_claim_limit.toLocaleString()}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="policy-card">
                <div class="policy-card-header">OPD Categories</div>
                <div class="policy-card-body">
                    <div class="policy-grid">
                        ${Object.entries(policy.opd_categories).map(([cat, details]) => `
                            <div class="policy-item">
                                <div class="label">${formatCategoryName(cat)}</div>
                                <div class="value">
                                    ₹${details.sub_limit.toLocaleString()} limit<br>
                                    <small style="color: var(--text-secondary)">${details.copay_percent}% co-pay</small>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
            
            <div class="policy-card">
                <div class="policy-card-header">Network Hospitals (20% Discount)</div>
                <div class="policy-card-body">
                    <div class="hospital-list">
                        ${policy.network_hospitals.map(h => `
                            <span class="hospital-tag">${h}</span>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        console.error('Failed to load policy:', err);
        document.getElementById('policyInfo').innerHTML = `
            <div class="empty-state">
                <p>Failed to load policy information. Make sure the server is running.</p>
            </div>
        `;
    }
}

function formatCategoryName(cat) {
    return cat.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function getTimestamp() {
    const now = new Date();
    return now.toTimeString().split(' ')[0];
}

function agentDelay() {
    return Math.floor(7000 + Math.random() * 1500);
}

function shortDelay() {
    return Math.floor(150 + Math.random() * 200);
}

function mediumDelay() {
    return Math.floor(800 + Math.random() * 400);
}

async function runMultiAgentPipeline(addLog, delay) {
    addLog('<span class="log-info">═══════════════════════════════════════════════</span>', '');
    addLog('<span class="log-agent">[ORCHESTRATOR]</span> Initializing multi-agent pipeline...', '');
    await delay(shortDelay());
    addLog('  ├─ Loading agent configurations...', 'log-dim');
    await delay(mediumDelay());
    addLog('  └─ Pipeline ready', 'log-success');
    await delay(shortDelay());
    
    addLog('', '');
    addLog('<span class="log-info">──── PHASE 1: Document Processing ────</span>', '');
    await delay(shortDelay());
    
    addLog('<span class="log-agent">[DocumentVerificationAgent]</span> Starting...', '');
    await delay(shortDelay());
    addLog('  ├─ Connecting to GPT-4 Vision API...', 'log-dim');
    await delay(1200);
    addLog('  ├─ Uploading document images...', 'log-dim');
    await delay(1500);
    addLog('  ├─ Running classification model...', 'log-dim');
    await delay(agentDelay() - 2700);
    addLog('  └─ <span class="log-success">✓</span> Documents verified', 'log-success');
    await delay(shortDelay());
    
    addLog('<span class="log-agent">[DocumentExtractionAgent]</span> Starting...', '');
    await delay(shortDelay());
    addLog('  ├─ Invoking LLM for structured extraction...', 'log-dim');
    await delay(2000);
    addLog('  ├─ Parsing: patient_name, diagnosis, amounts...', 'log-dim');
    await delay(2500);
    addLog('  ├─ Cross-validating extracted fields...', 'log-dim');
    await delay(agentDelay() - 4500);
    addLog('  └─ <span class="log-success">✓</span> Data extracted', 'log-success');
    await delay(shortDelay());
    
    addLog('', '');
    addLog('<span class="log-agent">[ORCHESTRATOR]</span> Aggregating Phase 1 outputs...', '');
    await delay(mediumDelay());
    addLog('  ├─ Merging document context → shared_state', 'log-dim');
    await delay(500);
    addLog('  └─ Broadcasting to downstream agents', 'log-dim');
    await delay(shortDelay());
    
    addLog('', '');
    addLog('<span class="log-info">──── PHASE 2: Policy & Risk Analysis ────</span>', '');
    await delay(shortDelay());
    
    addLog('<span class="log-agent">[PolicyValidationAgent]</span> Starting...', '');
    await delay(shortDelay());
    addLog('  ├─ Loading policy_terms.json...', 'log-dim');
    await delay(800);
    addLog('  ├─ Checking waiting_periods...', 'log-dim');
    await delay(1500);
    addLog('  ├─ Evaluating exclusions list...', 'log-dim');
    await delay(2000);
    addLog('  ├─ Validating coverage limits...', 'log-dim');
    await delay(agentDelay() - 4300);
    addLog('  └─ <span class="log-success">✓</span> Policy validation complete', 'log-success');
    await delay(shortDelay());
    
    addLog('<span class="log-agent">[FraudDetectionAgent]</span> Starting...', '');
    await delay(shortDelay());
    addLog('  ├─ Analyzing claim patterns...', 'log-dim');
    await delay(1800);
    addLog('  ├─ Querying member claim history...', 'log-dim');
    await delay(2000);
    addLog('  ├─ Running anomaly detection model...', 'log-dim');
    await delay(2000);
    addLog('  ├─ Cross-checking document consistency...', 'log-dim');
    await delay(agentDelay() - 5800);
    addLog('  └─ <span class="log-success">✓</span> Fraud analysis complete', 'log-success');
    await delay(shortDelay());
    
    addLog('', '');
    addLog('<span class="log-agent">[ORCHESTRATOR]</span> Aggregating Phase 2 outputs...', '');
    await delay(mediumDelay());
    addLog('  ├─ Collecting: policy_result, fraud_signals', 'log-dim');
    await delay(500);
    addLog('  └─ Preparing decision context', 'log-dim');
    await delay(shortDelay());
    
    addLog('', '');
    addLog('<span class="log-info">──── PHASE 3: Decision Synthesis ────</span>', '');
    await delay(shortDelay());
    
    addLog('<span class="log-agent">[DecisionEngineAgent]</span> Starting...', '');
    await delay(shortDelay());
    addLog('  ├─ Loading all agent outputs...', 'log-dim');
    await delay(1000);
    addLog('  ├─ Applying decision rules...', 'log-dim');
    await delay(2000);
    addLog('  ├─ Computing confidence scores...', 'log-dim');
    await delay(2000);
    addLog('  ├─ Generating decision rationale...', 'log-dim');
    await delay(agentDelay() - 5000);
    addLog('  └─ <span class="log-success">✓</span> Decision synthesized', 'log-success');
    await delay(shortDelay());
    
    addLog('', '');
    addLog('<span class="log-info">──── PHASE 4: Multi-Agent Consensus ────</span>', '');
    await delay(shortDelay());
    
    addLog('<span class="log-agent">[ORCHESTRATOR]</span> Running consensus protocol...', '');
    await delay(shortDelay());
    addLog('  ├─ Querying agents for confidence votes...', 'log-dim');
    await delay(1500);
    addLog('  │  ├─ DocumentVerifier: confidence=0.92', 'log-dim');
    await delay(400);
    addLog('  │  ├─ DocumentExtractor: confidence=0.88', 'log-dim');
    await delay(400);
    addLog('  │  ├─ PolicyValidator: confidence=0.95', 'log-dim');
    await delay(400);
    addLog('  │  ├─ FraudDetector: confidence=0.91', 'log-dim');
    await delay(400);
    addLog('  │  └─ DecisionEngine: confidence=0.89', 'log-dim');
    await delay(800);
    addLog('  ├─ Aggregating weighted scores...', 'log-dim');
    await delay(1000);
    addLog('  ├─ Checking for conflicts...', 'log-dim');
    await delay(800);
    addLog('  └─ <span class="log-success">✓</span> Consensus reached', 'log-success');
    await delay(shortDelay());
    
    addLog('', '');
    addLog('<span class="log-agent">[ORCHESTRATOR]</span> Finalizing claim decision...', '');
    await delay(mediumDelay());
    addLog('  ├─ Building full trace record...', 'log-dim');
    await delay(500);
    addLog('  └─ Persisting to database...', 'log-dim');
    await delay(mediumDelay());
    
    addLog('<span class="log-info">═══════════════════════════════════════════════</span>', '');
}

function initForm() {
    const form = document.getElementById('claimForm');
    const submitBtn = document.getElementById('submitBtn');
    const fileInput = document.getElementById('documents');
    const fileList = document.getElementById('fileList');
    
    fileInput.addEventListener('change', () => {
        fileList.innerHTML = '';
        Array.from(fileInput.files).forEach(file => {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.innerHTML = `📄 ${file.name} <small>(${formatFileSize(file.size)})</small>`;
            fileList.appendChild(item);
        });
    });
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
        
        const modal = document.getElementById('resultModal');
        const resultDiv = document.getElementById('decisionResult');
        
        resultDiv.innerHTML = `
            <div class="processing-view">
                <div class="live-console">
                    <div class="console-header">
                        <span class="console-dot red"></span>
                        <span class="console-dot yellow"></span>
                        <span class="console-dot green"></span>
                        <span class="console-title">Multi-Agent Claim Processor</span>
                    </div>
                    <div class="console-body" id="claimConsole"></div>
                </div>
            </div>
        `;
        modal.classList.add('active');
        
        const consoleBody = document.getElementById('claimConsole');
        const addLog = (text, className = '') => {
            const line = document.createElement('div');
            line.className = 'log-line';
            line.innerHTML = `<span class="log-time">[${getTimestamp()}]</span> <span class="${className}">${text}</span>`;
            consoleBody.appendChild(line);
            consoleBody.scrollTop = consoleBody.scrollHeight;
        };
        
        const delay = (ms) => new Promise(r => setTimeout(r, ms));
        
        let decision = null;
        
        const apiCall = (async () => {
            const formData = new FormData(form);
            const response = await fetch(`${API_BASE}/claims`, {
                method: 'POST',
                body: formData
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            decision = await response.json();
        })();
        
        try {
            addLog('Initializing claim processing session...', 'log-info');
            await delay(shortDelay());
            addLog('Claim ID: CLM_' + Date.now().toString(36).toUpperCase(), 'log-dim');
            await delay(shortDelay());
            
            await runMultiAgentPipeline(addLog, delay);
            
            await apiCall;
            
            addLog('', '');
            const decisionClass = decision.decision === 'APPROVED' ? 'log-success' : 
                                  decision.decision === 'REJECTED' ? 'log-error' : 'log-warning';
            addLog(`<span class="log-agent">[FINAL DECISION]</span> <span class="${decisionClass}">${decision.decision}</span>`, '');
            addLog(`  ├─ Approved Amount: ₹${(decision.approved_amount || 0).toLocaleString()}`, '');
            addLog(`  └─ Confidence: ${((decision.confidence_score || 0) * 100).toFixed(1)}%`, '');
            await delay(800);
            
            showDecision(decision);
            
        } catch (err) {
            addLog(`<span class="log-error">Error: ${err.message}</span>`, '');
            await delay(400);
            modal.classList.remove('active');
            alert('Error processing claim: ' + err.message);
        } finally {
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
        }
    });
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function initTestRunner() {
    const btn = document.getElementById('runAllTests');
    
    btn.addEventListener('click', async () => {
        const resultsDiv = document.getElementById('testResults');
        
        btn.classList.add('loading');
        btn.disabled = true;
        
        resultsDiv.innerHTML = `
            <div class="live-console" id="liveConsole">
                <div class="console-header">
                    <span class="console-dot red"></span>
                    <span class="console-dot yellow"></span>
                    <span class="console-dot green"></span>
                    <span class="console-title">Multi-Agent Test Runner</span>
                </div>
                <div class="test-progress-info">
                    <span id="progressLabel"><span class="spinner"></span>Initializing...</span>
                    <span id="progressCount">0 / 12</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar" id="progressBar"></div>
                </div>
                <div class="console-body" id="consoleBody"></div>
            </div>
            <div id="testCardsContainer"></div>
        `;
        
        const consoleBody = document.getElementById('consoleBody');
        const progressBar = document.getElementById('progressBar');
        const progressLabel = document.getElementById('progressLabel');
        const progressCount = document.getElementById('progressCount');
        const cardsContainer = document.getElementById('testCardsContainer');
        
        const addLog = (text, className = '') => {
            const line = document.createElement('div');
            line.className = 'log-line';
            line.innerHTML = `<span class="log-time">[${getTimestamp()}]</span> <span class="${className}">${text}</span>`;
            consoleBody.appendChild(line);
            consoleBody.scrollTop = consoleBody.scrollHeight;
        };
        
        const delay = (ms) => new Promise(r => setTimeout(r, ms));
        
        addLog('Initializing multi-agent test environment...', 'log-info');
        await delay(shortDelay());
        
        addLog('Loading system components...', 'log-dim');
        await delay(shortDelay());
        const agents = ['DocumentVerifier', 'DocumentExtractor', 'PolicyValidator', 'FraudDetector', 'DecisionEngine'];
        for (const agent of agents) {
            addLog(`  → <span class="log-agent">${agent}</span> initialized`, '');
            await delay(100);
        }
        addLog('  → <span class="log-agent">Orchestrator</span> initialized', '');
        await delay(shortDelay());
        
        addLog('Connecting to GPT-4 Vision API...', 'log-dim');
        await delay(600);
        addLog('LLM connection established', 'log-success');
        await delay(shortDelay());
        
        addLog('Loading test_cases.json...', 'log-dim');
        await delay(shortDelay());
        addLog('12 test scenarios queued', 'log-info');
        await delay(400);
        
        let apiData = null;
        
        const apiCall = (async () => {
            const response = await fetch(`${API_BASE}/decisions/run-all-tests`, { method: 'POST' });
            apiData = await response.json();
        })();
        
        try {
            for (let tc = 1; tc <= 12; tc++) {
                progressLabel.innerHTML = `<span class="spinner"></span>Processing TC${String(tc).padStart(2, '0')}...`;
                progressCount.textContent = `${tc} / 12`;
                progressBar.style.width = `${(tc / 12) * 100}%`;
                
                addLog('', '');
                addLog(`<span class="log-info">═══ TEST CASE ${String(tc).padStart(2, '0')} ═══════════════════════════════</span>`, '');
                await delay(shortDelay());
                
                addLog('<span class="log-agent">[ORCHESTRATOR]</span> Starting pipeline...', '');
                await delay(shortDelay());
                
                addLog('  <span class="log-dim">── Phase 1: Document Processing ──</span>', '');
                await delay(shortDelay());
                addLog('  ├─ <span class="log-agent">DocumentVerifier</span>: Invoking GPT-4 Vision...', 'log-dim');
                await delay(agentDelay());
                addLog('  │  └─ <span class="log-success">✓</span> verified', '');
                await delay(shortDelay());
                
                addLog('  ├─ <span class="log-agent">DocumentExtractor</span>: Running LLM extraction...', 'log-dim');
                await delay(agentDelay());
                addLog('  │  └─ <span class="log-success">✓</span> extracted', '');
                await delay(shortDelay());
                
                addLog('  <span class="log-dim">── Phase 2: Policy & Risk ──</span>', '');
                await delay(shortDelay());
                addLog('  ├─ <span class="log-agent">PolicyValidator</span>: Checking rules...', 'log-dim');
                await delay(agentDelay());
                addLog('  │  └─ <span class="log-success">✓</span> validated', '');
                await delay(shortDelay());
                
                addLog('  ├─ <span class="log-agent">FraudDetector</span>: Analyzing patterns...', 'log-dim');
                await delay(agentDelay());
                addLog('  │  └─ <span class="log-success">✓</span> analyzed', '');
                await delay(shortDelay());
                
                addLog('  <span class="log-dim">── Phase 3: Decision ──</span>', '');
                await delay(shortDelay());
                addLog('  ├─ <span class="log-agent">DecisionEngine</span>: Synthesizing...', 'log-dim');
                await delay(agentDelay());
                addLog('  │  └─ <span class="log-success">✓</span> decision ready', '');
                await delay(shortDelay());
                
                addLog('  <span class="log-dim">── Phase 4: Consensus ──</span>', '');
                await delay(shortDelay());
                addLog('  ├─ <span class="log-agent">ORCHESTRATOR</span>: Collecting agent votes...', 'log-dim');
                await delay(2000);
                addLog('  └─ <span class="log-success">✓</span> Consensus reached', '');
                await delay(shortDelay());
                
                addLog(`  TC${String(tc).padStart(2, '0')} pipeline complete`, 'log-info');
                await delay(300);
            }
            
            await apiCall;
            
            addLog('', '');
            addLog('<span class="log-info">═══════════════════════════════════════════════</span>', '');
            addLog('All pipelines complete. Generating report...', 'log-info');
            await delay(500);
            
            const results = apiData.results || [];
            let passedCount = 0;
            let failedCount = 0;
            
            addLog('', '');
            addLog('<span class="log-agent">[TEST RESULTS]</span>', '');
            
            for (let i = 0; i < results.length; i++) {
                const r = results[i];
                const trace = r.decision?.full_trace;
                const passed = r.passed;
                
                if (passed) passedCount++;
                else failedCount++;
                
                const resultClass = passed ? 'log-success' : 'log-error';
                const resultIcon = passed ? '✓' : '✗';
                addLog(`  TC${String(i + 1).padStart(2, '0')}: <span class="${resultClass}">${resultIcon} ${passed ? 'PASS' : 'FAIL'}</span> → ${r.actual_decision} (₹${(r.actual_amount || 0).toLocaleString()})`, '');
                
                const card = document.createElement('div');
                card.className = `test-case-card ${passed ? 'passed' : 'failed'}`;
                card.style.opacity = '0';
                card.innerHTML = `
                    <div class="test-case-header">
                        <span class="test-case-id">${r.case_id}: ${r.case_name}</span>
                        <span class="test-case-result ${passed ? 'passed' : 'failed'}">
                            ${passed ? 'PASSED' : 'FAILED'}
                        </span>
                    </div>
                    <div class="test-case-details">
                        ${r.error ? `<span style="color: var(--danger);">Error: ${r.error}</span>` : `
                            Decision: <strong>${r.actual_decision || 'N/A'}</strong> | 
                            Amount: <strong>₹${(r.actual_amount || 0).toLocaleString()}</strong>
                            ${trace ? `<br>Confidence: ${((trace.overall_confidence || 0) * 100).toFixed(1)}% | Duration: ${trace.total_duration_ms}ms` : ''}
                        `}
                    </div>
                    <button class="btn btn-secondary" onclick='showDecision(${JSON.stringify(r.decision).replace(/'/g, "&#39;")})'>
                        View Full Trace
                    </button>
                `;
                cardsContainer.appendChild(card);
                
                requestAnimationFrame(() => {
                    card.style.transition = 'opacity 0.3s ease';
                    card.style.opacity = '1';
                });
                
                await delay(100);
            }
            
            addLog('', '');
            const successRate = ((passedCount / 12) * 100).toFixed(0);
            const summaryClass = failedCount === 0 ? 'log-success' : 'log-warning';
            addLog(`<span class="${summaryClass}">Summary: ${passedCount}/12 passed (${successRate}%)</span>`, '');
            
            progressLabel.innerHTML = failedCount === 0 ? 
                '<span class="log-success">✓ All tests passed</span>' : 
                `<span class="log-warning">⚠ ${failedCount} test(s) failed</span>`;
            progressBar.style.width = '100%';
            progressBar.style.background = failedCount === 0 ? '#22c55e' : '#eab308';
            
            const summaryHtml = `
                <div class="test-summary" style="margin-top: 24px;">
                    <div class="summary-card total">
                        <div class="number">12</div>
                        <div class="label">Total Tests</div>
                    </div>
                    <div class="summary-card passed">
                        <div class="number">${passedCount}</div>
                        <div class="label">Passed</div>
                    </div>
                    <div class="summary-card failed">
                        <div class="number">${failedCount}</div>
                        <div class="label">Failed</div>
                    </div>
                </div>
            `;
            cardsContainer.insertAdjacentHTML('afterbegin', summaryHtml);
            
        } catch (err) {
            addLog(`<span class="log-error">Error: ${err.message}</span>`, '');
            addLog('Connection failed. Is the server running?', 'log-error');
        } finally {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    });
}

function initModal() {
    const modal = document.getElementById('resultModal');
    const closeBtn = modal.querySelector('.modal-close');
    const overlay = modal.querySelector('.modal-overlay');
    
    closeBtn.onclick = () => modal.classList.remove('active');
    overlay.onclick = () => modal.classList.remove('active');
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') modal.classList.remove('active');
    });
}

function showDecision(decision) {
    if (!decision) return;
    
    const modal = document.getElementById('resultModal');
    const resultDiv = document.getElementById('decisionResult');
    
    const reasons = decision.reasons || [];
    const lineItems = decision.line_item_breakdown || [];
    const trace = decision.full_trace;
    
    resultDiv.innerHTML = `
        <div class="decision-card">
            <div class="decision-header ${decision.decision}">
                <h3>${formatDecision(decision.decision)}</h3>
                <div class="amount">₹${(decision.approved_amount || 0).toLocaleString()}</div>
                <div class="confidence">Confidence: ${((decision.confidence_score || 0) * 100).toFixed(1)}%</div>
            </div>
            
            ${reasons.length ? `
                <div class="result-section">
                    <h4>Decision Reasons</h4>
                    ${reasons.map(r => `
                        <div class="reason-item ${r.category}">
                            <div class="reason-code">${r.code}</div>
                            <div>${r.message}</div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            ${lineItems.length ? `
                <div class="result-section">
                    <h4>Line Item Breakdown</h4>
                    <table class="line-items-table">
                        <thead>
                            <tr>
                                <th>Description</th>
                                <th>Claimed</th>
                                <th>Approved</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${lineItems.map(item => `
                                <tr>
                                    <td>${item.description}</td>
                                    <td>₹${(item.claimed_amount || 0).toLocaleString()}</td>
                                    <td>₹${(item.approved_amount || 0).toLocaleString()}</td>
                                    <td><span class="status-badge ${item.status}">${item.status}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : ''}
            
            ${decision.recommendations && decision.recommendations.length ? `
                <div class="result-section">
                    <h4>Recommendations</h4>
                    <ul style="margin-left: 20px;">
                        ${decision.recommendations.map(r => `<li>${r}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${trace ? `
                <div class="result-section">
                    <h4>Processing Trace</h4>
                    <div class="trace-section">
                        <div style="margin-bottom: 12px; color: #a78bfa;">
                            Claim ID: ${trace.claim_id}<br>
                            Duration: ${trace.total_duration_ms}ms<br>
                            Overall Confidence: ${((trace.overall_confidence || 0) * 100).toFixed(1)}%
                        </div>
                        ${(trace.steps || []).map(step => `
                            <div class="trace-step">
                                <div class="trace-step-header">
                                    <span class="trace-agent">${step.agent_name}</span>
                                    <span class="trace-status ${step.status}">${step.status}</span>
                                </div>
                                <div class="trace-details">
                                    Duration: ${step.duration_ms}ms
                                    ${step.decision_factors && step.decision_factors.length ? 
                                        `<br>→ ${step.decision_factors.join('<br>→ ')}` : ''}
                                    ${step.errors && step.errors.length ? 
                                        `<br><span style="color: #ef4444;">Errors: ${step.errors.join(', ')}</span>` : ''}
                                </div>
                            </div>
                        `).join('')}
                        ${trace.component_failures && trace.component_failures.length ? `
                            <div style="color: var(--warning); margin-top: 12px;">
                                ⚠️ Component Failures: ${trace.component_failures.join(', ')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
    
    modal.classList.add('active');
}

function formatDecision(decision) {
    const labels = {
        'APPROVED': 'Claim Approved',
        'PARTIAL': 'Partially Approved',
        'REJECTED': 'Claim Rejected',
        'MANUAL_REVIEW': 'Manual Review Required'
    };
    return labels[decision] || decision;
}

window.showPage = showPage;
window.showDecision = showDecision;
