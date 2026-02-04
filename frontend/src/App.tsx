import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
  suggested_replies?: string[];
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

const MAX_TEXTAREA_HEIGHT = 160;
const SCROLL_THRESHOLD = 96;

const stripNextStageFooter = (content: string) => {
  const footerRegex = /(?:\n|\r|\s)*---\s*\n\s*\*\*Next Stage:[\s\S]*$/i;
  const plainFooterRegex = /(?:\n|\r|\s)*Next Stage:[\s\S]*$/i;
  return content.replace(footerRegex, "").replace(plainFooterRegex, "").trim();
};

const extractGraphData = (message: ChatMessage): ChatMessage => {
  const jsonBlockRegex = /```json\s*(\{[\s\S]*?"json_graph_data"[\s\S]*?\})\s*```/;
  const fencedMatch = message.content.match(jsonBlockRegex);

  const cleanContent = stripNextStageFooter(message.content);

  if (fencedMatch && fencedMatch[1]) {
    try {
      const parsed = JSON.parse(fencedMatch[1]);
      if (parsed.json_graph_data) {
        return {
          ...message,
          content: cleanContent.replace(fencedMatch[0], "").trim(),
          graph_data: parsed.json_graph_data,
        };
      }
    } catch (e) {
      console.error("Failed to parse graph data JSON", e);
    }
  }

  const graphIndex = cleanContent.indexOf("\"json_graph_data\"");
  if (graphIndex !== -1) {
    const startIndex = cleanContent.lastIndexOf("{", graphIndex);
    if (startIndex !== -1) {
      let depth = 0;
      let endIndex = -1;
      for (let i = startIndex; i < cleanContent.length; i += 1) {
        const char = cleanContent[i];
        if (char === "{") depth += 1;
        if (char === "}") depth -= 1;
        if (depth === 0) {
          endIndex = i;
          break;
        }
      }
      if (endIndex !== -1) {
        const jsonSlice = cleanContent.slice(startIndex, endIndex + 1);
        try {
          const parsed = JSON.parse(jsonSlice);
          if (parsed.json_graph_data) {
            const stripped = cleanContent.replace(jsonSlice, "").trim();
            return {
              ...message,
              content: stripped,
              graph_data: parsed.json_graph_data,
            };
          }
        } catch (e) {
          console.error("Failed to parse inline graph data JSON", e);
        }
      }
    }
  }

  return {
    ...message,
    content: cleanContent,
  };
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
      return [];
    case "validation":
      return [];
    case "prd":
      return ["Generate prompts", "Refine requirements"];
    case "prompt_engineering":
      return ["Copy prompt", "Start over"];
    default:
      return [];
  }
};

const VALIDATION_SECTION_LABELS = [
  "Market Size",
  "Competitive Landscape",
  "Feasibility Score",
  "Key Risks",
  "Recommendation",
  "Actionable next steps",
];

