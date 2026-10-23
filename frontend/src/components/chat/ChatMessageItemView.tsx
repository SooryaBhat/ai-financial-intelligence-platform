import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import {
  Bot,
  User,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  ShoppingCart,
  Receipt,
  Boxes,
  TrendingUp,
  ShieldAlert,
  HeartPulse,
  Building2,
  BookOpen,
  Wrench,
  AlertCircle,
  Sparkles,
} from 'lucide-react'
import { ToolCallExecution } from '@/services/erp.service'

interface ChatMessageItemViewProps {
  message: {
    id?: string
    role: 'user' | 'assistant' | 'system'
    content: string
    created_at?: string
    metadata?: {
      tools_used?: ToolCallExecution[]
      provider?: string
      model?: string
      fallback_used?: boolean
      fallback_reason?: string
    }
  }
}

export const ChatMessageItemView: React.FC<ChatMessageItemViewProps> = ({ message }) => {
  const [copied, setCopied] = useState(false)
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({})

  const isUser = message.role === 'user'
  const toolsUsed = message.metadata?.tools_used || []
  const provider = message.metadata?.provider
  const model = message.metadata?.model
  const fallbackUsed = message.metadata?.fallback_used
  const fallbackReason = message.metadata?.fallback_reason

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const toggleTool = (toolIndex: number) => {
    setExpandedTools((prev) => ({
      ...prev,
      [toolIndex]: !prev[toolIndex],
    }))
  }

  const getToolMeta = (toolName: string) => {
    switch (toolName) {
      case 'get_company_profile':
        return { label: 'Company Profile', icon: Building2, color: 'text-indigo-700 bg-indigo-50 border-indigo-200' }
      case 'get_sales_analysis':
        return { label: 'Sales & Revenue Analysis', icon: ShoppingCart, color: 'text-emerald-700 bg-emerald-50 border-emerald-200' }
      case 'get_expense_summary':
        return { label: 'Expense Overview', icon: Receipt, color: 'text-amber-700 bg-amber-50 border-amber-200' }
      case 'get_inventory_status':
        return { label: 'Inventory & Stock Telemetry', icon: Boxes, color: 'text-blue-700 bg-blue-50 border-blue-200' }
      case 'forecast_revenue':
        return { label: 'Revenue Forecast (ML Engine)', icon: TrendingUp, color: 'text-purple-700 bg-purple-50 border-purple-200' }
      case 'detect_transaction_anomalies':
        return { label: 'Anomaly & Outlier Detection', icon: ShieldAlert, color: 'text-rose-700 bg-rose-50 border-rose-200' }
      case 'get_business_health_analysis':
        return { label: 'Business Health Composite', icon: HeartPulse, color: 'text-teal-700 bg-teal-50 border-teal-200' }
      case 'search_business_knowledge_base':
        return { label: 'Regulatory & Business Rules RAG', icon: BookOpen, color: 'text-sky-700 bg-sky-50 border-sky-200' }
      case 'get_profit_analysis':
        return { label: 'Profit & Margin Analysis', icon: TrendingUp, color: 'text-emerald-700 bg-emerald-50 border-emerald-200' }
      default:
        return { label: toolName.replace(/_/g, ' '), icon: Wrench, color: 'text-slate-700 bg-slate-50 border-slate-200' }
    }
  }

  const formattedTime = message.created_at
    ? new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : undefined

  if (isUser) {
    return (
      <div className="flex justify-end my-3">
        <div className="flex items-start max-w-2xl space-x-2 flex-row-reverse space-x-reverse">
          <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5">
            <User className="w-4 h-4" />
          </div>

          <div className="space-y-1 text-right">
            <div className="bg-teal-700 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm shadow-sm inline-block text-left leading-relaxed">
              <p className="whitespace-pre-wrap">{message.content}</p>
            </div>
            {formattedTime && (
              <div className="text-[10px] text-slate-400 px-1">{formattedTime}</div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start my-4 group">
      <div className="flex items-start max-w-3xl space-x-3 w-full">
        {/* Assistant Avatar */}
        <div className="w-8 h-8 rounded-full bg-teal-700 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5">
          <Bot className="w-4 h-4" />
        </div>

        <div className="space-y-2 flex-1 min-w-0">
          {/* Header row: Model badge & actions */}
          <div className="flex items-center justify-between text-xs text-slate-400">
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-slate-800 text-xs">ALLADIN Copilot</span>
              {provider && (
                <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600 border border-slate-200 capitalize">
                  {provider === 'ollama'
                    ? `Ollama (${model || 'qwen3:4b'})`
                    : provider === 'gemini'
                    ? `Gemini (${model || 'flash'})`
                    : 'Grounded ERP Engine'}
                </span>
              )}
              {formattedTime && <span className="text-[10px] text-slate-400">{formattedTime}</span>}
            </div>

            <button
              onClick={handleCopy}
              className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-all"
              title="Copy message"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>

          {/* Fallback Notice if active */}
          {fallbackUsed && fallbackReason && (
            <div className="bg-amber-50 border border-amber-200 rounded-md p-2 text-xs text-amber-800 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <span>{fallbackReason}</span>
            </div>
          )}

          {/* Tool Execution Details */}
          {toolsUsed.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider flex items-center space-x-1">
                <Sparkles className="w-3 h-3 text-teal-600" />
                <span>Authorized ERP Tools Executed ({toolsUsed.length})</span>
              </div>

              <div className="space-y-1">
                {toolsUsed.map((tool, idx) => {
                  const meta = getToolMeta(tool.tool)
                  const isExpanded = !!expandedTools[idx]

                  return (
                    <div
                      key={idx}
                      className="border border-slate-200 rounded-md bg-white overflow-hidden text-xs"
                    >
                      <button
                        type="button"
                        onClick={() => toggleTool(idx)}
                        className="w-full flex items-center justify-between p-2 text-left hover:bg-slate-50 transition-colors"
                      >
                        <div className="flex items-center space-x-2 min-w-0">
                          <span
                            className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border ${meta.color}`}
                          >
                            <meta.icon className="w-3 h-3 mr-1" />
                            {meta.label}
                          </span>
                          <span className="text-slate-600 truncate font-mono text-[11px]">
                            {tool.summary || `Executed ${tool.tool}`}
                          </span>
                        </div>
                        <div className="text-slate-400 shrink-0 ml-2">
                          {isExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5" />
                          )}
                        </div>
                      </button>

                      {isExpanded && (
                        <div className="p-2.5 bg-slate-50 border-t border-slate-200 text-[11px] font-mono space-y-2">
                          {Boolean(tool.args && Object.keys(tool.args).length > 0) && (
                            <div>
                              <div className="text-[10px] text-slate-500 font-sans font-semibold uppercase">
                                Parameters Passed:
                              </div>
                              <pre className="bg-white p-2 rounded border border-slate-200 mt-1 text-slate-700 overflow-x-auto">
                                {JSON.stringify(tool.args, null, 2)}
                              </pre>
                            </div>
                          )}

                          {Boolean(tool.result) && (
                            <div>
                              <div className="text-[10px] text-slate-500 font-sans font-semibold uppercase">
                                Verified Data Output:
                              </div>
                              <pre className="bg-white p-2 rounded border border-slate-200 mt-1 text-slate-700 overflow-x-auto max-h-40">
                                {JSON.stringify(tool.result, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Message Markdown Body */}
          <div className="bg-white border border-slate-200/80 rounded-2xl rounded-tl-sm p-4 text-sm text-slate-800 shadow-sm leading-relaxed prose prose-sm max-w-none prose-headings:font-semibold prose-headings:text-slate-900 prose-headings:mt-3 prose-headings:mb-1.5 prose-p:my-1.5 prose-ul:my-1.5 prose-li:my-0.5 prose-table:my-2 prose-th:bg-slate-50 prose-th:p-2 prose-td:p-2 prose-th:border prose-td:border prose-th:border-slate-200 prose-td:border-slate-200">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  )
}
