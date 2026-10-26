import React from 'react'
import { Outlet, Link } from 'react-router-dom'
import { AlladinLogo } from '@/components/brand/AlladinLogo'
import { ShieldCheck, HelpCircle } from 'lucide-react'

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden flex flex-col justify-between py-8 px-4 sm:px-6 lg:px-8 selection:bg-teal-500 selection:text-white">
      {/* Subtle decorative accents with pointer-events: none */}
      <img
        src="/assets/decorative/header-wave-teal.svg"
        alt=""
        aria-hidden="true"
        className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-5xl h-32 object-cover opacity-25 pointer-events-none select-none"
      />
      <img
        src="/assets/decorative/corner-glow.svg"
        alt=""
        aria-hidden="true"
        className="absolute top-0 right-0 w-80 h-80 opacity-20 pointer-events-none select-none"
      />

      {/* Top Header */}
      <header className="max-w-7xl mx-auto w-full flex items-center justify-between relative z-10">
        <AlladinLogo size="sm" showFullName={false} to="/" />
        <Link
          to="/help"
          className="text-xs text-slate-500 hover:text-teal-700 flex items-center gap-1 font-medium transition-colors"
        >
          <HelpCircle className="w-3.5 h-3.5" />
          <span>Documentation</span>
        </Link>
      </header>

      {/* Main Container */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md my-auto py-8 relative z-10">
        <div className="bg-white py-8 px-6 sm:px-8 border border-slate-200/90 rounded-2xl shadow-md">
          <Outlet />
        </div>
      </div>

      {/* Footer Note */}
      <footer className="text-center space-y-1 relative z-10">
        <div className="flex items-center justify-center gap-1.5 text-xs text-slate-500">
          <ShieldCheck className="w-4 h-4 text-teal-600" />
          <span>Tenant Isolated &bull; 256-bit Secure Ledger Encryption</span>
        </div>
        <p className="text-[11px] text-slate-400">
          ALLADIN &bull; AI-powered Ledger Learning & Decision Intelligence Network
        </p>
      </footer>
    </div>
  )
}