const parseValidationContent = (content: string) => {
  const lines = content.split("\n");
  const sections: { title: string; body: string }[] = [];
  let currentTitle: string | null = null;
  let buffer: string[] = [];

  const flush = () => {
    if (currentTitle) {
      sections.push({ title: currentTitle, body: buffer.join("\n").trim() });
    }
    buffer = [];
  };

  for (const line of lines) {
    const cleaned = line.replace(/\*\*/g, "").trim();
    const matchedTitle = VALIDATION_SECTION_LABELS.find(
      (label) => cleaned.toLowerCase() === label.toLowerCase()
    );
    if (matchedTitle) {
      flush();
      currentTitle = matchedTitle;
      continue;
    }
    if (currentTitle) {
      buffer.push(line);
    }
  }
  flush();

  if (sections.length < 2) {
    return null;
  }

  const allText = lines.join("\n");
  const feasibilityLine = allText.match(/Feasibility Score:.*$/im)?.[0]?.trim() ?? "";
  const recommendationLine = allText.match(/Recommendation:.*$/im)?.[0]?.trim() ?? "";
  const risksSection = sections.find((section) => section.title === "Key Risks");
  const topRisks = risksSection
    ? risksSection.body
        .split("\n")
        .map((line) => line.replace(/^[\-\*\d\.\s]+/, "").trim())
        .filter(Boolean)
        .slice(0, 3)
    : [];

  return {
    summary: {
      feasibility: feasibilityLine,
      recommendation: recommendationLine,
      risks: topRisks,
    },
    sections,
  };
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

function ValidationReport({
  data,
}: {
  data: NonNullable<ReturnType<typeof parseValidationContent>>;
}) {
  const { summary, sections } = data;
  const detailSections = sections.filter(
    (section) => section.title !== "Feasibility Score" && section.title !== "Recommendation"
  );

  return (
    <div className="validation-report">
      <div className="validation-summary">
        <div className="summary-header">Validation Snapshot</div>
        <div className="summary-grid">
          {summary.feasibility && (
            <div className="summary-card">
              <span className="summary-label">Feasibility</span>
              <span className="summary-value">{summary.feasibility}</span>
            </div>
          )}
          {summary.recommendation && (
            <div className="summary-card">
              <span className="summary-label">Recommendation</span>
              <span className="summary-value">{summary.recommendation}</span>
            </div>
          )}
        </div>
        {summary.risks.length > 0 && (
          <div className="summary-risks">
            <span className="summary-label">Top Risks</span>
            <ul>
              {summary.risks.map((risk) => (
                <li key={risk}>{risk}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="validation-sections">
        {detailSections.map((section) => (
          <details key={section.title} className="validation-section" open={section.title === "Market Size"}>
            <summary>{section.title}</summary>
            <div className="validation-section-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {section.body}
              </ReactMarkdown>
            </div>
          </details>
        ))}
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
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  const webSocketRef = useRef<WebSocket | null>(null);
  const streamingMessageRef = useRef<ChatMessage | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const chatWindowRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const lastMessageIdRef = useRef<string | null>(null);

  const isReady = status === "ready";
  const isConnectInFlight = status === "connecting" || status === "idle";

  const sessionTitle = useMemo(() => {
    if (!session) return "New Venture Coaching Session";
    return session.title ?? "Venture Coaching Session";
  }, [session]);

  const quickReplies = useMemo(() => {
    // Get the last assistant message to check if content is ready for quick replies
    const lastAssistantMsg = [...messages].reverse().find(m => m.role === "assistant");
    if (lastAssistantMsg?.suggested_replies?.length) {
      return lastAssistantMsg.suggested_replies;
    }
    return getQuickReplies(session?.current_stage);
  }, [session?.current_stage, messages]);

  const isNearBottom = useCallback(() => {
    const container = chatWindowRef.current;
    if (!container) return true;
    const distanceFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;
    return distanceFromBottom < SCROLL_THRESHOLD;
  }, []);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior });
    setUnreadCount(0);
    setIsAtBottom(true);
  }, []);

  const handleScroll = useCallback(() => {
    const nearBottom = isNearBottom();
    setIsAtBottom(nearBottom);
    if (nearBottom) {
      setUnreadCount(0);
    }
  }, [isNearBottom]);

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
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    const nextHeight = Math.min(textarea.scrollHeight, MAX_TEXTAREA_HEIGHT);
    textarea.style.height = `${nextHeight}px`;
  }, [inputValue]);

  useEffect(() => {
    if (messages.length === 0) return;

    const lastMessage = messages[messages.length - 1];
    const previousId = lastMessageIdRef.current;
    const isNewMessage = lastMessage.id !== previousId;
    const isStreamingFinalized =
      previousId === "streaming" &&
      lastMessage.id !== "streaming" &&
      lastMessage.role === "assistant";

    lastMessageIdRef.current = lastMessage.id;

    if (
      isNewMessage &&
      !isStreamingFinalized &&
      !isAtBottom &&
      lastMessage.role === "assistant"
    ) {
      setUnreadCount((count) => count + 1);
    }

    if (isAtBottom || lastMessage.role === "user") {
      scrollToBottom("smooth");
    }
  }, [messages, isAtBottom, scrollToBottom]);

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

      <main
        className="chat-window"
        ref={chatWindowRef}
        onScroll={handleScroll}
        role="log"
        aria-live="polite"
        aria-relevant="additions text"
        aria-busy={isSending}
      >
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

        {messages.map((message, index) => {
          const previous = messages[index - 1];
          const isGrouped = previous?.role === message.role;
          const validationData =
            message.role === "assistant" ? parseValidationContent(message.content) : null;

          return (
            <article
              key={message.id}
              className={`message message--${message.role} ${isGrouped ? "message--grouped" : ""}`}
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <div
                className={`message-avatar ${isGrouped ? "message-avatar--hidden" : ""}`}
                aria-hidden={isGrouped ? "true" : undefined}
              >
                {message.role === "user" ? "👤" : "🤖"}
              </div>
              <div className="message-bubble">
                {!isGrouped && (
                  <div className="message-metadata">
                    <span className="message-role">
                      {message.role === "user" ? "You" : "VentureBot"}
                    </span>
                    {message.created_at && (
                      <time>{formatTimestamp(message.created_at)}</time>
                    )}
                  </div>
                )}
                <div className="message-content">
                  {validationData ? (
                    <ValidationReport data={validationData} />
                  ) : (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  )}
                  {message.graph_data && <DataVisualizer data={message.graph_data} />}
                </div>
              </div>
            </article>
          );
        })}

        {unreadCount > 0 && !isAtBottom && (
          <button className="scroll-to-latest" onClick={() => scrollToBottom("smooth")}>
            {unreadCount} new message{unreadCount > 1 ? "s" : ""}
            <span aria-hidden="true">↓</span>
          </button>
        )}

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
            ref={textareaRef}
            aria-label="Message VentureBot"
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
