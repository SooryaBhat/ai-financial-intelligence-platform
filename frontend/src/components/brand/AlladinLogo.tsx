import React from 'react'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'

interface AlladinLogoProps {
  className?: string
  showTagline?: boolean
  showFullName?: boolean
  size?: 'sm' | 'md' | 'lg' | 'xl'
  to?: string
  variant?: 'standard' | 'wordmark' | 'icon-only'
}

export const AlladinLogo: React.FC<AlladinLogoProps> = ({
  className,
  showTagline = false,
  showFullName = false,
  size = 'md',
  to = '/',
  variant = 'standard',
}) => {
  const iconSizes = {
    sm: 'w-7 h-7',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
    xl: 'w-12 h-12',
  }

  const textSizes = {
    sm: 'text-base',
    md: 'text-lg',
    lg: 'text-xl',
    xl: 'text-2xl',
  }

  const wordmarkHeights = {
    sm: 'h-7',
    md: 'h-8',
    lg: 'h-10',
    xl: 'h-12',
  }

  if (variant === 'wordmark') {
    const wordmarkContent = (
      <img
        src="/assets/brand/alladin-logo.svg"
        alt="ALLADIN ERP · AI"
        className={cn('w-auto object-contain select-none', wordmarkHeights[size], className)}
      />
    )
    if (to) {
      return (
        <Link to={to} className="inline-flex hover:opacity-95 transition-opacity">
          {wordmarkContent}
        </Link>
      )
    }
    return wordmarkContent
  }

  if (variant === 'icon-only') {
    const iconOnlyContent = (
      <img
        src="/assets/brand/alladin-app-icon.svg"
        alt="ALLADIN Icon"
        className={cn('rounded-lg shadow-xs select-none object-contain', iconSizes[size], className)}
      />
    )
    if (to) {
      return (
        <Link to={to} className="inline-flex hover:opacity-95 transition-opacity">
          {iconOnlyContent}
        </Link>
      )
    }
    return iconOnlyContent
  }

  const content = (
    <div className={cn('flex items-center gap-2.5', className)}>
      {/* Official ALLADIN App Icon: Luminous teal genie lamp, AI flame & gold spark */}
      <div
        className={cn(
          'relative flex items-center justify-center rounded-lg overflow-hidden shadow-xs ring-1 ring-teal-500/20 shrink-0 select-none bg-[#073D4A]',
          iconSizes[size]
        )}
      >
        <img
          src="/assets/brand/alladin-app-icon.svg"
          alt="ALLADIN"
          className="w-full h-full object-contain"
        />
      </div>

      <div className="flex flex-col min-w-0">
        <div className="flex items-center gap-1.5 leading-none">
          <span className={cn('font-extrabold tracking-tight text-slate-900', textSizes[size])}>
            ALLADIN
          </span>
          <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded bg-teal-50 text-teal-700 border border-teal-200/70 leading-none">
            ERP·AI
          </span>
        </div>

        {showFullName && (
          <span className="text-[10px] text-slate-500 font-medium truncate mt-0.5">
            Ledger Learning & Analytics Network
          </span>
        )}

        {showTagline && !showFullName && (
          <span className="text-[10px] text-slate-500 font-medium truncate mt-0.5">
            From business data to intelligent decisions
          </span>
        )}
      </div>
    </div>
  )

  if (to) {
    return (
      <Link to={to} className="inline-flex hover:opacity-95 transition-opacity">
        {content}
      </Link>
    )
  }

  return content
}
