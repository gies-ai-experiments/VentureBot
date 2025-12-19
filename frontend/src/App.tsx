import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { DataVisualizer } from "./ChartComponents";
import type { GraphData } from "./ChartComponents";

type ChatMessage = {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  graph_data?: GraphData; // Optional graph data from backend
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

const extractGraphData = (message: ChatMessage): ChatMessage => {
  // Regex to find JSON block at the end of the message: ```json { ... } ```
  const jsonBlockRegex = /```json\s*(\{[\s\S]*?"json_graph_data"[\s\S]*?\})\s*```/;
  const match = message.content.match(jsonBlockRegex);

  if (match && match[1]) {
    try {
      const parsed = JSON.parse(match[1]);
      if (parsed.json_graph_data) {
        // Return message with graph data and content STRIPPED of the JSON block
        return {
          ...message,
          content: message.content.replace(match[0], '').trim(),
          graph_data: parsed.json_graph_data
        };
      }
    } catch (e) {
      console.error("Failed to parse graph data JSON", e);
    }
  }
  return message;
};

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

// Journey stages configuration
const JOURNEY_STAGES = [
  { key: "onboarding", label: "Discovery", icon: "👋", description: "Share your pain point" },
  { key: "idea_generation", label: "Ideas", icon: "💡", description: "Generate startup ideas" },
  { key: "validation", label: "Validate", icon: "📊", description: "Market validation" },
  { key: "prd", label: "PRD", icon: "📋", description: "Product requirements" },
  { key: "prompt_engineering", label: "Build", icon: "🚀", description: "No-code prompts" },
  { key: "complete", label: "Launch", icon: "🎉", description: "Ready to build!" },
];

// Quick reply suggestions based on stage
// Only show for stages with clear choices, not during free-form conversation
const getQuickReplies = (stage?: string): string[] => {
  if (!stage) return [];

  switch (stage) {
    case "onboarding":
      // No quick replies during conversational onboarding
      return [];
    case "idea_generation":
      return ["1", "2", "3", "4", "5"];
    case "validation":
      return ["Proceed to PRD", "Try a different idea"];
    case "prd":
      return ["Generate prompts", "Refine requirements"];
    case "prompt_engineering":
      return ["Copy prompt", "Start over"];
    default:
      return [];
  }
};

function JourneyProgress({ currentStage }: { currentStage?: string }) {
  const currentIndex = JOURNEY_STAGES.findIndex(s => s.key === currentStage);

  return (
    <div className="journey-progress">
      <div className="journey-track">
        {JOURNEY_STAGES.map((stage, index) => {
          const isComplete = index < currentIndex;
          const isCurrent = index === currentIndex;
          const isFuture = index > currentIndex;

          return (
            <div
              key={stage.key}
              className={`journey-step ${isComplete ? 'complete' : ''} ${isCurrent ? 'current' : ''} ${isFuture ? 'future' : ''}`}
            >
              <div className="step-indicator">
                <span className="step-icon">{stage.icon}</span>
                {index < JOURNEY_STAGES.length - 1 && (
                  <div className={`step-connector ${isComplete ? 'complete' : ''}`} />
                )}
              </div>
              <span className="step-label">{stage.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <div className="typing-avatar">🤖</div>
      <div className="typing-content">
        <div className="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <span className="typing-text">VentureBot is thinking...</span>
      </div>
    </div>
  );
}

function QuickReplies({
  replies,
  onSelect,
  disabled
}: {
  replies: string[];
  onSelect: (reply: string) => void;
  disabled: boolean;
}) {
  if (replies.length === 0) return null;

  return (
    <div className="quick-replies">
      {replies.map((reply) => (
        <button
          key={reply}
          className="quick-reply-chip"
          onClick={() => onSelect(reply)}
          disabled={disabled}
        >
          {reply}
        </button>
      ))}
    </div>
  );
}

function StageTransition({ stage }: { stage: string }) {
  const stageInfo = JOURNEY_STAGES.find(s => s.key === stage);
  if (!stageInfo) return null;

  return (
    <div className="stage-transition">
      <div className="stage-transition-content">
        <span className="stage-icon-large">{stageInfo.icon}</span>
        <div className="stage-info">
          <h3>Stage: {stageInfo.label}</h3>
          <p>{stageInfo.description}</p>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [status, setStatus] = useState<
    "idle" | "connecting" | "ready" | "error"
  >("idle");
  const [isSending, setIsSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showStageTransition, setShowStageTransition] = useState(false);
  const [previousStage, setPreviousStage] = useState<string | null>(null);

  const webSocketRef = useRef<WebSocket | null>(null);
  const streamingMessageRef = useRef<ChatMessage | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const isReady = status === "ready";
  const isConnectInFlight = status === "connecting" || status === "idle";

  const sessionTitle = useMemo(() => {
    if (!session) return "New Venture Coaching Session";
    return session.title ?? "Venture Coaching Session";
  }, [session]);

  const quickReplies = useMemo(() => {
    return getQuickReplies(session?.current_stage);
  }, [session?.current_stage]);

  // Handle stage transitions
  useEffect(() => {
    if (session?.current_stage && previousStage && session.current_stage !== previousStage) {
      setShowStageTransition(true);
      setTimeout(() => setShowStageTransition(false), 3000);
    }
    setPreviousStage(session?.current_stage || null);
  }, [session?.current_stage]);

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

        const sessionData = data.session;
        setSession(sessionData);

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
              extractGraphData(parsed.data),
            ]);
            setIsSending(false);
            break;
          case "stage_update":
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

  const submitMessage = (messageOverride?: string) => {
    const messageToSend = messageOverride ?? inputValue.trim();
    if (
      !messageToSend ||
      !session ||
      !webSocketRef.current ||
      webSocketRef.current.readyState !== WebSocket.OPEN
    ) {
      return;
    }

    setIsSending(true);
    const payload = { content: messageToSend };
    webSocketRef.current.send(JSON.stringify(payload));

    if (!messageOverride) {
      setInputValue("");
    }
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

  const handleQuickReply = (reply: string) => {
    submitMessage(reply);
  };

  return (
    <div className="app-shell">
      <header className="chat-header">
        <div className="header-brand">
          <div className="logo-mark">
            <span className="logo-icon">🚀</span>
          </div>
          <div>
            <h1>VentureBot</h1>
            <p className="subtitle">{sessionTitle}</p>
          </div>
        </div>
        <div className="header-controls">
          <div className={`connection-pill connection-pill--${status}`}>
            <span className="connection-dot"></span>
            {status === "ready" && "Live"}
            {status === "connecting" && "Connecting"}
            {status === "idle" && "Starting"}
            {status === "error" && "Offline"}
          </div>
        </div>
      </header>

      <JourneyProgress currentStage={session?.current_stage} />

      {showStageTransition && session?.current_stage && (
        <StageTransition stage={session.current_stage} />
      )}

      <main className="chat-window">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">🔑</div>
            <h2>Ready to unlock your startup idea?</h2>
            <p>
              A great idea is like a key, and a real pain point is the lock it opens.
              <br />
              Let's discover yours together.
            </p>
            <div className="empty-state-features">
              <div className="feature">
                <span className="feature-icon">💡</span>
                <span>Discover pain points</span>
              </div>
              <div className="feature">
                <span className="feature-icon">📊</span>
                <span>Validate ideas</span>
              </div>
              <div className="feature">
                <span className="feature-icon">🚀</span>
                <span>Build with AI</span>
              </div>
            </div>
            <p className="empty-state-cta">Type a message below to begin your journey</p>
          </div>
        )}

        {messages.map((message, index) => (
          <article
            key={message.id}
            className={`message message--${message.role}`}
            style={{ animationDelay: `${index * 0.05}s` }}
          >
            <div className="message-avatar">
              {message.role === "user" ? "👤" : "🤖"}
            </div>
            <div className="message-bubble">
              <div className="message-metadata">
                <span className="message-role">
                  {message.role === "user" ? "You" : "VentureBot"}
                </span>
                {message.created_at && (
                  <time>{formatTimestamp(message.created_at)}</time>
                )}
              </div>
              <div className="message-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
                {message.graph_data && <DataVisualizer data={message.graph_data} />}
              </div>
            </div>
          </article>
        ))}

        {isSending && <TypingIndicator />}

        <div ref={messagesEndRef} />
      </main>

      <footer className="composer">
        {errorMessage && <div className="error-banner">{errorMessage}</div>}

        <QuickReplies
          replies={quickReplies}
          onSelect={handleQuickReply}
          disabled={!isReady || isSending}
        />

        <form className="composer-form" onSubmit={handleSubmit}>
          <textarea
            name="message"
            rows={1}
            placeholder={
              isConnectInFlight
                ? "Connecting to VentureBot..."
                : "Share your idea, frustration, or ask a question..."
            }
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            disabled={!isReady || isSending}
            onKeyDown={handleComposerKeyDown}
          />
          <button
            type="submit"
            disabled={!isReady || isSending || !inputValue.trim()}
            aria-label="Send message"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </form>
        <p className="helper-text">
          <kbd>Enter</kbd> to send · <kbd>Shift + Enter</kbd> for new line
        </p>
      </footer>
    </div>
  );
}

export default App;
