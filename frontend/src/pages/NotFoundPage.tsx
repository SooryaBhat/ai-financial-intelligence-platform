import React from 'react'
import { Link } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-surface-50 dark:bg-surface-950 flex flex-col items-center justify-center p-6 text-center">
      <div className="flex items-center justify-center w-20 h-20 rounded-full bg-primary-50 dark:bg-primary-950/50 text-primary-600 dark:text-primary-400 font-extrabold text-3xl mb-4">
        404
      </div>
      <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-100">Page not found</h1>
      <p className="text-xs text-surface-500 dark:text-surface-400 max-w-sm mt-2 mb-6">
        The requested module or resource does not exist or has been moved.
      </p>
      <div className="flex items-center gap-3">
        <Link to="/dashboard">
          <Button variant="primary" leftIcon={<Home className="w-4 h-4" />}>
            Back to Dashboard
          </Button>
        </Link>
        <Button variant="outline" onClick={() => window.history.back()} leftIcon={<ArrowLeft className="w-4 h-4" />}>
          Go Back
        </Button>
      </div>
    </div>
  )
}
