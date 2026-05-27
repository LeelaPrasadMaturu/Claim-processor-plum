const AUTH_STORAGE_KEY = 'plum_claims_session';
const USERS_STORAGE_KEY = 'plum_registered_users';

const HARDCODED_USERS = [
    { email: 'admin@plumhq.com', password: 'admin123', name: 'Admin User', role: 'Administrator' },
    { email: 'agent@plumhq.com', password: 'agent123', name: 'Claims Agent', role: 'Agent' },
    { email: 'demo@plumhq.com', password: 'demo123', name: 'Demo User', role: 'Viewer' }
];

const SIGNUP_INVITE_CODE = 'PLUM2024';

function getRegisteredUsers() {
    try {
        return JSON.parse(localStorage.getItem(USERS_STORAGE_KEY) || '[]');
    } catch {
        return [];
    }
}

function saveRegisteredUsers(users) {
    localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(users));
}

function getAllUsers() {
    return [...HARDCODED_USERS, ...getRegisteredUsers()];
}

function getSession() {
    try {
        return JSON.parse(sessionStorage.getItem(AUTH_STORAGE_KEY));
    } catch {
        return null;
    }
}

function setSession(user) {
    sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({
        email: user.email,
        name: user.name,
        role: user.role
    }));
}

function clearSession() {
    sessionStorage.removeItem(AUTH_STORAGE_KEY);
}

function isAuthenticated() {
    return !!getSession();
}

function findUser(email, password) {
    const normalized = email.trim().toLowerCase();
    return getAllUsers().find(
        u => u.email.toLowerCase() === normalized && u.password === password
    );
}

function showAuthView(page) {
    document.getElementById('authView')?.classList.remove('hidden');
    document.getElementById('appShell')?.classList.add('hidden');
    
    document.querySelectorAll('.auth-page').forEach(p => p.classList.remove('active'));
    document.getElementById(page)?.classList.add('active');
}

function showAppView() {
    document.getElementById('authView')?.classList.add('hidden');
    document.getElementById('appShell')?.classList.remove('hidden');
    updateUserDisplay();
}

function updateUserDisplay() {
    const session = getSession();
    const el = document.getElementById('navUser');
    if (el && session) {
        el.innerHTML = `
            <span class="nav-user-name">${session.name}</span>
            <span class="nav-user-role">${session.role}</span>
        `;
    }
}

function showAuthError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.classList.add('visible');
    }
}

function clearAuthError(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = '';
        el.classList.remove('visible');
    }
}

function handleLogin(e) {
    e.preventDefault();
    clearAuthError('loginError');
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    const user = findUser(email, password);
    if (!user) {
        showAuthError('loginError', 'Invalid email or password. Use demo credentials below.');
        return;
    }
    
    setSession(user);
    showAppView();
    if (typeof window.onAuthSuccess === 'function') {
        window.onAuthSuccess();
    }
}

function handleSignup(e) {
    e.preventDefault();
    clearAuthError('signupError');
    
    const name = document.getElementById('signupName').value.trim();
    const email = document.getElementById('signupEmail').value.trim().toLowerCase();
    const password = document.getElementById('signupPassword').value;
    const confirm = document.getElementById('signupConfirm').value;
    const inviteCode = document.getElementById('signupInvite').value.trim();
    
    if (password.length < 6) {
        showAuthError('signupError', 'Password must be at least 6 characters.');
        return;
    }
    
    if (password !== confirm) {
        showAuthError('signupError', 'Passwords do not match.');
        return;
    }
    
    if (inviteCode !== SIGNUP_INVITE_CODE) {
        showAuthError('signupError', 'Invalid invite code.');
        return;
    }
    
    const exists = getAllUsers().some(u => u.email.toLowerCase() === email);
    if (exists) {
        showAuthError('signupError', 'An account with this email already exists.');
        return;
    }
    
    const registered = getRegisteredUsers();
    registered.push({
        email,
        password,
        name,
        role: 'Member'
    });
    saveRegisteredUsers(registered);
    
    setSession({ email, name, role: 'Member' });
    showAppView();
    if (typeof window.onAuthSuccess === 'function') {
        window.onAuthSuccess();
    }
}

function handleLogout() {
    clearSession();
    showAuthView('login');
    document.getElementById('loginForm')?.reset();
}

function initAuth() {
    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    document.getElementById('signupForm')?.addEventListener('submit', handleSignup);
    
    document.getElementById('showSignup')?.addEventListener('click', (e) => {
        e.preventDefault();
        showAuthView('signup');
        clearAuthError('loginError');
    });
    
    document.getElementById('showLogin')?.addEventListener('click', (e) => {
        e.preventDefault();
        showAuthView('login');
        clearAuthError('signupError');
    });
    
    document.getElementById('logoutBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        handleLogout();
    });
    
    if (isAuthenticated()) {
        showAppView();
    } else {
        showAuthView('login');
    }
}

window.isAuthenticated = isAuthenticated;
window.initAuth = initAuth;
