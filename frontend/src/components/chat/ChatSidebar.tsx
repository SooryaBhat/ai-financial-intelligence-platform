import React, { useState } from 'react'
import {
  Plus,
  Search,
  MessageSquare,
  Edit2,
  Trash2,
  Check,
  X,
  Brain,
  Bot,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { ChatSessionItem } from '@/services/chat.service'
import { Spinner } from '@/components/ui/Spinner'

interface ChatSidebarProps {
  sessions: ChatSessionItem[]
  activeSessionId: string | null
  isLoadingSessions: boolean
  onSelectSession: (sessionId: string) => void
  onNewChat: () => void
  onRenameSession: (sessionId: string, newTitle: string) => void
  onDeleteSession: (sessionId: string) => void
  onOpenMemorySettings: () => void
  activeMemoriesCount?: number
  providerInfo?: { provider: string; model?: string }
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  sessions,
  activeSessionId,
  isLoadingSessions,
  onSelectSession,
  onNewChat,
  onRenameSession,
  onDeleteSession,
  onOpenMemorySettings,
  activeMemoriesCount = 0,
  providerInfo,
  isCollapsed = false,
  onToggleCollapse,
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [deletingId, setDeletingId] = useState<string | null>(null)

  // Filter sessions by search term
  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Group sessions by date
  const groupSessions = (items: ChatSessionItem[]) => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    const sevenDaysAgo = new Date(today)
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)

    const groups: {
      today: ChatSessionItem[]
      yesterday: ChatSessionItem[]
      last7Days: ChatSessionItem[]
      older: ChatSessionItem[]
    } = {
      today: [],
      yesterday: [],
      last7Days: [],
      older: [],
    }

    items.forEach((s) => {
      const date = new Date(s.updated_at || s.created_at)
      if (date >= today) {
        groups.today.push(s)
      } else if (date >= yesterday) {
        groups.yesterday.push(s)
      } else if (date >= sevenDaysAgo) {
        groups.last7Days.push(s)
      } else {
        groups.older.push(s)
      }
    })

    return groups
  }

  const grouped = groupSessions(filteredSessions)

  const handleStartRename = (s: ChatSessionItem, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(s.id)
    setEditTitle(s.title)
  }

  const handleSaveRename = (s: ChatSessionItem, e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (editTitle.trim() && editTitle.trim() !== s.title) {
      onRenameSession(s.id, editTitle.trim())
    }
    setEditingId(null)
  }

  const handleDelete = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (deletingId === sessionId) {
      onDeleteSession(sessionId)
      setDeletingId(null)
    } else {
      setDeletingId(sessionId)
      setTimeout(() => {
        setDeletingId((prev) => (prev === sessionId ? null : prev))
      }, 4000)
    }
  }

  if (isCollapsed) {
    return (
      <div className="w-14 bg-white border-r border-slate-200 flex flex-col items-center py-4 space-y-4 shrink-0 transition-all">
        <button
          onClick={onToggleCollapse}
          title="Expand sidebar"
          className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg"
        >
          <ChevronRight className="w-5 h-5" />
        </button>

        <button
          onClick={onNewChat}
          title="New Chat"
          className="p-2.5 bg-teal-700 text-white rounded-lg hover:bg-teal-800 transition-colors shadow-sm"
        >
          <Plus className="w-5 h-5" />
        </button>

        <div className="flex-1" />

        <button
          onClick={onOpenMemorySettings}
          title={`AI Memories (${activeMemoriesCount})`}
          className="p-2 text-slate-500 hover:text-teal-700 hover:bg-teal-50 rounded-lg relative"
        >
          <Brain className="w-5 h-5" />
          {activeMemoriesCount > 0 && (
            <span className="absolute top-1 right-1 w-2 h-2 bg-teal-600 rounded-full" />
          )}
        </button>
      </div>
    )
  }

  return (
    <aside className="w-72 sm:w-80 bg-white border-r border-slate-200 flex flex-col h-full shrink-0 transition-all">
      {/* Top Header & New Chat button */}
      <div className="p-3 border-b border-slate-100 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-lg bg-teal-700 text-white flex items-center justify-center font-bold text-xs shadow-sm">
              <Bot className="w-4 h-4" />
            </div>
            <span className="font-semibold text-slate-900 text-sm">ALLADIN Chat</span>
          </div>

          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md"
              title="Collapse sidebar"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          )}
        </div>

        <Button
          onClick={onNewChat}
          className="w-full justify-center bg-teal-700 hover:bg-teal-800 text-white font-medium py-2 rounded-lg shadow-sm text-xs flex items-center space-x-2 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Chat</span>
        </Button>

        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600 focus:border-teal-600"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-2 top-2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-4">
        {isLoadingSessions ? (
          <div className="py-8 flex justify-center">
            <Spinner size="sm" />
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-xs px-4">
            <MessageSquare className="w-6 h-6 text-slate-300 mx-auto mb-2" />
            <p className="font-medium text-slate-500">No conversations found</p>
            <p className="text-[11px] text-slate-400 mt-1">
              {searchTerm ? 'Try a different search keyword' : 'Click "New Chat" to begin'}
            </p>
          </div>
        ) : (
          <>
            {[
              { title: 'Today', list: grouped.today },
              { title: 'Yesterday', list: grouped.yesterday },
              { title: 'Previous 7 Days', list: grouped.last7Days },
              { title: 'Older', list: grouped.older },
            ].map(
              ({ title, list }) =>
                list.length > 0 && (
                  <div key={title} className="space-y-1">
                    <div className="px-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                      {title}
                    </div>

                    <div className="space-y-0.5">
                      {list.map((session) => {
                        const isActive = activeSessionId === session.id
                        const isEditing = editingId === session.id
                        const isConfirmingDelete = deletingId === session.id

                        return (
                          <div
                            key={session.id}
                            onClick={() => !isEditing && onSelectSession(session.id)}
                            className={`group flex items-center justify-between px-2.5 py-2 rounded-lg text-xs cursor-pointer transition-colors ${
                              isActive
                                ? 'bg-teal-50 text-teal-900 font-medium border border-teal-200/60'
                                : 'text-slate-700 hover:bg-slate-100'
                            }`}
                          >
                            <div className="flex items-center space-x-2 truncate flex-1 min-w-0">
                              <MessageSquare
                                className={`w-3.5 h-3.5 shrink-0 ${
                                  isActive ? 'text-teal-700' : 'text-slate-400'
                                }`}
                              />

                              {isEditing ? (
                                <form
                                  onSubmit={(e) => handleSaveRename(session, e)}
                                  className="flex items-center space-x-1 flex-1 min-w-0"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <input
                                    type="text"
                                    value={editTitle}
                                    onChange={(e) => setEditTitle(e.target.value)}
                                    className="text-xs px-1.5 py-0.5 border border-teal-600 rounded bg-white w-full focus:outline-none"
                                    autoFocus
                                    onKeyDown={(e) => {
                                      if (e.key === 'Escape') setEditingId(null)
                                    }}
                                  />
                                  <button
                                    type="submit"
                                    className="p-1 text-teal-700 hover:bg-teal-100 rounded"
                                    title="Save"
                                  >
                                    <Check className="w-3.5 h-3.5" />
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => setEditingId(null)}
                                    className="p-1 text-slate-400 hover:bg-slate-200 rounded"
                                    title="Cancel"
                                  >
                                    <X className="w-3.5 h-3.5" />
                                  </button>
                                </form>
                              ) : (
                                <span className="truncate">{session.title}</span>
                              )}
                            </div>

                            {/* Actions on hover */}
                            {!isEditing && (
                              <div
                                className={`flex items-center space-x-1 shrink-0 ${
                                  isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                                } transition-opacity`}
                              >
                                <button
                                  type="button"
                                  title="Rename"
                                  onClick={(e) => handleStartRename(session, e)}
                                  className="p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded"
                                >
                                  <Edit2 className="w-3 h-3" />
                                </button>

                                <button
                                  type="button"
                                  title={isConfirmingDelete ? 'Confirm delete?' : 'Delete'}
                                  onClick={(e) => handleDelete(session.id, e)}
                                  className={`p-1 rounded transition-colors ${
                                    isConfirmingDelete
                                      ? 'bg-rose-600 text-white hover:bg-rose-700'
                                      : 'text-slate-400 hover:text-rose-600 hover:bg-rose-50'
                                  }`}
                                >
                                  <Trash2 className="w-3 h-3" />
                                </button>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
            )}
          </>
        )}
      </div>

      {/* Bottom Footer: Memories & Provider Info */}
      <div className="p-2.5 border-t border-slate-100 bg-slate-50/70 space-y-2">
        <button
          onClick={onOpenMemorySettings}
          className="w-full flex items-center justify-between px-2.5 py-1.5 text-xs text-slate-700 hover:bg-white rounded-lg border border-transparent hover:border-slate-200 transition-all group"
        >
          <div className="flex items-center space-x-2">
            <Brain className="w-4 h-4 text-teal-700 group-hover:scale-105 transition-transform" />
            <span className="font-medium text-slate-800">Memory Settings</span>
          </div>
          {activeMemoriesCount > 0 ? (
            <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-teal-100 text-teal-800 rounded-full">
              {activeMemoriesCount} active
            </span>
          ) : (
            <span className="text-[10px] text-slate-400">Configure</span>
          )}
        </button>

        {/* Provider details */}
        {providerInfo && (
          <div className="px-2 py-1 text-[11px] flex items-center justify-between text-slate-500 bg-white border border-slate-200/60 rounded-md">
            <span className="text-[10px] uppercase font-semibold text-slate-400">Model Engine:</span>
            <span className="font-medium text-slate-700 capitalize flex items-center space-x-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
              <span>
                {providerInfo.provider === 'ollama'
                  ? `Ollama (${providerInfo.model || 'qwen3:4b'})`
                  : providerInfo.provider === 'gemini'
                  ? `Gemini (${providerInfo.model || '2.5-flash'})`
                  : 'Grounded ERP Engine'}
              </span>
            </span>
          </div>
        )}
      </div>
    </aside>
  )
}
