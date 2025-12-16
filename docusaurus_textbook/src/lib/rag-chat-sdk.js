/**
 * RAG Chatbot JavaScript SDK
 * Lightweight, framework-agnostic SDK for integrating RAG chatbot into web applications
 * Enhanced with LocalStorage caching, offline support, and session history
 */

export class RagChatSDK {
  // Cache constants
  static CACHE_PREFIX = 'rag_cache_';
  static SESSION_KEY = 'rag_session_id';
  static SESSIONS_CACHE_KEY = 'rag_sessions_cache';
  static MAX_CACHED_SESSIONS = 10;
  static AUTO_SYNC_TIMEOUT = 5000; // 5 seconds

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

    // Caching
    this._isOnlineCached = true;
    this._syncInProgress = false;

    // Initialize auto-sync
    this._initAutoSync();
  }

  /**
   * Get session ID (from localStorage or create new)
   * @private
   */
  _getOrCreateSessionId() {
    let sessionId = localStorage.getItem(RagChatSDK.SESSION_KEY);

    if (!sessionId) {
      sessionId = this._generateUUID();
      localStorage.setItem(RagChatSDK.SESSION_KEY, sessionId);
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
   * Check if online (navigator.onLine + health check)
   * @private
   */
  async _isOnline() {
    // Quick check using navigator.onLine
    if (!navigator.onLine) {
      this._isOnlineCached = false;
      return false;
    }

    try {
      // Verify backend connectivity
      const response = await fetch(`${this.apiUrl}/health`, {
        method: 'GET',
        timeout: 3000,
      });
      this._isOnlineCached = response.ok;
      return response.ok;
    } catch (error) {
      this._isOnlineCached = false;
      return false;
    }
  }

  /**
   * Initialize auto-sync: sync cache on page load and online event
   * @private
   */
  _initAutoSync() {
    // Sync on page load (only if online)
    if (typeof window !== 'undefined') {
      window.addEventListener('load', () => this._autoSync());
      window.addEventListener('online', () => this._autoSync());
    }
  }

  /**
   * Auto-sync cached sessions with backend
   * @private
   */
  async _autoSync() {
    if (this._syncInProgress) return;

    this._syncInProgress = true;
    try {
      const isOnline = await this._isOnline();
      if (!isOnline) return;

      // Sync current session
      try {
        const session = await this._makeRequest(`/sessions/${this.sessionId}`, 'GET');
        this._updateSessionCache(session);
      } catch (error) {
        console.debug('Auto-sync failed:', error.message);
      }
    } finally {
      this._syncInProgress = false;
    }
  }

  /**
   * Update session cache in localStorage
   * @private
   */
  _updateSessionCache(sessionData) {
    try {
      const cacheKey = `${RagChatSDK.CACHE_PREFIX}${sessionData.session_id}`;
      const cached = {
        ...sessionData,
        lastAccessed: Date.now(),
      };
      localStorage.setItem(cacheKey, JSON.stringify(cached));

      // Update sessions cache (LRU tracking)
      this._updateSessionsCacheIndex(sessionData.session_id);
    } catch (error) {
      if (error.name === 'QuotaExceededError') {
        console.warn('LocalStorage quota exceeded, evicting old sessions');
        this._evictLRUIfNeeded();
        // Retry once
        try {
          const cacheKey = `${RagChatSDK.CACHE_PREFIX}${sessionData.session_id}`;
          const cached = {
            ...sessionData,
            lastAccessed: Date.now(),
          };
          localStorage.setItem(cacheKey, JSON.stringify(cached));
        } catch (retryError) {
          console.error('Failed to cache session after eviction:', retryError);
        }
      }
    }
  }

  /**
   * Get cached session
   * @private
   */
  _getCachedSession(sessionId) {
    try {
      const cacheKey = `${RagChatSDK.CACHE_PREFIX}${sessionId}`;
      const cached = localStorage.getItem(cacheKey);
      return cached ? JSON.parse(cached) : null;
    } catch (error) {
      console.error('Error reading cached session:', error);
      return null;
    }
  }

  /**
   * Update sessions cache index (for LRU tracking)
   * @private
   */
  _updateSessionsCacheIndex(sessionId) {
    try {
      let sessionCache = localStorage.getItem(RagChatSDK.SESSIONS_CACHE_KEY);
      let sessions = sessionCache ? JSON.parse(sessionCache) : [];

      // Remove if already exists
      sessions = sessions.filter(s => s.id !== sessionId);

      // Add to front (most recently used)
      sessions.unshift({
        id: sessionId,
        lastAccessed: Date.now(),
      });

      // Keep only recent sessions
      sessions = sessions.slice(0, RagChatSDK.MAX_CACHED_SESSIONS);

      localStorage.setItem(RagChatSDK.SESSIONS_CACHE_KEY, JSON.stringify(sessions));
    } catch (error) {
      console.error('Error updating sessions cache index:', error);
    }
  }

  /**
   * Evict least recently used (LRU) session if cache exceeds limit
   * @private
   */
  _evictLRUIfNeeded() {
    try {
      let sessionCache = localStorage.getItem(RagChatSDK.SESSIONS_CACHE_KEY);
      let sessions = sessionCache ? JSON.parse(sessionCache) : [];

      // Find least recently used (last in array after sorting)
      if (sessions.length >= RagChatSDK.MAX_CACHED_SESSIONS) {
        // Remove oldest session (except current)
        const toEvict = sessions
          .filter(s => s.id !== this.sessionId)
          .slice(-1)[0];

        if (toEvict) {
          const cacheKey = `${RagChatSDK.CACHE_PREFIX}${toEvict.id}`;
          localStorage.removeItem(cacheKey);
          console.debug(`Evicted LRU session: ${toEvict.id}`);
        }
      }
    } catch (error) {
      console.error('Error evicting LRU session:', error);
    }
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

      // Optimistic caching: cache response
      this._cacheMessage('user', sanitizedQuery, response.sources || []);
      this._cacheMessage('assistant', response.response, response.sources || []);

      // Trigger background sync
      this._autoSync().catch(() => {});

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

      // Optimistic caching: cache response
      this._cacheMessage('user', sanitizedQuery, response.sources || []);
      this._cacheMessage('assistant', response.response, response.sources || []);

      // Trigger background sync
      this._autoSync().catch(() => {});

      return response;
    } catch (error) {
      throw new Error(`Selected-text query failed: ${error.message}`);
    }
  }

  /**
   * Get session history with pagination
   * @param {string} sessionId - Session ID (defaults to current)
   * @param {number} limit - Number of messages (default 50)
   * @param {number} offset - Pagination offset (default 0)
   * @returns {Promise<object>} Session history with messages
   */
  async getSessionHistory(sessionId = null, limit = 50, offset = 0) {
    const targetSessionId = sessionId || this.sessionId;

    try {
      // Try to fetch from backend first
      const isOnline = await this._isOnline();

      if (isOnline) {
        const response = await this._makeRequest(
          `/sessions/${targetSessionId}?limit=${limit}&offset=${offset}`,
          'GET'
        );

        // Cache the session
        this._updateSessionCache(response);

        return response;
      } else {
        // Offline: return cached version
        const cached = this._getCachedSession(targetSessionId);
        if (cached) {
          return {
            ...cached,
            offline: true,
          };
        }

        // No cache available
        return {
          session_id: targetSessionId,
          messages: [],
          offline: true,
          error: 'Offline mode: no cached data available',
        };
      }
    } catch (error) {
      // Fallback to cached version
      const cached = this._getCachedSession(targetSessionId);
      if (cached) {
        return {
          ...cached,
          offline: true,
          error: `Network error: ${error.message}`,
        };
      }

      throw new Error(`Failed to retrieve session history: ${error.message}`);
    }
  }

  /**
   * Clear session data (logout) and clear cache
   */
  clearSession() {
    const sessionId = this.sessionId;

    // Clear localStorage entries for this session
    localStorage.removeItem(RagChatSDK.SESSION_KEY);
    localStorage.removeItem(`${RagChatSDK.CACHE_PREFIX}${sessionId}`);
    localStorage.removeItem(`rag_messages_${sessionId}`);

    // Update sessions cache index
    try {
      let sessionCache = localStorage.getItem(RagChatSDK.SESSIONS_CACHE_KEY);
      let sessions = sessionCache ? JSON.parse(sessionCache) : [];
      sessions = sessions.filter(s => s.id !== sessionId);
      localStorage.setItem(RagChatSDK.SESSIONS_CACHE_KEY, JSON.stringify(sessions));
    } catch (error) {
      console.error('Error clearing session from cache index:', error);
    }

    // Create new session
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

    try {
      localStorage.setItem(cacheKey, JSON.stringify(messages));
    } catch (error) {
      if (error.name === 'QuotaExceededError') {
        // Clear old messages if quota exceeded
        const recentMessages = messages.slice(-10);
        localStorage.setItem(cacheKey, JSON.stringify(recentMessages));
      }
    }
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
