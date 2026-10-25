/**
 * AudioMeterService
 * Measures real-time microphone volume levels via Web Audio API.
 * Powers character ear movements and concentric soundwave visualization.
 */

export class AudioMeterService {
  private audioContext: AudioContext | null = null
  private analyser: AnalyserNode | null = null
  private mediaStream: MediaStream | null = null
  private sourceNode: MediaStreamAudioSourceNode | null = null
  private animationFrameId: number | null = null
  private onLevelCallback: ((level: number) => void) | null = null
  private isRunning = false

  public async start(
    stream: MediaStream,
    onLevel: (level: number) => void
  ): Promise<void> {
    this.stop()
    this.mediaStream = stream
    this.onLevelCallback = onLevel

    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      if (!AudioCtx) {
        return
      }
      this.audioContext = new AudioCtx()
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume()
      }

      this.analyser = this.audioContext.createAnalyser()
      this.analyser.fftSize = 256
      this.analyser.smoothingTimeConstant = 0.5

      this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream)
      this.sourceNode.connect(this.analyser)

      this.isRunning = true
      this.tick()
    } catch (err) {
      console.warn('[AudioMeterService] Could not initialize Web Audio analyser:', err)
    }
  }

  private tick = (): void => {
    if (!this.isRunning || !this.analyser) return

    const dataArray = new Uint8Array(this.analyser.frequencyBinCount)
    this.analyser.getByteFrequencyData(dataArray)

    // Calculate Root-Mean-Square (RMS) amplitude
    let sum = 0
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i] * dataArray[i]
    }
    const rms = Math.sqrt(sum / dataArray.length)

    // Normalize roughly to 0.0 - 1.0 with soft exponential curve
    const normalized = Math.min(1.0, Math.max(0.0, (rms / 128.0) * 1.5))

    if (this.onLevelCallback) {
      this.onLevelCallback(normalized)
    }

    this.animationFrameId = requestAnimationFrame(this.tick)
  }

  public stop(): void {
    this.isRunning = false
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId)
      this.animationFrameId = null
    }

    if (this.sourceNode) {
      try {
        this.sourceNode.disconnect()
      } catch {
        // ignore
      }
      this.sourceNode = null
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      try {
        this.audioContext.close()
      } catch {
        // ignore
      }
      this.audioContext = null
    }

    if (this.onLevelCallback) {
      this.onLevelCallback(0)
      this.onLevelCallback = null
    }
    this.mediaStream = null
  }
}
