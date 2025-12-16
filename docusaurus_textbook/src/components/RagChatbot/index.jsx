/**
 * RagChatbot - Main Chat UI Component
 * Container component managing chat state and orchestrating interaction
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useDocusaurusContext } from '@docusaurus/useDocusaurusContext';
import RagChatSDK from '../../lib/rag-chat-sdk';
import ChatHeader from './ChatHeader';
import MessageList from './MessageList';
import InputField from './InputField';
import SelectionButton from './SelectionButton';
import styles from './styles.module.css';

export default function RagChatbot() {
  const { siteConfig } = useDocusaurusContext();
  const ragConfig = siteConfig.customFields?.ragChatbot || {};

  // Enable/disable flag
  if (!ragConfig.enabled) {
    return null;
  }

  // State management
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedText, setSelectedText] = useState(null);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  // Refs
  const sdkRef = useRef(null);
  const messageListRef = useRef(null);

  // Initialize SDK
  useEffect(() => {
    try {
      const sdk = new RagChatSDK(ragConfig.apiUrl || 'http://localhost:8000', {
        bookVersion: 'v1.0',
      });
      sdkRef.current = sdk;
      setSessionId(sdk.getSessionId());

      // Load cached messages from session
      const cached = sdk.getCachedMessages();
      if (cached.length > 0) {
        setMessages(cached.map(msg => ({
          role: msg.role,
          content: msg.content,
          sources: msg.sources || [],
        })));
      }
    } catch (err) {
      setError('Failed to initialize chat SDK');
      console.error('SDK initialization error:', err);
    }
  }, [ragConfig]);

  // Handle text selection
  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection();
      const text = selection.toString().trim();

      if (text.length > 0 && text.length <= (ragConfig.maxSelectedTextLength || 10000)) {
        setSelectedText(text);
      } else if (text.length === 0) {
        setSelectedText(null);
      }
    };

    // Debounce selection handler
    let timeout;
    const debouncedHandler = () => {
      clearTimeout(timeout);
      timeout = setTimeout(handleSelection, 300);
    };

    document.addEventListener('selectionchange', debouncedHandler);
    return () => {
      document.removeEventListener('selectionchange', debouncedHandler);
      clearTimeout(timeout);
    };
  }, [ragConfig.maxSelectedTextLength]);

  // Send message
  const handleSendMessage = useCallback(
    async (query, useSelectedText = false) => {
      if (!sdkRef.current) {
        setError('Chat SDK not initialized');
        return;
      }

      if (!query.trim()) {
        setError('Query cannot be empty');
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        let response;

        if (useSelectedText && selectedText) {
          // Selected-text mode
          response = await sdkRef.current.querySelectedText(query, selectedText);
          // Clear selection after query
          setSelectedText(null);
          window.getSelection().removeAllRanges();
        } else {
          // Full-book mode
          response = await sdkRef.current.query(query);
        }

        // Add user message
        const userMessage = {
          role: 'user',
          content: query,
          timestamp: new Date().toISOString(),
        };

        // Add bot message
        const botMessage = {
          role: 'assistant',
          content: response.response,
          sources: response.sources || [],
          mode: response.mode,
          latency_ms: response.latency_ms,
          timestamp: new Date().toISOString(),
        };

        // Update state
        setMessages(prev => [...prev, userMessage, botMessage]);

        // Cache messages
        sdkRef.current._cacheMessage('user', query);
        sdkRef.current._cacheMessage('assistant', response.response, response.sources);
      } catch (err) {
        setError(err.message || 'Failed to process query');
        console.error('Query error:', err);
      } finally {
        setIsLoading(false);
      }
    },
    [selectedText]
  );

  // Toggle chat open/close
  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  // Clear chat
  const handleClearChat = () => {
    setMessages([]);
    setError(null);
    if (sdkRef.current) {
      sdkRef.current.clearSession();
      setSessionId(sdkRef.current.getSessionId());
    }
  };

  // Close on escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  return (
    <div className={styles.chatContainer}>
      {/* Toggle Button */}
      <button
        className={styles.toggleButton}
        onClick={toggleChat}
        aria-label="Open chat assistant"
        aria-expanded={isOpen}
        title="Chat with AI assistant"
      >
        <span className={styles.icon}>💬</span>
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div
          className={styles.chatWindow}
          role="dialog"
          aria-labelledby="chat-title"
          aria-modal="true"
        >
          <ChatHeader
            sessionId={sessionId}
            onClear={handleClearChat}
            onClose={toggleChat}
          />

          {/* Messages */}
          <MessageList
            ref={messageListRef}
            messages={messages}
            isLoading={isLoading}
          />

          {/* Error Message */}
          {error && (
            <div className={styles.errorMessage} role="alert">
              {error}
            </div>
          )}

          {/* Selected Text Button */}
          {selectedText && (
            <SelectionButton
              selectedText={selectedText}
              onQuery={handleSendMessage}
              isLoading={isLoading}
            />
          )}

          {/* Input Field */}
          <InputField
            onSend={handleSendMessage}
            onSelectedTextSend={(query) => handleSendMessage(query, true)}
            isLoading={isLoading}
            hasSelectedText={!!selectedText}
            maxLength={ragConfig.maxQueryLength || 500}
          />
        </div>
      )}
    </div>
  );
}
