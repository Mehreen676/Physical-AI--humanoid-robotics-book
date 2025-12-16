/**
 * ChatHeader - Header component with title and action buttons
 */

import React from 'react';
import styles from './styles.module.css';

export default function ChatHeader({ sessionId, onClear, onClose }) {
  const handleClear = () => {
    if (window.confirm('Clear all messages? This cannot be undone.')) {
      onClear();
    }
  };

  return (
    <div className={styles.chatHeader} id="chat-title">
      <div className={styles.headerContent}>
        <h3 className={styles.chatTitle}>AI Learning Assistant</h3>
        <p className={styles.headerSubtitle}>Ask questions about the course materials</p>
      </div>

      <div className={styles.headerActions}>
        <button
          className={styles.headerButton}
          onClick={handleClear}
          aria-label="Clear chat history"
          title="Clear all messages"
        >
          🗑️
        </button>
        <button
          className={styles.headerButton}
          onClick={onClose}
          aria-label="Close chat"
          title="Close chat window"
        >
          ✕
        </button>
      </div>

      {sessionId && (
        <div className={styles.sessionId} title={`Session: ${sessionId}`}>
          Session: {sessionId.substring(0, 8)}...
        </div>
      )}
    </div>
  );
}
