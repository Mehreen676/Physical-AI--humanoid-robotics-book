/**
 * SelectionButton - "Ask about this" button for selected text
 */

import React, { useState } from 'react';
import styles from './styles.module.css';

export default function SelectionButton({
  selectedText,
  onQuery,
  isLoading,
}) {
  const [customQuery, setCustomQuery] = useState('');
  const [showInput, setShowInput] = useState(false);

  const handleQuickAsk = () => {
    // Default question about selection
    const query = 'Please explain this.';
    onQuery(query, true); // true = use selected text
    setShowInput(false);
    setCustomQuery('');
  };

  const handleCustomAsk = () => {
    if (customQuery.trim()) {
      onQuery(customQuery, true); // true = use selected text
      setShowInput(false);
      setCustomQuery('');
    }
  };

  const previewText = selectedText.substring(0, 50) + (selectedText.length > 50 ? '...' : '');

  return (
    <div className={styles.selectionButton} role="complementary">
      <div className={styles.selectionPreview}>
        <span className={styles.selectionIcon}>💡</span>
        <p className={styles.selectionText}>Selected: "{previewText}"</p>
      </div>

      {!showInput ? (
        <div className={styles.selectionActions}>
          <button
            className={styles.quickAskButton}
            onClick={handleQuickAsk}
            disabled={isLoading}
            aria-label="Ask about the selected text"
          >
            Ask about this
          </button>
          <button
            className={styles.customAskButton}
            onClick={() => setShowInput(true)}
            disabled={isLoading}
            aria-label="Ask a custom question about the selected text"
          >
            Custom question
          </button>
        </div>
      ) : (
        <div className={styles.customQueryInput}>
          <input
            type="text"
            placeholder="What do you want to know about this text?"
            value={customQuery}
            onChange={(e) => setCustomQuery(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && customQuery.trim()) {
                handleCustomAsk();
              }
            }}
            disabled={isLoading}
            autoFocus
            aria-label="Custom question about selected text"
          />
          <div className={styles.customQueryActions}>
            <button
              onClick={handleCustomAsk}
              disabled={isLoading || !customQuery.trim()}
              title="Send custom question"
            >
              ✓
            </button>
            <button
              onClick={() => {
                setShowInput(false);
                setCustomQuery('');
              }}
              disabled={isLoading}
              title="Cancel"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
