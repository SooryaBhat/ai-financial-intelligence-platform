import React, { useState, useEffect, useRef, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Send,
  Bot,
  Brain,
  Sparkles,
  Menu,
  RotateCcw,
  AlertCircle,
  FileText,
  ChevronDown,
  ChevronUp,
  Mic,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { useAuth } from '@/hooks/useAuth'
import {
  chatService,
  ChatMessageItem,
} from '@/services/chat.service'
import { ChatSidebar } from '@/components/chat/ChatSidebar'
import { ChatMessageItemView } from '@/components/chat/ChatMessageItemView'
import { MemorySettingsModal } from '@/components/chat/MemorySettingsModal'
import { VoiceConversationModal } from '@/components/voice/VoiceConversationModal'
import { ModelSelector } from '@/components/chat/ModelSelector'
import { ModuleIcon } from '@/components/ui/ModuleIcon'

export const MlChatPage: React.FC = () => {
  const { activeCompany } = useAuth()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const [inputMessage, setInputMessage] = useState('')
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [isMemoryModalOpen, setIsMemoryModalOpen] = useState(false)
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false)
  const [showSummaryDetails, setShowSummaryDetails] = useState(false)

  // Default provider: Ollama (Local qwen3:4b), with user preference persistence
  const [selectedProvider, setSelectedProvider] = useState<'ollama' | 'gemini'>(() => {
    const saved = localStorage.getItem('alladin_llm_provider')
    return saved === 'gemini' ? 'gemini' : 'ollama'
  })

  const [providerInfo, setProviderInfo] = useState<{ provider: string; model?: string }>({
    provider: selectedProvider,
    model: selectedProvider === 'ollama' ? 'qwen3:4b' : '2.5-flash',
  })

  const handleSelectProvider = (prov: 'ollama' | 'gemini') => {
    setSelectedProvider(prov)
    localStorage.setItem('alladin_llm_provider', prov)
    setProviderInfo({
      provider: prov,
      model: prov === 'ollama' ? 'qwen3:4b' : '2.5-flash',
    })
  }

  // Selected session ID from URL or null
  const selectedSessionId = searchParams.get('session_id')

  // 1. Fetch user sessions
  const {
    data: sessions = [],
    isLoading: isLoadingSessions,
  } = useQuery({
    queryKey: ['chat-sessions', activeCompany?.id || activeCompany?.company_id],
    queryFn: () => chatService.listSessions(),
    enabled: !!(activeCompany?.id || activeCompany?.company_id),
  })

  // 2. Fetch active memories count
  const { data: activeMemories = [] } = useQuery({
    queryKey: ['ai-memories-count', activeCompany?.id || activeCompany?.company_id],
    queryFn: () => chatService.listMemories(),
    enabled: !!(activeCompany?.id || activeCompany?.company_id),
  })

  // Resolve current active session object
  const activeSession = sessions.find((s) => s.id === selectedSessionId) || null

  // Auto-select latest session if available and none selected
  useEffect(() => {
    if (!selectedSessionId && sessions.length > 0) {
      setSearchParams({ session_id: sessions[0].id }, { replace: true })
    }
  }, [sessions, selectedSessionId, setSearchParams])

  // 3. Fetch messages for active session
  const {
    data: messages = [],
    isLoading: isLoadingMessages,
  } = useQuery({
    queryKey: ['chat-messages', selectedSessionId],
    queryFn: () => (selectedSessionId ? chatService.listMessages(selectedSessionId) : Promise.resolve([])),
    enabled: !!selectedSessionId,
  })

  // Optimistic pending user messages (displayed immediately on submit before server responds)
  const [pendingMessages, setPendingMessages] = useState<ChatMessageItem[]>([])
  // Store last submitted text to allow clean retry on failure
  const [lastSubmittedText, setLastSubmittedText] = useState<string>('')

  // Merge server messages with unconfirmed pending messages
  const displayMessages = useMemo(() => {
    if (!pendingMessages.length) return messages
    // Filter out optimistic messages whose content has now appeared in server messages
    const unconfirmed = pendingMessages.filter(
      (pm) => !messages.some((sm) => sm.role === 'user' && sm.content.trim() === pm.content.trim())
    )
    return [...messages, ...unconfirmed]
  }, [messages, pendingMessages])

  // Reset pending state when active session changes
  useEffect(() => {
    setPendingMessages([])
    setLastSubmittedText('')
  }, [selectedSessionId])

  // Focus input on session change
  useEffect(() => {
    inputRef.current?.focus()
  }, [selectedSessionId])

  // 4. Send Message Mutation
  const sendMutation = useMutation({
    mutationFn: (text: string) =>
      chatService.sendMessage(text, selectedSessionId || undefined, selectedProvider),
    onSuccess: (data) => {
      if (data?.provider) {
        setProviderInfo({ provider: data.provider, model: data.model })
      }
      // If we didn't have a session, select the newly returned session
      if (!selectedSessionId && data.session_id) {
        setSearchParams({ session_id: data.session_id }, { replace: true })
      }
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['chat-messages', data.session_id || selectedSessionId] })
      queryClient.invalidateQueries({ queryKey: ['ai-memories-count'] })
    },
  })

  // Scroll to bottom on new messages or optimistic submits
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [displayMessages, isLoadingMessages, sendMutation.isPending])

  // 5. Create Session Mutation
  const createSessionMutation = useMutation({
    mutationFn: (title?: string) => chatService.createSession(title),
    onSuccess: (newSession) => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
      setSearchParams({ session_id: newSession.id })
    },
  })

  // 6. Rename Session Mutation
  const renameMutation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) =>
      chatService.updateSession(id, { title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
    },
  })

  // 7. Delete Session Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => chatService.deleteSession(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
      if (selectedSessionId === deletedId) {
        const remaining = sessions.filter((s) => s.id !== deletedId)
        if (remaining.length > 0) {
          setSearchParams({ session_id: remaining[0].id })
        } else {
          setSearchParams({})
        }
      }
    },
  })

  const handleSend = (e?: React.FormEvent, directText?: string) => {
    if (e) e.preventDefault()
    const text = (directText || inputMessage).trim()
    if (!text || sendMutation.isPending) return

    setLastSubmittedText(text)

    // Capture text and immediately append optimistic user message
    const tempId = `optimistic-${Date.now()}`
    const optimisticMsg: ChatMessageItem = {
      id: tempId,
      session_id: selectedSessionId || 'pending',
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    setPendingMessages((prev) => [...prev, optimisticMsg])
    setInputMessage('')

    sendMutation.mutate(text)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = () => {
    createSessionMutation.mutate('New Conversation')
  }

  const suggestedPrompts = [
    'What is our company profile and active currency?',
    'Summarize sales and revenue performance for December 2024.',
    'Which products are below the reorder threshold?',
    'Explain the 6-month revenue forecast.',
    'Show unusual transactions that need review.',
    'What is affecting our business health score?',
  ]

  return (
    <div className="flex h-[calc(100vh-4.25rem)] bg-slate-50 overflow-hidden -m-4 sm:-m-6 lg:-m-8 min-w-0">
      {/* ── Left Sidebar (ChatGPT-style) ───────────────────────── */}
      <ChatSidebar
        sessions={sessions}
        activeSessionId={selectedSessionId}
        isLoadingSessions={isLoadingSessions}
        onSelectSession={(id) => setSearchParams({ session_id: id })}
        onNewChat={handleNewChat}
        onRenameSession={(id, title) => renameMutation.mutate({ id, title })}
        onDeleteSession={(id) => deleteMutation.mutate(id)}
        onOpenMemorySettings={() => setIsMemoryModalOpen(true)}
        activeMemoriesCount={activeMemories.length}
        providerInfo={providerInfo}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
      />

      {/* ── Main Chat Area ─────────────────────────────────────── */}
      <div className="flex-1 flex flex-col h-full bg-white min-w-0">
        {/* Chat Header */}
        <header className="h-14 border-b border-slate-200 px-4 flex items-center justify-between shrink-0 bg-white shadow-xs">
          <div className="flex items-center space-x-3 min-w-0">
            {isSidebarCollapsed && (
              <button
                onClick={() => setIsSidebarCollapsed(false)}
                className="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg"
                title="Open sidebar"
              >
                <Menu className="w-5 h-5" />
              </button>
            )}

            <div className="min-w-0">
              <h1 className="text-sm font-semibold text-slate-900 truncate">
                {activeSession?.title || 'New AI Conversation'}
              </h1>
              <p className="text-[11px] text-slate-400 truncate">
                {activeCompany?.company_name || 'Organization'} • Scoped to authenticated ERP records
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Voice Mode Button */}
            <button
              onClick={() => setIsVoiceModalOpen(true)}
              className="flex items-center space-x-1.5 px-3 py-1 text-xs text-white bg-teal-700 hover:bg-teal-800 rounded-full font-medium shadow-xs transition-colors"
              title="Start voice conversation with Alladin character"
            >
              <Mic className="w-3.5 h-3.5" />
              <span>Voice Mode</span>
            </button>

            {/* Memory indicator button */}
            <button
              onClick={() => setIsMemoryModalOpen(true)}
              className="flex items-center space-x-1.5 px-2.5 py-1 text-xs text-slate-600 hover:text-teal-800 bg-slate-100 hover:bg-teal-50 border border-slate-200 hover:border-teal-200 rounded-full transition-colors"
              title="View and configure persistent AI memories"
            >
              <Brain className="w-3.5 h-3.5 text-teal-700" />
              <span className="hidden sm:inline font-medium">Memory</span>
              {activeMemories.length > 0 && (
                <span className="px-1.5 py-0.2 bg-teal-700 text-white text-[10px] rounded-full font-bold">
                  {activeMemories.length}
                </span>
              )}
            </button>

            {/* Interactive Model Selector (Ollama Default / Gemini Alternative) */}
            <ModelSelector
              selectedProvider={selectedProvider}
              onSelectProvider={handleSelectProvider}
            />
          </div>
        </header>

        {/* Running Conversation Summary Banner (if present) */}
        {activeSession?.summary && (
          <div className="bg-slate-50/90 border-b border-slate-200 px-4 py-2 text-xs text-slate-600 flex items-center justify-between transition-all">
            <div className="flex items-center space-x-2 min-w-0 flex-1 mr-2">
              <FileText className="w-3.5 h-3.5 text-teal-700 shrink-0" />
              <span className="font-semibold text-slate-700 shrink-0">Context Summary:</span>
              <span className="truncate text-slate-500 text-[11px]">{activeSession.summary}</span>
            </div>
            <button
              onClick={() => setShowSummaryDetails((prev) => !prev)}
              className="text-[11px] text-teal-700 hover:text-teal-800 font-medium shrink-0 flex items-center"
            >
              {showSummaryDetails ? 'Hide' : 'View'}
              {showSummaryDetails ? <ChevronUp className="w-3 h-3 ml-0.5" /> : <ChevronDown className="w-3 h-3 ml-0.5" />}
            </button>
          </div>
        )}

        {showSummaryDetails && activeSession?.summary && (
          <div className="bg-teal-50/50 border-b border-teal-200/60 p-3 text-xs text-slate-700 leading-relaxed">
            <div className="font-semibold text-teal-900 mb-1">Preserved Long-Conversation Summary</div>
            <p className="text-slate-600 text-xs">{activeSession.summary}</p>
          </div>
        )}

        {/* Messages Scroll Thread */}
        <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 space-y-3">
          {isLoadingMessages ? (
            <div className="py-16 flex flex-col items-center justify-center space-y-2 text-slate-400">
              <Spinner size="lg" />
              <p className="text-xs">Loading conversation history...</p>
            </div>
          ) : displayMessages.length === 0 ? (
            /* Empty State / Welcome Screen */
            <div className="py-12 max-w-2xl mx-auto text-center space-y-6">
              <div className="mx-auto flex justify-center">
                <ModuleIcon name="ai-copilot-voice" size="xl" className="w-16 h-16" />
              </div>

              <div className="space-y-2">
                <h2 className="text-lg font-semibold text-slate-900">
                  ALLADIN AI Financial Copilot
                </h2>
                <p className="text-xs text-slate-500 max-w-lg mx-auto leading-relaxed">
                  Ask natural language questions grounded in live ledger records, inventory levels,
                  and predictive machine learning models for{' '}
                  <span className="font-semibold text-slate-700">
                    {activeCompany?.company_name || 'your enterprise'}
                  </span>
                  .
                </p>
              </div>

              {/* Suggested Questions */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left pt-2">
                {suggestedPrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSend(undefined, prompt)}
                    className="p-3 bg-white border border-slate-200 rounded-xl hover:border-teal-500 hover:shadow-xs transition-all text-xs text-slate-700 hover:text-teal-900 flex items-start space-x-2 text-left group"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-teal-600 mt-0.5 shrink-0 group-hover:scale-110 transition-transform" />
                    <span>{prompt}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {displayMessages.map((msg) => (
                <ChatMessageItemView key={msg.id} message={msg} />
              ))}

              {/* Pending Assistant Response Skeleton */}
              {sendMutation.isPending && (
                <div className="flex justify-start my-4">
                  <div className="flex items-start max-w-2xl space-x-3 w-full">
                    <div className="w-8 h-8 rounded-full bg-teal-700 text-white flex items-center justify-center shrink-0 shadow-sm animate-pulse">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center space-x-2 text-xs text-slate-400">
                        <span className="font-semibold text-slate-800">ALLADIN Copilot</span>
                        <span className="text-[10px] text-teal-700 font-medium animate-pulse">
                          Querying live ERP records & ML models...
                        </span>
                      </div>
                      <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm p-4 text-xs text-slate-500 shadow-sm flex items-center space-x-3">
                        <Spinner size="sm" />
                        <span>Analyzing verified business data and synthesizing response...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Error banner */}
              {sendMutation.isError && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex flex-col sm:flex-row sm:items-center justify-between gap-2 my-2">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                    <span>
                      {(sendMutation.error as any)?.response?.data?.error?.message ||
                        (sendMutation.error as any)?.message ||
                        'Failed to receive AI response. Please retry.'}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 self-end sm:self-auto shrink-0">
                    {selectedProvider === 'ollama' && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-teal-300 text-teal-800 hover:bg-teal-50 text-[11px]"
                        onClick={() => {
                          handleSelectProvider('gemini')
                          if (lastSubmittedText) {
                            handleSend(undefined, lastSubmittedText)
                          }
                        }}
                      >
                        Switch to Gemini (Cloud)
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-rose-300 text-rose-800 hover:bg-rose-100 text-[11px]"
                      onClick={() => {
                        if (lastSubmittedText) {
                          handleSend(undefined, lastSubmittedText)
                        }
                      }}
                    >
                      <RotateCcw className="w-3.5 h-3.5 mr-1" />
                      Retry
                    </Button>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Chat Input Bar */}
        <div className="p-3 sm:p-4 border-t border-slate-200 bg-white shrink-0">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto space-y-1.5">
            <div className="relative flex items-center rounded-xl border border-slate-300 focus-within:border-teal-600 focus-within:ring-1 focus-within:ring-teal-600 bg-white shadow-xs transition-all">
              <textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about sales, revenue forecast, inventory, business health, or tell it to remember a preference..."
                rows={1}
                className="w-full resize-none py-3 pl-4 pr-20 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none max-h-32 bg-transparent"
              />

              <div className="absolute right-2.5 flex items-center space-x-1.5">
                <button
                  type="button"
                  onClick={() => setIsVoiceModalOpen(true)}
                  className="p-1.5 text-slate-400 hover:text-teal-700 hover:bg-teal-50 rounded-lg transition-colors"
                  title="Open Voice Mode with Alladin character"
                >
                  <Mic className="w-4 h-4" />
                </button>

                <button
                  type="submit"
                  disabled={!inputMessage.trim() || sendMutation.isPending}
                  className="p-2 bg-teal-700 text-white rounded-lg hover:bg-teal-800 disabled:opacity-40 disabled:hover:bg-teal-700 transition-colors shadow-xs"
                  title="Send message (Enter)"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-[10px] text-slate-400 px-1">
              <span>Press Enter to send, Shift+Enter for new line</span>
              <span>100% verified ledger truth • RLS isolated</span>
            </div>
          </form>
        </div>
      </div>

      {/* ── Voice Assistant Conversation Modal ───────────────── */}
      {isVoiceModalOpen && (
        <VoiceConversationModal
          isOpen={isVoiceModalOpen}
          onClose={() => {
            setIsVoiceModalOpen(false)
            // Invalidate messages so returning from voice immediately loads turns
            if (selectedSessionId) {
              queryClient.invalidateQueries({ queryKey: ['chat-messages', selectedSessionId] })
            }
            queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
          }}
          activeSessionId={selectedSessionId}
          onSessionUpdated={(newSid) => {
            setSearchParams({ session_id: newSid })
          }}
          companyName={activeCompany?.company_name}
        />
      )}

      {/* ── Persistent Memory Settings Modal ─────────────────── */}
      <MemorySettingsModal
        isOpen={isMemoryModalOpen}
        onClose={() => setIsMemoryModalOpen(false)}
      />
    </div>
  )
}
