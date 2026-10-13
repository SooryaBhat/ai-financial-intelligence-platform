import React, { useState } from 'react'
import { Outlet, Link } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Navbar } from './Navbar'
import { CommandPalette } from '@/components/search/CommandPalette'
import { AIAssistantDrawer } from '@/components/ai/AIAssistantDrawer'
import { Bot, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

export const DashboardLayout: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [isAIAssistantOpen, setIsAIAssistantOpen] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* ── Top Navbar ── */}
      <Navbar
        onMobileMenuToggle={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        isSidebarCollapsed={isSidebarCollapsed}
        onOpenSearch={() => setIsSearchOpen(true)}
        onToggleAIAssistant={() => setIsAIAssistantOpen(!isAIAssistantOpen)}
      />

      <div className="flex-1 flex min-h-0">
        {/* Desktop Collapsible Sidebar */}
        <div className="hidden lg:block">
          <Sidebar
            isCollapsed={isSidebarCollapsed}
            onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          />
        </div>

        {/* Mobile Navigation Overlay */}
        {isMobileMenuOpen && (
          <div className="fixed inset-0 z-40 lg:hidden">
            <div
              onClick={() => setIsMobileMenuOpen(false)}
              className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            />
            <div className="relative z-50 w-64 h-full bg-white shadow-xl">
              <Sidebar
                isCollapsed={false}
                onToggle={() => setIsMobileMenuOpen(false)}
              />
            </div>
          </div>
        )}

        {/* Main Operational Workspace Content */}
        <div
          className={cn(
            'flex-1 flex flex-col min-w-0 transition-all duration-200',
            isSidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64'
          )}
        >
          <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto animate-fade-in">
            <Outlet />
          </main>

          {/* Application Shell Footer */}
          <footer className="py-3 px-6 border-t border-slate-200 bg-white text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-700">ALLADIN</span>
              <span>&bull;</span>
              <span>AI-powered Ledger Learning & Decision Intelligence</span>
            </div>
            <div className="flex items-center gap-4 text-slate-500 text-[11px]">
              <Link to="/help" className="hover:text-teal-700 flex items-center gap-1">
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Help & Guides</span>
              </Link>
              <button
                onClick={() => setIsAIAssistantOpen(true)}
                className="hover:text-teal-700 flex items-center gap-1"
              >
                <Bot className="w-3.5 h-3.5" />
                <span>AI Copilot</span>
              </button>
            </div>
          </footer>
        </div>
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
        className="fixed bottom-5 right-5 z-30 flex items-center gap-2 px-3 py-2 rounded-full bg-teal-700 text-white shadow-lg hover:bg-teal-800 transition-all hover:scale-105 group border border-teal-600/40"
        title="Open ALLADIN AI Assistant"
      >
        <Bot className="w-4 h-4 text-teal-200" />
        <span className="text-xs font-semibold pr-1 hidden sm:inline">Ask Copilot</span>
      </button>
    </div>
  )
}
