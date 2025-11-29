import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type ChatMessage = {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
};

type ChatSession = {
  id: string;
  title?: string | null;
  current_stage?: string;
  created_at: string;
  updated_at: string;
};

type SessionStartResponse = {
  session: ChatSession;
  onboarding_message?: ChatMessage | null;
};

type GatewayEvent =
  | { event: "session_ready"; data: ChatSession }
  | { event: "user_message" | "assistant_message"; data: ChatMessage }
  | { event: "assistant_token"; data: string }
  | {
      event: "stage_update";
      data: { current_stage: string; session: ChatSession };
    }
  | { event: "error"; data: string };

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://localhost:8000";

const toWebSocketUrl = (baseUrl: string) => {
  if (baseUrl.startsWith("https://")) {
    return `wss://${baseUrl.slice("https://".length)}`;
  }
  if (baseUrl.startsWith("http://")) {
    return `ws://${baseUrl.slice("http://".length)}`;
  }
  return baseUrl;
};

const formatTimestamp = (value?: string) => {
  if (!value) return "";
  const date = new Date(value);
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
};

function App() {
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [status, setStatus] = useState<
    "idle" | "connecting" | "ready" | "error"
  >("idle");
  const [isSending, setIsSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const webSocketRef = useRef<WebSocket | null>(null);
  const streamingMessageRef = useRef<ChatMessage | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const isReady = status === "ready";
  const isConnectInFlight = status === "connecting" || status === "idle";

  const sessionTitle = useMemo(() => {
    if (!session) return "New Venture Coaching Session";
    return session.title ?? "Venture Coaching Session";
  }, [session]);

  useEffect(() => {
    let isCancelled = false;

    const bootstrap = async () => {
      setStatus("connecting");
      try {
        const response = await fetch(`${API_BASE_URL}/api/chat/sessions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: "MVP Demo Session",
            auto_start: false,
          }),
        });

        if (!response.ok) {
          throw new Error(
            `Session creation failed with status ${response.status}`
          );
        }

        const data: SessionStartResponse = await response.json();
        if (isCancelled) return;

        // Extract session from the new response format
        const sessionData = data.session;
        setSession(sessionData);

        // If there's an onboarding message, add it to messages
        if (data.onboarding_message) {
          setMessages([data.onboarding_message]);
        }

        connectWebSocket(sessionData.id);
      } catch (error) {
        console.error("Failed to initialize chat session", error);
        if (!isCancelled) {
          setStatus("error");
          setErrorMessage(
            "Unable to start a new session. Please refresh the page to retry."
          );
        }
      }
    };

    bootstrap();

    return () => {
      isCancelled = true;
      webSocketRef.current?.close();
      webSocketRef.current = null;
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const connectWebSocket = (sessionId: string) => {
    const wsUrl = `${toWebSocketUrl(API_BASE_URL)}/api/chat/ws/${sessionId}`;
    const socket = new WebSocket(wsUrl);

    webSocketRef.current = socket;
    setStatus("connecting");
    setErrorMessage(null);

    socket.onopen = () => setStatus("ready");

    socket.onmessage = (event) => {
      try {
        const parsed: GatewayEvent = JSON.parse(event.data);

        switch (parsed.event) {
          case "session_ready":
            setSession(parsed.data);
            break;
          case "user_message":
            setMessages((previous) => [...previous, parsed.data]);
            break;
          case "assistant_token": {
            const current = streamingMessageRef.current;
            if (!current) {
              const draft: ChatMessage = {
                id: "streaming",
                session_id: sessionId,
                role: "assistant",
                content: parsed.data,
              };
              streamingMessageRef.current = draft;
              setMessages((previous) => [...previous, draft]);
            } else {
              current.content += parsed.data;
              setMessages((previous) => {
                const copy = [...previous];
                copy[copy.length - 1] = { ...current };
                return copy;
              });
            }
            break;
          }
          case "assistant_message":
            streamingMessageRef.current = null;
            setMessages((previous) => [
              ...previous.filter((msg) => msg.id !== "streaming"),
              parsed.data,
            ]);
            setIsSending(false);
            break;
          case "stage_update":
            // Update session with new stage info
            setSession(parsed.data.session);
            break;
          case "error":
            setErrorMessage(parsed.data);
            setIsSending(false);
            break;
        }
      } catch (error) {
        console.error("Failed to parse gateway event", error);
      }
    };

    socket.onerror = () => {
      setStatus("error");
      setErrorMessage("Connection error. Please refresh the page.");
    };

    socket.onclose = () => {
      setStatus("error");
      webSocketRef.current = null;
    };
  };

  const submitMessage = () => {
    if (
      !inputValue.trim() ||
      !session ||
      !webSocketRef.current ||
      webSocketRef.current.readyState !== WebSocket.OPEN
    ) {
      return;
    }

    setIsSending(true);
    const payload = { content: inputValue.trim() };
    webSocketRef.current.send(JSON.stringify(payload));

    setInputValue("");
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    submitMessage();
  };

  const handleComposerKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submitMessage();
    }
  };

  return (
    <div className="app-shell">
      <header className="chat-header">
        <div>
          <h1>VentureBots MVP</h1>
          <p className="subtitle">{sessionTitle}</p>
        </div>
        <div className="header-controls">
          {session?.current_stage && (
            <div className="stage-badge">
              Stage: {session.current_stage.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
            </div>
          )}
          <div className={`connection-pill connection-pill--${status}`}>
            {status === "ready" && "Connected"}
            {status === "connecting" && "Connecting…"}
            {status === "idle" && "Starting…"}
            {status === "error" && "Offline"}
          </div>
        </div>
      </header>

      <main className="chat-window">
        {messages.length === 0 && (
          <div className="empty-state">
            <h2>Welcome to your startup coaching session</h2>
            <p>
              Share your idea, pain point, or goal. VentureBots will orchestrate
              the crew and guide you through the journey.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <article
            key={message.id}
            className={`message message--${message.role}`}
          >
            <div className="message-metadata">
              <span className="message-role">
                {message.role === "user" ? "You" : "VentureBots"}
              </span>
              {message.created_at && (
                <time>{formatTimestamp(message.created_at)}</time>
              )}
            </div>
            <div className="message-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          </article>
        ))}
        <div ref={messagesEndRef} />
      </main>

      <footer className="composer">
        {errorMessage && <div className="error-banner">{errorMessage}</div>}
        <form className="composer-form" onSubmit={handleSubmit}>
          <textarea
            name="message"
            rows={1}
            placeholder={
              isConnectInFlight
                ? "Connecting to VentureBots…"
                : "Describe your venture idea or ask where to start."
            }
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            disabled={!isReady || isSending}
            onKeyDown={handleComposerKeyDown}
          />
          <button
            type="submit"
            disabled={!isReady || isSending || !inputValue.trim()}
          >
            {isSending ? "Sending…" : "Send"}
          </button>
        </form>
        <p className="helper-text">
          Press <kbd>Enter</kbd> to send, <kbd>Shift + Enter</kbd> for a new
          line.
        </p>
      </footer>
    </div>
  );
}

export default App;
