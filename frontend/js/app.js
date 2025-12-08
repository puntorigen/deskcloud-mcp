/**
 * Claude Computer Use - Main Application
 * =======================================
 * 
 * Orchestrates the UI, API calls, and SSE streaming.
 * Provides a reactive interface for session management and chat.
 */

class ComputerUseApp {
    constructor() {
        // API client for backend communication
        this.api = new ApiClient('/api/v1');
        
        // SSE client for real-time updates
        this.sse = new SSEClient({
            onText: (data) => this.handleTextEvent(data),
            onThinking: (data) => this.handleThinkingEvent(data),
            onToolUse: (data) => this.handleToolUseEvent(data),
            onToolResult: (data) => this.handleToolResultEvent(data),
            onComplete: (data) => this.handleCompleteEvent(data),
            onError: (data) => this.handleErrorEvent(data),
            onStatus: (data) => this.handleStatusEvent(data),
        });
        
        // Application state
        this.currentSessionId = null;
        this.sessions = [];
        this.isProcessing = false;
        this.config = null;
        
        // Initialize when DOM is ready
        this.init();
    }

    // =========================================================================
    // Initialization
    // =========================================================================

    async init() {
        // Cache DOM elements
        this.cacheElements();
        
        // Bind event handlers
        this.bindEvents();
        
        // Load initial data
        await this.loadConfig();
        await this.loadSessions();
        
        // Update connection status
        this.updateConnectionStatus('connected');
    }

    /**
     * Cache frequently accessed DOM elements.
     */
    cacheElements() {
        // Header
        this.connectionStatus = document.getElementById('connection-status');
        this.newSessionBtn = document.getElementById('new-session-btn');
        
        // Session panel
        this.sessionList = document.getElementById('session-list');
        this.refreshSessionsBtn = document.getElementById('refresh-sessions-btn');
        
        // VNC panel
        this.vncIframe = document.getElementById('vnc-iframe');
        this.vncPlaceholder = document.getElementById('vnc-placeholder');
        this.vncFullscreenBtn = document.getElementById('vnc-fullscreen-btn');
        
        // Chat panel
        this.sessionStatus = document.getElementById('session-status');
        this.messagesContainer = document.getElementById('messages-container');
        this.messages = document.getElementById('messages');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        
        // Modal
        this.modal = document.getElementById('new-session-modal');
        this.modalForm = document.getElementById('new-session-form');
        this.sessionTitleInput = document.getElementById('session-title');
        this.sessionModelSelect = document.getElementById('session-model');
        this.systemPromptInput = document.getElementById('system-prompt');
        
        // Toast container
        this.toastContainer = document.getElementById('toast-container');
    }

