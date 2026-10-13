import React from 'react'
import { Link } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AlladinLogoProps {
  className?: string
  showTagline?: boolean
  showFullName?: boolean
  size?: 'sm' | 'md' | 'lg'
  to?: string
}

export const AlladinLogo: React.FC<AlladinLogoProps> = ({
  className,
  showTagline = false,
  showFullName = false,
  size = 'md',
  to = '/',
}) => {
  const iconSizes = {
    sm: 'w-7 h-7 text-xs',
    md: 'w-8 h-8 text-sm',
    lg: 'w-10 h-10 text-base',
  }

  const textSizes = {
    sm: 'text-base',
    md: 'text-lg',
    lg: 'text-xl',
  }

  const content = (
    <div className={cn('flex items-center gap-2.5', className)}>
      {/* Brand Icon: Minimalist geometric emblem with subtle teal gradient & AI sparkle */}
      <div
        className={cn(
          'relative flex items-center justify-center rounded-lg bg-gradient-to-br from-teal-600 to-teal-800 text-white font-black tracking-wider shadow-sm ring-1 ring-teal-700/20 shrink-0 select-none',
          iconSizes[size]
        )}
      >
        <span className="font-mono tracking-tighter">A</span>
        <Sparkles className="w-2.5 h-2.5 absolute -top-1 -right-1 text-teal-300 pointer-events-none" />
      </div>

      <div className="flex flex-col min-w-0">
        <div className="flex items-center gap-1.5 leading-none">
          <span className={cn('font-bold tracking-tight text-slate-900', textSizes[size])}>
            ALLADIN
          </span>
          <span className="px-1 py-0.5 text-[9px] font-semibold uppercase tracking-wider rounded bg-teal-50 text-teal-700 border border-teal-200/60 leading-none">
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
