import React, { useEffect, useState } from 'react'
import { VoiceState } from '@/services/voice/voice.types'

interface AnimatedCharacterProps {
  state: VoiceState
  audioLevel?: number // 0.0 to 1.0 (microphone loudness for ears & soundwaves)
  visemeLevel?: number // 0.0 to 1.0 (speech audio intensity for mouth movement)
  className?: string
}

export const AnimatedCharacter: React.FC<AnimatedCharacterProps> = ({
  state,
  audioLevel = 0,
  visemeLevel = 0,
  className = '',
}) => {
  const [isBlinking, setIsBlinking] = useState(false)

  // Periodic natural blinking cycle
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      // Don't blink if interrupted or error
      if (state === 'interrupted') return
      setIsBlinking(true)
      setTimeout(() => setIsBlinking(false), 160)
    }, 3800)

    return () => clearInterval(blinkInterval)
  }, [state])

  // Dynamic ear rotation based on mic audio level when listening
  const earTwitch = state === 'listening' ? Math.min(18, audioLevel * 30) : 0

  // Calculate mouth opening height (base 4px, up to 26px when speaking)
  const mouthHeight =
    state === 'speaking'
      ? Math.max(6, Math.min(26, 6 + visemeLevel * 20))
      : state === 'interrupted'
      ? 14
      : state === 'listening'
      ? 8
      : 4

  const mouthWidth =
    state === 'speaking'
      ? Math.max(22, Math.min(34, 22 + visemeLevel * 10))
      : state === 'interrupted'
      ? 16
      : 22

  return (
    <div className={`relative flex items-center justify-center select-none ${className}`}>
      {/* ── Outer Aura & Concentric Soundwave Rings ────────────── */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        {state === 'listening' && (
          <>
            <div
              className="absolute rounded-full border-2 border-teal-400/40 animate-ping"
              style={{
                width: `${160 + audioLevel * 70}px`,
                height: `${160 + audioLevel * 70}px`,
                animationDuration: '2s',
              }}
            />
            <div
              className="absolute rounded-full bg-teal-500/10 transition-all duration-100"
              style={{
                width: `${210 + audioLevel * 50}px`,
                height: `${210 + audioLevel * 50}px`,
              }}
            />
          </>
        )}

        {state === 'speaking' && (
          <div
            className="absolute rounded-full border-2 border-cyan-400/30 animate-pulse"
            style={{
              width: `${190 + visemeLevel * 40}px`,
              height: `${190 + visemeLevel * 40}px`,
              animationDuration: '0.8s',
            }}
          />
        )}

        {state === 'processing' && (
          <div className="absolute w-56 h-56 rounded-full border border-dashed border-amber-400/60 animate-spin [animation-duration:8s]" />
        )}
      </div>

      {/* ── Character Container with Floating Motion ──────────── */}
      <div
        className={`relative z-10 transition-transform duration-300 ${
          state === 'speaking'
            ? 'animate-bounce [animation-duration:2.5s]'
            : state === 'processing'
            ? 'animate-pulse [animation-duration:1.5s]'
            : 'animate-[float_4s_ease-in-out_infinite]'
        }`}
      >
        <svg
          viewBox="0 0 240 240"
          className="w-56 h-56 sm:w-64 sm:h-64 drop-shadow-xl overflow-visible"
        >
          <defs>
            {/* Gradients */}
            <radialGradient id="bodyGrad" cx="40%" cy="35%" r="65%">
              <stop offset="0%" stopColor="#2DD4BF" />
              <stop offset="60%" stopColor="#0F766E" />
              <stop offset="100%" stopColor="#115E59" />
            </radialGradient>

            <linearGradient id="turbanGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0D9488" />
              <stop offset="50%" stopColor="#042F2E" />
              <stop offset="100%" stopColor="#134E4A" />
            </linearGradient>

            <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FDE047" />
              <stop offset="50%" stopColor="#EAB308" />
              <stop offset="100%" stopColor="#CA8A04" />
            </linearGradient>

            <linearGradient id="eyeGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#0F172A" />
              <stop offset="100%" stopColor="#1E293B" />
            </linearGradient>

            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* ── Feline / Genie Ears ───────────────────────────── */}
          {/* Left Ear */}
          <g
            className="transition-transform duration-150 origin-[75px_75px]"
            style={{ transform: `rotate(${-earTwitch}deg)` }}
          >
            <path
              d="M 60 75 Q 40 25 75 35 Q 90 55 90 75 Z"
              fill="url(#bodyGrad)"
              stroke="#042F2E"
              strokeWidth="2.5"
            />
            {/* Ear Inner Pink */}
            <path
              d="M 64 68 Q 50 35 73 42 Q 82 56 82 68 Z"
              fill="#F472B6"
              opacity="0.85"
            />
          </g>

          {/* Right Ear */}
          <g
            className="transition-transform duration-150 origin-[165px_75px]"
            style={{ transform: `rotate(${earTwitch}deg)` }}
          >
            <path
              d="M 180 75 Q 200 25 165 35 Q 150 55 150 75 Z"
              fill="url(#bodyGrad)"
              stroke="#042F2E"
              strokeWidth="2.5"
            />
            {/* Ear Inner Pink */}
            <path
              d="M 176 68 Q 190 35 167 42 Q 158 56 158 68 Z"
              fill="#F472B6"
              opacity="0.85"
            />
          </g>

          {/* ── Genie Head / Face ─────────────────────────────── */}
          <ellipse
            cx="120"
            cy="125"
            rx="62"
            ry="54"
            fill="url(#bodyGrad)"
            stroke="#042F2E"
            strokeWidth="3"
          />

          {/* Soft Muzzle / Cheeks */}
          <ellipse
            cx="120"
            cy="138"
            rx="36"
            ry="24"
            fill="#CCFBF1"
            opacity="0.9"
          />

          {/* ── Genie Turban & Jewel ──────────────────────────── */}
          {/* Turban Wrap */}
          <path
            d="M 68 85 Q 120 50 172 85 Q 185 70 170 55 Q 120 30 70 55 Q 55 70 68 85 Z"
            fill="url(#turbanGrad)"
            stroke="#042F2E"
            strokeWidth="2.5"
          />
          {/* Turban Center Fold */}
          <ellipse
            cx="120"
            cy="68"
            rx="22"
            ry="14"
            fill="#0F766E"
            stroke="#134E4A"
            strokeWidth="2"
          />

          {/* Golden ERP Medallion / Jewel */}
          <circle
            cx="120"
            cy="68"
            r="8"
            fill="url(#goldGrad)"
            stroke="#78350F"
            strokeWidth="1.5"
            filter={state === 'processing' ? 'url(#glow)' : undefined}
          />
          {/* Ruby center in medallion */}
          <circle
            cx="120"
            cy="68"
            r="4"
            fill={state === 'processing' ? '#F59E0B' : '#EF4444'}
            className={state === 'processing' ? 'animate-ping' : ''}
          />

          {/* Genie Feather */}
          <path
            d="M 120 60 Q 125 35 140 22 Q 132 38 123 58 Z"
            fill="url(#goldGrad)"
            stroke="#78350F"
            strokeWidth="1"
          />

          {/* ── Eyes & Eyebrows ───────────────────────────────── */}
          {/* Left Eye */}
          <g transform="translate(90, 114)">
            {isBlinking || state === 'error' ? (
              // Blinked or dizzy eye line
              <path
                d={state === 'error' ? 'M -12 2 L 0 -4 L 12 2' : 'M -14 0 Q 0 4 14 0'}
                fill="none"
                stroke="#042F2E"
                strokeWidth="3.5"
                strokeLinecap="round"
              />
            ) : (
              <>
                {/* Eye White */}
                <ellipse cx="0" cy="0" rx="15" ry="17" fill="#FFFFFF" />
                {/* Iris */}
                <ellipse
                  cx={state === 'processing' ? '1' : state === 'listening' ? '0' : '0'}
                  cy={state === 'processing' ? '-4' : '0'}
                  rx="10"
                  ry="12"
                  fill="url(#eyeGrad)"
                />
                {/* Pupil Light Highlights */}
                <circle cx="-3" cy="-4" r="4.5" fill="#FFFFFF" />
                <circle cx="4" cy="3" r="2" fill="#FFFFFF" />
              </>
            )}
            {/* Eyebrow */}
            <path
              d={
                state === 'listening'
                  ? 'M -14 -20 Q 0 -24 14 -18'
                  : state === 'error'
                  ? 'M -14 -16 Q 0 -20 14 -22'
                  : 'M -14 -18 Q 0 -21 14 -18'
              }
              fill="none"
              stroke="#042F2E"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          </g>

          {/* Right Eye */}
          <g transform="translate(150, 114)">
            {isBlinking || state === 'error' ? (
              <path
                d={state === 'error' ? 'M -12 2 L 0 -4 L 12 2' : 'M -14 0 Q 0 4 14 0'}
                fill="none"
                stroke="#042F2E"
                strokeWidth="3.5"
                strokeLinecap="round"
              />
            ) : (
              <>
                <ellipse cx="0" cy="0" rx="15" ry="17" fill="#FFFFFF" />
                <ellipse
                  cx={state === 'processing' ? '1' : state === 'listening' ? '0' : '0'}
                  cy={state === 'processing' ? '-4' : '0'}
                  rx="10"
                  ry="12"
                  fill="url(#eyeGrad)"
                />
                <circle cx="-3" cy="-4" r="4.5" fill="#FFFFFF" />
                <circle cx="4" cy="3" r="2" fill="#FFFFFF" />
              </>
            )}
            {/* Eyebrow */}
            <path
              d={
                state === 'listening'
                  ? 'M -14 -18 Q 0 -24 14 -20'
                  : state === 'error'
                  ? 'M -14 -22 Q 0 -20 14 -16'
                  : 'M -14 -18 Q 0 -21 14 -18'
              }
              fill="none"
              stroke="#042F2E"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          </g>

          {/* ── Cute Button Nose ──────────────────────────────── */}
          <polygon
            points="120,131 114,126 126,126"
            fill="#F472B6"
            stroke="#042F2E"
            strokeWidth="1.2"
          />

          {/* ── Cheeks Blush ─────────────────────────────────── */}
          <ellipse
            cx="76"
            cy="132"
            rx="9"
            ry="5"
            fill="#F472B6"
            opacity={state === 'error' ? 0.8 : 0.45}
          />
          <ellipse
            cx="164"
            cy="132"
            rx="9"
            ry="5"
            fill="#F472B6"
            opacity={state === 'error' ? 0.8 : 0.45}
          />

          {/* ── Whiskers ─────────────────────────────────────── */}
          {/* Left Whiskers */}
          <path d="M 68 135 L 42 133" stroke="#042F2E" strokeWidth="1.5" strokeLinecap="round" />
          <path d="M 68 141 L 44 145" stroke="#042F2E" strokeWidth="1.5" strokeLinecap="round" />
          {/* Right Whiskers */}
          <path d="M 172 135 L 198 133" stroke="#042F2E" strokeWidth="1.5" strokeLinecap="round" />
          <path d="M 172 141 L 196 145" stroke="#042F2E" strokeWidth="1.5" strokeLinecap="round" />

          {/* ── Dynamic Synchronized Mouth ───────────────────── */}
          <g transform="translate(120, 142)">
            {state === 'error' ? (
              // Frown / wavy mouth
              <path
                d="M -10 6 Q 0 0 10 6"
                fill="none"
                stroke="#042F2E"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            ) : mouthHeight <= 5 ? (
              // Gentle smile line
              <path
                d="M -11 0 Q 0 7 11 0"
                fill="none"
                stroke="#042F2E"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            ) : (
              // Open animated mouth synchronized with speech visemes
              <g>
                <ellipse
                  cx="0"
                  cy={mouthHeight / 2}
                  rx={mouthWidth / 2}
                  ry={mouthHeight / 2}
                  fill="#881337"
                  stroke="#042F2E"
                  strokeWidth="2"
                />
                {/* Tongue inside */}
                {mouthHeight > 10 && (
                  <ellipse
                    cx="0"
                    cy={mouthHeight - 3}
                    rx={mouthWidth / 3}
                    ry={mouthHeight / 4}
                    fill="#F43F5E"
                  />
                )}
              </g>
            )}
          </g>

          {/* ── Magic Sparkles when Processing ───────────────── */}
          {state === 'processing' && (
            <g className="animate-spin origin-[120px_120px] [animation-duration:4s]">
              <path
                d="M 50 70 L 53 77 L 60 80 L 53 83 L 50 90 L 47 83 L 40 80 L 47 77 Z"
                fill="#FBBF24"
              />
              <path
                d="M 190 70 L 193 77 L 200 80 L 193 83 L 190 90 L 187 83 L 180 80 L 187 77 Z"
                fill="#FBBF24"
              />
              <circle cx="120" cy="25" r="4" fill="#38BDF8" />
            </g>
          )}

          {/* ── Little Sweatdrop on Error ────────────────────── */}
          {state === 'error' && (
            <path
              d="M 172 100 C 172 94 177 88 177 88 C 177 88 182 94 182 100 C 182 104 177.5 106 177 106 C 176.5 106 172 104 172 100 Z"
              fill="#38BDF8"
              opacity="0.9"
            />
          )}
        </svg>

        {/* Soft Genie Shadow */}
        <div className="mx-auto w-32 h-3.5 bg-slate-900/10 rounded-full blur-xs mt-1 transition-all" />
      </div>
    </div>
  )
}
