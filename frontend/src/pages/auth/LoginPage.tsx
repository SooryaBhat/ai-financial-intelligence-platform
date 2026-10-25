import React, { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Mail, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/hooks/useToast'
import axios from 'axios'

const loginSchema = z.object({
  email: z.string().email('Please enter a valid business email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginFormData = z.infer<typeof loginSchema>

export const LoginPage: React.FC = () => {
  const { login } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/apps'

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true)
    try {
      await login(data)
      toast.success('Successfully authenticated')
      navigate(from, { replace: true })
    } catch (err: unknown) {
      let errorMessage = 'An unexpected error occurred during authentication.'

      if (axios.isAxiosError(err)) {
        if (!err.response) {
          // Network error, CORS failure, or server unreachable
          if (err.code === 'ECONNABORTED' || err.message?.toLowerCase().includes('timeout')) {
            errorMessage = 'Authentication request timed out. Please try again.'
          } else {
            errorMessage = 'Unable to connect to the server. Please check your network or verify the backend service is running.'
          }
        } else if (err.response.status === 401 || err.response.status === 400) {
          // Genuine authentication failure
          const detail = err.response.data?.detail || err.response.data?.message
          errorMessage = typeof detail === 'string' ? detail : 'Invalid email or password'
        } else if (err.response.status === 429) {
          errorMessage = 'Too many login attempts. Please wait a moment and try again.'
        } else if (err.response.status >= 500) {
          const detail = err.response.data?.detail
          errorMessage = typeof detail === 'string' ? detail : 'Authentication service is temporarily unavailable. Please try again later.'
        } else {
          const detail = err.response.data?.detail || err.response.data?.message
          errorMessage = typeof detail === 'string' ? detail : 'Authentication failed. Please verify your credentials.'
        }
      } else if (err instanceof Error) {
        errorMessage = err.message
      }

      toast.error(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-1">
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Sign in to ALLADIN</h2>
        <p className="text-xs text-slate-500">
          Enter your credentials to access your ERP workspace & forecasts
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Work Email Address"
          type="email"
          placeholder="name@company.com"
          leftIcon={<Mail className="w-4 h-4 text-slate-400" />}
          error={errors.email?.message}
          {...register('email')}
        />

        <div className="space-y-1">
          <div className="relative">
            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              leftIcon={<Lock className="w-4 h-4 text-slate-400" />}
              error={errors.password?.message}
              {...register('password')}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-8 text-slate-400 hover:text-slate-600 transition-colors"
              title={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          <div className="flex justify-end pt-1">
            <Link
              to="/forgot-password"
              className="text-xs font-semibold text-teal-700 hover:text-teal-800 hover:underline"
            >
              Forgot password?
            </Link>
          </div>
        </div>

        <Button
          type="submit"
          variant="primary"
          className="w-full mt-2"
          isLoading={isLoading}
          rightIcon={<ArrowRight className="w-4 h-4" />}
        >
          Sign in to Workspace
        </Button>
      </form>

      <div className="text-center text-xs text-slate-500 pt-3 border-t border-slate-100">
        New to ALLADIN?{' '}
        <Link to="/register" className="font-semibold text-teal-700 hover:text-teal-800 hover:underline">
          Create company account
        </Link>
      </div>
    </div>
  )
}
