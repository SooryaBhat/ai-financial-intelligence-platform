/**
 * WebVoiceProvider
 * Orchestrates SpeechRecognition, authenticated FastAPI voice-turn backend, and SpeechSynthesis.
 * Manages state transitions: idle -> listening -> processing -> speaking -> (cooldown) -> listening.
 * Features instance isolation, push-to-talk default, smooth session ID updates, and detailed diagnostics.
 */

import api from '@/lib/api'
import { ApiSuccessResponse } from '@/types/api.types'
import {
  IVoiceProvider,
  VoiceCallbacks,
  VoiceMode,
  VoiceState,
  VoiceTurnResult,
} from './voice.types'
import { SpeechRecognitionService } from './speech-recognition.service'
import { SpeechSynthesisService } from './speech-synthesis.service'

const logDev = (instanceId: string, msg: string, ...data: unknown[]) => {
  if (import.meta.env.DEV) {
    console.log(`[VoiceAssistant:Provider:${instanceId}] ${msg}`, ...data)
  }
}

export class WebVoiceProvider implements IVoiceProvider {
  public readonly name = 'WebVoiceProvider'
  public readonly instanceId = 'wvp_' + Math.random().toString(36).slice(2, 8)

  private speechRecognition = new SpeechRecognitionService()
  private speechSynthesis = new SpeechSynthesisService()

  private callbacks: VoiceCallbacks | null = null
  private currentState: VoiceState = 'idle'
  private currentMode: VoiceMode = 'push_to_talk'
  private activeSessionId: string | null = null
  private lastReplyText = ''

  // Locks & timers
  private isProcessing = false
  private isAssistantSpeaking = false
  private isDestroyed = false
  private cooldownTimer: number | null = null
  private pulseTimer: number | null = null

  constructor() {
    logDev(this.instanceId, 'Instantiated WebVoiceProvider.')
  }

  public isSupported(): boolean {
    return this.speechRecognition.isSupported() && this.speechSynthesis.isSupported()
  }

  public isDestroyedStatus(): boolean {
    return this.isDestroyed
  }

  public setSessionId(sessionId: string | null): void {
    if (this.isDestroyed) {
      logDev(this.instanceId, 'setSessionId called on destroyed provider; ignoring.')
      return
    }
    const prev = this.activeSessionId
    this.activeSessionId = sessionId
    logDev(this.instanceId, `Updated active session ID: '${prev}' -> '${sessionId}' (recognition unaffected).`)
  }

  public getSessionId(): string | null {
    return this.activeSessionId
  }

  public setMode(mode: VoiceMode): void {
    logDev(this.instanceId, `Setting voice mode: ${mode}`)
    this.currentMode = mode
  }

  public getMode(): VoiceMode {
    return this.currentMode
  }

  public setLanguage(lang: string): void {
    logDev(this.instanceId, `Setting recognition language: ${lang}`)
    this.speechRecognition.setLanguage(lang)
  }

  public getLanguage(): string {
    return this.speechRecognition.getLanguage()
  }

  public async init(callbacks: VoiceCallbacks): Promise<void> {
    logDev(this.instanceId, 'Initializing WebVoiceProvider with callbacks.')
    this.callbacks = callbacks
    this.isDestroyed = false
    this.setState('idle')
  }

  private setState(state: VoiceState): void {
    if (this.isDestroyed && state !== 'idle') return
    logDev(this.instanceId, `State transition -> ${state}`)
    this.currentState = state
    this.callbacks?.onStateChange(state)
  }

  public getState(): VoiceState {
    return this.currentState
  }

