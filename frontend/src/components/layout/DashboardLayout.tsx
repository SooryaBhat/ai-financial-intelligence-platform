import React, { useState } from 'react'
import { Outlet, Link } from 'react-router-dom'
import { Navbar } from './Navbar'
import { CommandPalette } from '@/components/search/CommandPalette'
import { AIAssistantDrawer } from '@/components/ai/AIAssistantDrawer'
import { Bot, HelpCircle, LayoutGrid } from 'lucide-react'

export const DashboardLayout: React.FC = () => {
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [isAIAssistantOpen, setIsAIAssistantOpen] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* ── Top Navbar (Primary Modular Navigation, App Launcher, Search, Company Switcher) ── */}
      <Navbar
        onOpenSearch={() => setIsSearchOpen(true)}
        onToggleAIAssistant={() => setIsAIAssistantOpen(!isAIAssistantOpen)}
      />

      {/* ── Main Operational Workspace (Full Width, No Permanent Left Sidebar) ── */}
      <div className="flex-1 flex flex-col min-w-0 w-full overflow-x-clip">
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto animate-fade-in min-w-0">
          <Outlet />
        </main>

        {/* Application Shell Footer */}
        <footer className="py-3 px-6 border-t border-slate-200 bg-white text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-800">ALLADIN</span>
            <span className="text-slate-300">&bull;</span>
            <span className="text-slate-500">Enterprise ERP & Financial Intelligence Platform</span>
          </div>
          <div className="flex items-center gap-4 text-slate-500 text-xs">
            <Link to="/apps" className="hover:text-teal-700 flex items-center gap-1 transition-colors">
              <LayoutGrid className="w-3.5 h-3.5 text-slate-400" />
              <span>All Modules</span>
            </Link>
            <Link to="/help" className="hover:text-teal-700 flex items-center gap-1 transition-colors">
              <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
              <span>Documentation & Guides</span>
            </Link>
            <button
              onClick={() => setIsAIAssistantOpen(true)}
              className="hover:text-teal-700 flex items-center gap-1 transition-colors font-medium text-teal-700"
            >
              <Bot className="w-3.5 h-3.5" />
              <span>Ask AI Copilot</span>
            </button>
          </div>
        </footer>
      </div>

      {/* ── Global Search Command Palette (Ctrl+K) ── */}
      <CommandPalette
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onOpenAIAssistant={() => setIsAIAssistantOpen(true)}
      />

      {/* ── Persistent AI Assistant Slide-over Drawer ── */}
      <AIAssistantDrawer
        isOpen={isAIAssistantOpen}
        onClose={() => setIsAIAssistantOpen(false)}
      />

      {/* Floating Quick Action for AI Copilot (bottom right) */}
      <button
        onClick={() => setIsAIAssistantOpen(true)}
        className="fixed bottom-5 right-5 z-30 flex items-center gap-2 px-3.5 py-2.5 rounded-full bg-teal-700 text-white shadow-lg hover:bg-teal-800 transition-all hover:scale-105 group border border-teal-600/40"
        title="Open ALLADIN AI Assistant"
      >
        <Bot className="w-4 h-4 text-teal-200" />
        <span className="text-xs font-semibold pr-1 hidden sm:inline">Ask Copilot</span>
      </button>
    </div>
  )
}
