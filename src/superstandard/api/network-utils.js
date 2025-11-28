/**
 * Network Utilities for Robust API Communication
 *
 * Provides:
 * - Automatic retry with exponential backoff
 * - Timeout handling
 * - Connection status checking
 * - Better error messages
 * - CORS handling
 * - Network status detection
 */

class NetworkError extends Error {
    constructor(message, statusCode = null, isTimeout = false, isOffline = false) {
        super(message);
        this.name = 'NetworkError';
        this.statusCode = statusCode;
        this.isTimeout = isTimeout;
        this.isOffline = isOffline;
    }
}

class NetworkUtils {
    constructor(config = {}) {
        this.config = {
            maxRetries: config.maxRetries || 3,
            initialRetryDelay: config.initialRetryDelay || 1000,
            maxRetryDelay: config.maxRetryDelay || 10000,
            timeout: config.timeout || 30000, // 30 seconds default
            retryOn: config.retryOn || [408, 429, 500, 502, 503, 504],
            ...config
        };

        this.isOnline = navigator.onLine;
        this.setupNetworkListeners();
    }

    setupNetworkListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            console.log('[NetworkUtils] Connection restored');
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            console.log('[NetworkUtils] Connection lost');
        });
    }

    /**
     * Check if server is reachable
     */
    async checkServerHealth(baseUrl) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);

            const response = await fetch(`${baseUrl}/api/health`, {
                method: 'GET',
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            clearTimeout(timeoutId);

            return {
                reachable: response.ok,
                status: response.status,
                statusText: response.statusText
            };
        } catch (error) {
            console.error('[NetworkUtils] Server health check failed:', error);
            return {
                reachable: false,
                error: error.message
            };
        }
    }

    /**
     * Sleep for exponential backoff
     */
    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Calculate retry delay with exponential backoff
     */
    getRetryDelay(retryCount) {
        const delay = Math.min(
            this.config.initialRetryDelay * Math.pow(2, retryCount),
            this.config.maxRetryDelay
        );
        // Add jitter to prevent thundering herd
        return delay + Math.random() * 1000;
    }

    /**
     * Determine if error is retryable
     */
    isRetryable(error, statusCode) {
        // Network errors are retryable
        if (error.name === 'TypeError' || error.name === 'NetworkError') {
            return true;
        }

        // Timeout errors are retryable
        if (error.name === 'AbortError') {
            return true;
        }

        // Specific status codes are retryable
        if (statusCode && this.config.retryOn.includes(statusCode)) {
            return true;
        }

        return false;
    }

    /**
     * Enhanced fetch with retry, timeout, and better error handling
     */
    async fetchWithRetry(url, options = {}) {
        // Check if offline first
        if (!this.isOnline) {
            throw new NetworkError(
                'No internet connection. Please check your network and try again.',
                null,
                false,
                true
            );
        }

        const maxRetries = options.maxRetries !== undefined ? options.maxRetries : this.config.maxRetries;
        const timeout = options.timeout || this.config.timeout;

        let lastError;
        let lastStatusCode;

        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                // Create abort controller for timeout
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeout);

                try {
                    const response = await fetch(url, {
                        ...options,
                        signal: controller.signal,
                        headers: {
                            'Content-Type': 'application/json',
                            ...options.headers
                        }
                    });

                    clearTimeout(timeoutId);

                    // Handle HTTP errors
                    if (!response.ok) {
                        lastStatusCode = response.status;

                        // Try to get error message from response
                        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                        try {
                            const errorData = await response.json();
                            if (errorData.message || errorData.error || errorData.detail) {
                                errorMessage = errorData.message || errorData.error || errorData.detail;
                            }
                        } catch (e) {
                            // Couldn't parse error response, use default message
                        }

                        // Check if we should retry
                        if (attempt < maxRetries && this.isRetryable(null, response.status)) {
                            const delay = this.getRetryDelay(attempt);
                            console.log(`[NetworkUtils] Attempt ${attempt + 1} failed with status ${response.status}. Retrying in ${Math.round(delay)}ms...`);
                            await this.sleep(delay);
                            continue;
                        }

                        throw new NetworkError(errorMessage, response.status);
                    }

                    // Success!
                    return response;

                } catch (error) {
                    clearTimeout(timeoutId);

                    // Handle timeout
                    if (error.name === 'AbortError') {
                        lastError = new NetworkError(
                            `Request timed out after ${timeout}ms. The server might be slow or unreachable.`,
                            null,
                            true
                        );
                    } else {
                        lastError = error;
                    }

                    throw lastError;
                }

            } catch (error) {
                lastError = error;

                // Check if we should retry
                if (attempt < maxRetries && this.isRetryable(error, lastStatusCode)) {
                    const delay = this.getRetryDelay(attempt);
                    console.log(`[NetworkUtils] Attempt ${attempt + 1} failed: ${error.message}. Retrying in ${Math.round(delay)}ms...`);
                    await this.sleep(delay);
                    continue;
                }

                // All retries exhausted
                break;
            }
        }

        // Format final error message
        if (lastError) {
            if (lastError instanceof NetworkError) {
                throw lastError;
            }

            // Convert generic errors to NetworkError
            let message = lastError.message || 'Unknown network error';

            // Provide helpful messages for common errors
            if (message.includes('Failed to fetch')) {
                message = 'Cannot connect to server. Please ensure:\n' +
                    '1. The server is running\n' +
                    '2. You have an active internet connection\n' +
                    '3. The server URL is correct\n' +
                    '4. CORS is properly configured';
            }

            throw new NetworkError(
                `Network request failed after ${maxRetries + 1} attempts: ${message}`,
                lastStatusCode
            );
        }

        // This should never happen, but just in case
        throw new NetworkError('Unknown error occurred');
    }

    /**
     * Convenience method for GET requests
     */
    async get(url, options = {}) {
        const response = await this.fetchWithRetry(url, {
            ...options,
            method: 'GET'
        });
        return await response.json();
    }

    /**
     * Convenience method for POST requests
     */
    async post(url, data, options = {}) {
        const response = await this.fetchWithRetry(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        });
        return await response.json();
    }

    /**
     * Convenience method for PUT requests
     */
    async put(url, data, options = {}) {
        const response = await this.fetchWithRetry(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        });
        return await response.json();
    }

    /**
     * Convenience method for DELETE requests
     */
    async delete(url, options = {}) {
        const response = await this.fetchWithRetry(url, {
            ...options,
            method: 'DELETE'
        });
        return await response.json();
    }

    /**
     * Show user-friendly error notification
     */
    showErrorNotification(error, containerId = null) {
        const message = this.formatErrorMessage(error);

        if (containerId) {
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = `
                    <div class="error-notification" style="
                        background: rgba(248, 113, 113, 0.2);
                        border: 2px solid #f87171;
                        padding: 15px;
                        border-radius: 8px;
                        margin-top: 15px;
                        color: white;
                    ">
                        <strong>Error:</strong> ${message}
                    </div>
                `;

                // Auto-dismiss after 10 seconds
                setTimeout(() => {
                    container.innerHTML = '';
                }, 10000);
            }
        } else {
            alert(message);
        }
    }

    /**
     * Format error message for display
     */
    formatErrorMessage(error) {
        if (error instanceof NetworkError) {
            if (error.isOffline) {
                return '❌ You are offline. Please check your internet connection and try again.';
            }

            if (error.isTimeout) {
                return '⏱️ Request timed out. The server is taking too long to respond. Please try again.';
            }

            if (error.statusCode) {
                switch (error.statusCode) {
                    case 400:
                        return '❌ Bad request. Please check your input and try again.';
                    case 401:
                        return '🔒 Unauthorized. Please log in and try again.';
                    case 403:
                        return '🚫 Access denied. You don't have permission for this action.';
                    case 404:
                        return '🔍 Not found. The requested resource doesn't exist.';
                    case 429:
                        return '⏸️ Too many requests. Please wait a moment and try again.';
                    case 500:
                        return '🔥 Server error. The server encountered an error. Please try again later.';
                    case 503:
                        return '⚠️ Service unavailable. The server is temporarily down. Please try again later.';
                    default:
                        return `❌ Error (${error.statusCode}): ${error.message}`;
                }
            }

            return `❌ ${error.message}`;
        }

        return `❌ An unexpected error occurred: ${error.message || 'Unknown error'}`;
    }

    /**
     * Test server connection and provide diagnostics
     */
    async diagnoseConnection(baseUrl) {
        const results = {
            online: this.isOnline,
            serverReachable: false,
            serverUrl: baseUrl,
            issues: [],
            suggestions: []
        };

        if (!this.isOnline) {
            results.issues.push('Device is offline');
            results.suggestions.push('Check your internet connection');
            return results;
        }

        try {
            const health = await this.checkServerHealth(baseUrl);

            if (health.reachable) {
                results.serverReachable = true;
                results.serverStatus = health.status;
            } else {
                results.issues.push('Cannot reach server');
                results.suggestions.push(`Ensure server is running at ${baseUrl}`);
                results.suggestions.push('Check if the port is correct');
                results.suggestions.push('Verify firewall settings');

                if (health.error) {
                    results.error = health.error;

                    if (health.error.includes('CORS')) {
                        results.issues.push('CORS policy blocking request');
                        results.suggestions.push('Configure CORS headers on the server');
                    }
                }
            }
        } catch (error) {
            results.issues.push(`Connection test failed: ${error.message}`);
            results.suggestions.push('Check server logs for more details');
        }

        return results;
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NetworkUtils, NetworkError };
}