  public async startListening(): Promise<void> {
    if (this.isDestroyed) {
      logDev(this.instanceId, 'startListening called on destroyed provider; ignoring.')
      return
    }

    logDev(this.instanceId, `startListening() called [mode=${this.currentMode}].`)
    this.cancelCooldown()
    this.cancelSpeech()

    try {
      this.setState('listening')

      // Direct speech recognition without conflicting getUserMedia capture
      this.speechRecognition.start(
        {
          onStart: () => {
            logDev(this.instanceId, 'Speech recognition has started listening.')
            this.setState('listening')
          },
          onAudioStart: () => {
            this.callbacks?.onAudioStart?.()
            this.startPulseVisualizer()
          },
          onSoundStart: () => {
            this.callbacks?.onSoundStart?.()
            this.callbacks?.onAudioLevelChange(0.5)
          },
          onSpeechStart: () => {
            this.callbacks?.onSpeechStart?.()
            this.callbacks?.onAudioLevelChange(0.85)
          },
          onInterim: (text) => {
            if (this.currentState !== 'listening') {
              this.setState('listening')
            }
            this.callbacks?.onInterimTranscript(text)
          },
          onFinal: (finalText) => {
            logDev(this.instanceId, `Received final transcript from STT (length ${finalText.length}):`, finalText)
            this.callbacks?.onFinalTranscript(finalText)
            this.stopPulseVisualizer()

            if (finalText.trim()) {
              this.processTranscript(finalText.trim())
            }
          },
          onError: (errorMsg) => {
            logDev(this.instanceId, 'STT reported error:', errorMsg)
            this.stopPulseVisualizer()
            this.callbacks?.onError(errorMsg)
            this.setState('error')
          },
          onEnd: () => {
            logDev(this.instanceId, 'STT onEnd callback received.')
            this.stopPulseVisualizer()
            if (this.currentState === 'listening' && this.currentMode === 'push_to_talk') {
              this.setState('idle')
            }
          },
        },
        this.currentMode === 'auto'
      )
    } catch (err: any) {
      logDev(this.instanceId, 'startListening failed:', err)
      this.stopPulseVisualizer()
      this.setState('error')
      this.callbacks?.onError(err.message || 'Could not start voice listening.')
    }
  }

  public stopListening(): void {
    logDev(this.instanceId, 'stopListening() called.')
    this.cancelCooldown()
    this.stopPulseVisualizer()
    this.speechRecognition.stop()
    if (this.currentState === 'listening') {
      this.setState('idle')
    }
  }

  /**
   * Push-to-talk finish action: commits current speech and triggers assistant.
   */
  public finishSpeakingManually(): void {
    logDev(this.instanceId, 'finishSpeakingManually() called.')
    this.stopPulseVisualizer()
    const committed = this.speechRecognition.stopAndCommit()
    if (!committed && this.currentState === 'listening') {
      this.setState('idle')
    }
  }

  /**
   * Process a confirmed transcript by calling the FastAPI voice endpoint.
   */
  private async processTranscript(transcript: string): Promise<void> {
    if (this.isProcessing) {
      logDev(this.instanceId, 'Concurrent backend call blocked; turn in progress.')
      return
    }

    this.isProcessing = true
    this.setState('processing')
    this.speechRecognition.pause()

    logDev(this.instanceId, `Dispatching transcript to /api/v1/voice/turn [sessionId=${this.activeSessionId}]...`)

    try {
      const response = await api.post<ApiSuccessResponse<VoiceTurnResult>>(
        '/api/v1/voice/turn',
        {
          session_id: this.activeSessionId,
          transcript,
        }
      )

      logDev(this.instanceId, `Received backend turn response: HTTP ${response.status}`)
      const result = response.data?.data

      if (!result || !result.reply) {
        throw new Error('Received an empty response from the AI assistant.')
      }

      logDev(this.instanceId, `Turn successful. Reply length: ${result.reply.length}, Tools used: ${result.tools_used?.length || 0}`)

      this.activeSessionId = result.session_id
      this.lastReplyText = result.reply
      this.callbacks?.onAssistantReply(result)

      // Speak assistant response with synchronized mouth movement
      this.playSpeech(result.reply)
    } catch (err: any) {
      logDev(this.instanceId, 'Backend voice turn error:', err)
      const errorMsg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.detail ||
        err?.message ||
        'Failed to retrieve answer from AI assistant.'
      this.callbacks?.onError(errorMsg)
      this.setState('error')
    } finally {
      this.isProcessing = false
    }
  }

