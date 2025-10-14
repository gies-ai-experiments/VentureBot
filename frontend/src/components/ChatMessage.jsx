import React from 'react';

const roleLabels = {
  user: 'You',
  assistant: 'VentureBot',
  system: 'System',
};

const ChatMessage = ({ role, content, isPending = false }) => {
  const classes = ['chat-message', `chat-message--${role}`];
  if (isPending) {
    classes.push('chat-message--pending');
  }

  return (
    <article className={classes.join(' ')}>
      <header className="chat-message__role">{roleLabels[role] ?? 'Message'}</header>
      <p className="chat-message__content">
        {isPending ? (
          <span className="typing-indicator" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
        ) : (
          content
        )}
        {isPending && <span className="sr-only">VentureBot is typing</span>}
      </p>
    </article>
  );
};

export default ChatMessage;