    /**
     * Bind event handlers to DOM elements.
     */
    bindEvents() {
        // New session button
        this.newSessionBtn.addEventListener('click', () => this.openModal());
        
        // Refresh sessions
        this.refreshSessionsBtn.addEventListener('click', () => this.loadSessions());
        
        // Modal events
        this.modal.querySelector('.modal__backdrop').addEventListener('click', () => this.closeModal());
        this.modal.querySelector('.modal__close').addEventListener('click', () => this.closeModal());
        this.modal.querySelector('.modal__cancel').addEventListener('click', () => this.closeModal());
        this.modalForm.addEventListener('submit', (e) => this.handleCreateSession(e));
        
        // Message input
        this.messageInput.addEventListener('keydown', (e) => this.handleInputKeydown(e));
        this.messageInput.addEventListener('input', () => this.autoResizeInput());
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // VNC fullscreen
        this.vncFullscreenBtn.addEventListener('click', () => this.toggleVncFullscreen());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleGlobalKeydown(e));
    }

    // =========================================================================
    // Data Loading
    // =========================================================================

    /**
     * Load API configuration.
     */
    async loadConfig() {
        try {
            this.config = await this.api.getConfig();
        } catch (error) {
            console.error('Failed to load config:', error);
            this.showToast('Failed to load configuration', 'error');
        }
    }

    /**
     * Load all sessions from the API.
     */
    async loadSessions() {
        try {
            const response = await this.api.listSessions();
            this.sessions = response.sessions;
            this.renderSessionList();
        } catch (error) {
            console.error('Failed to load sessions:', error);
            this.showToast('Failed to load sessions', 'error');
        }
    }

    /**
     * Load a specific session and its messages.
     * @param {string} sessionId - Session ID to load
     */
    async loadSession(sessionId) {
        try {
            const session = await this.api.getSession(sessionId);
            this.currentSessionId = sessionId;
            
            // Update UI
            this.renderSessionList();
            this.renderMessages(session.messages);
            this.updateSessionStatus(session.status);
            this.enableInput(session.status !== 'processing');
            
            // Load VNC
            this.loadVnc(session.vnc_url);
            
        } catch (error) {
            console.error('Failed to load session:', error);
            this.showToast('Failed to load session', 'error');
        }
    }

    // =========================================================================
    // Session Management
    // =========================================================================

    /**
     * Create a new session.
     * @param {Event} e - Form submit event
     */
    async handleCreateSession(e) {
        e.preventDefault();
        
        const title = this.sessionTitleInput.value.trim();
        const model = this.sessionModelSelect.value;
        const systemPrompt = this.systemPromptInput.value.trim();
        
        try {
            const session = await this.api.createSession({
                title: title || undefined,
                model,
                system_prompt_suffix: systemPrompt || undefined,
            });
            
            this.closeModal();
            this.showToast('Session created successfully', 'success');
            
            // Add to list and load it
            this.sessions.unshift(session);
            await this.loadSession(session.id);
            
        } catch (error) {
            console.error('Failed to create session:', error);
            this.showToast(error.message || 'Failed to create session', 'error');
        }
    }

    /**
     * Delete a session.
     * @param {string} sessionId - Session ID to delete
     */
    async deleteSession(sessionId) {
        if (!confirm('Are you sure you want to delete this session?')) {
            return;
        }
        
        try {
            await this.api.deleteSession(sessionId);
            
            // Remove from list
            this.sessions = this.sessions.filter(s => s.id !== sessionId);
            this.renderSessionList();
            
            // Clear current session if it was deleted
            if (this.currentSessionId === sessionId) {
                this.currentSessionId = null;
                this.clearMessages();
                this.hideVnc();
                this.disableInput();
            }
            
            this.showToast('Session deleted', 'success');
            
        } catch (error) {
            console.error('Failed to delete session:', error);
            this.showToast('Failed to delete session', 'error');
        }
    }

    // =========================================================================
    // Message Handling
    // =========================================================================

    /**
     * Send a message to the current session.
     */
    async sendMessage() {
        const content = this.messageInput.value.trim();
        if (!content || !this.currentSessionId || this.isProcessing) {
            return;
        }
        
        // Clear input and disable
        this.messageInput.value = '';
        this.autoResizeInput();
        this.setProcessing(true);
        
        // Add user message to UI immediately
        this.appendMessage({
            role: 'user',
            content,
            timestamp: new Date().toISOString(),
        });
        
        try {
            // Send to API
            const response = await this.api.sendMessage(this.currentSessionId, content);
            
            // Connect to SSE stream
            const streamUrl = this.api.getStreamUrl(this.currentSessionId);
            this.sse.connect(streamUrl, this.currentSessionId);
            
        } catch (error) {
            console.error('Failed to send message:', error);
            this.showToast(error.message || 'Failed to send message', 'error');
            this.setProcessing(false);
        }
    }

    /**
     * Handle keyboard input in message textarea.
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleInputKeydown(e) {
        // Enter to send (without shift)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    /**
     * Auto-resize textarea based on content.
     */
    autoResizeInput() {
        const textarea = this.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    // =========================================================================
    // SSE Event Handlers
    // =========================================================================

    handleTextEvent(data) {
        this.appendMessage({
            role: 'assistant',
            content: data.content,
            timestamp: data.timestamp,
        });
    }

    handleThinkingEvent(data) {
        this.appendMessage({
            role: 'thinking',
            content: data.content,
            timestamp: data.timestamp,
        });
    }

    handleToolUseEvent(data) {
        this.appendMessage({
            role: 'tool',
            content: `Using tool: ${data.tool}\nInput: ${JSON.stringify(data.input, null, 2)}`,
            timestamp: data.timestamp,
            toolUseId: data.tool_use_id,
        });
    }

    handleToolResultEvent(data) {
        const content = data.error 
            ? `Error: ${data.error}`
            : data.output || 'Tool executed successfully';
            
        this.appendMessage({
            role: 'tool',
            content,
            timestamp: data.timestamp,
            screenshot: data.screenshot,
        });
    }

    handleCompleteEvent(data) {
        this.setProcessing(false);
        this.updateSessionStatus('active');
        
        // Refresh session to get persisted messages
        setTimeout(() => this.loadSessions(), 1000);
    }

    handleErrorEvent(data) {
        this.showToast(data.error || 'An error occurred', 'error');
        
        if (data.code === 'NO_ACTIVITY') {
            // Not an error, just no active processing
            return;
        }
        
        this.setProcessing(false);
    }

    handleStatusEvent(data) {
        if (data.status === 'processing') {
            this.updateSessionStatus('processing');
        } else if (data.status === 'connected') {
            this.updateConnectionStatus('connected');
        } else if (data.status === 'error') {
            this.updateConnectionStatus('disconnected');
        }
    }

    // =========================================================================
    // UI Rendering
    // =========================================================================

    /**
     * Render the session list.
     */
    renderSessionList() {
        if (this.sessions.length === 0) {
            this.sessionList.innerHTML = `
                <div class="session-list__empty">
                    <p>No sessions yet</p>
                    <p class="text-muted">Create a new session to get started</p>
                </div>
            `;
            return;
        }
        
        this.sessionList.innerHTML = this.sessions.map(session => `
            <div class="session-item ${session.id === this.currentSessionId ? 'session-item--active' : ''}"
                 data-session-id="${session.id}">
                <div class="session-item__title">${this.escapeHtml(session.title || 'Untitled Session')}</div>
                <div class="session-item__meta">
                    <span class="session-item__status session-item__status--${session.status}">
                        ${session.status}
                    </span>
                    <span>${this.formatDate(session.created_at)}</span>
                </div>
            </div>
        `).join('');
        
        // Bind click handlers
        this.sessionList.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', () => {
                const sessionId = item.dataset.sessionId;
                this.loadSession(sessionId);
            });
        });
    }

    /**
     * Render messages in the chat panel.
     * @param {Array} messages - Messages to render
     */
    renderMessages(messages) {
        if (!messages || messages.length === 0) {
            this.messages.innerHTML = `
                <div class="messages__empty">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                    <p>No messages yet</p>
                    <p class="text-muted">Send a message to start the conversation</p>
                </div>
            `;
            return;
        }
        
        this.messages.innerHTML = '';
        messages.forEach(msg => this.appendMessage(msg, false));
        this.scrollToBottom();
    }

    /**
     * Append a message to the chat.
     * @param {Object} message - Message object
     * @param {boolean} scroll - Whether to scroll to bottom
     */
    appendMessage(message, scroll = true) {
        // Remove empty state if present
        const emptyState = this.messages.querySelector('.messages__empty');
        if (emptyState) {
            emptyState.remove();
        }
        
        const role = message.role || 'assistant';
        const content = typeof message.content === 'string' 
            ? message.content 
            : this.formatContent(message.content);
        
        const messageHtml = `
            <div class="message message--${role}">
                <div class="message__header">
                    <span class="message__role">${this.getRoleLabel(role)}</span>
                    <span class="message__time">${this.formatTime(message.timestamp || message.created_at)}</span>
                </div>
                <div class="message__content">${this.escapeHtml(content)}</div>
                ${message.screenshot ? `
                    <div class="message__screenshot">
                        <img src="data:image/png;base64,${message.screenshot}" alt="Screenshot">
                    </div>
                ` : ''}
            </div>
        `;
        
        this.messages.insertAdjacentHTML('beforeend', messageHtml);
        
        if (scroll) {
            this.scrollToBottom();
        }
    }

    /**
     * Clear all messages.
     */
    clearMessages() {
        this.messages.innerHTML = `
            <div class="messages__empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                <p>Select a session to view messages</p>
                <p class="text-muted">Or create a new session to start chatting</p>
            </div>
        `;
    }

    /**
     * Scroll messages container to bottom.
     */
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    // =========================================================================
    // VNC Handling
    // =========================================================================

    /**
     * Load VNC viewer.
     * @param {string} vncUrl - VNC URL from session
     */
    loadVnc(vncUrl) {
        if (vncUrl) {
            this.vncIframe.src = vncUrl;
            this.vncPlaceholder.classList.add('hidden');
        }
    }

    /**
     * Hide VNC viewer.
     */
    hideVnc() {
        this.vncIframe.src = 'about:blank';
        this.vncPlaceholder.classList.remove('hidden');
    }

    /**
     * Toggle VNC fullscreen.
     */
    toggleVncFullscreen() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            this.vncIframe.requestFullscreen();
        }
    }

    // =========================================================================
    // UI State
    // =========================================================================

    /**
     * Update connection status badge.
     * @param {string} status - 'connected' | 'disconnected' | 'processing'
     */
    updateConnectionStatus(status) {
        this.connectionStatus.className = `status-badge status-badge--${status}`;
        this.connectionStatus.querySelector('.status-badge__text').textContent = 
            status.charAt(0).toUpperCase() + status.slice(1);
    }

    /**
     * Update session status display.
     * @param {string} status - Session status
     */
    updateSessionStatus(status) {
        this.sessionStatus.textContent = status;
        this.sessionStatus.className = `session-status session-status--${status}`;
    }

    /**
     * Set processing state.
     * @param {boolean} processing - Whether currently processing
     */
    setProcessing(processing) {
        this.isProcessing = processing;
        this.enableInput(!processing);
        this.updateConnectionStatus(processing ? 'processing' : 'connected');
    }

    /**
     * Enable message input.
     * @param {boolean} enabled - Whether to enable
     */
    enableInput(enabled = true) {
        this.messageInput.disabled = !enabled;
        this.sendBtn.disabled = !enabled;
        
        if (enabled) {
            this.messageInput.focus();
        }
    }

    /**
     * Disable message input.
     */
    disableInput() {
        this.enableInput(false);
    }

    // =========================================================================
    // Modal
    // =========================================================================

    openModal() {
        this.modal.classList.add('active');
        this.sessionTitleInput.value = '';
        this.systemPromptInput.value = '';
        this.sessionTitleInput.focus();
    }

    closeModal() {
        this.modal.classList.remove('active');
    }

    // =========================================================================
    // Toast Notifications
    // =========================================================================

    /**
     * Show a toast notification.
     * @param {string} message - Message to display
     * @param {string} type - 'success' | 'error' | 'warning' | 'info'
     * @param {number} duration - Duration in ms
     */
    showToast(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.className = `toast toast--${type}`;
        toast.textContent = message;
        
        this.toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'toastOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    // =========================================================================
    // Keyboard Shortcuts
    // =========================================================================

    handleGlobalKeydown(e) {
        // Escape to close modal
        if (e.key === 'Escape' && this.modal.classList.contains('active')) {
            this.closeModal();
        }
        
        // Ctrl/Cmd + N for new session
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            this.openModal();
        }
    }

    // =========================================================================
    // Utilities
    // =========================================================================

    /**
     * Escape HTML to prevent XSS.
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Format message content (handles arrays of blocks).
     * @param {any} content - Content to format
     * @returns {string} Formatted string
     */
    formatContent(content) {
        if (typeof content === 'string') {
            return content;
        }
        
        if (Array.isArray(content)) {
            return content.map(block => {
                if (typeof block === 'string') return block;
                if (block.type === 'text') return block.text;
                if (block.type === 'tool_use') return `[Tool: ${block.name}]`;
                if (block.type === 'tool_result') return block.content || '[Tool result]';
                return JSON.stringify(block);
            }).join('\n');
        }
        
        return JSON.stringify(content, null, 2);
    }

    /**
     * Get display label for message role.
     * @param {string} role - Message role
     * @returns {string} Display label
     */
    getRoleLabel(role) {
        const labels = {
            user: 'You',
            assistant: 'Claude',
            tool: 'Tool',
            thinking: 'Thinking',
        };
        return labels[role] || role;
    }

    /**
     * Format date for display.
     * @param {string} dateStr - ISO date string
     * @returns {string} Formatted date
     */
    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString(undefined, { 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    }

    /**
     * Format time for display.
     * @param {string} dateStr - ISO date string
     * @returns {string} Formatted time
     */
    formatTime(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleTimeString(undefined, {
            hour: '2-digit',
            minute: '2-digit',
        });
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ComputerUseApp();
});

