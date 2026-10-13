import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useToast } from '@/hooks/useToast'

const forgotSchema = z.object({
  email: z.string().email('Please enter a valid work email address'),
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
      await new Promise((resolve) => setTimeout(resolve, 800))
      setIsSubmitted(true)
      toast.success(`Password reset link dispatched to ${data.email}`)
    } catch {
      toast.error('Failed to dispatch reset email')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-1">
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Reset Password</h2>
        <p className="text-xs text-slate-500">
          Enter your registered email address to receive recovery instructions
        </p>
      </div>

      {isSubmitted ? (
        <div className="text-center py-4 space-y-4">
          <div className="inline-flex p-3 rounded-full bg-teal-50 text-teal-700">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            If an ALLADIN account is associated with this email, we have sent instructions to reset your password.
          </p>
          <Button variant="outline" className="w-full" onClick={() => setIsSubmitted(false)}>
            Request another link
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Work Email Address"
            type="email"
            placeholder="name@company.com"
            leftIcon={<Mail className="w-4 h-4 text-slate-400" />}
            error={errors.email?.message}
            {...register('email')}
          />

          <Button type="submit" variant="primary" className="w-full mt-2" isLoading={isLoading}>
            Send Recovery Link
          </Button>
        </form>
      )}

      <div className="text-center pt-2">
        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to sign in
        </Link>
      </div>
    </div>
  )
}
