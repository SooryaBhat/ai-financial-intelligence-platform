/**
 * Voice Assistant Types and Interfaces
 */

export type VoiceState =
  | 'idle'
  | 'listening'
  | 'processing'
  | 'speaking'
  | 'interrupted'
  | 'error'

export type VoiceMode = 'auto' | 'push_to_talk'

export interface VoiceToolExecution {
  tool: string
  summary?: string
  args?: Record<string, unknown>
  result?: unknown
}

export interface VoiceTurnResult {
  session_id: string
  transcript: string
  reply: string
  tools_used?: VoiceToolExecution[]
  provider: string
  model: string
}

export interface VoiceCallbacks {
  onStateChange: (state: VoiceState) => void
  onAudioLevelChange: (level: number) => void // 0.0 to 1.0 (for soundwaves and ear movement)
  onVisemeLevelChange: (level: number) => void // 0.0 to 1.0 (for mouth movement)
  onInterimTranscript: (text: string) => void
  onFinalTranscript: (text: string) => void
  onAssistantReply: (result: VoiceTurnResult) => void
  onError: (errorMessage: string) => void
  onAudioStart?: () => void
  onSoundStart?: () => void
  onSpeechStart?: () => void
}

export interface IVoiceProvider {
  readonly name: string
  isSupported(): boolean
  init(callbacks: VoiceCallbacks): Promise<void>
  startListening(): Promise<void>
  stopListening(): void
  sendTranscriptManually(text: string, sessionId?: string): Promise<void>
  cancelSpeech(): void
  replayLastSpeech(text: string): void
  setMode(mode: VoiceMode): void
  destroy(): void
}
