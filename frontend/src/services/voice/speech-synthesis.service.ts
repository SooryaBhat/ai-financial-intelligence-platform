/**
 * SpeechSynthesisService
 * Robust Web SpeechSynthesis wrapper for text-to-speech.
 * Handles Chromium paused bugs, garbage-collection protection, Markdown sanitization, and viseme synchronization.
 */

export interface SpeechSynthesisCallbacks {
  onStart: () => void
  onViseme: (level: number) => void // 0.0 to 1.0
  onEnd: () => void
  onError: (error: string) => void
}

const logDev = (msg: string, ...data: unknown[]) => {
  if (import.meta.env.DEV) {
    console.log(`[VoiceAssistant:TTS] ${msg}`, ...data)
  }
}

// Module-level set to prevent Chromium V8 garbage collector from aborting speech mid-playback
const activeUtterances = new Set<SpeechSynthesisUtterance>()

export class SpeechSynthesisService {
  private currentUtterance: SpeechSynthesisUtterance | null = null
  private visemeTimer: number | null = null
  private heartbeatTimer: number | null = null
  private callbacks: SpeechSynthesisCallbacks | null = null
  private isSpeaking = false
  private loadedVoices: SpeechSynthesisVoice[] = []

  constructor() {
    this.initVoices()
  }

  public isSupported(): boolean {
    return typeof window !== 'undefined' && 'speechSynthesis' in window
  }

  private initVoices(): void {
    if (!this.isSupported()) return

    try {
      this.loadedVoices = window.speechSynthesis.getVoices() || []
      window.speechSynthesis.onvoiceschanged = () => {
        this.loadedVoices = window.speechSynthesis.getVoices() || []
        logDev('Voices loaded asynchronously:', this.loadedVoices.length)
      }
    } catch (e) {
      logDev('Could not initialize voices:', e)
    }
  }