  public async sendTranscriptManually(text: string, sessionId?: string): Promise<void> {
    if (sessionId) {
      this.activeSessionId = sessionId
    }
    await this.processTranscript(text)
  }

  private playSpeech(text: string): void {
    if (this.isDestroyed) return

    this.cancelCooldown()
    this.speechRecognition.pause()
    this.setState('speaking')
    logDev(this.instanceId, 'Starting speech playback for assistant reply...')

    this.speechSynthesis.speak(text, {
      onStart: () => {
        this.isAssistantSpeaking = true
        this.setState('speaking')
      },
      onViseme: (level) => {
        this.callbacks?.onVisemeLevelChange(level)
      },
      onEnd: () => {
        logDev(this.instanceId, 'Assistant speech playback finished.')
        this.isAssistantSpeaking = false
        this.callbacks?.onVisemeLevelChange(0)

        if (this.currentMode === 'auto' && !this.isDestroyed) {
          logDev(this.instanceId, 'Auto-mode: 450ms cooldown before listening...')
          this.cooldownTimer = window.setTimeout(() => {
            if (this.currentMode === 'auto' && !this.isAssistantSpeaking && !this.isDestroyed) {
              this.startListening()
            } else {
              this.setState('idle')
            }
          }, 450)
        } else {
          this.setState('idle')
        }
      },
      onError: (err) => {
        logDev(this.instanceId, 'Assistant speech synthesis error:', err)
        this.isAssistantSpeaking = false
        this.callbacks?.onVisemeLevelChange(0)
        this.setState('error')
        this.callbacks?.onError(err)
      },
    })
  }

  public cancelSpeech(): void {
    logDev(this.instanceId, 'cancelSpeech() called.')
    this.cancelCooldown()
    this.isAssistantSpeaking = false
    this.speechSynthesis.cancel()
    this.callbacks?.onVisemeLevelChange(0)

    if (this.currentState === 'speaking') {
      this.setState('interrupted')
    }
  }

  public replayLastSpeech(text?: string): void {
    const toPlay = text || this.lastReplyText
    if (toPlay) {
      logDev(this.instanceId, 'Replaying last response...')
      this.cancelSpeech()
      this.playSpeech(toPlay)
    }
  }

  private cancelCooldown(): void {
    if (this.cooldownTimer !== null) {
      clearTimeout(this.cooldownTimer)
      this.cooldownTimer = null
    }
  }

  private startPulseVisualizer(): void {
    this.stopPulseVisualizer()
    let step = 0
    this.pulseTimer = window.setInterval(() => {
      step = (step + 1) % 10
      const simulatedLevel = 0.2 + Math.sin(step * 0.6) * 0.15
      this.callbacks?.onAudioLevelChange(Math.max(0, simulatedLevel))
    }, 150)
  }

  private stopPulseVisualizer(): void {
    if (this.pulseTimer !== null) {
      clearInterval(this.pulseTimer)
      this.pulseTimer = null
    }
    this.callbacks?.onAudioLevelChange(0)
  }

  public destroy(reason = 'component_unmount'): void {
    if (this.isDestroyed) return
    this.isDestroyed = true

    logDev(this.instanceId, `Destroying WebVoiceProvider. Reason: ${reason}`)
    this.cancelCooldown()
    this.stopPulseVisualizer()
    this.cancelSpeech()
    this.speechRecognition.destroy()
    this.speechSynthesis.destroy()
    this.callbacks = null
    this.isProcessing = false
    this.isAssistantSpeaking = false
    this.currentState = 'idle'
  }
}

// Fallback singleton for backward-compatibility if imported elsewhere
export const webVoiceProvider = new WebVoiceProvider()
