// Kitchen Table - Client-side JavaScript

// Utility functions
const API = {
    async call(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'An error occurred');
            }
            
            return data;
        } catch (error) {
            throw error;
        }
    }
};

function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.classList.add('show');
        setTimeout(() => el.classList.remove('show'), 5000);
    }
}

function showSuccess(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.classList.add('show');
        setTimeout(() => el.classList.remove('show'), 5000);
    }
}

function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'none';
}

function formatTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const seconds = Math.floor((now - time) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { weekday: 'long', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

// Auth Forms
if (typeof mode !== 'undefined') {
    const form = document.getElementById('auth-form');
    
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const errorEl = document.getElementById('error-message');
            const successEl = document.getElementById('success-message');
            if (errorEl) errorEl.classList.remove('show');
            if (successEl) successEl.classList.remove('show');
            
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            
            try {
                let response;
                
                if (mode === 'signup') {
                    response = await API.call('/api/auth/signup', {
                        method: 'POST',
                        body: JSON.stringify(data)
                    });
                } else if (mode === 'login') {
                    response = await API.call('/api/auth/login', {
                        method: 'POST',
                        body: JSON.stringify(data)
                    });
                } else if (mode === 'forgot') {
                    response = await API.call('/api/auth/forgot-password', {
                        method: 'POST',
                        body: JSON.stringify(data)
                    });
                    
                    if (successEl) {
                        successEl.textContent = response.message;
                        if (response.reset_token) {
                            successEl.textContent += ` Reset link: ${window.location.origin}/reset-password/${response.reset_token}`;
                        }
                        successEl.classList.add('show');
                    }
                    form.reset();
                    return;
                } else if (mode === 'reset') {
                    if (data.password !== data.confirm_password) {
                        throw new Error('Passwords do not match');
                    }
                    response = await API.call('/api/auth/reset-password', {
                        method: 'POST',
                        body: JSON.stringify({
                            token: document.getElementById('token').value,
                            password: data.password
                        })
                    });
                }
                
                if (response.redirect) {
                    window.location.href = response.redirect;
                }
            } catch (error) {
                if (errorEl) {
                    errorEl.textContent = error.message;
                    errorEl.classList.add('show');
                }
            }
        });
    }
}

// Create Table Form
const createTableForm = document.getElementById('create-table-form');
if (createTableForm) {
    createTableForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(createTableForm);
        const data = Object.fromEntries(formData);
        
        try {
            showLoading();
            const response = await API.call('/api/table/create', {
                method: 'POST',
                body: JSON.stringify({
                    name: data.table_name,
                    prompt_time: data.prompt_time
                })
            });
            
            if (response.redirect) {
                window.location.href = response.redirect;
            }
        } catch (error) {
            hideLoading();
            showError('error-message', error.message);
        }
    });
}

// Join Table Form
const joinTableForm = document.getElementById('join-table-form');
if (joinTableForm) {
    const inviteCodeInput = document.getElementById('invite_code');
    
    // Auto-format invite code
    if (inviteCodeInput) {
        inviteCodeInput.addEventListener('input', (e) => {
            let value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
            if (value.length > 4) {
                value = value.slice(0, 4) + '-' + value.slice(4, 8);
            }
            e.target.value = value;
        });
    }
    
    joinTableForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(joinTableForm);
        const data = Object.fromEntries(formData);
        
        try {
            showLoading();
            const response = await API.call('/api/table/join', {
                method: 'POST',
                body: JSON.stringify({
                    invite_code: data.invite_code
                })
            });
            
            if (response.redirect) {
                window.location.href = response.redirect;
            }
        } catch (error) {
            hideLoading();
            showError('error-message', error.message);
        }
    });
}

// Logout
const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
        try {
            await API.call('/api/auth/logout', { method: 'POST' });
            window.location.href = '/';
        } catch (error) {
            console.error('Logout error:', error);
        }
    });
}

