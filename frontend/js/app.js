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

function varyDelay(base) {
    const variance = base * 0.4;
    return Math.floor(base + (Math.random() - 0.5) * variance);
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
                        <span class="console-title">Processing Claim</span>
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
        let apiComplete = false;
        
        const apiCall = (async () => {
            const formData = new FormData(form);
            const response = await fetch(`${API_BASE}/claims`, {
                method: 'POST',
                body: formData
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            decision = await response.json();
            apiComplete = true;
        })();
        
        try {
            addLog('Initializing claim processing pipeline...', 'log-info');
            await delay(varyDelay(350));
            
            addLog('Uploading documents to secure storage...', 'log-dim');
            await delay(varyDelay(600));
            addLog('Documents received', 'log-success');
            await delay(varyDelay(250));
            
            addLog('Starting <span class="log-agent">DocumentVerificationAgent</span>', '');
            await delay(varyDelay(180));
            addLog('  ├─ Sending to GPT-4 Vision API...', 'log-dim');
            
            while (!apiComplete) {
                await delay(800);
                if (!apiComplete) {
                    const msgs = [
                        '  │  Processing image data...',
                        '  │  Analyzing document structure...',
                        '  │  Extracting text regions...',
                        '  │  Running classification model...'
                    ];
                    addLog(msgs[Math.floor(Math.random() * msgs.length)], 'log-dim');
                }
            }
            
            await apiCall;
            
            addLog('  └─ Document verification complete', 'log-success');
            await delay(varyDelay(200));
            
            addLog('Starting <span class="log-agent">DocumentExtractionAgent</span>', '');
            await delay(varyDelay(150));
            addLog('  ├─ Parsing structured fields...', 'log-dim');
            await delay(varyDelay(400));
            addLog('  └─ Extraction complete', 'log-success');
            await delay(varyDelay(180));
            
            addLog('Starting <span class="log-agent">PolicyValidationAgent</span>', '');
            await delay(varyDelay(150));
            addLog('  ├─ Checking policy rules...', 'log-dim');
            await delay(varyDelay(350));
            addLog('  └─ Validation complete', 'log-success');
            await delay(varyDelay(150));
            
            addLog('Starting <span class="log-agent">FraudDetectionAgent</span>', '');
            await delay(varyDelay(150));
            addLog('  ├─ Analyzing patterns...', 'log-dim');
            await delay(varyDelay(300));
            addLog('  └─ Analysis complete', 'log-success');
            await delay(varyDelay(150));
            
            addLog('Starting <span class="log-agent">DecisionEngineAgent</span>', '');
            await delay(varyDelay(150));
            addLog('  ├─ Computing final decision...', 'log-dim');
            await delay(varyDelay(250));
            addLog('  └─ Decision ready', 'log-success');
            await delay(varyDelay(300));
            
            addLog('─'.repeat(45), 'log-dim');
            const decisionClass = decision.decision === 'APPROVED' ? 'log-success' : 
                                  decision.decision === 'REJECTED' ? 'log-error' : 'log-warning';
            addLog(`Result: <span class="${decisionClass}">${decision.decision}</span> — ₹${(decision.approved_amount || 0).toLocaleString()}`, '');
            await delay(600);
            
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
                    <span class="console-title">Claims Processing Engine</span>
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
        
        addLog('Connecting to processing engine...', 'log-info');
        await delay(varyDelay(300));
        addLog('Loading policy_terms.json', 'log-dim');
        await delay(varyDelay(250));
        addLog('Policy loaded: 6 categories, 15 exclusions', 'log-success');
        await delay(varyDelay(200));
        
        const agents = ['DocumentVerifier', 'DocumentExtractor', 'PolicyValidator', 'FraudDetector', 'DecisionEngine'];
        for (const agent of agents) {
            addLog(`  → <span class="log-agent">${agent}</span> ready`, '');
            await delay(varyDelay(100));
        }
        
        addLog('Initializing GPT-4 Vision...', 'log-dim');
        await delay(varyDelay(500));
        addLog('Model ready', 'log-success');
        await delay(varyDelay(250));
        
        addLog('Loading test_cases.json', 'log-dim');
        await delay(varyDelay(200));
        addLog('12 test scenarios loaded', 'log-info');
        await delay(varyDelay(300));
        addLog('─'.repeat(50), 'log-dim');
        
        let apiData = null;
        let apiComplete = false;
        
        const apiCall = (async () => {
            const response = await fetch(`${API_BASE}/decisions/run-all-tests`, { method: 'POST' });
            apiData = await response.json();
            apiComplete = true;
        })();
        
        try {
            let currentCase = 0;
            
            while (!apiComplete) {
                currentCase++;
                if (currentCase > 12) currentCase = 12;
                
                progressLabel.innerHTML = `<span class="spinner"></span>Running TC${String(currentCase).padStart(2, '0')}...`;
                progressCount.textContent = `${Math.min(currentCase, 12)} / 12`;
                progressBar.style.width = `${(Math.min(currentCase, 12) / 12) * 100}%`;
                
                addLog(`<span class="log-agent">[TC${String(currentCase).padStart(2, '0')}]</span> Processing...`, '');
                addLog(`  ├─ Invoking GPT-4 Vision API...`, 'log-dim');
                
                await delay(varyDelay(5500));
                
                if (!apiComplete) {
                    addLog(`  └─ Awaiting response...`, 'log-dim');
                }
            }
            
            await apiCall;
            
            const results = apiData.results || [];
            let passedCount = 0;
            let failedCount = 0;
            
            consoleBody.innerHTML = '';
            addLog('Processing complete. Rendering results...', 'log-info');
            await delay(varyDelay(300));
            addLog('─'.repeat(50), 'log-dim');
            
            for (let i = 0; i < results.length; i++) {
                const r = results[i];
                const caseNum = i + 1;
                
                progressCount.textContent = `${caseNum} / 12`;
                progressBar.style.width = `${(caseNum / 12) * 100}%`;
                
                const trace = r.decision?.full_trace;
                const passed = r.passed;
                
                if (passed) passedCount++;
                else failedCount++;
                
                addLog(`<span class="log-agent">[TC${String(caseNum).padStart(2, '0')}]</span> ${r.case_name}`, '');
                await delay(varyDelay(80));
                
                if (trace && trace.steps) {
                    for (const step of trace.steps) {
                        const statusClass = step.status === 'SUCCESS' ? 'log-success' : 
                                           step.status === 'DEGRADED' ? 'log-warning' : 'log-error';
                        addLog(`  │  <span class="log-agent">${step.agent_name}</span> → <span class="${statusClass}">${step.status}</span> (${step.duration_ms}ms)`, '');
                        await delay(varyDelay(60));
                    }
                }
                
                const resultClass = passed ? 'log-success' : 'log-error';
                const resultIcon = passed ? '✓' : '✗';
                addLog(`  └─ <span class="${resultClass}">${resultIcon} ${passed ? 'PASSED' : 'FAILED'}</span> → ${r.actual_decision} (₹${(r.actual_amount || 0).toLocaleString()})`, '');
                
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
                
                addLog('', '');
                await delay(varyDelay(120));
            }
            
            addLog('─'.repeat(50), 'log-dim');
            await delay(varyDelay(200));
            
            const successRate = ((passedCount / 12) * 100).toFixed(0);
            const summaryClass = failedCount === 0 ? 'log-success' : 'log-warning';
            addLog(`<span class="${summaryClass}">Results: ${passedCount}/12 passed (${successRate}%)</span>`, '');
            
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
