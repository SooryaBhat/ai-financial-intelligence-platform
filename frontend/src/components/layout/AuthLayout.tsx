import React from 'react'
import { Outlet, Link } from 'react-router-dom'
import { ThemeSwitch } from './ThemeSwitch'

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-surface-50 dark:bg-surface-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative selection:bg-primary-500 selection:text-white">
      {/* Top right theme switcher */}
      <div className="absolute top-4 right-4">
        <ThemeSwitch />
      </div>

      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
        <Link to="/login" className="inline-flex items-center gap-3">
          <div className="flex items-center justify-center w-11 h-11 rounded-2xl bg-gradient-to-tr from-primary-600 to-indigo-500 text-white font-black text-xl shadow-lg">
            F
          </div>
          <span className="font-extrabold text-2xl tracking-tight text-surface-900 dark:text-surface-100">
            FinIntel AI
          </span>
        </Link>
        <p className="mt-2 text-xs font-medium text-surface-500 dark:text-surface-400">
          AI Financial Intelligence & Enterprise ERP Platform
        </p>
      </div>

      {/* Auth Form Box */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="bg-white dark:bg-surface-900 py-8 px-6 sm:px-10 border border-surface-200 dark:border-surface-800 rounded-2xl shadow-card-lg">
          <Outlet />
        </div>
      </div>

      <p className="mt-8 text-center text-xs text-surface-400">
        Protected by Enterprise Bank-Grade 256-bit Encryption
      </p>
    </div>
  )
}