// Table Page (Today)
if (window.location.pathname === '/table') {
    let pollInterval;
    
    async function loadTableInfo() {
        try {
            const data = await API.call('/api/table/info');
            document.getElementById('table-name').textContent = `🏠 ${data.table.name}`;
        } catch (error) {
            console.error('Error loading table info:', error);
        }
    }
    
    async function loadTodayPrompt() {
        try {
            const data = await API.call('/api/prompt/today');
            
            // Update date
            document.getElementById('date-label').textContent = 'TODAY';
            document.getElementById('date-value').textContent = formatDate(data.date);
            
            // Update prompt
            document.getElementById('prompt-text').textContent = data.prompt.prompt_text;
            
            // Update response section
            const responseSection = document.getElementById('response-section');
            
            if (data.user_response) {
                // User has responded - show all responses
                renderResponses(data.prompt.responses, data.user_response.user_id);
                
                // Start polling for new responses
                startPolling();
            } else {
                // Show response form
                renderResponseForm();
            }
        } catch (error) {
            console.error('Error loading prompt:', error);
            showError('error-message', error.message);
        }
    }
    
    function renderResponseForm() {
        const responseSection = document.getElementById('response-section');
        responseSection.innerHTML = `
            <div class="response-form">
                <textarea 
                    id="response-textarea" 
                    class="response-textarea" 
                    placeholder="Share your answer..." 
                    maxlength="500"
                ></textarea>
                <div id="char-count" class="char-count">0 / 500</div>
                <div id="form-error" class="error-message"></div>
                <button id="submit-response-btn" class="btn btn-primary">Share your answer</button>
            </div>
        `;
        
        const textarea = document.getElementById('response-textarea');
        const charCount = document.getElementById('char-count');
        const submitBtn = document.getElementById('submit-response-btn');
        
        textarea.addEventListener('input', () => {
            const length = textarea.value.length;
            charCount.textContent = `${length} / 500`;
            
            if (length > 450) {
                charCount.classList.add('warning');
            } else {
                charCount.classList.remove('warning');
            }
            
            if (length === 500) {
                charCount.classList.add('error');
            } else {
                charCount.classList.remove('error');
            }
        });
        
        submitBtn.addEventListener('click', async () => {
            const response = textarea.value.trim();
            
            if (!response) {
                showError('form-error', 'Please enter a response');
                return;
            }
            
            try {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Sharing...';
                
                const data = await API.call('/api/response/submit', {
                    method: 'POST',
                    body: JSON.stringify({ response })
                });
                
                // Reload to show responses
                await loadTodayPrompt();
            } catch (error) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Share your answer';
                showError('form-error', error.message);
            }
        });
    }
    
    function renderResponses(responses, currentUserId) {
        const responseSection = document.getElementById('response-section');
        
        if (!responses || responses.length === 0) {
            responseSection.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">☕</div>
                    <p>You're the first one here today!</p>
                </div>
            `;
            return;
        }
        
        const responsesHTML = responses.map(r => `
            <div class="response-card" data-response-id="${r.id}">
                <div class="response-header">
                    <span class="response-author ${r.user_id === currentUserId ? 'you' : ''}">
                        ${r.user_id === currentUserId ? 'You' : r.display_name}
                    </span>
                    <span class="response-time">${formatTimeAgo(r.created_at)}</span>
                </div>
                <p class="response-text">${escapeHtml(r.response_text)}</p>
            </div>
        `).join('');
        
        responseSection.innerHTML = `
            <div class="responses-container">
                ${responsesHTML}
            </div>
        `;
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    async function pollForNewResponses() {
        try {
            const data = await API.call('/api/response/poll');
            const currentResponses = document.querySelectorAll('.response-card');
            
            if (data.responses && data.responses.length > currentResponses.length) {
                // New responses available - reload
                await loadTodayPrompt();
            }
        } catch (error) {
            console.error('Poll error:', error);
        }
    }
    
    function startPolling() {
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(pollForNewResponses, 30000); // Poll every 30 seconds
    }
    
    // Initialize
    loadTableInfo();
    loadTodayPrompt();
}

// Yesterday Page
if (window.location.pathname === '/table/yesterday') {
    async function loadTableInfo() {
        try {
            const data = await API.call('/api/table/info');
            document.getElementById('table-name').textContent = `🏠 ${data.table.name}`;
        } catch (error) {
            console.error('Error loading table info:', error);
        }
    }
    
    async function loadYesterdayPrompt() {
        try {
            const data = await API.call('/api/prompt/yesterday');
            
            // Update date
            document.getElementById('date-label').textContent = 'YESTERDAY';
            document.getElementById('date-value').textContent = formatDate(data.date);
            
            // Update prompt
            document.getElementById('prompt-text').textContent = data.prompt.prompt_text;
            
            // Render responses
            const container = document.getElementById('responses-container');
            
            if (!data.responses || data.responses.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🤷</div>
                        <p>No one answered yesterday's question</p>
                    </div>
                `;
                return;
            }
            
            const responsesHTML = data.responses.map(r => `
                <div class="response-card">
                    <div class="response-header">
                        <span class="response-author ${data.user_response && r.user_id === data.user_response.user_id ? 'you' : ''}">
                            ${data.user_response && r.user_id === data.user_response.user_id ? 'You' : r.display_name}
                        </span>
                        <span class="response-time">${formatTimeAgo(r.created_at)}</span>
                    </div>
                    <p class="response-text">${escapeHtml(r.response_text)}</p>
                </div>
            `).join('');
            
            container.innerHTML = responsesHTML;
        } catch (error) {
            console.error('Error loading yesterday prompt:', error);
            const container = document.getElementById('responses-container');
            container.innerHTML = `
                <div class="empty-state">
                    <p>No prompt available for yesterday</p>
                </div>
            `;
        }
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Initialize
    loadTableInfo();
    loadYesterdayPrompt();
}

