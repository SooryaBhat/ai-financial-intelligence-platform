import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bell, CheckCheck } from 'lucide-react'
import { notificationService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { ErrorState } from '@/components/ui/ErrorState'
import { useToast } from '@/hooks/useToast'
import { formatDate } from '@/lib/utils'

interface NotificationRecord {
  id: string
  title?: string
  message?: string
  is_read?: boolean
  created_at?: string
  [key: string]: unknown
}

export const NotificationsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationService.list(),
  })

  const markReadMutation = useMutation({
    mutationFn: (ids: string[]) => notificationService.markRead(ids),
    onSuccess: () => {
      toast.success('Notifications marked as read')
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  if (isError) return <ErrorState title="Failed to load notifications" onRetry={() => refetch()} />

  const notifications = (Array.isArray(data) ? data : []) as NotificationRecord[]

  const handleMarkAllRead = () => {
    const unreadIds = notifications.filter((n) => !n.is_read).map((n) => n.id)
    if (unreadIds.length > 0) {
      markReadMutation.mutate(unreadIds)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">System Notifications & Alerts</h1>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            Operational notifications, stock level alerts, and AI anomaly warnings
          </p>
        </div>
        <Button variant="outline" onClick={handleMarkAllRead} leftIcon={<CheckCheck className="w-4 h-4 text-emerald-600" />}>
          Mark All Read
        </Button>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          <div className="p-8 text-center text-xs text-surface-400">Loading system notifications...</div>
        ) : notifications.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-surface-200 dark:border-surface-800 rounded-2xl bg-white dark:bg-surface-900">
            <Bell className="w-8 h-8 text-surface-300 mx-auto mb-2" />
            <p className="text-sm font-semibold text-surface-900 dark:text-surface-100">All caught up!</p>
            <p className="text-xs text-surface-400 mt-1">No system alerts or unread notifications.</p>
          </div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              className={`p-4 rounded-xl border transition-colors flex items-start justify-between gap-4 ${
                !n.is_read
                  ? 'bg-primary-50/50 dark:bg-primary-950/20 border-primary-200 dark:border-primary-800/40'
                  : 'bg-white dark:bg-surface-900 border-surface-200 dark:border-surface-800'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-surface-100 dark:bg-surface-800 text-surface-500 mt-0.5">
                  <Bell className="w-4 h-4 text-primary-600" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-xs text-surface-900 dark:text-surface-100">
                      {n.title || 'System Alert'}
                    </span>
                    {!n.is_read && <Badge variant="info">New</Badge>}
                  </div>
                  <p className="text-xs text-surface-600 dark:text-surface-400 mt-1">{n.message || 'Notification detail.'}</p>
                  <p className="text-[10px] text-surface-400 mt-2">{n.created_at ? formatDate(n.created_at) : 'Just now'}</p>
                </div>
              </div>
              {!n.is_read && (
                <Button variant="ghost" size="sm" onClick={() => markReadMutation.mutate([n.id])}>
                  Dismiss
                </Button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
