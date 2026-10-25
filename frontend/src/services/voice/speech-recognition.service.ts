/**
 * SpeechRecognitionService
 * Web Speech API wrapper for speech-to-text.
 * Provides diagnostics for onaudiostart, onsoundstart, onspeechstart, onresult, onerror, onend.
 * Supports push-to-talk, manual commits, configurable languages, and intentional stop tracking.
 */

interface IWindowSpeechRecognition extends Window {
  SpeechRecognition?: any
  webkitSpeechRecognition?: any
}

export interface SpeechRecognitionCallbacks {
  onStart: () => void
  onAudioStart?: () => void
  onSoundStart?: () => void
  onSpeechStart?: () => void
  onInterim: (text: string) => void
  onFinal: (text: string) => void
  onError: (error: string) => void
  onEnd: () => void
}

const logDev = (instanceId: string, msg: string, ...data: unknown[]) => {
  if (import.meta.env.DEV) {
    console.log(`[VoiceAssistant:STT:${instanceId}] ${msg}`, ...data)
  }
}

export class SpeechRecognitionService {
  public readonly id = 'stt_' + Math.random().toString(36).slice(2, 8)

  private recognition: any = null
  private isListening = false
  private isStarting = false
  private isPaused = false
  private isIntentionalStop = false
  private callbacks: SpeechRecognitionCallbacks | null = null
  private autoRestart = false

  // Diagnostics telemetry
  public hasAudioStarted = false
  public hasSoundStarted = false
  public hasSpeechStarted = false

  // Language configuration
  private language = 'en-US'

  // Transcript accumulation & debouncing
  private accumulatedFinalText = ''
  private currentInterimText = ''
  private silenceTimer: number | null = null
  private hasSubmittedCurrentTurn = false

  public isSupported(): boolean {
    const win = window as IWindowSpeechRecognition
    return Boolean(win.SpeechRecognition || win.webkitSpeechRecognition)
  }

  public setLanguage(lang: string): void {
    this.language = lang || 'en-US'
    if (this.recognition) {
      this.recognition.lang = this.language
    }
    logDev(this.id, `Language set to ${this.language}`)
  }

  public getLanguage(): string {
    return this.language
  }

