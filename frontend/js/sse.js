/**
 * SSE Client
 * ==========
 * 
 * Handles Server-Sent Events connection for real-time agent updates.
 * Provides event-based interface with automatic reconnection handling.
 */

class SSEClient {
    /**
     * Create an SSE client instance.
     * @param {Object} options - Configuration options
     * @param {Function} [options.onText] - Handler for text events
     * @param {Function} [options.onThinking] - Handler for thinking events
     * @param {Function} [options.onToolUse] - Handler for tool use events
     * @param {Function} [options.onToolResult] - Handler for tool result events
     * @param {Function} [options.onComplete] - Handler for completion events
     * @param {Function} [options.onError] - Handler for error events
     * @param {Function} [options.onStatus] - Handler for status changes
     */
    constructor(options = {}) {
        this.options = options;
        this.eventSource = null;
        this.isConnected = false;
        this.sessionId = null;
    }

    // =========================================================================
    // Connection Management
    // =========================================================================

    /**
     * Connect to SSE stream for a session.
     * @param {string} url - SSE endpoint URL
     * @param {string} sessionId - Session ID for tracking
     */
    connect(url, sessionId) {
        // Close existing connection if any
        this.disconnect();

        this.sessionId = sessionId;
        this.eventSource = new EventSource(url);

        // Connection lifecycle events
        this.eventSource.onopen = () => {
            this.isConnected = true;
            this._emit('onStatus', { status: 'connected', sessionId });
        };

        this.eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            this.isConnected = false;
            this._emit('onStatus', { status: 'error', sessionId, error });
            
            // EventSource will auto-reconnect, but if it's in CLOSED state,
            // we need to handle it
            if (this.eventSource.readyState === EventSource.CLOSED) {
                this._emit('onError', { 
                    error: 'Connection closed', 
                    code: 'CONNECTION_CLOSED' 
                });
            }
        };

        // Register event handlers
        this._registerEventHandlers();
    }

    /**
     * Disconnect from SSE stream.
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.isConnected = false;
        this.sessionId = null;
    }

    // =========================================================================
    // Event Handlers
    // =========================================================================

    /**
     * Register handlers for all SSE event types.
     * @private
     */
    _registerEventHandlers() {
        if (!this.eventSource) return;

        // Text content from Claude
        this.eventSource.addEventListener('text', (e) => {
            try {
                const data = JSON.parse(e.data);
                this._emit('onText', data);
            } catch (err) {
                console.error('Error parsing text event:', err);
            }
        });

        // Thinking/reasoning content
        this.eventSource.addEventListener('thinking', (e) => {
            try {
                const data = JSON.parse(e.data);
                this._emit('onThinking', data);
            } catch (err) {
                console.error('Error parsing thinking event:', err);
            }
        });

        // Tool invocation
        this.eventSource.addEventListener('tool_use', (e) => {
            try {
                const data = JSON.parse(e.data);
                this._emit('onToolUse', data);
            } catch (err) {
                console.error('Error parsing tool_use event:', err);
            }
        });

        // Tool execution result
        this.eventSource.addEventListener('tool_result', (e) => {
            try {
                const data = JSON.parse(e.data);
                this._emit('onToolResult', data);
            } catch (err) {
                console.error('Error parsing tool_result event:', err);
            }
        });

        // Message completion
        this.eventSource.addEventListener('message_complete', (e) => {
            try {
                const data = JSON.parse(e.data);
                this._emit('onComplete', data);
                // Auto-disconnect on completion
                this.disconnect();
            } catch (err) {
                console.error('Error parsing message_complete event:', err);
            }
        });

        // Error events
        this.eventSource.addEventListener('error', (e) => {
            // Note: This is the 'error' event type from server, not connection error
            try {
                const data = JSON.parse(e.data);
                this._emit('onError', data);
            } catch (err) {
                // Connection error, not a server-sent error event
                console.error('SSE error event:', err);
            }
        });

        // Status updates
        this.eventSource.addEventListener('status', (e) => {
            try {
                const data = JSON.parse(e.data);
                this._emit('onStatus', data);
            } catch (err) {
                console.error('Error parsing status event:', err);
            }
        });

        // Keepalive (ignore, just maintains connection)
        this.eventSource.addEventListener('keepalive', () => {
            // Keepalive received - connection is healthy
        });

        // Message start
        this.eventSource.addEventListener('message_start', (e) => {
            try {
                const data = JSON.parse(e.data);
                this._emit('onStatus', { status: 'processing', ...data });
            } catch (err) {
                console.error('Error parsing message_start event:', err);
            }
        });
    }

    /**
     * Emit an event to the configured handler.
     * @private
     * @param {string} handlerName - Handler method name
     * @param {Object} data - Event data
     */
    _emit(handlerName, data) {
        const handler = this.options[handlerName];
        if (typeof handler === 'function') {
            try {
                handler(data);
            } catch (err) {
                console.error(`Error in ${handlerName} handler:`, err);
            }
        }
    }

    // =========================================================================
    // Utility Methods
    // =========================================================================

    /**
     * Check if currently connected.
     * @returns {boolean}
     */
    get connected() {
        return this.isConnected && 
               this.eventSource && 
               this.eventSource.readyState === EventSource.OPEN;
    }

    /**
     * Get connection state string.
     * @returns {string} 'connecting' | 'open' | 'closed'
     */
    get state() {
        if (!this.eventSource) return 'closed';
        switch (this.eventSource.readyState) {
            case EventSource.CONNECTING: return 'connecting';
            case EventSource.OPEN: return 'open';
            case EventSource.CLOSED: return 'closed';
            default: return 'unknown';
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SSEClient };
}

