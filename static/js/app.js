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

function formatTimeUntilPrompt(seconds) {
    if (seconds <= 0) return '';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
        return `Today's prompt available in ${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `Today's prompt available in ${minutes}m`;
    } else {
        return `Today's prompt available in less than 1 minute`;
    }
}

function getUserPillClass(userId) {
    const colors = ['pill-lavender', 'pill-mint', 'pill-peach', 'pill-sky', 'pill-rose', 'pill-lemon', 'pill-sage', 'pill-lilac'];
    return colors[userId % colors.length];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatPromptTime(time24) {
    // Convert 24-hour time (e.g., "17:00") to 12-hour format (e.g., "5:00 PM")
    const [hours, minutes] = time24.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour % 12 || 12;
    return `${hour12}:${minutes} ${ampm}`;
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
                    
                    // Show success message for password reset
                    if (successEl) {
                        successEl.textContent = response.message || 'Password reset successful! Redirecting to login...';
                        successEl.classList.add('show');
                    }
                    form.reset();
                    
                    // Redirect to login after 2 seconds
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                    return;
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

// Table Page (Today) - PART 2
if (window.location.pathname === '/table') {
    let pollInterval;
    let currentPromptData = null;
    
    async function loadTodayPrompt() {
        try {
            const data = await API.call('/api/prompt/today');
            currentPromptData = data;
            
            // Determine if we're before or after today's prompt time
            const isBeforePromptTime = data.seconds_until_next_prompt > 0 && data.seconds_until_next_prompt < 86400;
            
            // Update date label - show YESTERDAY if we're before prompt time
            document.getElementById('date-label').textContent = isBeforePromptTime ? 'YESTERDAY' : 'TODAY';
            document.getElementById('date-value').textContent = formatDate(data.date);
            
            // Show countdown if before prompt time
            if (isBeforePromptTime) {
                const timeUntil = document.getElementById('time-until-prompt');
                timeUntil.textContent = formatTimeUntilPrompt(data.seconds_until_next_prompt);
                timeUntil.style.display = 'block';
            } else {
                // Hide countdown after prompt time
                const timeUntil = document.getElementById('time-until-prompt');
                if (timeUntil) {
                    timeUntil.style.display = 'none';
                }
            }
            
            // Update prompt
            document.getElementById('prompt-text').textContent = data.prompt.prompt_text;
            
            // Update history link
            const historyDate = new Date(data.date);
            historyDate.setDate(historyDate.getDate() - 1);
            const historyLink = document.getElementById('history-link');
            historyLink.href = `/table/history?date=${historyDate.toISOString().split('T')[0]}`;
            historyLink.textContent = `← ${formatDate(historyDate.toISOString().split('T')[0])}`;
            
            // Update response section
            const responseSection = document.getElementById('response-section');
            
            if (data.user_response) {
                // User has responded - show all responses
                renderResponses(data.prompt.responses, data.user_response.user_id, data.prompt.is_editable);
                startPolling();
            } else {
                // Show response form with count
                renderResponseForm(data.prompt.response_count);
            }
        } catch (error) {
            console.error('Error loading prompt:', error);
            showError('error-message', error.message);
        }
    }
    
    function renderResponseForm(responseCount) {
        const responseSection = document.getElementById('response-section');
        
        let countHTML = '';
        if (responseCount > 0) {
            const plural = responseCount === 1 ? 'person has' : 'people have';
            countHTML = `<div style="text-align: center; margin-bottom: 1rem; color: var(--text-secondary); font-size: 0.95rem;">${responseCount} ${plural} answered today</div>`;
        }
        
        responseSection.innerHTML = countHTML + `
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
                
                await loadTodayPrompt();
            } catch (error) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Share your answer';
                showError('form-error', error.message);
            }
        });
    }
    
    function renderResponses(responses, currentUserId, isEditable) {
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
        
        const responsesHTML = responses.map(r => {
            const isCurrentUser = r.user_id === currentUserId;
            const pillClass = getUserPillClass(r.user_id);
            const editedLabel = r.edited_at ? ' <span style="font-size: 0.75rem; opacity: 0.7;">(edited)</span>' : '';
            const editButton = isCurrentUser && isEditable ? 
                `<button class="edit-response-btn" data-response-id="${r.id}" data-prompt-id="${currentPromptData.prompt.id}" style="background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 0.85rem; padding: 0.25rem 0.5rem;">✏️ Edit</button>` : '';
            
            return `
                <div class="response-card" data-response-id="${r.id}">
                    <div class="response-header">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            ${isCurrentUser 
                                ? `<span class="response-author you">You</span>`
                                : `<span class="response-author pill ${pillClass}">${escapeHtml(r.display_name)}</span>`
                            }
                            ${editButton}
                        </div>
                        <span class="response-time">${formatTimeAgo(r.created_at)}${editedLabel}</span>
                    </div>
                    <p class="response-text" data-original-text="${escapeHtml(r.response_text)}">${escapeHtml(r.response_text)}</p>
                </div>
            `;
        }).join('');
        
        responseSection.innerHTML = `
            <div class="responses-container">
                ${responsesHTML}
            </div>
        `;
        
        // Add edit functionality
        document.querySelectorAll('.edit-response-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const responseCard = e.target.closest('.response-card');
                const responseText = responseCard.querySelector('.response-text');
                const originalText = responseText.dataset.originalText;
                const promptId = e.target.dataset.promptId;
                
                // Replace text with textarea
                responseText.innerHTML = `
                    <textarea class="response-textarea" style="width: 100%; min-height: 80px;">${originalText}</textarea>
                    <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                        <button class="btn btn-primary btn-small save-edit-btn">Save</button>
                        <button class="btn btn-secondary btn-small cancel-edit-btn">Cancel</button>
                    </div>
                `;
                
                const saveBtn = responseText.querySelector('.save-edit-btn');
                const cancelBtn = responseText.querySelector('.cancel-edit-btn');
                const textarea = responseText.querySelector('textarea');
                
                cancelBtn.addEventListener('click', () => {
                    responseText.innerHTML = escapeHtml(originalText);
                });
                
                saveBtn.addEventListener('click', async () => {
                    const newText = textarea.value.trim();
                    if (!newText) {
                        alert('Response cannot be empty');
                        return;
                    }
                    
                    try {
                        saveBtn.disabled = true;
                        saveBtn.textContent = 'Saving...';
                        
                        await API.call('/api/response/edit', {
                            method: 'PUT',
                            body: JSON.stringify({
                                prompt_id: promptId,
                                response: newText
                            })
                        });
                        
                        await loadTodayPrompt();
                    } catch (error) {
                        alert(error.message);
                        saveBtn.disabled = false;
                        saveBtn.textContent = 'Save';
                    }
                });
            });
        });
    }
    
    async function pollForNewResponses() {
        try {
            const data = await API.call('/api/response/poll');
            const currentResponses = document.querySelectorAll('.response-card');
            
            if (data.responses && data.responses.length > currentResponses.length) {
                await loadTodayPrompt();
            }
        } catch (error) {
            console.error('Poll error:', error);
        }
    }
    
    function startPolling() {
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(pollForNewResponses, 30000);
    }
    
    loadTodayPrompt();
}

// History Page
if (window.location.pathname === '/table/history') {
    async function loadHistoryPrompt() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const dateParam = urlParams.get('date') || currentDate;
            
            const data = await API.call(`/api/prompt/date/${dateParam}`);
            
            // Update date
            document.getElementById('date-label').textContent = formatDate(data.date).split(',')[0].toUpperCase();
            document.getElementById('date-value').textContent = formatDate(data.date).split(',').slice(1).join(',');
            
            // Update prompt
            document.getElementById('prompt-text').textContent = data.prompt.prompt_text;
            
            // Navigation buttons
            const currentDate = new Date(data.date);
            const prevDate = new Date(currentDate);
            prevDate.setDate(prevDate.getDate() - 1);
            const nextDate = new Date(currentDate);
            nextDate.setDate(nextDate.getDate() + 1);
            const today = new Date();
            
            const prevLink = document.getElementById('prev-day-link');
            const nextLink = document.getElementById('next-day-link');
            
            // Show prev if within 7 days
            const daysBack = Math.floor((today - currentDate) / (1000 * 60 * 60 * 24));
            if (daysBack < 7) {
                prevLink.href = `/table/history?date=${prevDate.toISOString().split('T')[0]}`;
                prevLink.textContent = `← ${formatDate(prevDate.toISOString().split('T')[0])}`;
                prevLink.style.display = 'inline-block';
            } else {
                prevLink.style.display = 'none';
            }
            
            // Show next if not today
            if (daysBack > 0) {
                nextLink.href = `/table/history?date=${nextDate.toISOString().split('T')[0]}`;
                nextLink.textContent = `${formatDate(nextDate.toISOString().split('T')[0])} →`;
                nextLink.style.display = 'inline-block';
            } else {
                nextLink.style.display = 'none';
            }
            
            // Render responses
            const container = document.getElementById('responses-container');
            
            if (!data.responses || data.responses.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🤷</div>
                        <p>No one answered this question</p>
                    </div>
                `;
                return;
            }
            
            const responsesHTML = data.responses.map(r => {
                const isCurrentUser = data.user_response && r.user_id === data.user_response.user_id;
                const pillClass = getUserPillClass(r.user_id);
                const editedLabel = r.edited_at ? ' <span style="font-size: 0.75rem; opacity: 0.7;">(edited)</span>' : '';
                
                return `
                    <div class="response-card">
                        <div class="response-header">
                            ${isCurrentUser 
                                ? `<span class="response-author you">You</span>`
                                : `<span class="response-author pill ${pillClass}">${escapeHtml(r.display_name)}</span>`
                            }
                            <span class="response-time">${formatTimeAgo(r.created_at)}${editedLabel}</span>
                        </div>
                        <p class="response-text">${escapeHtml(r.response_text)}</p>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = responsesHTML;
        } catch (error) {
            console.error('Error loading history prompt:', error);
            const container = document.getElementById('responses-container');
            container.innerHTML = `
                <div class="empty-state">
                    <p>No prompt available for this date</p>
                </div>
            `;
        }
    }
    
    loadHistoryPrompt();
}

// Settings Page
if (window.location.pathname === '/table/settings') {
    async function loadSettings() {
        try {
            const data = await API.call('/api/table/info');
            
            // Update profile info
            document.getElementById('display_name').value = data.user.display_name || data.user.username;
            document.getElementById('username-display').textContent = data.user.username;
            
            // Update table info (visible to all members)
            document.getElementById('table-name-display').textContent = data.table.name;
            document.getElementById('invite-code-display').textContent = data.table.invite_code;
            
            // Format and display prompt time for all members
            const promptTimeFormatted = formatPromptTime(data.table.prompt_time);
            document.getElementById('prompt-time-display').textContent = promptTimeFormatted;
            
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

    // Leave table modal
    const leaveTableBtn = document.getElementById('leave-table-btn');
    const leaveModal = document.getElementById('leave-modal');
    const cancelLeaveBtn = document.getElementById('cancel-leave-btn');
    const confirmLeaveBtn = document.getElementById('confirm-leave-btn');
    
    if (leaveTableBtn) {
        leaveTableBtn.addEventListener('click', () => {
            leaveModal.style.display = 'flex';
        });
    }
    
    if (cancelLeaveBtn) {
        cancelLeaveBtn.addEventListener('click', () => {
            leaveModal.style.display = 'none';
        });
    }
    
    if (confirmLeaveBtn) {
        confirmLeaveBtn.addEventListener('click', async () => {
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
                leaveModal.style.display = 'none';
                alert(error.message);
            }
        });
    }

    // Delete account modal
    const deleteAccountBtn = document.getElementById('delete-account-btn');
    const deleteModal = document.getElementById('delete-modal');
    const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
    const deleteConfirmForm = document.getElementById('delete-confirm-form');
    
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', () => {
            deleteModal.style.display = 'flex';
            document.getElementById('delete-password').value = '';
            const deleteError = document.getElementById('delete-error');
            if (deleteError) deleteError.classList.remove('show');
        });
    }
    
    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', () => {
            deleteModal.style.display = 'none';
        });
    }
    
    if (deleteConfirmForm) {
        deleteConfirmForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const password = document.getElementById('delete-password').value;
            
            if (!password) {
                showError('delete-error', 'Please enter your password');
                return;
            }
            
            try {
                const submitBtn = deleteConfirmForm.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.textContent = 'Deleting...';
                
                const response = await API.call('/api/user/delete', {
                    method: 'POST',
                    body: JSON.stringify({ password })
                });
                
                if (response.redirect) {
                    window.location.href = response.redirect;
                }
            } catch (error) {
                const submitBtn = deleteConfirmForm.querySelector('button[type="submit"]');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Yes, Delete My Account';
                showError('delete-error', error.message);
            }
        });
    }
    
    // Profile form
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(profileForm);
            const data = Object.fromEntries(formData);
            
            try {
                const submitBtn = profileForm.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.textContent = 'Saving...';
                
                await API.call('/api/user/profile', {
                    method: 'PUT',
                    body: JSON.stringify({
                        display_name: data.display_name
                    })
                });
                
                showSuccess('profile-message', 'Display name updated successfully!');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Display Name';
                
                // Reload settings to show updated info
                await loadSettings();
            } catch (error) {
                const submitBtn = profileForm.querySelector('button[type="submit"]');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Display Name';
                showError('profile-error', error.message);
            }
        });
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
    
    // Settings form (owner only)
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
                const submitBtn = settingsForm.querySelector('button[type="submit"]');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Changes';
                showError('settings-error', error.message);
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
                <button class="table-switcher-trigger" id="table-switcher-btn">
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
    window.location.pathname === '/table/history' ||
    window.location.pathname === '/table/yesterday' || 
    window.location.pathname === '/table/settings') {
    document.addEventListener('DOMContentLoaded', () => {
        new TableSwitcher();
    });
}