  public start(callbacks: SpeechRecognitionCallbacks, continuous = false): void {
    if (!this.isSupported()) {
      callbacks.onError('Speech Recognition is not supported by this browser. Please use Google Chrome, Microsoft Edge, or Safari.')
      return
    }

    if (this.isListening || this.isStarting) {
      logDev(this.id, 'Recognition already active or starting; skipping duplicate start().')
      return
    }

    this.callbacks = callbacks
    this.autoRestart = continuous
    this.isPaused = false
    this.isIntentionalStop = false
    this.hasSubmittedCurrentTurn = false
    this.accumulatedFinalText = ''
    this.currentInterimText = ''
    this.hasAudioStarted = false
    this.hasSoundStarted = false
    this.hasSpeechStarted = false
    this.clearSilenceTimer()

    const win = window as IWindowSpeechRecognition
    const SpeechRec = win.SpeechRecognition || win.webkitSpeechRecognition

    try {
      this.recognition = new SpeechRec()
      this.recognition.continuous = continuous
      this.recognition.interimResults = true
      this.recognition.lang = this.language
      this.recognition.maxAlternatives = 1

      // ── Full Diagnostics Hooks ─────────────────────────────────
      this.recognition.onstart = () => {
        logDev(this.id, 'STT onstart: recognition service initialized.')
        this.isListening = true
        this.isStarting = false
        this.callbacks?.onStart()
      }

      this.recognition.onaudiostart = () => {
        this.hasAudioStarted = true
        logDev(this.id, 'STT onaudiostart: audio hardware stream capturing.')
        this.callbacks?.onAudioStart?.()
      }

      this.recognition.onsoundstart = () => {
        this.hasSoundStarted = true
        logDev(this.id, 'STT onsoundstart: audio sound energy detected.')
        this.callbacks?.onSoundStart?.()
      }

      this.recognition.onspeechstart = () => {
        this.hasSpeechStarted = true
        logDev(this.id, 'STT onspeechstart: human speech recognized!')
        this.callbacks?.onSpeechStart?.()
      }

      this.recognition.onspeechend = () => {
        logDev(this.id, 'STT onspeechend: human speech ended.')
      }

      this.recognition.onsoundend = () => {
        logDev(this.id, 'STT onsoundend: sound energy ended.')
      }

      this.recognition.onaudioend = () => {
        logDev(this.id, 'STT onaudioend: audio capture stopped.')
      }

      this.recognition.onnomatch = () => {
        logDev(this.id, 'STT onnomatch: sound was heard, but no words were recognized.')
      }

      this.recognition.onresult = (event: any) => {
        if (this.isPaused || this.hasSubmittedCurrentTurn) return

        let interim = ''
        let newFinalChunk = ''

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const item = event.results[i]
          const text = item[0]?.transcript || ''
          if (item.isFinal) {
            newFinalChunk += text
          } else {
            interim += text
          }
        }

        if (newFinalChunk) {
          this.accumulatedFinalText = (this.accumulatedFinalText + ' ' + newFinalChunk).trim()
          logDev(this.id, 'STT onresult: interim-final chunk received ->', newFinalChunk)
        }
        this.currentInterimText = interim

        const liveText = (this.accumulatedFinalText + ' ' + this.currentInterimText).trim()
        if (liveText && this.callbacks) {
          this.callbacks.onInterim(liveText)
        }

        // In continuous auto mode, reset the silence timer on each word
        if (this.autoRestart) {
          this.resetSilenceTimer()
        }
      }

      this.recognition.onerror = (event: any) => {
        const err = event.error
        logDev(this.id, `STT onerror: '${err}'. [audioStarted=${this.hasAudioStarted}, speechStarted=${this.hasSpeechStarted}, intentional=${this.isIntentionalStop}]`)

        if (err === 'aborted') {
          // Intentional stop / cleanup
          return
        }

        if (err === 'no-speech') {
          if (!this.autoRestart) {
            // Push-to-talk mode: surface helpful error with retry
            this.callbacks?.onError('No speech was detected. Please check your microphone input device and tap Start Listening to speak.')
          }
          return
        }

        if (err === 'not-allowed' || err === 'service-not-allowed') {
          this.autoRestart = false
          this.callbacks?.onError('Microphone permission was denied. Please allow microphone access in your browser address bar.')
          return
        }

        if (err === 'audio-capture') {
          this.autoRestart = false
          this.callbacks?.onError('No microphone audio detected. Please verify your microphone is plugged in and selected as default.')
          return
        }

        if (err === 'network') {
          this.callbacks?.onError('Speech recognition network error. Chrome speech recognition requires an active internet connection.')
          return
        }

        this.callbacks?.onError(`Speech recognition error (${err}). Please check your microphone settings.`)
      }

      this.recognition.onend = () => {
        logDev(this.id, `STT onend fired. [intentional=${this.isIntentionalStop}, autoRestart=${this.autoRestart}, speechStarted=${this.hasSpeechStarted}]`)
        this.isListening = false
        this.isStarting = false

        if (this.isIntentionalStop) {
          this.callbacks?.onEnd()
          return
        }

        // If continuous auto mode and user spoke and finished naturally:
        if (this.autoRestart && !this.hasSubmittedCurrentTurn && this.accumulatedFinalText.trim() && !this.isPaused) {
          this.commitFinalTranscript()
          return
        }

        // If continuous auto mode and no final transcript yet:
        if (this.autoRestart && !this.isPaused && this.callbacks) {
          logDev(this.id, 'Auto-restarting continuous STT in 400ms...')
          setTimeout(() => {
            if (this.autoRestart && !this.isPaused && !this.isListening && !this.isIntentionalStop) {
              try {
                this.recognition?.start()
              } catch (startErr) {
                logDev(this.id, 'Auto-restart skipped:', startErr)
              }
            }
          }, 400)
        } else {
          this.callbacks?.onEnd()
        }
      }

      this.isStarting = true
      logDev(this.id, `Calling recognition.start() [lang=${this.language}, continuous=${continuous}]...`)
      this.recognition.start()
    } catch (err: any) {
      this.isStarting = false
      this.isListening = false
      logDev(this.id, 'recognition.start() exception:', err)
      if (err.name !== 'InvalidStateError') {
        this.callbacks?.onError(err.message || 'Could not start speech recognition.')
      }
    }
  }

  private resetSilenceTimer(): void {
    this.clearSilenceTimer()
    this.silenceTimer = window.setTimeout(() => {
      if (!this.hasSubmittedCurrentTurn && !this.isPaused) {
        const fullText = (this.accumulatedFinalText + ' ' + this.currentInterimText).trim()
        if (fullText) {
          logDev(this.id, 'Silence detected in auto mode; committing final transcript:', fullText)
          this.accumulatedFinalText = fullText
          this.commitFinalTranscript()
        }
      }
    }, 1300)
  }

  private clearSilenceTimer(): void {
    if (this.silenceTimer !== null) {
      clearTimeout(this.silenceTimer)
      this.silenceTimer = null
    }
  }

  /**
   * Commits the accumulated transcript exactly once.
   */
  public commitFinalTranscript(): void {
    this.clearSilenceTimer()
    const textToSubmit = (this.accumulatedFinalText + ' ' + this.currentInterimText).trim()

    if (!textToSubmit || this.hasSubmittedCurrentTurn) {
      logDev(this.id, 'commitFinalTranscript skipped: empty or already submitted.')
      return
    }

    this.hasSubmittedCurrentTurn = true
    this.isPaused = true
    logDev(this.id, 'Committing final transcript to assistant ->', textToSubmit)

    this.stop()

    if (this.callbacks) {
      this.callbacks.onFinal(textToSubmit)
    }
  }

  /**
   * Push-to-talk stop and commit.
   * If there is recognized speech, commits it. If empty, stops and returns false.
   */
  public stopAndCommit(): boolean {
    this.clearSilenceTimer()
    const textToSubmit = (this.accumulatedFinalText + ' ' + this.currentInterimText).trim()

    if (textToSubmit) {
      this.commitFinalTranscript()
      return true
    } else {
      logDev(this.id, 'stopAndCommit: no speech accumulated; canceling.')
      this.stop()
      return false
    }
  }

  public pause(): void {
    logDev(this.id, 'Pausing STT during assistant speech.')
    this.isPaused = true
    this.clearSilenceTimer()
    this.stop()
  }

  public resume(callbacks: SpeechRecognitionCallbacks, continuous = false): void {
    logDev(this.id, 'Resuming STT.')
    this.isPaused = false
    this.hasSubmittedCurrentTurn = false
    this.accumulatedFinalText = ''
    this.currentInterimText = ''
    this.start(callbacks, continuous)
  }

  public stop(): void {
    this.isIntentionalStop = true
    this.isListening = false
    this.isStarting = false
    this.clearSilenceTimer()

    if (this.recognition) {
      try {
        this.recognition.abort()
      } catch {
        // ignore
      }
      this.recognition = null
    }
  }

  public destroy(): void {
    logDev(this.id, 'Destroying speech recognition service.')
    this.autoRestart = false
    this.isPaused = true
    this.clearSilenceTimer()
    this.stop()
    this.callbacks = null
    this.accumulatedFinalText = ''
    this.currentInterimText = ''
  }
}
