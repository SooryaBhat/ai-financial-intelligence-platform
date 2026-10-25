import React, { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, Check, Server, Cloud, AlertCircle } from 'lucide-react'
import { chatService } from '@/services/chat.service'

interface ModelSelectorProps {
  selectedProvider: 'ollama' | 'gemini'
  onSelectProvider: (provider: 'ollama' | 'gemini') => void
  className?: string
  compact?: boolean
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedProvider,
  onSelectProvider,
  className = '',
  compact = false,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Fetch available providers and probe status from backend
  const { data: providersData } = useQuery({
    queryKey: ['llm-providers'],
    queryFn: () => chatService.getProviders(),
    staleTime: 30000, // Probe every 30s
    refetchOnWindowFocus: false,
  })

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const providers = providersData?.providers || [
    {
      id: 'ollama',
      name: 'Ollama — Local',
      model: 'qwen3:4b',
      badge: 'Local / Private',
      is_default: true,
      available: true,
      status: 'connected',
      description: 'Runs on local Ollama (qwen3:4b) with complete data privacy.',
    },
    {
      id: 'gemini',
      name: 'Gemini — Cloud',
      model: 'gemini-2.5-flash',
      badge: 'Cloud / High Accuracy',
      is_default: false,
      available: true,
      status: 'configured',
      description: 'Google Gemini 2.5 Flash cloud model for advanced multi-turn reasoning.',
    },
  ]

  const activeInfo = providers.find((p) => p.id === selectedProvider) || providers[0]

  return (
    <div className={`relative inline-block text-left ${className}`} ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-all ${
          selectedProvider === 'ollama'
            ? 'bg-slate-50 hover:bg-slate-100 border-slate-300 text-slate-800'
            : 'bg-teal-50/70 hover:bg-teal-100/70 border-teal-200 text-teal-900'
        }`}
        title="Switch active LLM provider (Ollama Local vs Gemini Cloud)"
      >
        {selectedProvider === 'ollama' ? (
          <Server className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
        ) : (
          <Cloud className="w-3.5 h-3.5 text-teal-600 shrink-0" />
        )}

        <div className="flex items-center space-x-1">
          <span className="font-semibold">
            {selectedProvider === 'ollama' ? (compact ? 'Ollama' : 'Ollama Local') : (compact ? 'Gemini' : 'Gemini Cloud')}
          </span>
          <span className={compact ? 'hidden sm:inline text-[10px] text-slate-500 font-normal' : 'text-[10px] text-slate-500 font-normal'}>
            ({selectedProvider === 'ollama' ? activeInfo.model || 'qwen3:4b' : '2.5-flash'})
          </span>
        </div>

        {/* Status dot */}
        <span
          className={`w-2 h-2 rounded-full shrink-0 ${
            activeInfo.status === 'offline'
              ? 'bg-rose-500 animate-pulse'
              : activeInfo.status === 'model_missing'
              ? 'bg-amber-500'
              : 'bg-emerald-500'
          }`}
          title={`Status: ${activeInfo.status}`}
        />

        <ChevronDown className="w-3 h-3 text-slate-400 shrink-0 ml-0.5" />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-1.5 w-72 rounded-xl bg-white border border-slate-200 shadow-xl z-50 py-1 text-slate-800 animate-in fade-in-50 zoom-in-95 duration-100">
          <div className="px-3 py-1.5 border-b border-slate-100">
            <p className="text-[11px] font-semibold text-slate-900">Select LLM Provider</p>
            <p className="text-[10px] text-slate-500">
              Choose on-device local execution or cloud intelligence.
            </p>
          </div>

          <div className="p-1 space-y-1">
            {providers.map((p) => {
              const isSelected = p.id === selectedProvider
              const isOllama = p.id === 'ollama'

              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => {
                    onSelectProvider(p.id as 'ollama' | 'gemini')
                    setIsOpen(false)
                  }}
                  className={`w-full text-left p-2 rounded-lg flex items-start space-x-2.5 transition-colors ${
                    isSelected
                      ? 'bg-teal-50/60 border border-teal-200/80 text-teal-950'
                      : 'hover:bg-slate-50 border border-transparent text-slate-700'
                  }`}
                >
                  <div className="mt-0.5 shrink-0">
                    {isOllama ? (
                      <Server className={`w-4 h-4 ${isSelected ? 'text-teal-700' : 'text-slate-500'}`} />
                    ) : (
                      <Cloud className={`w-4 h-4 ${isSelected ? 'text-teal-700' : 'text-slate-500'}`} />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-xs font-semibold text-slate-900">{p.name}</span>
                        {p.is_default && (
                          <span className="px-1.5 py-0.2 text-[9px] font-semibold bg-emerald-100 text-emerald-800 rounded">
                            Default
                          </span>
                        )}
                      </div>
                      {isSelected && <Check className="w-3.5 h-3.5 text-teal-700 shrink-0" />}
                    </div>

                    <div className="flex items-center space-x-2 mt-0.5">
                      <span className="text-[10px] font-mono font-medium text-slate-600 bg-slate-100 px-1 rounded">
                        {p.model}
                      </span>
                      <span
                        className={`text-[9px] px-1 rounded font-medium ${
                          p.status === 'connected' || p.status === 'configured'
                            ? 'bg-emerald-50 text-emerald-700'
                            : p.status === 'offline'
                            ? 'bg-rose-50 text-rose-700'
                            : 'bg-amber-50 text-amber-700'
                        }`}
                      >
                        {p.status === 'connected'
                          ? '● Ready'
                          : p.status === 'configured'
                          ? '● Cloud Ready'
                          : p.status === 'offline'
                          ? '● Offline'
                          : `● ${p.status}`}
                      </span>
                    </div>

                    <p className="text-[10px] text-slate-500 mt-1 leading-tight line-clamp-2">
                      {p.description}
                    </p>
                  </div>
                </button>
              )
            })}
          </div>

          {activeInfo.status === 'offline' && selectedProvider === 'ollama' && (
            <div className="m-1 p-2 bg-rose-50 border border-rose-200 rounded-lg text-[10px] text-rose-700 flex items-start space-x-1.5">
              <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-600 mt-0.5" />
              <div>
                <span className="font-semibold">Ollama offline:</span> Start Ollama with{' '}
                <code className="bg-rose-100 px-1 rounded">ollama serve</code> or switch to Gemini Cloud.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
