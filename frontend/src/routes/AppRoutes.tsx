import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './ProtectedRoute'

// Layouts
import { AuthLayout } from '@/components/layout/AuthLayout'
import { DashboardLayout } from '@/components/layout/DashboardLayout'

// Auth & Core Pages
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage'
import { OnboardingPage } from '@/pages/onboarding/OnboardingPage'
import { DashboardPage } from '@/pages/dashboard/DashboardPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

// ERP Module Pages
import { CompaniesPage } from '@/pages/erp/CompaniesPage'
import { BranchesPage } from '@/pages/erp/BranchesPage'
import { UsersPage } from '@/pages/erp/UsersPage'
import { CustomersPage } from '@/pages/erp/CustomersPage'
import { SuppliersPage } from '@/pages/erp/SuppliersPage'
import { CategoriesPage } from '@/pages/erp/CategoriesPage'
import { ProductsPage } from '@/pages/erp/ProductsPage'
import { WarehousesPage } from '@/pages/erp/WarehousesPage'
import { InventoryPage } from '@/pages/erp/InventoryPage'
import { StockMovementsPage } from '@/pages/erp/StockMovementsPage'
import { SalesPage } from '@/pages/erp/SalesPage'
import { PurchasesPage } from '@/pages/erp/PurchasesPage'
import { InvoicesPage } from '@/pages/erp/InvoicesPage'
import { PaymentsPage } from '@/pages/erp/PaymentsPage'
import { ExpensesPage } from '@/pages/erp/ExpensesPage'
import { ReportsPage } from '@/pages/erp/ReportsPage'
import { NotificationsPage } from '@/pages/erp/NotificationsPage'
import { SettingsPage } from '@/pages/erp/SettingsPage'

// ML & AI Intelligence Pages
import { MlRevenuePage } from '@/pages/erp/MlRevenuePage'
import { MlSalesPage } from '@/pages/erp/MlSalesPage'
import { MlInventoryPage } from '@/pages/erp/MlInventoryPage'
import { MlProfitPage } from '@/pages/erp/MlProfitPage'
import { MlExpensePage } from '@/pages/erp/MlExpensePage'
import { MlBusinessHealthPage } from '@/pages/erp/MlBusinessHealthPage'
import { MlAnomaliesPage } from '@/pages/erp/MlAnomaliesPage'
import { MlChatPage } from '@/pages/erp/MlChatPage'

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Auth Public Routes */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route
          path="/onboard"
          element={
            <ProtectedRoute requireOnboarding={false}>
              <OnboardingPage />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Protected Dashboard & ERP Module Routes */}
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />

        {/* Platform & Organization */}
        <Route path="/companies" element={<CompaniesPage />} />
        <Route path="/branches" element={<BranchesPage />} />
        <Route path="/users" element={<UsersPage />} />

        {/* Directory */}
        <Route path="/customers" element={<CustomersPage />} />
        <Route path="/suppliers" element={<SuppliersPage />} />

        {/* Inventory & Products */}
        <Route path="/categories" element={<CategoriesPage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/warehouses" element={<WarehousesPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/stock-movements" element={<StockMovementsPage />} />

        {/* Commercial & Financial */}
        <Route path="/sales" element={<SalesPage />} />
        <Route path="/purchases" element={<PurchasesPage />} />
        <Route path="/invoices" element={<InvoicesPage />} />
        <Route path="/payments" element={<PaymentsPage />} />
        <Route path="/expenses" element={<ExpensesPage />} />

        {/* Reports & System */}
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/settings" element={<SettingsPage />} />

        {/* AI & ML Intelligence Suite */}
        <Route path="/ml/revenue" element={<MlRevenuePage />} />
        <Route path="/ml/sales" element={<MlSalesPage />} />
        <Route path="/ml/inventory" element={<MlInventoryPage />} />
        <Route path="/ml/profit" element={<MlProfitPage />} />
        <Route path="/ml/expense" element={<MlExpensePage />} />
        <Route path="/ml/business-health" element={<MlBusinessHealthPage />} />
        <Route path="/ml/anomalies" element={<MlAnomaliesPage />} />
        <Route path="/ml/chat" element={<MlChatPage />} />
      </Route>

      {/* Fallback 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