  /**
   * Cleans Markdown syntax so the character speaks natural sentences.
   */
  public sanitizeTextForSpeech(markdownText: string): string {
    if (!markdownText) return ''

    let text = markdownText

    // Remove code blocks
    text = text.replace(/```[\s\S]*?```/g, ' [code omitted] ')
    text = text.replace(/`([^`]+)`/g, '$1')

    // Remove markdown links: [text](url) -> text
    text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')

    // Remove headers: ### Header -> Header
    text = text.replace(/^#{1,6}\s+/gm, '')

    // Remove bullet points / blockquotes
    text = text.replace(/^[\s*-+>]+\s+/gm, '')

    // Remove bold and italics
    text = text.replace(/[*_]{1,3}([^*_]+)[*_]{1,3}/g, '$1')

    // Replace markdown tables
    text = text.replace(/\|/g, ', ')

    // Replace currency symbols and common acronyms for natural pronunciation
    text = text.replace(/₹\s*/g, ' rupees ')
    text = text.replace(/\$\s*/g, ' dollars ')

    // Normalize multiple spaces/newlines
    text = text.replace(/\s+/g, ' ').trim()

    // If text is excessively long (over 600 chars), prioritize the first 3 key sentences for speech
    if (text.length > 600) {
      const sentences = text.match(/[^.!?]+[.!?]+/g)
      if (sentences && sentences.length > 2) {
        text = sentences.slice(0, 3).join(' ')
      }
    }

    if (!text.trim()) {
      text = 'Here is the analysis from your company records.'
    }

    return text
  }

  public speak(text: string, callbacks: SpeechSynthesisCallbacks): void {
    if (!this.isSupported()) {
      callbacks.onError('Web Speech Synthesis is not supported in this browser.')
      return
    }

    this.cancel()
    this.callbacks = callbacks

    const speechText = this.sanitizeTextForSpeech(text)
    if (!speechText) {
      logDev('Cleaned text empty; ending speech turn.')
      callbacks.onEnd()
      return
    }

    logDev('Starting speech synthesis (length):', speechText.length)

    try {
      const utterance = new SpeechSynthesisUtterance(speechText)
      this.currentUtterance = utterance

      // Retain utterance in global set to prevent Chromium garbage collection
      activeUtterances.add(utterance)

      // Pick the best natural English voice
      const voices = this.loadedVoices.length > 0 ? this.loadedVoices : window.speechSynthesis.getVoices()
      const preferredVoice = voices.find(
        (v) =>
          (v.lang.startsWith('en') &&
            (v.name.includes('Natural') ||
              v.name.includes('Google') ||
              v.name.includes('Samantha') ||
              v.name.includes('Neural') ||
              v.name.includes('Online'))) ||
          v.lang === 'en-US' ||
          v.lang.startsWith('en')
      )

      if (preferredVoice) {
        utterance.voice = preferredVoice
        logDev('Using voice:', preferredVoice.name)
      }
      utterance.lang = preferredVoice?.lang || 'en-US'
      utterance.pitch = 1.05
      utterance.rate = 1.0

      utterance.onstart = () => {
        logDev('Speech synthesis onstart event fired.')
        this.isSpeaking = true
        this.callbacks?.onStart()
        this.startVisemeOscillation()
        this.startHeartbeat()
      }

      utterance.onboundary = () => {
        if (this.isSpeaking && this.callbacks) {
          // Trigger peak viseme mouth aperture on word boundary
          this.callbacks.onViseme(0.75 + Math.random() * 0.25)
        }
      }

      utterance.onend = () => {
        logDev('Speech synthesis onend event fired.')
        activeUtterances.delete(utterance)
        this.cleanupPlayback()
        this.callbacks?.onViseme(0)
        this.callbacks?.onEnd()
      }

      utterance.onerror = (e) => {
        logDev('Speech synthesis onerror event:', e.error)
        activeUtterances.delete(utterance)
        this.cleanupPlayback()
        this.callbacks?.onViseme(0)

        if (e.error !== 'interrupted' && e.error !== 'canceled') {
          this.callbacks?.onError(`Speech playback error (${e.error})`)
        } else {
          this.callbacks?.onEnd()
        }
      }

      // Chromium resume bug fix: cancel and resume right before speak
      window.speechSynthesis.cancel()
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume()
      }

      window.speechSynthesis.speak(utterance)

      // Secondary resume check to ensure audio playback initiates immediately
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume()
      }
    } catch (err: any) {
      logDev('speak() threw exception:', err)
      this.cleanupPlayback()
      this.callbacks?.onError(err.message || 'Speech synthesis failed to start.')
    }
  }

  /**
   * Chromium 15-second heartbeat bug fix:
   * Keeps audio running if Chromium tries to pause long utterances.
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatTimer = window.setInterval(() => {
      if (this.isSpeaking && window.speechSynthesis.speaking && window.speechSynthesis.paused) {
        logDev('Resuming paused speech synthesis via heartbeat.')
        window.speechSynthesis.resume()
      }
    }, 4000)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private startVisemeOscillation(): void {
    this.stopVisemeOscillation()
    let phase = 0

    this.visemeTimer = window.setInterval(() => {
      if (!this.isSpeaking || !this.callbacks) return
      phase += 0.35
      // Natural mouth movement curve
      const val = Math.max(0, Math.sin(phase) * 0.75 + Math.random() * 0.25)
      this.callbacks.onViseme(val)
    }, 110)
  }

  private stopVisemeOscillation(): void {
    if (this.visemeTimer !== null) {
      clearInterval(this.visemeTimer)
      this.visemeTimer = null
    }
  }

  private cleanupPlayback(): void {
    this.isSpeaking = false
    this.stopVisemeOscillation()
    this.stopHeartbeat()
    this.currentUtterance = null
  }

  public cancel(): void {
    logDev('Canceling speech synthesis.')
    this.cleanupPlayback()
    if (this.callbacks) {
      this.callbacks.onViseme(0)
    }
    if (this.isSupported()) {
      try {
        window.speechSynthesis.cancel()
      } catch {
        // ignore
      }
    }
    activeUtterances.clear()
  }

  public destroy(): void {
    this.cancel()
    this.callbacks = null
  }
}
