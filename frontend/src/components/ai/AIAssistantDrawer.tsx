import React, { useState, useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import {
  Bot,
  X,
  Send,
  Trash2,
  RefreshCw,
  Info,
  ShoppingCart,
  Receipt,
  Boxes,
  TrendingUp,
  ShieldAlert,
  HeartPulse,
  Wrench,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { mlService, ToolCallExecution } from '@/services/erp.service'
import { useAuth } from '@/hooks/useAuth'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: string[]
  tools_used?: ToolCallExecution[]
}

interface AIAssistantDrawerProps {
  isOpen: boolean
  onClose: () => void
}

export const AIAssistantDrawer: React.FC<AIAssistantDrawerProps> = ({
  isOpen,
  onClose,
}) => {
  const location = useLocation()
  const { activeCompany } = useAuth()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({})


  // Initialize messages from sessionStorage if available
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const stored = sessionStorage.getItem('alladin_ai_chat')
      if (stored) return JSON.parse(stored)
    } catch {
      // ignore
    }
    return [
      {
        id: 'welcome-1',
        role: 'assistant',
        content: `Hello! I am your ALLADIN Decision Intelligence Copilot. I can analyze your company records, explain ML forecasts, and inspect inventory telemetry for ${
          activeCompany?.company_name || 'your workspace'
        }. How can I assist you today?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]
  })

  // Save messages to sessionStorage
  useEffect(() => {
    try {
      sessionStorage.setItem('alladin_ai_chat', JSON.stringify(messages))
    } catch {
      // ignore
    }
  }, [messages])

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
    }
  }, [messages, isOpen])

  // Contextual suggested prompts based on current route
  const getContextualPrompts = () => {
    const path = location.pathname
    if (path.includes('/products') || path.includes('/inventory') || path.includes('/warehouses')) {
      return [
        'Which products may need replenishment?',
        'Show items below reorder threshold.',
        'What is our total stock valuation?',
      ]
    }
    if (path.includes('/revenue') || path.includes('/profit')) {
      return [
        'Explain the revenue forecast.',
        'What factors affect our net profit projection?',
        'How does XGBoost compare to SARIMA?',
      ]
    }
    if (path.includes('/sales') || path.includes('/invoices')) {
      return [
        "Summarize this month's sales.",
        'Are there any overdue customer invoices?',
        'What is our average order value?',
      ]
    }
    if (path.includes('/expenses')) {
      return [
        'Show unusual expenses that need review.',
        'Which expense category had the highest increase?',
        'Are operating expenses within budget?',
      ]
    }
    if (path.includes('/business-health')) {
      return [
        'What is affecting our business health score?',
        'How can we improve our receivable aging ratio?',
        'Evaluate our cashflow runway.',
      ]
    }
    return [
      "Summarize this month's sales.",
      'Which products may need replenishment?',
      'Explain the revenue forecast.',
      'Show unusual expenses that need review.',
    ]
  }

  const handleSend = async (messageToSend?: string) => {
    const text = (messageToSend ?? input).trim()
    if (!text || isLoading) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMessage])
    if (!messageToSend) setInput('')
    setIsLoading(true)
    setError(null)

    try {
      const response = await mlService.chatAssistant(text, {
        current_page: location.pathname,
        company_id: activeCompany?.company_id || activeCompany?.id,
      })

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content:
          response?.message ||
          'Analysis complete based on current ledger and model telemetry.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        tools_used: response?.tools_used,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch {
      setError(
        'Unable to query the AI intelligence engine. Please check backend connection and retry.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const getToolMeta = (toolName: string) => {
    switch (toolName) {
      case 'get_sales_analysis':
        return { label: 'Sales Analysis', icon: ShoppingCart, bg: 'bg-emerald-50 text-emerald-800 border-emerald-200' }
      case 'get_expense_summary':
        return { label: 'Expense Summary', icon: Receipt, bg: 'bg-amber-50 text-amber-800 border-amber-200' }
      case 'get_inventory_status':
        return { label: 'Inventory & Stock', icon: Boxes, bg: 'bg-blue-50 text-blue-800 border-blue-200' }
      case 'forecast_revenue':
        return { label: 'Revenue Forecast (ML)', icon: TrendingUp, bg: 'bg-purple-50 text-purple-800 border-purple-200' }
      case 'detect_transaction_anomalies':
        return { label: 'Anomaly Detection', icon: ShieldAlert, bg: 'bg-rose-50 text-rose-800 border-rose-200' }
      case 'get_business_health_analysis':
        return { label: 'Business Health', icon: HeartPulse, bg: 'bg-teal-50 text-teal-800 border-teal-200' }
      default:
        return { label: toolName.replace(/_/g, ' '), icon: Wrench, bg: 'bg-slate-50 text-slate-800 border-slate-200' }
    }
  }


  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const clearChat = () => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: 'Conversation history cleared. How can I assist you with your business data?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ])
    sessionStorage.removeItem('alladin_ai_chat')
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-hidden pointer-events-none">
      {/* Dim overlay that allows seeing the background page while overlaying */}
      <div
        className="absolute inset-0 bg-slate-900/20 backdrop-blur-[1px] transition-opacity pointer-events-auto"
        onClick={onClose}
      />

      {/* Slide-over Right Panel */}
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10 pointer-events-auto">
        <div className="w-screen max-w-md bg-white border-l border-slate-200 shadow-2xl flex flex-col ring-1 ring-slate-900/5 animate-slide-in">
          {/* Header */}
          <div className="px-5 py-4 border-b border-slate-200 bg-slate-50/80 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center font-bold shadow-sm">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-900">ALLADIN AI Assistant</h3>
                  <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
                </div>
                <p className="text-[10px] text-slate-500 font-medium">
                  {activeCompany?.company_name || 'Active Workspace'} &bull; Database Grounded
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={clearChat}
                title="Clear conversation"
                className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={onClose}
                title="Close drawer (ESC)"
                className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Context Notice Banner */}
          <div className="px-4 py-2 bg-teal-50/70 border-b border-teal-100/60 flex items-center justify-between text-[11px] text-teal-800">
            <span className="flex items-center gap-1.5 truncate">
              <Info className="w-3.5 h-3.5 shrink-0 text-teal-600" />
              <span className="truncate">Context active: {location.pathname}</span>
            </span>
            <span className="text-[10px] uppercase font-bold tracking-wider text-teal-700 bg-white/70 px-1.5 py-0.5 rounded border border-teal-200/50">
              Grounded
            </span>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${
                  msg.role === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-1 px-1">
                  <span className="text-[10px] font-semibold text-slate-500">
                    {msg.role === 'user' ? 'You' : 'ALLADIN Copilot'}
                  </span>
                  <span className="text-[9px] text-slate-400">{msg.timestamp}</span>
                </div>

                <div
                  className={`p-3.5 rounded-xl text-xs leading-relaxed max-w-[88%] ${
                    msg.role === 'user'
                      ? 'bg-teal-700 text-white font-medium rounded-tr-none shadow-sm'
                      : 'bg-slate-50 text-slate-800 border border-slate-200 rounded-tl-none whitespace-pre-wrap'
                  }`}
                >
                  <div>{msg.content}</div>

                  {msg.tools_used && msg.tools_used.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-slate-200/80 space-y-1.5">
                      <div className="flex items-center gap-1 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                        <Wrench className="w-3 h-3 text-teal-600" />
                        <span>Verified ERP Tools Executed</span>
                      </div>
                      <div className="space-y-1">
                        {msg.tools_used.map((toolCall, tIdx) => {
                          const meta = getToolMeta(toolCall.tool)
                          const IconComponent = meta.icon
                          const toggleKey = `${msg.id}-${tIdx}`
                          const isExpanded = !!expandedTools[toggleKey]

                          return (
                            <div
                              key={tIdx}
                              className={`rounded-lg border text-[11px] overflow-hidden ${meta.bg}`}
                            >
                              <button
                                type="button"
                                onClick={() =>
                                  setExpandedTools((prev) => ({
                                    ...prev,
                                    [toggleKey]: !prev[toggleKey],
                                  }))
                                }
                                className="w-full px-2.5 py-1.5 flex items-center justify-between font-medium text-left hover:opacity-90 transition-opacity"
                              >
                                <span className="flex items-center gap-1.5">
                                  <IconComponent className="w-3.5 h-3.5 shrink-0" />
                                  <span className="truncate">{meta.label}</span>
                                </span>
                                {isExpanded ? (
                                  <ChevronDown className="w-3 h-3 opacity-60 shrink-0" />
                                ) : (
                                  <ChevronRight className="w-3 h-3 opacity-60 shrink-0" />
                                )}
                              </button>
                              {isExpanded && (
                                <div className="px-2.5 pb-2 pt-1 border-t border-current/10 text-[10px] space-y-1 font-normal opacity-90">
                                  {toolCall.summary && (
                                    <p className="font-medium">{toolCall.summary}</p>
                                  )}
                                  {toolCall.args && Object.keys(toolCall.args).length > 0 && (
                                    <p className="font-mono text-[9px] opacity-75">
                                      Args: {JSON.stringify(toolCall.args)}
                                    </p>
                                  )}
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-500 w-fit">
                <Spinner size="sm" />
                <span>Reading company ledger and synthesizing insight...</span>
              </div>
            )}

            {error && (
              <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 space-y-2">
                <p>{error}</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleSend(messages[messages.length - 1]?.content)}
                  leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                >
                  Retry Query
                </Button>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Contextual Suggestion Chips */}
          <div className="px-4 py-2 border-t border-slate-100 bg-slate-50/50">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
              Suggested Prompts for this View
            </span>
            <div className="flex flex-wrap gap-1.5">
              {getContextualPrompts().map((prompt, i) => (
                <button
                  key={i}
                  disabled={isLoading}
                  onClick={() => handleSend(prompt)}
                  className="px-2.5 py-1 text-[11px] rounded-md border border-slate-200 bg-white text-slate-700 hover:border-teal-400 hover:text-teal-800 hover:bg-teal-50/50 transition-colors text-left"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          {/* Input Box Footer */}
          <div className="p-3 border-t border-slate-200 bg-white">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleSend()
              }}
              className="space-y-2"
            >
              <div className="relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a question about your sales, forecasts, or inventory (Enter to send)..."
                  rows={2}
                  disabled={isLoading}
                  className="w-full text-xs p-2.5 pr-10 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-600 focus:border-teal-600 resize-none bg-slate-50 placeholder:text-slate-400"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="absolute right-2.5 bottom-3 p-1.5 rounded-md bg-teal-600 text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-teal-700 transition-colors shadow-sm"
                  title="Send message"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="flex items-center justify-between text-[10px] text-slate-400 px-1">
                <span>Shift + Enter for new line</span>
                <span>Protected by tenant isolation</span>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
