import React, { useEffect, useMemo, useRef, useState } from 'react';
import ChatMessage from './components/ChatMessage.jsx';

const getMessageId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;

const backendBaseUrl = (import.meta.env.VITE_BACKEND_URL ?? '').replace(/\/$/, '');

const createSession = async (userId) => {
  const target = backendBaseUrl ? `${backendBaseUrl}/api/sessions` : '/api/sessions';

  const response = await fetch(target, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Unable to create a VentureBot session.');
  }

  return response.json();
};

const postChatMessage = async (sessionId, content) => {
  const target = backendBaseUrl ? `${backendBaseUrl}/api/chat` : '/api/chat';
  const response = await fetch(target, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message: content }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Unable to reach the chatbot backend.');
  }

  const payload = await response.json();
  return payload;
};

function App() {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [session, setSession] = useState(null);
  const [isSending, setIsSending] = useState(false);
  const [isInitialising, setIsInitialising] = useState(true);
  const [error, setError] = useState(null);
  const chatLogRef = useRef(null);

  const userId = useMemo(() => {
    const storageKey = 'venturebot-user-id';
    const existing = window.localStorage.getItem(storageKey);
    if (existing) {
      return existing;
    }
    const generated = `user-${crypto.randomUUID?.() ?? getMessageId()}`;
    window.localStorage.setItem(storageKey, generated);
    return generated;
  }, []);

  useEffect(() => {
    const initialiseSession = async () => {
      setIsInitialising(true);
      setError(null);
      try {
        const payload = await createSession(userId);
        setSession({
          id: payload.session_id,
          stage: payload.stage,
          userId,
        });
        setMessages([
          {
            id: getMessageId(),
            role: 'assistant',
            content: payload.initial_message,
          },
        ]);
      } catch (err) {
        console.error(err);
        setError(
          err instanceof Error
            ? err.message
            : 'Something went wrong while connecting to VentureBot.',
        );
      } finally {
        setIsInitialising(false);
      }
    };

    initialiseSession();
  }, [userId]);

  useEffect(() => {
    if (!chatLogRef.current) {
      return;
    }
    chatLogRef.current.scrollTo({
      top: chatLogRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const trimmed = draft.trim();

    if (!trimmed || !session?.id) {
      return;
    }

    const userMessage = {
      id: getMessageId(),
      role: 'user',
      content: trimmed,
    };

    const pendingId = getMessageId();
    const pendingAssistant = {
      id: pendingId,
      role: 'assistant',
      content: '',
      isPending: true,
    };

    setMessages((prev) => [...prev, userMessage, pendingAssistant]);
    setDraft('');
    setIsSending(true);

    try {
      const payload = await postChatMessage(session.id, trimmed);
      setSession((prev) =>
        prev
          ? {
              ...prev,
              stage: payload.stage ?? prev.stage,
            }
          : prev,
      );

      setMessages((prev) =>
        prev.map((message) =>
          message.id === pendingId
            ? {
                ...message,
                isPending: false,
                content:
                  payload.message ??
                  'VentureBot responded without a message. Please try again.',
              }
            : message,
        ),
      );
    } catch (error) {
      setMessages((prev) =>
        prev.map((message) =>
          message.id === pendingId
            ? {
                ...message,
                role: 'system',
                isPending: false,
                content:
                  error instanceof Error
                    ? error.message
                    : 'Unexpected error contacting VentureBot.',
            }
            : message,
        ),
      );
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>VentureBot Chat</h1>
        <p className="app-subtitle">
          {session?.stage
            ? `Current stage: ${session.stage.replaceAll('_', ' ')}`
            : 'A lightweight React client for conversing with the assistant.'}
        </p>
      </header>

      <main className="chat-panel">
        <section
          ref={chatLogRef}
          className="chat-log"
          aria-busy={isSending}
          aria-live="polite"
        >
          {isInitialising && (
            <ChatMessage
              role="system"
              content="Connecting to VentureBot…"
              isPending
            />
          )}
          {error && !isInitialising && (
            <ChatMessage role="system" content={error} />
          )}
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              role={message.role}
              content={message.content}
              isPending={Boolean(message.isPending)}
            />
          ))}
        </section>

        <form className="chat-input" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="chat-message">
            Message VentureBot
          </label>
          <textarea
            id="chat-message"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Type your next question or instruction..."
            rows={3}
            disabled={isSending || isInitialising || !session?.id}
            required
          />
          <div className="chat-actions">
            <button
              type="submit"
              disabled={isSending || isInitialising || !session?.id}
            >
              {isInitialising
                ? 'Initialising…'
                : isSending
                  ? 'Sending…'
                  : 'Send'}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}

export default App;
