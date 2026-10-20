import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Send,
  Bot,
  User,
  ShoppingCart,
  Receipt,
  Boxes,
  TrendingUp,
  ShieldAlert,
  HeartPulse,
  Building2,
  Wrench,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { mlService, ToolCallExecution } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { useAuth } from '@/hooks/useAuth'

interface ChatMessage {
  sender: 'user' | 'assistant'
  text: string
  timestamp: string
  tools_used?: ToolCallExecution[]
  provider?: string
  model?: string
  fallback_used?: boolean
  fallback_reason?: string
}

export const MlChatPage: React.FC = () => {
  const { activeCompany } = useAuth()
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({})
  const [providerInfo, setProviderInfo] = useState<{ provider: string; model?: string }>({
    provider: 'ollama',
    model: 'qwen3:4b',
  })
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: 'assistant',
      text: `Hello! I am your ALLADIN Decision Intelligence Copilot. How can I assist you with company profile queries, revenue forecasts, stock replenishment, or business health for ${
        activeCompany?.company_name || 'your organization'
      }?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ])
  const [inputMessage, setInputMessage] = useState('')

  const getToolMeta = (toolName: string) => {
    switch (toolName) {
      case 'get_company_profile':
        return { label: 'Company Profile', icon: Building2, bg: 'bg-indigo-50 text-indigo-800 border-indigo-200' }
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

  const chatMutation = useMutation({
    mutationFn: (msg: string) =>
      mlService.chatAssistant(msg, {
        company_id: activeCompany?.company_id || activeCompany?.id,
      }),
    onSuccess: (data) => {
      if (data?.provider) {
        setProviderInfo({ provider: data.provider, model: data.model })
      }
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: data?.message || 'I have analyzed your query based on current ledger records and ML forecasts.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          tools_used: data?.tools_used,
          provider: data?.provider,
          model: data?.model,
          fallback_used: data?.fallback_used,
          fallback_reason: data?.fallback_reason,
        },
      ])
    },
    onError: (err: any) => {
      const errDetail =
        err?.response?.data?.error?.message ||
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        'Unable to query the AI intelligence engine. Please check backend connection and retry.'
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: `⚠️ Error: ${errDetail}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    },
  })

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim()) return

    const userText = inputMessage.trim()
    setInputMessage('')
    setMessages((prev) => [
      ...prev,
      {
        sender: 'user',
        text: userText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ])

    chatMutation.mutate(userText)
  }

  const suggestedPrompts = [
    'What is the name of our company and our business profile?',
    "Summarize sales and revenue for December 2024.",
    'Which products may need replenishment?',
    'Explain the 6-month revenue forecast.',
    'Show unusual expenses that need review.',
    'What is affecting our business health score?',
  ]

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title="AI Copilot & Business Assistant"
        description="Ask natural language questions grounded in your company's live ledger records, warehouse stock levels, and predictive ML models"
        icon={<Bot className="w-5 h-5 text-teal-700" />}
        badge={<span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-teal-50 text-teal-800 border border-teal-200">AI Copilot</span>}
        breadcrumbs={[
          { label: 'Apps', href: '/apps' },
          { label: 'Intelligence' },
          { label: 'AI Copilot' },
        ]}
      />

      <Card className="h-[560px] flex flex-col justify-between overflow-hidden bg-white border-slate-200 shadow-sm">
        <CardHeader className="border-b border-slate-100 py-3 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm font-semibold flex items-center gap-2 text-slate-900">
              <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
              <span>ALLADIN Intelligence Copilot Active</span>
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              {activeCompany?.company_name || 'Active Workspace'} &bull; Database Grounded &bull; Multi-Tenant Isolated
            </CardDescription>
          </div>
          <Badge
            variant="default"
            className={
              providerInfo.provider === 'ollama'
                ? 'bg-blue-50 text-blue-800 border-blue-200'
                : providerInfo.provider === 'gemini'
                ? 'bg-teal-50 text-teal-800 border-teal-200'
                : 'bg-amber-50 text-amber-800 border-amber-200'
            }
          >
            {providerInfo.provider === 'ollama'
              ? `FastAPI • Ollama (${providerInfo.model || 'qwen3:4b'})`
              : providerInfo.provider === 'gemini'
              ? 'FastAPI • Gemini Grounded'
              : 'FastAPI • ERP Rule Engine'}
          </Badge>
        </CardHeader>

        {/* Chat Messages Body */}
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 ${
                  msg.sender === 'user'
                    ? 'bg-teal-700 text-white shadow-sm'
                    : 'bg-slate-100 text-teal-800 border border-slate-200'
                }`}
              >
                {msg.sender === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>
              <div
                className={`max-w-[82%] p-3.5 rounded-xl text-xs leading-relaxed space-y-1 ${
                  msg.sender === 'user'
                    ? 'bg-teal-700 text-white rounded-tr-none shadow-sm'
                    : 'bg-slate-50 text-slate-800 border border-slate-200 rounded-tl-none whitespace-pre-wrap'
                }`}
              >
                <div>{msg.text}</div>

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
                        const toggleKey = `page-${i}-${tIdx}`
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

                <div className="flex items-center justify-between text-[9px] pt-1 gap-2">
                  {msg.provider && msg.sender === 'assistant' ? (
                    <span className="font-medium text-slate-500 truncate">
                      {msg.provider === 'ollama'
                        ? `Ollama (${msg.model || 'qwen3:4b'})`
                        : msg.provider === 'gemini'
                        ? 'Gemini Grounded'
                        : 'ERP Rule Engine'}
                      {msg.fallback_used ? ' • Fallback' : ''}
                    </span>
                  ) : <span />}
                  <span className={`shrink-0 ${msg.sender === 'user' ? 'text-teal-200' : 'text-slate-400'}`}>
                    {msg.timestamp}
                  </span>
                </div>
              </div>
            </div>
          ))}

          {chatMutation.isPending && (
            <div className="flex items-center gap-2 text-xs text-slate-500 p-2 bg-slate-50 rounded-lg w-fit border border-slate-200">
              <Spinner size="sm" />
              <span>Synthesizing answer from company records...</span>
            </div>
          )}
        </CardContent>

        {/* Suggested Prompts Strip */}
        <div className="px-4 py-2 border-t border-slate-100 bg-slate-50/60">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider whitespace-nowrap">
              Suggestions:
            </span>
            {suggestedPrompts.map((prompt, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setInputMessage(prompt)
                }}
                className="px-2.5 py-1 text-[11px] rounded-md border border-slate-200 bg-white text-slate-700 hover:border-teal-400 hover:text-teal-800 whitespace-nowrap transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Chat Input */}
        <div className="p-3 border-t border-slate-200 bg-white">
          <form onSubmit={handleSend} className="flex items-center gap-2">
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask e.g. 'Summarize this month's revenue and pending orders'..."
              className="flex-1 text-xs"
            />
            <Button
              variant="primary"
              type="submit"
              isLoading={chatMutation.isPending}
              leftIcon={<Send className="w-3.5 h-3.5" />}
            >
              Send
            </Button>
          </form>
        </div>
      </Card>
    </div>
  )
}
