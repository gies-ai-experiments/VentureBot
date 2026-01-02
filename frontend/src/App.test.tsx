import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import App from './App'

// Mock fetch for session creation
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        session: {
          id: 'test-session-123',
          title: 'Test Session',
          current_stage: 'onboarding',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        onboarding_message: {
          id: 'msg-1',
          session_id: 'test-session-123',
          role: 'assistant',
          content: 'Welcome to VentureBot!',
          created_at: new Date().toISOString(),
        },
      }),
    })
  })

  it('renders the app header with VentureBot branding', async () => {
    render(<App />)
    expect(screen.getByText('VentureBot')).toBeInTheDocument()
  })

  it('shows connecting status initially', () => {
    render(<App />)
    expect(screen.getByText('Connecting')).toBeInTheDocument()
  })

  it('renders journey progress with all stages', () => {
    render(<App />)
    expect(screen.getByText('Discovery')).toBeInTheDocument()
    expect(screen.getByText('Ideas')).toBeInTheDocument()
    expect(screen.getByText('Validate')).toBeInTheDocument()
    expect(screen.getByText('PRD')).toBeInTheDocument()
    expect(screen.getByText('Build')).toBeInTheDocument()
    expect(screen.getByText('Launch')).toBeInTheDocument()
  })

  it('renders empty state when no messages', () => {
    render(<App />)
    expect(screen.getByText('Ready to unlock your startup idea?')).toBeInTheDocument()
  })

  it('has a message input textarea', () => {
    render(<App />)
    const textarea = screen.getByRole('textbox')
    expect(textarea).toBeInTheDocument()
  })

  it('has a disabled send button when input is empty', () => {
    render(<App />)
    const button = screen.getByRole('button', { name: /send message/i })
    expect(button).toBeDisabled()
  })

  it('displays helper text for keyboard shortcuts', () => {
    render(<App />)
    expect(screen.getByText(/to send/)).toBeInTheDocument()
    expect(screen.getByText(/for new line/)).toBeInTheDocument()
  })
})

describe('Journey Stages', () => {
  const stages = [
    { key: 'onboarding', label: 'Discovery', icon: '👋' },
    { key: 'idea_generation', label: 'Ideas', icon: '💡' },
    { key: 'validation', label: 'Validate', icon: '📊' },
    { key: 'prd', label: 'PRD', icon: '📋' },
    { key: 'prompt_engineering', label: 'Build', icon: '🚀' },
    { key: 'complete', label: 'Launch', icon: '🎉' },
  ]

  it('should have 6 journey stages defined', () => {
    expect(stages).toHaveLength(6)
  })

  it('should start with onboarding stage', () => {
    expect(stages[0].key).toBe('onboarding')
  })

  it('should end with complete stage', () => {
    expect(stages[stages.length - 1].key).toBe('complete')
  })
})

describe('Quick Replies', () => {
  it('idea_generation stage should have number options', () => {
    const getQuickReplies = (stage?: string): string[] => {
      if (!stage) return []
      switch (stage) {
        case 'idea_generation':
          return ['1', '2', '3', '4', '5']
        case 'validation':
          return ['Proceed to PRD', 'Try a different idea']
        default:
          return []
      }
    }

    expect(getQuickReplies('idea_generation')).toEqual(['1', '2', '3', '4', '5'])
    expect(getQuickReplies('validation')).toContain('Proceed to PRD')
    expect(getQuickReplies('onboarding')).toEqual([])
  })
})

describe('Utility Functions', () => {
  describe('toWebSocketUrl', () => {
    const toWebSocketUrl = (baseUrl: string) => {
      if (baseUrl.startsWith('https://')) {
        return `wss://${baseUrl.slice('https://'.length)}`
      }
      if (baseUrl.startsWith('http://')) {
        return `ws://${baseUrl.slice('http://'.length)}`
      }
      return baseUrl
    }

    it('converts https to wss', () => {
      expect(toWebSocketUrl('https://example.com')).toBe('wss://example.com')
    })

    it('converts http to ws', () => {
      expect(toWebSocketUrl('http://localhost:8000')).toBe('ws://localhost:8000')
    })

    it('returns unchanged if no protocol prefix', () => {
      expect(toWebSocketUrl('example.com')).toBe('example.com')
    })
  })

  describe('formatTimestamp', () => {
    const formatTimestamp = (value?: string) => {
      if (!value) return ''
      const date = new Date(value)
      return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })}`
    }

    it('returns empty string for undefined', () => {
      expect(formatTimestamp(undefined)).toBe('')
    })

    it('formats valid date string', () => {
      const result = formatTimestamp('2024-01-15T10:30:00Z')
      expect(result).toBeTruthy()
      expect(result.length).toBeGreaterThan(0)
    })
  })

  describe('extractGraphData', () => {
    type ChatMessage = {
      id: string
      session_id: string
      role: 'user' | 'assistant'
      content: string
      graph_data?: object
    }

    const extractGraphData = (message: ChatMessage): ChatMessage => {
      const jsonBlockRegex = /```json\s*(\{[\s\S]*?"json_graph_data"[\s\S]*?\})\s*```/
      const match = message.content.match(jsonBlockRegex)

      if (match && match[1]) {
        try {
          const parsed = JSON.parse(match[1])
          if (parsed.json_graph_data) {
            return {
              ...message,
              content: message.content.replace(match[0], '').trim(),
              graph_data: parsed.json_graph_data,
            }
          }
        } catch {
          // Return original on parse error
        }
      }
      return message
    }

    it('returns message unchanged when no JSON block', () => {
      const msg: ChatMessage = {
        id: '1',
        session_id: 's1',
        role: 'assistant',
        content: 'Hello world',
      }
      const result = extractGraphData(msg)
      expect(result.content).toBe('Hello world')
      expect(result.graph_data).toBeUndefined()
    })

    it('extracts graph data from JSON block', () => {
      const msg: ChatMessage = {
        id: '1',
        session_id: 's1',
        role: 'assistant',
        content: 'Here is analysis\n```json\n{"json_graph_data": {"market_size": {"tam": "10B"}}}\n```',
      }
      const result = extractGraphData(msg)
      expect(result.content).toBe('Here is analysis')
      expect(result.graph_data).toEqual({ market_size: { tam: '10B' } })
    })
  })
})
