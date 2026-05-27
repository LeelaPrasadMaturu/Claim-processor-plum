const API_BASE = '/api';

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initForm();
    initTestRunner();
    initModal();
    loadMembers();
    loadPolicyInfo();
});

// Navigation
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

// Load Members
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

// Load Policy Info
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

// Form Handling
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
        
        try {
            const formData = new FormData(form);
            
            const response = await fetch(`${API_BASE}/claims`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const decision = await response.json();
            showDecision(decision);
            
        } catch (err) {
            alert('Error processing claim: ' + err.message);
            console.error(err);
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

// Test Runner
function initTestRunner() {
    const btn = document.getElementById('runAllTests');
    
    btn.addEventListener('click', async () => {
        const resultsDiv = document.getElementById('testResults');
        
        btn.classList.add('loading');
        btn.disabled = true;
        resultsDiv.innerHTML = '<div class="loading-state">Running tests...</div>';
        
        try {
            const response = await fetch(`${API_BASE}/decisions/run-all-tests`, {
                method: 'POST'
            });
            const data = await response.json();
            
            resultsDiv.innerHTML = `
                <div class="test-summary">
                    <div class="summary-card total">
                        <div class="number">${data.summary.total}</div>
                        <div class="label">Total Tests</div>
                    </div>
                    <div class="summary-card passed">
                        <div class="number">${data.summary.passed}</div>
                        <div class="label">Passed</div>
                    </div>
                    <div class="summary-card failed">
                        <div class="number">${data.summary.failed}</div>
                        <div class="label">Failed</div>
                    </div>
                </div>
                
                <div class="test-cases">
                    ${data.results.map(r => `
                        <div class="test-case-card ${r.passed ? 'passed' : 'failed'}">
                            <div class="test-case-header">
                                <span class="test-case-id">${r.case_id}: ${r.case_name}</span>
                                <span class="test-case-result ${r.passed ? 'passed' : 'failed'}">
                                    ${r.passed ? 'PASSED' : 'FAILED'}
                                </span>
                            </div>
                            <div class="test-case-details">
                                ${r.error ? `<span style="color: var(--danger);">Error: ${r.error}</span>` : `
                                    Expected: <strong>${r.expected_decision || 'N/A'}</strong> | 
                                    Actual: <strong>${r.actual_decision || 'N/A'}</strong>
                                    ${r.expected_amount !== null && r.expected_amount !== undefined ? 
                                        `<br>Amount: ₹${(r.actual_amount || 0).toLocaleString()}` : ''}
                                `}
                            </div>
                            <button class="btn btn-secondary" onclick='showDecision(${JSON.stringify(r.decision).replace(/'/g, "&#39;")})'>
                                View Details
                            </button>
                        </div>
                    `).join('')}
                </div>
            `;
        } catch (err) {
            resultsDiv.innerHTML = `
                <div class="empty-state">
                    <p style="color: var(--danger);">Error running tests: ${err.message}</p>
                </div>
            `;
        } finally {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    });
}

// Modal
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

// Make showPage globally available
window.showPage = showPage;
window.showDecision = showDecision;
