import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Brain,
  Trash2,
  Plus,
  Check,
  X,
  Search,
  Sparkles,
  FileText,
  Sliders,
  Target,
  Building,
} from 'lucide-react'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Spinner } from '@/components/ui/Spinner'
import { chatService, AIMemoryItem } from '@/services/chat.service'

interface MemorySettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export const MemorySettingsModal: React.FC<MemorySettingsModalProps> = ({
  isOpen,
  onClose,
}) => {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [isAdding, setIsAdding] = useState(false)
  const [newContent, setNewContent] = useState('')
  const [newCategory, setNewCategory] = useState<AIMemoryItem['category']>('preference')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [confirmClear, setConfirmClear] = useState(false)

  const { data: memories = [], isLoading } = useQuery({
    queryKey: ['ai-memories', search, selectedCategory],
    queryFn: () =>
      chatService.listMemories(
        selectedCategory === 'all' ? undefined : selectedCategory,
        search
      ),
    enabled: isOpen,
  })

  const createMutation = useMutation({
    mutationFn: (payload: { content: string; category: string }) =>
      chatService.createMemory(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-memories'] })
      setIsAdding(false)
      setNewContent('')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, content, is_active }: { id: string; content?: string; is_active?: boolean }) =>
      chatService.updateMemory(id, { content, is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-memories'] })
      setEditingId(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => chatService.deleteMemory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-memories'] })
    },
  })

  const clearAllMutation = useMutation({
    mutationFn: () => chatService.clearAllMemories(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-memories'] })
      setConfirmClear(false)
    },
  })

  const getCategoryMeta = (cat: string) => {
    switch (cat) {
      case 'preference':
        return { label: 'Preference', icon: Sliders, color: 'bg-indigo-50 text-indigo-700 border-indigo-200' }
      case 'reporting':
        return { label: 'Reporting Rule', icon: FileText, color: 'bg-emerald-50 text-emerald-700 border-emerald-200' }
      case 'business_fact':
        return { label: 'Business Fact', icon: Building, color: 'bg-amber-50 text-amber-700 border-amber-200' }
      case 'goal':
        return { label: 'Goal & Target', icon: Target, color: 'bg-purple-50 text-purple-700 border-purple-200' }
      default:
        return { label: cat, icon: Sparkles, color: 'bg-slate-50 text-slate-700 border-slate-200' }
    }
  }

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newContent.trim()) return
    createMutation.mutate({ content: newContent.trim(), category: newCategory })
  }

  const handleSaveEdit = (id: string) => {
    if (!editContent.trim()) return
    updateMutation.mutate({ id, content: editContent.trim() })
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="AI Copilot Persistent Memories"
      description="Manage long-term context, preferences, and recurring business rules that carry across your conversations."
      maxWidth="2xl"
      footer={
        <div className="flex items-center justify-between w-full">
          <div>
            {confirmClear ? (
              <div className="flex items-center space-x-2">
                <span className="text-xs text-rose-600 font-medium">Clear all your memories?</span>
                <Button
                  size="sm"
                  variant="danger"
                  isLoading={clearAllMutation.isPending}
                  onClick={() => clearAllMutation.mutate()}
                >
                  Yes, Clear
                </Button>
                <Button size="sm" variant="outline" onClick={() => setConfirmClear(false)}>
                  Cancel
                </Button>
              </div>
            ) : (
              <Button
                size="sm"
                variant="outline"
                className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 border-rose-200"
                onClick={() => setConfirmClear(true)}
                disabled={memories.length === 0}
              >
                Clear All Memories
              </Button>
            )}
          </div>
          <Button variant="outline" onClick={onClose}>
            Done
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Info banner */}
        <div className="bg-teal-50 border border-teal-200 rounded-lg p-3 text-xs text-teal-800 flex items-start space-x-2">
          <Brain className="w-4 h-4 text-teal-700 mt-0.5 shrink-0" />
          <p>
            Memories provide persistent context (such as preferred reporting currency, fiscal cycles, or key business
            targets). <strong>Memories never override live ledger numbers</strong> — the assistant always verifies ERP
            tools for current metrics.
          </p>
        </div>

        {/* Filter & Add row */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-1 overflow-x-auto pb-1 text-xs">
            {['all', 'preference', 'reporting', 'business_fact', 'goal'].map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`px-2.5 py-1 rounded-full font-medium transition-colors ${
                  selectedCategory === cat
                    ? 'bg-teal-700 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {cat === 'all' ? 'All Memories' : getCategoryMeta(cat).label}
              </button>
            ))}
          </div>

          {!isAdding && (
            <Button
              size="sm"
              variant="primary"
              className="bg-teal-700 hover:bg-teal-800 text-white text-xs"
              onClick={() => setIsAdding(true)}
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              Add Memory
            </Button>
          )}
        </div>

        {/* Add Memory Form */}
        {isAdding && (
          <form onSubmit={handleCreate} className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-700">Add New Persistent Memory</span>
              <button
                type="button"
                onClick={() => setIsAdding(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <textarea
              className="w-full text-xs p-2.5 border border-slate-300 rounded-md focus:ring-1 focus:ring-teal-600 focus:border-teal-600 bg-white"
              rows={2}
              placeholder="e.g. Always display sales comparisons in INR Lakhs, or Our fiscal year starts in April"
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              required
            />
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-xs text-slate-500">Category:</span>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value as any)}
                  className="text-xs border border-slate-300 rounded px-2 py-1 bg-white"
                >
                  <option value="preference">Preference</option>
                  <option value="reporting">Reporting Rule</option>
                  <option value="business_fact">Business Fact</option>
                  <option value="goal">Goal & Target</option>
                </select>
              </div>
              <div className="flex items-center space-x-2">
                <Button size="sm" variant="outline" type="button" onClick={() => setIsAdding(false)}>
                  Cancel
                </Button>
                <Button
                  size="sm"
                  variant="primary"
                  type="submit"
                  isLoading={createMutation.isPending}
                  className="bg-teal-700 hover:bg-teal-800 text-white"
                >
                  Save Memory
                </Button>
              </div>
            </div>
          </form>
        )}

        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <Input
            placeholder="Search saved memories..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 text-xs"
          />
        </div>

        {/* Memories List */}
        <div className="max-h-80 overflow-y-auto space-y-2 pr-1">
          {isLoading ? (
            <div className="py-8 flex justify-center">
              <Spinner size="md" />
            </div>
          ) : memories.length === 0 ? (
            <div className="py-8 text-center text-slate-500 text-xs">
              <Brain className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="font-medium">No saved memories found</p>
              <p className="text-slate-400 mt-0.5">
                Tell the assistant "Remember that..." or use "Add Memory" above.
              </p>
            </div>
          ) : (
            memories.map((mem) => {
              const meta = getCategoryMeta(mem.category)
              const isEditing = editingId === mem.id

              return (
                <div
                  key={mem.id}
                  className={`p-3 border rounded-lg transition-all ${
                    mem.is_active ? 'bg-white border-slate-200' : 'bg-slate-50 border-slate-200 opacity-60'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border ${meta.color}`}
                        >
                          <meta.icon className="w-3 h-3 mr-1" />
                          {meta.label}
                        </span>
                        <span className="text-[10px] text-slate-400">
                          {new Date(mem.created_at).toLocaleDateString([], {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </span>
                      </div>

                      {isEditing ? (
                        <div className="mt-2 space-y-2">
                          <textarea
                            className="w-full text-xs p-2 border border-slate-300 rounded bg-white"
                            rows={2}
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                          />
                          <div className="flex items-center space-x-2">
                            <Button size="sm" variant="primary" onClick={() => handleSaveEdit(mem.id)}>
                              <Check className="w-3.5 h-3.5 mr-1" />
                              Save
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => setEditingId(null)}>
                              Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <p className="text-xs text-slate-700 leading-relaxed font-normal">{mem.content}</p>
                      )}
                    </div>

                    {!isEditing && (
                      <div className="flex items-center space-x-1 shrink-0">
                        <button
                          type="button"
                          title={mem.is_active ? 'Active (Click to pause)' : 'Paused (Click to activate)'}
                          onClick={() => updateMutation.mutate({ id: mem.id, is_active: !mem.is_active })}
                          className={`p-1 rounded text-xs transition-colors ${
                            mem.is_active
                              ? 'text-emerald-700 hover:bg-emerald-50'
                              : 'text-slate-400 hover:bg-slate-200'
                          }`}
                        >
                          {mem.is_active ? 'Active' : 'Off'}
                        </button>
                        <button
                          type="button"
                          title="Edit memory"
                          onClick={() => {
                            setEditingId(mem.id)
                            setEditContent(mem.content)
                          }}
                          className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100"
                        >
                          <Sliders className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          title="Delete memory"
                          onClick={() => deleteMutation.mutate(mem.id)}
                          className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </Modal>
  )
}
