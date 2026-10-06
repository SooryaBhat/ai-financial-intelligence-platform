import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Mail, ArrowLeft, CheckCircle } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useToast } from '@/hooks/useToast'

const forgotSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
})

type ForgotFormData = z.infer<typeof forgotSchema>

export const ForgotPasswordPage: React.FC = () => {
  const toast = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotFormData>({
    resolver: zodResolver(forgotSchema),
  })

  const onSubmit = async (data: ForgotFormData) => {
    setIsLoading(true)
    try {
      // Simulate endpoint request
      await new Promise((resolve) => setTimeout(resolve, 1000))
      setIsSubmitted(true)
      toast.success(`Reset link sent to ${data.email}`)
    } catch {
      toast.error('Failed to send reset link')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-xl font-bold text-surface-900 dark:text-surface-100">Reset your password</h2>
        <p className="text-xs text-surface-500 dark:text-surface-400 mt-1">
          Enter your registered email to receive password reset instructions
        </p>
      </div>

      {isSubmitted ? (
        <div className="text-center py-4 space-y-4">
          <div className="inline-flex p-3 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600">
            <CheckCircle className="w-8 h-8" />
          </div>
          <p className="text-xs text-surface-600 dark:text-surface-300">
            If an account exists for your email, we have sent instructions to reset your password.
          </p>
          <Button variant="outline" className="w-full" onClick={() => setIsSubmitted(false)}>
            Send again
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Email address"
            type="email"
            placeholder="name@company.com"
            leftIcon={<Mail className="w-4 h-4" />}
            error={errors.email?.message}
            {...register('email')}
          />

          <Button type="submit" variant="primary" className="w-full" isLoading={isLoading}>
            Send Reset Instructions
          </Button>
        </form>
      )}

      <div className="text-center pt-2">
        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-surface-600 dark:text-surface-400 hover:text-surface-900 dark:hover:text-surface-100"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to sign in
        </Link>
      </div>
    </div>
  )
}
