import React, { useEffect, useState, useRef, useCallback } from 'react'
import {
  Mic,
  Volume2,
  Square,
  RotateCcw,
  Sparkles,
  X,
  MessageSquare,
  Wrench,
  Radio,
  AlertCircle,
  Send,
  Globe,
  RefreshCw,
} from 'lucide-react'
import { AnimatedCharacter } from './AnimatedCharacter'
import {
  VoiceMode,
  VoiceState,
  VoiceTurnResult,
} from '@/services/voice/voice.types'
import { WebVoiceProvider } from '@/services/voice/web-voice.provider'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'

interface VoiceConversationModalProps {
  isOpen: boolean
  onClose: () => void
  activeSessionId?: string | null
  onSessionUpdated?: (sessionId: string) => void
  companyName?: string
}

const SUPPORTED_LANGUAGES = [
  { code: 'en-US', label: 'English (US)' },
  { code: 'en-GB', label: 'English (UK)' },
  { code: 'en-IN', label: 'English (India)' },
  { code: 'es-ES', label: 'Español' },
  { code: 'de-DE', label: 'Deutsch' },
  { code: 'fr-FR', label: 'Français' },
]

export const VoiceConversationModal: React.FC<VoiceConversationModalProps> = ({
  isOpen,
  onClose,
  activeSessionId,
  onSessionUpdated,
  companyName = 'ALLADIN Enterprise',
}) => {
  const [state, setState] = useState<VoiceState>('idle')
  const [mode, setMode] = useState<VoiceMode>('push_to_talk')
  const [selectedLanguage, setSelectedLanguage] = useState<string>('en-US')
  const [audioLevel, setAudioLevel] = useState<number>(0)
  const [visemeLevel, setVisemeLevel] = useState<number>(0)
  const [userTranscript, setUserTranscript] = useState<string>('')
  const [interimTranscript, setInterimTranscript] = useState<string>('')
  const [assistantReply, setAssistantReply] = useState<VoiceTurnResult | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [expandedTools, setExpandedTools] = useState<boolean>(false)

  // Hardware/Speech detection diagnostics telemetry
  const [hasAudioHardware, setHasAudioHardware] = useState<boolean>(false)
  const [hasDetectedSpeech, setHasDetectedSpeech] = useState<boolean>(false)

  // Stable provider instance reference
  const providerRef = useRef<WebVoiceProvider | null>(null)

  // Track props and state in refs so callbacks never go stale
  const onSessionUpdatedRef = useRef(onSessionUpdated)
  onSessionUpdatedRef.current = onSessionUpdated

  const selectedLanguageRef = useRef(selectedLanguage)
  selectedLanguageRef.current = selectedLanguage

  const modeRef = useRef(mode)
  modeRef.current = mode

  // Mount effect: instantiate and initialize provider for this modal session
  useEffect(() => {
    const provider = new WebVoiceProvider()
    providerRef.current = provider

    provider.setSessionId(activeSessionId || null)
    provider.setMode(modeRef.current)
    provider.setLanguage(selectedLanguageRef.current)

    provider.init({
      onStateChange: (newState) => {
        setState(newState)
        if (newState === 'listening') {
          setErrorMessage(null)
        }
      },
      onAudioLevelChange: (lvl) => setAudioLevel(lvl),
      onVisemeLevelChange: (lvl) => setVisemeLevel(lvl),
      onInterimTranscript: (interim) => {
        setInterimTranscript(interim)
      },
      onFinalTranscript: (final) => {
        setUserTranscript(final)
        setInterimTranscript('')
      },
      onAssistantReply: (result) => {
        setAssistantReply(result)
        if (result.session_id) {
          onSessionUpdatedRef.current?.(result.session_id)
        }
      },
      onError: (err) => {
        setErrorMessage(err)
      },
      onAudioStart: () => {
        setHasAudioHardware(true)
      },
      onSpeechStart: () => {
        setHasDetectedSpeech(true)
      },
    })

    return () => {
      provider.destroy('modal_close_unmount')
      if (providerRef.current === provider) {
        providerRef.current = null
      }
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Handle session ID updates without recreating the provider
  useEffect(() => {
    if (activeSessionId && providerRef.current && !providerRef.current.isDestroyedStatus()) {
      providerRef.current.setSessionId(activeSessionId)
    }
  }, [activeSessionId])

  // Handle language change
  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLang = e.target.value
    setSelectedLanguage(newLang)
    if (providerRef.current && !providerRef.current.isDestroyedStatus()) {
      providerRef.current.setLanguage(newLang)
    }
  }

  // Handle mode toggle (Push-to-Talk vs Auto Hands-Free)
  const handleToggleMode = () => {
    const nextMode: VoiceMode = mode === 'push_to_talk' ? 'auto' : 'push_to_talk'
    setMode(nextMode)
    if (providerRef.current && !providerRef.current.isDestroyedStatus()) {
      providerRef.current.setMode(nextMode)
      if (nextMode === 'auto' && state === 'idle') {
        providerRef.current.startListening()
      }
    }
  }

  // Push-to-Talk primary action
  const handleStartListening = () => {
    setErrorMessage(null)
    setHasAudioHardware(false)
    setHasDetectedSpeech(false)
    setUserTranscript('')
    setInterimTranscript('')
    if (providerRef.current && !providerRef.current.isDestroyedStatus()) {
      providerRef.current.startListening()
    }
  }

  const handleStopAndSend = () => {
    if (providerRef.current && !providerRef.current.isDestroyedStatus()) {
      providerRef.current.finishSpeakingManually()
    }
  }

  const handleMicToggle = () => {
    if (state === 'listening') {
      handleStopAndSend()
    } else {
      handleStartListening()
    }
  }

  // Interrupt assistant speech
  const handleInterrupt = () => {
    if (providerRef.current && !providerRef.current.isDestroyedStatus()) {
      providerRef.current.cancelSpeech()
    }
  }

  // Replay assistant speech
  const handleReplay = () => {
    setErrorMessage(null)
    if (assistantReply?.reply && providerRef.current && !providerRef.current.isDestroyedStatus()) {
      providerRef.current.replayLastSpeech(assistantReply.reply)
    }
  }

  // Keyboard accessibility
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!isOpen) return

      if (e.code === 'Escape') {
        e.preventDefault()
        onClose()
      } else if (
        e.code === 'Space' &&
        (e.target as HTMLElement).tagName !== 'INPUT' &&
        (e.target as HTMLElement).tagName !== 'TEXTAREA' &&
        (e.target as HTMLElement).tagName !== 'SELECT'
      ) {
        e.preventDefault()
        handleMicToggle()
      } else if ((e.key === 'r' || e.key === 'R') && (e.target as HTMLElement).tagName !== 'INPUT') {
        e.preventDefault()
        handleReplay()
      } else if ((e.key === 'i' || e.key === 'I') && (e.target as HTMLElement).tagName !== 'INPUT') {
        e.preventDefault()
        handleInterrupt()
      }
    },
    [isOpen, state, assistantReply] // eslint-disable-line react-hooks/exhaustive-deps
  )

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-900/60 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh]">
        {/* ── Top Header ─────────────────────────────────────────── */}
        <header className="px-5 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/70 shrink-0">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-full bg-teal-700 text-white flex items-center justify-center shadow-xs">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-slate-900">Alladin Voice Assistant</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-teal-100 text-teal-800 border border-teal-200">
                  {mode === 'push_to_talk' ? 'Push-to-Talk' : 'Hands-Free'}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                {companyName} • Authorized Ledger Grounding
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Language Selection */}
            <div className="hidden sm:flex items-center space-x-1 px-2 py-1 text-xs rounded-full border border-slate-200 bg-white text-slate-600">
              <Globe className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={selectedLanguage}
                onChange={handleLanguageChange}
                className="text-[11px] bg-transparent border-none outline-hidden cursor-pointer text-slate-700 font-medium"
                title="Recognition Language"
              >
                {SUPPORTED_LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Mode Switch (Push-to-Talk vs Hands-Free) */}
            <button
              onClick={handleToggleMode}
              className="flex items-center space-x-1.5 px-3 py-1 text-xs rounded-full border border-slate-200 hover:border-slate-300 bg-white text-slate-600 transition-colors shadow-2xs"
              title="Toggle Conversational Hands-Free vs Push-to-Talk"
            >
              <Radio className={`w-3.5 h-3.5 ${mode === 'auto' ? 'text-teal-700 animate-pulse' : 'text-slate-400'}`} />
              <span className="text-[11px] font-medium hidden sm:inline">
                {mode === 'push_to_talk' ? 'Push-to-Talk' : 'Hands-Free'}
              </span>
            </button>

            {/* Close / Return to text chat */}
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
              title="Close and return to text chat (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* ── Center Stage: Animated Character & Diagnostics ──────── */}
        <div className="flex-1 flex flex-col items-center justify-center p-6 bg-radial from-teal-50/50 via-white to-slate-50/60 overflow-y-auto">
          {/* Animated Character */}
          <div className="relative my-2">
            <AnimatedCharacter
              state={state}
              audioLevel={audioLevel}
              visemeLevel={visemeLevel}
            />
          </div>

          {/* Current State Pill Badge */}
          <div className="mt-2 flex items-center space-x-2 px-3.5 py-1.5 rounded-full text-xs font-medium shadow-2xs transition-all duration-200">
            {state === 'listening' && (
              <div className="flex items-center space-x-2 text-teal-800 bg-teal-50 border border-teal-200 px-3 py-1 rounded-full">
                <span className="w-2.5 h-2.5 rounded-full bg-teal-600 animate-ping" />
                <span>
                  {hasDetectedSpeech
                    ? 'Hearing speech... tap Stop & Send when done'
                    : hasAudioHardware
                    ? 'Microphone active... speak now'
                    : 'Listening... connecting microphone'}
                </span>
              </div>
            )}

            {state === 'processing' && (
              <div className="flex items-center space-x-2 text-amber-800 bg-amber-50 border border-amber-200 px-3 py-1 rounded-full">
                <Spinner size="sm" />
                <span>Analyzing records & running ERP tools...</span>
              </div>
            )}

            {state === 'speaking' && (
              <div className="flex items-center space-x-2 text-cyan-900 bg-cyan-50 border border-cyan-200 px-3 py-1 rounded-full">
                <Volume2 className="w-3.5 h-3.5 text-cyan-700 animate-pulse" />
                <span>Alladin is speaking...</span>
              </div>
            )}

            {state === 'interrupted' && (
              <div className="flex items-center space-x-2 text-slate-700 bg-slate-100 border border-slate-200 px-3 py-1 rounded-full">
                <Square className="w-3.5 h-3.5 text-slate-500" />
                <span>Speech paused. Ready for next question.</span>
              </div>
            )}

            {state === 'idle' && (
              <div className="flex items-center space-x-2 text-slate-600 bg-slate-100 border border-slate-200 px-3 py-1 rounded-full">
                <Mic className="w-3.5 h-3.5 text-slate-500" />
                <span>Tap Start Listening or press Space to speak</span>
              </div>
            )}

            {state === 'error' && (
              <div className="flex items-center space-x-2 text-rose-700 bg-rose-50 border border-rose-200 px-3 py-1 rounded-full">
                <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                <span>Recognition issue encountered</span>
              </div>
            )}
          </div>

          {/* Actionable Error Card with Retry Button */}
          {errorMessage && (
            <div className="w-full max-w-md mt-3 p-3 bg-rose-50 border border-rose-200 rounded-xl shadow-xs text-xs text-rose-800 flex items-center justify-between gap-2">
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <p className="leading-relaxed">{errorMessage}</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleStartListening}
                className="shrink-0 bg-white border-rose-300 text-rose-700 hover:bg-rose-100"
              >
                <RefreshCw className="w-3 h-3 mr-1" />
                Retry
              </Button>
            </div>
          )}

          {/* ── Transcription Card: User Query & Assistant Answer ── */}
          <div className="w-full max-w-lg mt-4 space-y-2.5">
            {/* Live User Speech Bubble */}
            {(userTranscript || interimTranscript) && (
              <div className="p-3 bg-white border border-teal-200 rounded-xl shadow-xs text-xs text-slate-800 animate-in fade-in slide-in-from-bottom-2">
                <div className="flex items-center space-x-1.5 text-[10px] font-bold text-teal-700 uppercase tracking-wider mb-1">
                  <Mic className="w-3 h-3" />
                  <span>You said:</span>
                </div>
                <p className="leading-relaxed font-medium">
                  {userTranscript}{' '}
                  {interimTranscript && (
                    <span className="text-teal-600 italic bg-teal-50 px-1 py-0.5 rounded">{interimTranscript}</span>
                  )}
                </p>
              </div>
            )}

            {/* Assistant Spoken Response Bubble */}
            {assistantReply && (
              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl shadow-xs text-xs text-slate-800 space-y-2 animate-in fade-in slide-in-from-bottom-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1.5 text-[10px] font-bold text-slate-600 uppercase tracking-wider">
                    <Sparkles className="w-3 h-3 text-teal-700" />
                    <span>Alladin Verified Insight</span>
                  </div>
                  <span className="text-[10px] text-slate-400 capitalize">
                    {assistantReply.provider} • {assistantReply.model}
                  </span>
                </div>

                <p className="leading-relaxed whitespace-pre-wrap line-clamp-5">
                  {assistantReply.reply}
                </p>

                {/* ERP Tool Execution Summary Badge */}
                {assistantReply.tools_used && assistantReply.tools_used.length > 0 && (
                  <div className="pt-1.5 border-t border-slate-200/80">
                    <button
                      onClick={() => setExpandedTools((prev) => !prev)}
                      className="text-[11px] text-teal-700 hover:text-teal-800 font-medium flex items-center space-x-1"
                    >
                      <Wrench className="w-3 h-3" />
                      <span>
                        {assistantReply.tools_used.length} ERP Tool{assistantReply.tools_used.length > 1 ? 's' : ''} executed ({expandedTools ? 'hide' : 'view'})
                      </span>
                    </button>

                    {expandedTools && (
                      <div className="mt-1.5 space-y-1">
                        {assistantReply.tools_used.map((t, idx) => (
                          <div
                            key={idx}
                            className="p-1.5 bg-white border border-slate-200 rounded text-[10px] font-mono text-slate-600"
                          >
                            <span className="font-semibold text-teal-800">{t.tool}</span>:{' '}
                            {t.summary || JSON.stringify(t.args || {})}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ── Bottom Controls Bar ───────────────────────────────── */}
        <footer className="p-4 border-t border-slate-200 bg-white flex flex-col sm:flex-row items-center justify-between gap-3 shrink-0">
          {/* Left: Keyboard Hints */}
          <div className="text-[11px] text-slate-400 flex items-center space-x-3">
            <span>Space: Mic • Esc: Exit • R: Replay • I: Stop</span>
          </div>

          {/* Center: Explicit Push-to-Talk Controls */}
          <div className="flex items-center space-x-3">
            {/* Replay Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleReplay}
              disabled={!assistantReply?.reply || state === 'speaking'}
              className="rounded-full px-3 py-1.5"
              title="Replay assistant answer (R)"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1" />
              Replay
            </Button>

            {/* Primary Action Button (Start Listening / Stop & Send) */}
            {state === 'listening' ? (
              <button
                onClick={handleStopAndSend}
                className="px-5 py-2.5 rounded-full bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs shadow-md flex items-center space-x-2 ring-4 ring-teal-400/40 animate-pulse transition-all"
                title="Finish speaking and send question"
              >
                <Send className="w-4 h-4" />
                <span>Stop & Send Question</span>
              </button>
            ) : (
              <button
                onClick={handleStartListening}
                disabled={state === 'processing'}
                className="px-5 py-2.5 rounded-full bg-slate-900 hover:bg-teal-700 text-white font-semibold text-xs shadow-md flex items-center space-x-2 transition-all hover:scale-105"
                title="Tap to speak"
              >
                <Mic className="w-4 h-4 text-teal-300" />
                <span>Start Listening</span>
              </button>
            )}

            {/* Interrupt / Stop Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleInterrupt}
              disabled={state !== 'speaking'}
              className="rounded-full px-3 py-1.5 text-rose-700 border-rose-200 hover:bg-rose-50"
              title="Stop speaking (I)"
            >
              <Square className="w-3.5 h-3.5 mr-1 text-rose-600 fill-current" />
              Stop
            </Button>
          </div>

          {/* Right: Return to Text Chat Button */}
          <div>
            <Button
              variant="secondary"
              size="sm"
              onClick={onClose}
              className="text-xs"
              leftIcon={<MessageSquare className="w-3.5 h-3.5" />}
            >
              Return to Chat
            </Button>
          </div>
        </footer>
      </div>
    </div>
  )
}
