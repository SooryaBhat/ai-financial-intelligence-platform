import React from 'react'
import { Sun, Moon, Laptop } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'

export const ThemeSwitch: React.FC<{ className?: string }> = ({ className }) => {
  const { theme, setTheme } = useTheme()

  const toggleTheme = () => {
    if (theme === 'light') setTheme('dark')
    else if (theme === 'dark') setTheme('system')
    else setTheme('light')
  }

  return (
    <button
      onClick={toggleTheme}
      title={`Theme: ${theme}`}
      className={cn(
        'p-2 rounded-lg text-surface-500 hover:text-surface-900 dark:text-surface-400 dark:hover:text-surface-100 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors',
        className
      )}
    >
      {theme === 'light' && <Sun className="w-5 h-5 text-amber-500" />}
      {theme === 'dark' && <Moon className="w-5 h-5 text-indigo-400" />}
      {theme === 'system' && <Laptop className="w-5 h-5 text-surface-500" />}
    </button>
  )
}