// Settings Page
if (window.location.pathname === '/table/settings') {
    async function loadSettings() {
        try {
            const data = await API.call('/api/table/info');
            
            // Update table info
            document.getElementById('table-name-display').textContent = data.table.name;
            document.getElementById('invite-code-display').textContent = data.table.invite_code;
            
            // Show owner settings if user is owner
            if (data.table.is_owner) {
                document.getElementById('owner-settings').style.display = 'block';
                document.getElementById('table_name').value = data.table.name;
                document.getElementById('prompt_time').value = data.table.prompt_time;
            }
            
            // Render members
            const membersList = document.getElementById('members-list');
            const membersHTML = data.members.map(m => `
                <div class="member-item">
                    <div class="member-info">
                        <div class="member-name">${m.display_name}</div>
                        <div class="member-username">@${m.username}</div>
                    </div>
                    ${m.role === 'owner' ? '<span class="member-role">Owner</span>' : ''}
                </div>
            `).join('');
            
            membersList.innerHTML = membersHTML;
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }
    
    // Copy invite code
    const copyCodeBtn = document.getElementById('copy-code-btn');
    if (copyCodeBtn) {
        copyCodeBtn.addEventListener('click', () => {
            const code = document.getElementById('invite-code-display').textContent;
            navigator.clipboard.writeText(code).then(() => {
                copyCodeBtn.textContent = 'Copied!';
                setTimeout(() => {
                    copyCodeBtn.textContent = 'Copy Code';
                }, 2000);
            });
        });
    }
    
    // Settings form
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(settingsForm);
            const data = Object.fromEntries(formData);
            
            try {
                const submitBtn = settingsForm.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.textContent = 'Saving...';
                
                await API.call('/api/table/settings', {
                    method: 'PUT',
                    body: JSON.stringify({
                        name: data.table_name,
                        prompt_time: data.prompt_time
                    })
                });
                
                showSuccess('settings-message', 'Settings saved successfully!');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Changes';
                
                // Reload settings
                await loadSettings();
            } catch (error) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Changes';
                showError('settings-message', error.message);
            }
        });
    }
    
    // Leave table
    const leaveTableBtn = document.getElementById('leave-table-btn');
    if (leaveTableBtn) {
        leaveTableBtn.addEventListener('click', async () => {
            if (!confirm('Are you sure you want to leave this table? You will need an invite code to rejoin.')) {
                return;
            }
            
            try {
                showLoading();
                const response = await API.call('/api/table/leave', {
                    method: 'POST'
                });
                
                if (response.redirect) {
                    window.location.href = response.redirect;
                }
            } catch (error) {
                hideLoading();
                alert(error.message);
            }
        });
    }
    
    // Initialize
    loadSettings();
}

// Table Switcher functionality
class TableSwitcher {
    constructor() {
        this.currentTable = null;
        this.tables = [];
        this.isOpen = false;
        this.init();
    }
    
