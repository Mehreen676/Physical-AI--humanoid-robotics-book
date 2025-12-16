/**
 * MessageList - Scrollable message display component
 */

import React, { useEffect, useRef, forwardRef } from 'react';
import MessageBubble from './MessageBubble';
import styles from './styles.module.css';

const MessageList = forwardRef(({ messages, isLoading }, ref) => {
  const scrollRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <div
      className={styles.messageList}
      ref={scrollRef}
      role="log"
      aria-live="polite"
      aria-atomic="false"
    >
      {messages.length === 0 ? (
        <div className={styles.emptyState}>
          <p>👋 Welcome! Ask me anything about the course materials.</p>
          <p style={{ fontSize: '0.9em', marginTop: '8px' }}>
            💡 Tip: You can also select text in the course and ask about it.
          </p>
        </div>
      ) : (
        messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} index={idx} />
        ))
      )}

      {isLoading && (
        <div className={styles.typingIndicator} aria-label="AI is typing">
          <span></span>
          <span></span>
          <span></span>
        </div>
      )}
    </div>
  );
});

MessageList.displayName = 'MessageList';

export default MessageList;
