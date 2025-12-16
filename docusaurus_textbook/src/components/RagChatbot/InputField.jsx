/**
 * InputField - Text input with send button and character count
 */

import React, { useState, useRef, useEffect } from 'react';
import styles from './styles.module.css';

export default function InputField({
  onSend,
  onSelectedTextSend,
  isLoading,
  hasSelectedText,
  maxLength = 500,
}) {
  const [input, setInput] = useState('');
  const [charCount, setCharCount] = useState(0);
  const [showWarning, setShowWarning] = useState(false);
  const textareaRef = useRef(null);

  // Auto-resize textarea
  const handleInput = (e) => {
    const text = e.target.value;
    const count = text.length;

    setInput(text);
    setCharCount(count);
    setShowWarning(count > maxLength);

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(
        textareaRef.current.scrollHeight,
        120
      ) + 'px';
    }
  };

  // Handle Enter key
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !isLoading) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = input.trim();
    if (trimmed && !isLoading) {
      // Send to full-book or selected-text based on context
      if (hasSelectedText) {
        onSelectedTextSend(trimmed);
      } else {
        onSend(trimmed, false);
      }
      setInput('');
      setCharCount(0);
      setShowWarning(false);

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  return (
    <div className={styles.inputContainer}>
      {showWarning && (
        <div className={styles.charWarning}>
          ⚠️ Message exceeds {maxLength} characters. Please shorten.
        </div>
      )}

      <div className={styles.inputWrapper}>
        <textarea
          ref={textareaRef}
          className={styles.input}
          placeholder={hasSelectedText ? '💡 Ask about the selected text...' : 'Type your question here...'}
          value={input}
          onChange={handleInput}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          aria-label="Type your question"
          maxLength={maxLength + 100} // Allow slight overflow for warning
          rows={1}
        />

        <div className={styles.inputFooter}>
          <span className={styles.charCount} aria-live="polite">
            {charCount}/{maxLength}
          </span>

          <button
            className={styles.sendButton}
            onClick={handleSend}
            disabled={isLoading || !input.trim() || showWarning}
            aria-label={hasSelectedText ? 'Ask about selected text' : 'Send message'}
            title={
              hasSelectedText
                ? 'Send question about selected text'
                : 'Send message (Ctrl+Enter)'
            }
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </div>
      </div>

      <div className={styles.inputHelp}>
        {hasSelectedText && (
          <p>
            ✨ <strong>Selected text mode:</strong> Your question will be answered
            using only the text you highlighted.
          </p>
        )}
        <p>Press Enter to send, Shift+Enter for newline</p>
      </div>
    </div>
  );
}
