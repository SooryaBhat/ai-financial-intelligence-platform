import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Building2, Globe, DollarSign, ArrowRight } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { authService } from '@/services/auth.service'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/hooks/useToast'

const onboardSchema = z.object({
  company_name: z.string().min(2, 'Company name must be at least 2 characters'),
  company_slug: z
    .string()
    .min(2, 'Slug must be at least 2 characters')
    .regex(/^[a-z0-9-]+$/, 'Slug can only contain lowercase letters, numbers, and hyphens'),
  industry: z.string().optional(),
  country: z.string().optional(),
  currency: z.string().length(3, 'Currency must be a 3-letter code (e.g. USD)'),
  timezone: z.string().min(1, 'Timezone is required'),
})

type OnboardFormData = z.infer<typeof onboardSchema>

export const OnboardingPage: React.FC = () => {
  const { refreshUser, setActiveCompanyId } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<OnboardFormData>({
    resolver: zodResolver(onboardSchema),
    defaultValues: {
      currency: 'USD',
      timezone: 'UTC',
      country: 'United States',
      industry: 'Technology',
    },
  })

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    const slugified = val
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9 -]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
    setValue('company_slug', slugified, { shouldValidate: true })
  }

  const onSubmit = async (data: OnboardFormData) => {
    setIsLoading(true)
    try {
      const company = await authService.onboard(data)
      const compName = company.company_name || company.name || 'Company'
      const compId = company.company_id || company.id

      toast.success(`Company "${compName}" created successfully!`)
      if (compId) {
        setActiveCompanyId(compId)
      }
      await refreshUser()
      navigate('/dashboard', { replace: true })
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Failed to set up company profile'
      toast.error(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-xl font-bold text-surface-900 dark:text-surface-100">Company Onboarding</h2>
        <p className="text-xs text-surface-500 dark:text-surface-400 mt-1">
          Configure your primary company workspace to get started
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Company Name"
          type="text"
          placeholder="Acme Financial Corp"
          leftIcon={<Building2 className="w-4 h-4" />}
          error={errors.company_name?.message}
          {...register('company_name', { onChange: handleNameChange })}
        />

        <Input
          label="Company Slug (Unique Identifier)"
          type="text"
          placeholder="acme-financial"
          leftIcon={<Globe className="w-4 h-4" />}
          error={errors.company_slug?.message}
          {...register('company_slug')}
        />

        <div className="grid grid-cols-2 gap-3">
          <Select
            label="Industry"
            options={[
              { label: 'Technology', value: 'Technology' },
              { label: 'Retail & E-commerce', value: 'Retail' },
              { label: 'Manufacturing', value: 'Manufacturing' },
              { label: 'Healthcare', value: 'Healthcare' },
              { label: 'Financial Services', value: 'Financial' },
            ]}
            error={errors.industry?.message}
            {...register('industry')}
          />

          <Select
            label="Default Currency"
            options={[
              { label: 'USD ($)', value: 'USD' },
              { label: 'EUR (€)', value: 'EUR' },
              { label: 'GBP (£)', value: 'GBP' },
              { label: 'CAD ($)', value: 'CAD' },
              { label: 'INR (₹)', value: 'INR' },
            ]}
            leftIcon={<DollarSign className="w-4 h-4" />}
            error={errors.currency?.message}
            {...register('currency')}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Country"
            type="text"
            placeholder="United States"
            error={errors.country?.message}
            {...register('country')}
          />

          <Input
            label="Timezone"
            type="text"
            placeholder="UTC"
            error={errors.timezone?.message}
            {...register('timezone')}
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          className="w-full mt-2"
          isLoading={isLoading}
          rightIcon={<ArrowRight className="w-4 h-4" />}
        >
          Launch Financial Workspace
        </Button>
      </form>
    </div>
  )
}
