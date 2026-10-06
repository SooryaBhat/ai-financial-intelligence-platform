import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings as SettingsIcon, Save, Key, Shield, DollarSign } from 'lucide-react'
import { settingService } from '@/services/erp.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { ErrorState } from '@/components/ui/ErrorState'
import { useToast } from '@/hooks/useToast'

export const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const toast = useToast()

  const [fiscalYearStart, setFiscalYearStart] = useState('01-01')
  const [taxRate, setTaxRate] = useState('10.0')
  const [defaultCurrency, setDefaultCurrency] = useState('USD')

  const { isError, refetch } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const data = await settingService.listAll()
      if (data && typeof data === 'object') {
        const d = data as Record<string, { value?: string }>
        if (d.fiscal_year_start?.value) setFiscalYearStart(d.fiscal_year_start.value)
        if (d.default_tax_rate?.value) setTaxRate(d.default_tax_rate.value)
        if (d.default_currency?.value) setDefaultCurrency(d.default_currency.value)
      }
      return data
    },
  })

  const saveSettingMutation = useMutation({
    mutationFn: async () => {
      await settingService.upsert('fiscal_year_start', fiscalYearStart, 'Fiscal year start date')
      await settingService.upsert('default_tax_rate', taxRate, 'Default VAT/Sales Tax rate (%)')
      await settingService.upsert('default_currency', defaultCurrency, 'Primary ledger currency')
    },
    onSuccess: () => {
      toast.success('Platform preferences saved')
      queryClient.invalidateQueries({ queryKey: ['settings'] })
    },
    onError: () => toast.error('Failed to save settings'),
  })

  if (isError) return <ErrorState title="Failed to load settings" onRetry={() => refetch()} />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100 flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-primary-600" />
          <span>System Settings & Governance</span>
        </h1>
        <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
          Tenant settings, tax rates, accounting periods, and security rules
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <DollarSign className="w-4 h-4 text-emerald-600" />
              <span>Accounting & Tax Parameters</span>
            </CardTitle>
            <CardDescription>Fiscal calendar, default currency, and tax percentage</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select
              label="Default Base Currency"
              value={defaultCurrency}
              onChange={(e) => setDefaultCurrency(e.target.value)}
              options={[
                { label: 'USD ($)', value: 'USD' },
                { label: 'EUR (€)', value: 'EUR' },
                { label: 'GBP (£)', value: 'GBP' },
                { label: 'CAD ($)', value: 'CAD' },
                { label: 'INR (₹)', value: 'INR' },
              ]}
            />
            <Input
              label="Fiscal Year Start (MM-DD)"
              value={fiscalYearStart}
              onChange={(e) => setFiscalYearStart(e.target.value)}
              placeholder="01-01"
            />
            <Input
              label="Default Tax / VAT Rate (%)"
              type="number"
              step="0.1"
              value={taxRate}
              onChange={(e) => setTaxRate(e.target.value)}
              placeholder="10.0"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Shield className="w-4 h-4 text-indigo-600" />
              <span>Security & Audit Policy</span>
            </CardTitle>
            <CardDescription>Session timeouts, 2FA requirements, and data retention</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input label="Session Expiry (Minutes)" type="number" defaultValue="60" readOnly className="bg-surface-100 dark:bg-surface-800" />
            <Input label="Audit Log Retention (Days)" type="number" defaultValue="365" readOnly className="bg-surface-100 dark:bg-surface-800" />
            <div className="p-3 rounded-lg border border-surface-200 dark:border-surface-800 bg-surface-50 dark:bg-surface-800/40 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-primary-600" />
                <span className="font-semibold text-surface-900 dark:text-surface-100">Enforce Supabase 2FA</span>
              </div>
              <span className="font-mono text-emerald-600 font-bold">ACTIVE</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-end pt-4">
        <Button
          variant="primary"
          onClick={() => saveSettingMutation.mutate()}
          isLoading={saveSettingMutation.isPending}
          leftIcon={<Save className="w-4 h-4" />}
        >
          Save Platform Settings
        </Button>
      </div>
    </div>
  )
}
