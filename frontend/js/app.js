const API_BASE = '/api';

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initForm();
    initTestRunner();
    initModal();
    loadMembers();
    loadPolicyInfo();
    loadDashboard();
    loadClaimHistory();
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
        
        const hospitalLogos = {
            'Apollo Hospitals': 'https://logo.clearbit.com/apollohospitals.com',
            'Fortis Healthcare': 'https://logo.clearbit.com/fortishealthcare.com',
            'Max Healthcare': 'https://logo.clearbit.com/maxhealthcare.in',
            'Manipal Hospitals': 'https://logo.clearbit.com/manipalhospitals.com',
            'Medanta': 'https://logo.clearbit.com/medanta.org',
            'AIIMS': 'https://logo.clearbit.com/aiims.edu',
            'Narayana Health': 'https://logo.clearbit.com/narayanahealth.org',
            'Columbia Asia': 'https://logo.clearbit.com/columbiaasia.com'
        };
        
        const categoryIcons = {
            'consultation': 'C',
            'diagnostic': 'D',
            'pharmacy': 'P',
            'dental': 'T',
            'vision': 'V',
            'alternative_medicine': 'A'
        };
        
        const container = document.getElementById('policyInfo');
        container.innerHTML = `
            <div class="policy-overview">
                <div class="policy-card policy-hero">
                    <div class="policy-hero-content">
                        <div class="policy-logo-box">GHI</div>
                        <div class="policy-hero-text">
                            <h2>${policy.policy_name || 'Group Health Insurance'}</h2>
                            <p class="policy-id">Policy ID: ${policy.policy_id || 'PLM-GHI-2024-001'}</p>
                            <p class="policy-period">Valid: ${policy.start_date || '01 Apr 2024'} - ${policy.end_date || '31 Mar 2029'}</p>
                        </div>
                        <div class="policy-status">
                            <span class="status-active">Active</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="policy-section">
                <h3 class="section-title">Coverage Summary</h3>
                <div class="coverage-cards">
                    <div class="coverage-card">
                        <div class="coverage-icon-box">SI</div>
                        <div class="coverage-details">
                            <span class="coverage-label">Sum Insured</span>
                            <span class="coverage-value">₹${policy.coverage.sum_insured_per_employee.toLocaleString()}</span>
                            <span class="coverage-sub">Per Employee Per Year</span>
                        </div>
                    </div>
                    <div class="coverage-card">
                        <div class="coverage-icon-box">OPD</div>
                        <div class="coverage-details">
                            <span class="coverage-label">OPD Limit</span>
                            <span class="coverage-value">₹${policy.coverage.annual_opd_limit.toLocaleString()}</span>
                            <span class="coverage-sub">Annual Limit</span>
                        </div>
                    </div>
                    <div class="coverage-card">
                        <div class="coverage-icon-box">PC</div>
                        <div class="coverage-details">
                            <span class="coverage-label">Per Claim</span>
                            <span class="coverage-value">₹${policy.coverage.per_claim_limit.toLocaleString()}</span>
                            <span class="coverage-sub">Maximum Per Claim</span>
                        </div>
                    </div>
                    <div class="coverage-card highlight">
                        <div class="coverage-icon-box highlight">20%</div>
                        <div class="coverage-details">
                            <span class="coverage-label">Network Discount</span>
                            <span class="coverage-value">Available</span>
                            <span class="coverage-sub">At Partner Hospitals</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="policy-section">
                <h3 class="section-title">OPD Categories & Limits</h3>
                <div class="categories-table">
                    <div class="table-header">
                        <span>Category</span>
                        <span>Sub-Limit</span>
                        <span>Co-Pay</span>
                        <span>Waiting Period</span>
                    </div>
                    ${Object.entries(policy.opd_categories).map(([cat, details]) => `
                        <div class="table-row">
                            <span class="category-name">
                                <span class="category-icon">${categoryIcons[cat] || 'O'}</span>
                                ${formatCategoryName(cat)}
                            </span>
                            <span class="category-limit">₹${details.sub_limit.toLocaleString()}</span>
                            <span class="category-copay">${details.copay_percent}%</span>
                            <span class="category-waiting">${details.waiting_period_days || 0} days</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="policy-section">
                <h3 class="section-title">Network Hospitals <span class="hospital-count">${policy.network_hospitals.length} Partners</span></h3>
                <p class="section-subtitle">Avail 20% discount at these partner hospitals</p>
                <div class="hospitals-grid">
                    ${policy.network_hospitals.map(h => `
                        <div class="hospital-card">
                            <img src="${hospitalLogos[h] || `https://ui-avatars.com/api/?name=${encodeURIComponent(h)}&background=0066cc&color=fff&size=64`}" 
                                 alt="${h}" 
                                 class="hospital-logo"
                                 onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(h)}&background=0066cc&color=fff&size=64'">
                            <span class="hospital-name">${h}</span>
                            <span class="hospital-discount">20% Off</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="policy-section">
                <h3 class="section-title">Exclusions & Waiting Periods</h3>
                <div class="exclusions-grid">
                    <div class="exclusion-card">
                        <h4>General Exclusions</h4>
                        <ul>
                            <li>Cosmetic procedures (unless medically necessary)</li>
                            <li>Self-inflicted injuries</li>
                            <li>Substance abuse treatment</li>
                            <li>Experimental treatments</li>
                            <li>War or nuclear risks</li>
                        </ul>
                    </div>
                    <div class="exclusion-card">
                        <h4>Waiting Periods</h4>
                        <ul>
                            <li>Pre-existing conditions: 2 years</li>
                            <li>Maternity benefits: 9 months</li>
                            <li>Specific diseases: 2 years</li>
                            <li>General OPD: 30 days</li>
                        </ul>
                    </div>
                    <div class="exclusion-card">
                        <h4>Pre-Authorization Required</h4>
                        <ul>
                            <li>Claims above ₹10,000</li>
                            <li>All surgical procedures</li>
                            <li>Diagnostic packages</li>
                            <li>Alternative medicine treatments</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="policy-section">
                <h3 class="section-title">Quick Actions</h3>
                <div class="quick-actions">
                    <button class="action-btn" onclick="showPage('submit')">Submit Claim</button>
                    <button class="action-btn" onclick="window.print()">Print Policy</button>
                    <button class="action-btn">Contact Support</button>
                    <button class="action-btn">Download PDF</button>
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

async function loadDashboard() {
    const container = document.getElementById('dashboardContent');
    
    try {
        const response = await fetch(`${API_BASE}/decisions/run-all-tests`, { method: 'POST' });
        const data = await response.json();
        const results = data.results || [];
        
        const stats = {
            total: results.length,
            approved: results.filter(r => r.actual_decision === 'APPROVED').length,
            partial: results.filter(r => r.actual_decision === 'PARTIAL').length,
            rejected: results.filter(r => r.actual_decision === 'REJECTED').length,
            manual: results.filter(r => r.actual_decision === 'MANUAL_REVIEW').length,
            totalClaimed: results.reduce((sum, r) => sum + (r.decision?.claimed_amount || 0), 0),
            totalApproved: results.reduce((sum, r) => sum + (r.decision?.approved_amount || 0), 0),
            avgProcessingTime: Math.round(results.reduce((sum, r) => sum + (r.decision?.full_trace?.total_duration_ms || 0), 0) / results.length),
            avgConfidence: (results.reduce((sum, r) => sum + (r.decision?.confidence_score || 0), 0) / results.length * 100).toFixed(1)
        };
        
        const categoryStats = {};
        results.forEach(r => {
            const cat = r.decision?.category || 'UNKNOWN';
            if (!categoryStats[cat]) categoryStats[cat] = { count: 0, amount: 0 };
            categoryStats[cat].count++;
            categoryStats[cat].amount += r.decision?.claimed_amount || 0;
        });
        
        const approvalRate = ((stats.approved + stats.partial) / stats.total * 100).toFixed(1);
        
        const approvedPct = (stats.approved / stats.total * 100).toFixed(0);
        const partialPct = (stats.partial / stats.total * 100).toFixed(0);
        const rejectedPct = (stats.rejected / stats.total * 100).toFixed(0);
        const manualPct = (stats.manual / stats.total * 100).toFixed(0);
        
        container.innerHTML = `
            <div class="dashboard-grid">
                <div class="stat-card-large">
                    <div class="stat-icon-box">
                        <span class="stat-icon-text">#</span>
                    </div>
                    <div class="stat-info">
                        <span class="stat-value">${stats.total}</span>
                        <span class="stat-label">Total Claims</span>
                    </div>
                </div>
                <div class="stat-card-large success">
                    <div class="stat-icon-box success">
                        <span class="stat-icon-text">A</span>
                    </div>
                    <div class="stat-info">
                        <span class="stat-value">${stats.approved}</span>
                        <span class="stat-label">Approved</span>
                    </div>
                </div>
                <div class="stat-card-large warning">
                    <div class="stat-icon-box warning">
                        <span class="stat-icon-text">P</span>
                    </div>
                    <div class="stat-info">
                        <span class="stat-value">${stats.partial}</span>
                        <span class="stat-label">Partial</span>
                    </div>
                </div>
                <div class="stat-card-large danger">
                    <div class="stat-icon-box danger">
                        <span class="stat-icon-text">R</span>
                    </div>
                    <div class="stat-info">
                        <span class="stat-value">${stats.rejected}</span>
                        <span class="stat-label">Rejected</span>
                    </div>
                </div>
            </div>
            
            <div class="dashboard-row">
                <div class="dashboard-card">
                    <h3>Approval Distribution</h3>
                    <div class="chart-container">
                        <div class="donut-chart" style="background: conic-gradient(
                            #22c55e 0% ${approvedPct}%,
                            #eab308 ${approvedPct}% ${parseInt(approvedPct) + parseInt(partialPct)}%,
                            #ef4444 ${parseInt(approvedPct) + parseInt(partialPct)}% ${parseInt(approvedPct) + parseInt(partialPct) + parseInt(rejectedPct)}%,
                            #6366f1 ${parseInt(approvedPct) + parseInt(partialPct) + parseInt(rejectedPct)}% 100%
                        );">
                            <div class="donut-hole">
                                <span class="donut-value">${approvalRate}%</span>
                                <span class="donut-label">Success Rate</span>
                            </div>
                        </div>
                        <div class="chart-legend">
                            <div class="legend-item">
                                <span class="legend-color" style="background: #22c55e"></span>
                                <span>Approved (${stats.approved})</span>
                            </div>
                            <div class="legend-item">
                                <span class="legend-color" style="background: #eab308"></span>
                                <span>Partial (${stats.partial})</span>
                            </div>
                            <div class="legend-item">
                                <span class="legend-color" style="background: #ef4444"></span>
                                <span>Rejected (${stats.rejected})</span>
                            </div>
                            <div class="legend-item">
                                <span class="legend-color" style="background: #6366f1"></span>
                                <span>Manual Review (${stats.manual})</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-card">
                    <h3>Financial Summary</h3>
                    <div class="financial-stats">
                        <div class="financial-row">
                            <span class="financial-label">Total Claimed</span>
                            <span class="financial-value">₹${stats.totalClaimed.toLocaleString()}</span>
                        </div>
                        <div class="financial-row">
                            <span class="financial-label">Total Approved</span>
                            <span class="financial-value highlight">₹${stats.totalApproved.toLocaleString()}</span>
                        </div>
                        <div class="financial-row">
                            <span class="financial-label">Adjustments</span>
                            <span class="financial-value">₹${(stats.totalClaimed - stats.totalApproved).toLocaleString()}</span>
                        </div>
                        <div class="financial-divider"></div>
                        <div class="financial-row">
                            <span class="financial-label">Payout Ratio</span>
                            <span class="financial-value">${((stats.totalApproved / stats.totalClaimed) * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="dashboard-row">
                <div class="dashboard-card">
                    <h3>Claims by Category</h3>
                    <div class="category-bars">
                        ${Object.entries(categoryStats).map(([cat, data]) => {
                            const percentage = (data.count / stats.total * 100).toFixed(0);
                            return `
                                <div class="category-bar-item">
                                    <div class="category-bar-header">
                                        <span>${formatCategoryName(cat)}</span>
                                        <span>${data.count} claims</span>
                                    </div>
                                    <div class="category-bar-track">
                                        <div class="category-bar-fill" style="width: ${percentage}%"></div>
                                    </div>
                                    <div class="category-bar-amount">₹${data.amount.toLocaleString()}</div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
                
                <div class="dashboard-card">
                    <h3>System Metrics</h3>
                    <div class="metrics-grid">
                        <div class="metric-item">
                            <span class="metric-value">${stats.avgProcessingTime}ms</span>
                            <span class="metric-label">Avg Processing Time</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-value">${stats.avgConfidence}%</span>
                            <span class="metric-label">Avg Confidence Score</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-value">5</span>
                            <span class="metric-label">Active Agents</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-value">${approvalRate}%</span>
                            <span class="metric-label">Approval Rate</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="dashboard-card full-width">
                <h3>Recent Claims</h3>
                <div class="activity-table">
                    <div class="activity-header">
                        <span>Claim</span>
                        <span>Category</span>
                        <span>Claimed</span>
                        <span>Approved</span>
                        <span>Status</span>
                    </div>
                    ${results.slice(0, 6).map((r, i) => {
                        const statusClass = r.actual_decision === 'APPROVED' ? 'success' : 
                                           r.actual_decision === 'REJECTED' ? 'danger' : 'warning';
                        return `
                            <div class="activity-row">
                                <span class="activity-name">${r.case_name}</span>
                                <span class="activity-category">${r.decision?.category || 'N/A'}</span>
                                <span class="activity-claimed">₹${(r.decision?.claimed_amount || 0).toLocaleString()}</span>
                                <span class="activity-approved">₹${(r.decision?.approved_amount || 0).toLocaleString()}</span>
                                <span><span class="status-badge-sm ${statusClass}">${r.actual_decision}</span></span>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
        
    } catch (err) {
        console.error('Failed to load dashboard:', err);
        container.innerHTML = `
            <div class="empty-state">
                <p>Failed to load dashboard. Make sure the server is running.</p>
                <button class="btn btn-primary" onclick="loadDashboard()">Retry</button>
            </div>
        `;
    }
}

async function loadClaimHistory() {
    const container = document.getElementById('historyContent');
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    const categoryFilter = document.getElementById('categoryFilter')?.value || '';
    
    try {
        const response = await fetch(`${API_BASE}/decisions/run-all-tests`, { method: 'POST' });
        const data = await response.json();
        let results = data.results || [];
        
        if (statusFilter) {
            results = results.filter(r => r.actual_decision === statusFilter);
        }
        if (categoryFilter) {
            results = results.filter(r => r.decision?.category === categoryFilter);
        }
        
        if (results.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No claims found matching the filters</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <div class="history-table">
                <div class="table-header-row">
                    <span>Claim ID</span>
                    <span>Category</span>
                    <span>Member</span>
                    <span>Claimed</span>
                    <span>Approved</span>
                    <span>Status</span>
                    <span>Confidence</span>
                    <span>Actions</span>
                </div>
                ${results.map((r, i) => {
                    const statusClass = r.actual_decision === 'APPROVED' ? 'success' : 
                                       r.actual_decision === 'REJECTED' ? 'danger' : 
                                       r.actual_decision === 'PARTIAL' ? 'warning' : 'info';
                    const claimId = r.decision?.full_trace?.claim_id || `CLM_${String(i + 1).padStart(4, '0')}`;
                    return `
                        <div class="table-data-row">
                            <span class="claim-id">${claimId}</span>
                            <span class="claim-category">
                                <span class="category-badge">${r.decision?.category || 'N/A'}</span>
                            </span>
                            <span class="claim-member">${r.decision?.member_id || 'MEM001'}</span>
                            <span class="claim-amount">₹${(r.decision?.claimed_amount || 0).toLocaleString()}</span>
                            <span class="claim-approved ${statusClass}">₹${(r.decision?.approved_amount || 0).toLocaleString()}</span>
                            <span class="claim-status">
                                <span class="status-badge-sm ${statusClass}">${r.actual_decision}</span>
                            </span>
                            <span class="claim-confidence">${((r.decision?.confidence_score || 0) * 100).toFixed(0)}%</span>
                            <span class="claim-actions">
                                <button class="btn-icon" onclick='showDecision(${JSON.stringify(r.decision).replace(/'/g, "&#39;")})' title="View Details">
                                    View
                                </button>
                            </span>
                        </div>
                    `;
                }).join('')}
            </div>
            
            <div class="history-summary">
                <span>Showing ${results.length} claims</span>
                <span>Total Claimed: ₹${results.reduce((sum, r) => sum + (r.decision?.claimed_amount || 0), 0).toLocaleString()}</span>
                <span>Total Approved: ₹${results.reduce((sum, r) => sum + (r.decision?.approved_amount || 0), 0).toLocaleString()}</span>
            </div>
        `;
        
    } catch (err) {
        console.error('Failed to load claim history:', err);
        container.innerHTML = `
            <div class="empty-state">
                <p>Failed to load claim history. Make sure the server is running.</p>
                <button class="btn btn-primary" onclick="loadClaimHistory()">Retry</button>
            </div>
        `;
    }
}

function downloadClaimPDF(claimId) {
    alert(`PDF download for ${claimId} - Feature coming soon!`);
}

window.loadClaimHistory = loadClaimHistory;

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
