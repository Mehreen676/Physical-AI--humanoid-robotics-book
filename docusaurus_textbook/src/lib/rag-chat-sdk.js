/**
 * RAG Chatbot JavaScript SDK
 * Lightweight, framework-agnostic SDK for integrating RAG chatbot into web applications
 */

export class RagChatSDK {
  /**
   * Initialize RagChatSDK with configuration
   * @param {string} apiUrl - Backend API URL (e.g., 'http://localhost:8000')
   * @param {object} options - Configuration options
   */
  constructor(apiUrl, options = {}) {
    this.apiUrl = apiUrl;
    this.retryAttempts = options.retryAttempts || 3;
    this.retryDelay = options.retryDelay || 1000; // milliseconds
    this.timeoutMs = options.timeoutMs || 30000;

    // Session management
    this.sessionId = this._getOrCreateSessionId();
    this.bookVersion = options.bookVersion || 'v1.0';
  }

  /**
   * Get session ID (from localStorage or create new)
   * @private
   */
  _getOrCreateSessionId() {
    const storageKey = 'rag_session_id';
    let sessionId = localStorage.getItem(storageKey);

    if (!sessionId) {
      sessionId = this._generateUUID();
      localStorage.setItem(storageKey, sessionId);
    }

    return sessionId;
  }

  /**
   * Generate UUID v4
   * @private
   */
  _generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  /**
   * Get current session ID
   */
  getSessionId() {
    return this.sessionId;
  }

  /**
   * Validate input text
   * @private
   * @param {string} text - Text to validate
   * @param {number} maxLength - Maximum allowed length
   * @returns {object} {valid: boolean, message: string, truncated: boolean}
   */
  _validateInput(text, maxLength = 500) {
    if (!text || text.trim().length === 0) {
      return {
        valid: false,
        message: 'Input cannot be empty',
        truncated: false,
      };
    }

    if (text.length > maxLength) {
      return {
        valid: true,
        message: `Input truncated to ${maxLength} characters`,
        truncated: true,
        text: text.substring(0, maxLength),
      };
    }

    return {
      valid: true,
      truncated: false,
      text: text,
    };
  }

  /**
   * Sanitize input to prevent XSS
   * @private
   */
  _sanitizeInput(text) {
    if (!text) return '';

    // Remove HTML tags
    let sanitized = text.replace(/<[^>]*>/g, '');

    // Remove script-like patterns
    sanitized = sanitized.replace(/javascript:/gi, '');
    sanitized = sanitized.replace(/on\w+\s*=/gi, '');

    // Trim whitespace
    sanitized = sanitized.trim();

    return sanitized;
  }

  /**
   * Make HTTP request with retry logic
   * @private
   */
  async _makeRequest(endpoint, method = 'POST', body = null, retryCount = 0) {
    try {
      const options = {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: this.timeoutMs,
      };

      if (body) {
        options.body = JSON.stringify(body);
      }

      const response = await fetch(`${this.apiUrl}${endpoint}`, options);

      // Handle rate limiting with Retry-After header
      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After') || '60';
        const waitTime = parseInt(retryAfter) * 1000;
        throw new Error(`Rate limited. Retry after ${retryAfter}s`);
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: `HTTP ${response.status}`,
        }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Retry logic with exponential backoff
      if (retryCount < this.retryAttempts) {
        const delay = this.retryDelay * Math.pow(2, retryCount);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this._makeRequest(endpoint, method, body, retryCount + 1);
      }

      throw error;
    }
  }

  /**
   * Query the knowledge base (full-book mode)
   * @param {string} query - User question
   * @param {object} options - Query options
   * @returns {Promise<object>} Query response
   */
  async query(query, options = {}) {
    // Validate query
    const validation = this._validateInput(query, 500);
    if (!validation.valid) {
      throw new Error(validation.message);
    }

    const sanitizedQuery = this._sanitizeInput(validation.text || query);

    try {
      const response = await this._makeRequest('/query', 'POST', {
        query: sanitizedQuery,
        session_id: this.sessionId,
        book_version: options.bookVersion || this.bookVersion,
        mode: 'full_book',
        top_k: options.topK || 5,
        chapter_filter: options.chapterFilter || null,
      });

      return response;
    } catch (error) {
      throw new Error(`Query failed: ${error.message}`);
    }
  }

  /**
   * Query using selected text (selected-text mode)
   * @param {string} query - User question
   * @param {string} selectedText - User-highlighted text
   * @param {object} options - Query options
   * @returns {Promise<object>} Query response
   */
  async querySelectedText(query, selectedText, options = {}) {
    // Validate query
    const queryValidation = this._validateInput(query, 500);
    if (!queryValidation.valid) {
      throw new Error(queryValidation.message);
    }

    // Validate selected text
    const textValidation = this._validateInput(selectedText, 10000);
    if (!textValidation.valid) {
      throw new Error('Selected text cannot be empty');
    }

    const sanitizedQuery = this._sanitizeInput(queryValidation.text || query);
    const sanitizedText = this._sanitizeInput(textValidation.text || selectedText);

    if (textValidation.truncated) {
      console.warn('Selected text truncated to 10,000 characters');
    }

    try {
      const response = await this._makeRequest('/query-selected-text', 'POST', {
        query: sanitizedQuery,
        selected_text: sanitizedText,
        session_id: this.sessionId,
        book_version: options.bookVersion || this.bookVersion,
        mode: 'selected_text',
      });

      return response;
    } catch (error) {
      throw new Error(`Selected-text query failed: ${error.message}`);
    }
  }

  /**
   * Get session history (stub for Phase 3)
   * @param {string} sessionId - Session ID (defaults to current)
   * @returns {Promise<object>} Session history
   */
  async getSessionHistory(sessionId = null) {
    // Phase 3: Implement full history retrieval from backend
    // For now, return cached messages from localStorage
    const cacheKey = `rag_messages_${sessionId || this.sessionId}`;
    const cached = localStorage.getItem(cacheKey);

    return {
      session_id: sessionId || this.sessionId,
      messages: cached ? JSON.parse(cached) : [],
    };
  }

  /**
   * Clear session data (logout)
   */
  clearSession() {
    const sessionId = this.sessionId;
    localStorage.removeItem('rag_session_id');
    localStorage.removeItem(`rag_messages_${sessionId}`);
    this.sessionId = this._getOrCreateSessionId();
  }

  /**
   * Cache message locally (for session persistence)
   * @private
   */
  _cacheMessage(role, content, sources = []) {
    const cacheKey = `rag_messages_${this.sessionId}`;
    const messages = this._getCachedMessages();

    messages.push({
      role,
      content,
      sources,
      timestamp: new Date().toISOString(),
    });

    localStorage.setItem(cacheKey, JSON.stringify(messages));
  }

  /**
   * Get cached messages
   * @private
   */
  _getCachedMessages() {
    const cacheKey = `rag_messages_${this.sessionId}`;
    const cached = localStorage.getItem(cacheKey);
    return cached ? JSON.parse(cached) : [];
  }

  /**
   * Get cached messages
   */
  getCachedMessages() {
    return this._getCachedMessages();
  }
}

export default RagChatSDK;
