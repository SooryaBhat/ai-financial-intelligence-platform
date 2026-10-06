import React, { useState, useEffect } from 'react'
import { Search as SearchIcon, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface SearchProps {
  value?: string
  onChange: (value: string) => void
  placeholder?: string
  debounceMs?: number
  className?: string
}

export const Search: React.FC<SearchProps> = ({
  value: initialValue = '',
  onChange,
  placeholder = 'Search...',
  debounceMs = 300,
  className,
}) => {
  const [searchTerm, setSearchTerm] = useState(initialValue)

  useEffect(() => {
    setSearchTerm(initialValue)
  }, [initialValue])

  useEffect(() => {
    const handler = setTimeout(() => {
      if (searchTerm !== initialValue) {
        onChange(searchTerm)
      }
    }, debounceMs)

    return () => clearTimeout(handler)
  }, [searchTerm, onChange, debounceMs, initialValue])

  const handleClear = () => {
    setSearchTerm('')
    onChange('')
  }

  return (
    <div className={cn('relative w-full max-w-xs', className)}>
      <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
      <input
        type="text"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-9 pr-8 py-2 text-xs rounded-lg border border-surface-300 dark:border-surface-700 bg-white dark:bg-surface-900 text-surface-900 dark:text-surface-100 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors"
      />
      {searchTerm && (
        <button
          onClick={handleClear}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600 dark:hover:text-surface-200"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  )
}
