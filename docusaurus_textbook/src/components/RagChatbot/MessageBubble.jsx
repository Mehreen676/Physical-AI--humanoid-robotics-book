/**
 * MessageBubble - Individual message display with citations
 */

import React, { memo } from 'react';
import styles from './styles.module.css';

function MessageBubble({ message, index }) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`${styles.messageBubbleContainer} ${
        isUser ? styles.userBubble : styles.botBubble
      }`}
      role="article"
      aria-label={`${isUser ? 'Your' : 'Assistant'} message`}
    >
      <div className={styles.messageBubble}>
        <p className={styles.messageContent}>{message.content}</p>

        {/* Citations */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className={styles.citations}>
            <p className={styles.citationsLabel}>📚 Sources:</p>
            {message.sources.map((source, idx) => (
              <div key={idx} className={styles.citation}>
                <strong>{source.chapter}</strong>
                {source.section && ` › ${source.section}`}
                {source.similarity_score && (
                  <span className={styles.similarity}>
                    ({(source.similarity_score * 100).toFixed(0)}% match)
                  </span>
                )}
                {source.content && (
                  <p className={styles.citationContent}>
                    &quot;{source.content.substring(0, 100)}
                    {source.content.length > 100 ? '...' : ''}&quot;
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Latency */}
        {!isUser && message.latency_ms && (
          <div className={styles.messageMetadata}>
            ⏱️ {message.latency_ms}ms | Mode: {message.mode || 'full_book'}
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(MessageBubble);
