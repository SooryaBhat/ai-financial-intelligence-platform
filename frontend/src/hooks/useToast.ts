import toast from 'react-hot-toast'

export const useToast = () => {
  return {
    success: (message: string) => {
      toast.success(message, {
        style: {
          borderRadius: '8px',
          background: 'var(--bg-surface)',
          color: 'var(--text-primary)',
          border: '1px solid var(--border)',
        },
      })
    },
    error: (message: string) => {
      toast.error(message, {
        style: {
          borderRadius: '8px',
          background: 'var(--bg-surface)',
          color: 'var(--text-primary)',
          border: '1px solid var(--border)',
        },
      })
    },
    info: (message: string) => {
      toast(message, {
        icon: 'ℹ️',
        style: {
          borderRadius: '8px',
          background: 'var(--bg-surface)',
          color: 'var(--text-primary)',
          border: '1px solid var(--border)',
        },
      })
    },
  }
}