    async init() {
        // Only initialize on pages that need it
        const switcherContainer = document.getElementById('table-switcher-container');
        if (!switcherContainer) return;
        
        await this.loadTables();
        this.render();
        this.attachEventListeners();
    }
    
    async loadTables() {
        try {
            const data = await API.call('/api/table/list');
            this.tables = data.tables;
            this.currentTable = data.current_table_id;
        } catch (error) {
            console.error('Error loading tables:', error);
        }
    }
    
    render() {
        const container = document.getElementById('table-switcher-container');
        if (!container) return;
        
        const currentTableData = this.tables.find(t => t.is_current);
        const currentTableName = currentTableData ? currentTableData.name : 'Select Table';
        
        container.innerHTML = `
            <div class="table-switcher" id="table-switcher">
                <button class="table-switcher-button" id="table-switcher-btn">
                    <span class="table-icon">🏠</span>
                    <span class="table-current-name">${escapeHtml(currentTableName)}</span>
                    <span class="arrow">▼</span>
                </button>
                <div class="table-switcher-dropdown">
                    <div class="table-switcher-header">Your Tables</div>
                    <div class="table-list" id="table-list">
                        ${this.renderTableList()}
                    </div>
                    <div class="table-switcher-divider"></div>
                    <button class="table-switcher-action" id="create-new-table-btn">
                        <span class="icon">+</span>
                        <span>Create New Table</span>
                    </button>
                    <button class="table-switcher-action" id="join-table-btn">
                        <span class="icon">🔗</span>
                        <span>Join Table</span>
                    </button>
                </div>
            </div>
        `;
    }
    
    renderTableList() {
        return this.tables.map(table => `
            <button class="table-list-item ${table.is_current ? 'active' : ''}" 
                    data-table-id="${table.id}">
                <div class="table-info">
                    <div class="table-name">${escapeHtml(table.name)}</div>
                    <div class="table-role">${table.role === 'owner' ? 'Owner' : 'Member'}</div>
                </div>
                ${table.is_current ? '<span class="check-icon">✓</span>' : ''}
            </button>
        `).join('');
    }
    
    attachEventListeners() {
        const switcherBtn = document.getElementById('table-switcher-btn');
        const switcher = document.getElementById('table-switcher');
        
        if (switcherBtn) {
            switcherBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggle();
            });
        }
        
        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (switcher && !switcher.contains(e.target)) {
                this.close();
            }
        });
        
        // Table selection
        const tableItems = document.querySelectorAll('.table-list-item');
        tableItems.forEach(item => {
            item.addEventListener('click', async (e) => {
                const tableId = parseInt(item.dataset.tableId);
                if (tableId !== this.currentTable) {
                    await this.switchTable(tableId);
                }
                this.close();
            });
        });
        
        // Create new table
        const createBtn = document.getElementById('create-new-table-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                window.location.href = '/create-table';
            });
        }
        
        // Join table
        const joinBtn = document.getElementById('join-table-btn');
        if (joinBtn) {
            joinBtn.addEventListener('click', () => {
                window.location.href = '/join-table';
            });
        }
    }
    
    toggle() {
        const switcher = document.getElementById('table-switcher');
        if (switcher) {
            this.isOpen = !this.isOpen;
            if (this.isOpen) {
                switcher.classList.add('open');
            } else {
                switcher.classList.remove('open');
            }
        }
    }
    
    close() {
        const switcher = document.getElementById('table-switcher');
        if (switcher) {
            this.isOpen = false;
            switcher.classList.remove('open');
        }
    }
    
    async switchTable(tableId) {
        try {
            showLoading();
            await API.call('/api/table/switch', {
                method: 'POST',
                body: JSON.stringify({ table_id: tableId })
            });
            
            // Reload the page to show new table content
            window.location.reload();
        } catch (error) {
            hideLoading();
            alert('Error switching tables: ' + error.message);
        }
    }
}

// Initialize table switcher on relevant pages
if (window.location.pathname === '/table' || 
    window.location.pathname === '/table/yesterday' || 
    window.location.pathname === '/table/settings') {
    document.addEventListener('DOMContentLoaded', () => {
        new TableSwitcher();
    });
}
