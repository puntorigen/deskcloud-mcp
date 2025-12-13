/**
 * API Client
 * ==========
 * 
 * Handles all HTTP communication with the FastAPI backend.
 * Provides typed methods for each API endpoint with error handling.
 */

class ApiClient {
    /**
     * Create an API client instance.
     * @param {string} baseUrl - Base URL for API requests (e.g., '/api/v1')
     */
    constructor(baseUrl = '/api/v1') {
        this.baseUrl = baseUrl;
    }

    // =========================================================================
    // HTTP Helpers
    // =========================================================================

    /**
     * Make an HTTP request with JSON handling.
     * @param {string} endpoint - API endpoint path
     * @param {RequestInit} options - Fetch options
     * @returns {Promise<any>} Parsed JSON response
     * @throws {ApiError} On non-2xx responses
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const response = await fetch(url, {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers,
            },
        });

        // Handle non-JSON responses (like 204 No Content)
        if (response.status === 204) {
            return null;
        }

        // Parse JSON response
        let data;
        try {
            data = await response.json();
        } catch (e) {
            data = null;
        }

        // Handle errors
        if (!response.ok) {
            const error = new ApiError(
                data?.detail || data?.error || `HTTP ${response.status}`,
                response.status,
                data
            );
            throw error;
        }

        return data;
    }

    // =========================================================================
    // Session Endpoints
    // =========================================================================

    /**
     * Create a new chat session.
     * @param {Object} params - Session parameters
     * @param {string} [params.title] - Session title
     * @param {string} [params.model] - Claude model to use
     * @param {string} [params.provider] - API provider
     * @param {string} [params.system_prompt_suffix] - Custom instructions
     * @returns {Promise<Session>} Created session
     */
    async createSession({ title, model, provider, system_prompt_suffix } = {}) {
        return this.request('/sessions', {
            method: 'POST',
            body: JSON.stringify({
                title,
                model,
                provider,
                system_prompt_suffix,
            }),
        });
    }

    /**
     * List all sessions.
     * @param {Object} params - Query parameters
     * @param {boolean} [params.include_archived=false] - Include archived sessions
     * @param {number} [params.limit=50] - Maximum results
     * @param {number} [params.offset=0] - Results offset
     * @returns {Promise<SessionList>} Session list with total count
     */
    async listSessions({ include_archived = false, limit = 50, offset = 0 } = {}) {
        const params = new URLSearchParams({
            include_archived: String(include_archived),
            limit: String(limit),
            offset: String(offset),
        });
        return this.request(`/sessions?${params}`);
    }

    /**
     * Get a session with its message history.
     * @param {string} sessionId - Session ID
     * @returns {Promise<SessionWithMessages>} Session with messages
     */
    async getSession(sessionId) {
        return this.request(`/sessions/${sessionId}`);
    }

    /**
     * Delete (archive) a session.
     * @param {string} sessionId - Session ID
     * @returns {Promise<void>}
     */
    async deleteSession(sessionId) {
        return this.request(`/sessions/${sessionId}`, {
            method: 'DELETE',
        });
    }

    // =========================================================================
    // Message Endpoints
    // =========================================================================

    /**
     * Send a message to a session.
     * @param {string} sessionId - Session ID
     * @param {string} content - Message content
     * @returns {Promise<MessageSendResponse>} Response with stream URL
     */
    async sendMessage(sessionId, content) {
        return this.request(`/sessions/${sessionId}/messages`, {
            method: 'POST',
            body: JSON.stringify({ content }),
        });
    }

    /**
     * Cancel ongoing processing for a session.
     * @param {string} sessionId - Session ID
     * @returns {Promise<Object>} Cancellation status
     */
    async cancelProcessing(sessionId) {
        return this.request(`/sessions/${sessionId}/cancel`, {
            method: 'POST',
        });
    }

    // =========================================================================
    // Health Endpoints
    // =========================================================================

    /**
     * Check API health status.
     * @returns {Promise<HealthResponse>} Health check response
     */
    async healthCheck() {
        return this.request('/health');
    }

    /**
     * Get API configuration.
     * @returns {Promise<ConfigResponse>} Configuration info
     */
    async getConfig() {
        return this.request('/config');
    }

    // =========================================================================
    // Utility Methods
    // =========================================================================

    /**
     * Get the SSE stream URL for a session.
     * @param {string} sessionId - Session ID
     * @returns {string} Full URL for EventSource
     */
    getStreamUrl(sessionId) {
        return `${this.baseUrl}/sessions/${sessionId}/stream`;
    }
}

/**
 * Custom error class for API errors.
 */
class ApiError extends Error {
    /**
     * @param {string} message - Error message
     * @param {number} status - HTTP status code
     * @param {Object} data - Response data
     */
    constructor(message, status, data = null) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
    }

    /**
     * Check if this is a client error (4xx).
     */
    get isClientError() {
        return this.status >= 400 && this.status < 500;
    }

    /**
     * Check if this is a server error (5xx).
     */
    get isServerError() {
        return this.status >= 500;
    }

    /**
     * Check if this is a rate limit error.
     */
    get isRateLimited() {
        return this.status === 429;
    }

    /**
     * Check if this is a not found error.
     */
    get isNotFound() {
        return this.status === 404;
    }
}

// Export for module usage (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApiClient, ApiError };
}

