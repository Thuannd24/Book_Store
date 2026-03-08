import { Routes, Route, Navigate } from 'react-router-dom'

// Layouts
import { CustomerLayout } from './components/layout/CustomerLayout'
import { StaffLayout } from './components/layout/StaffLayout'
import { ManagerLayout } from './components/layout/ManagerLayout'

// Guards
import { RequireCustomer, RequireStaff, RequireManager } from './utils/guards'

// Customer pages
import HomePage from './pages/customer/HomePage'
import RegisterPage from './pages/customer/RegisterPage'
import LoginPage from './pages/customer/LoginPage'
import BookListPage from './pages/customer/BookListPage'
import BookDetailPage from './pages/customer/BookDetailPage'
import CartPage from './pages/customer/CartPage'
import CheckoutPage from './pages/customer/CheckoutPage'
import OrderHistoryPage from './pages/customer/OrderHistoryPage'
import ReviewPage from './pages/customer/ReviewPage'
import RecommendationPage from './pages/customer/RecommendationPage'
import ProfilePage from './pages/customer/ProfilePage'

// Staff pages
import StaffLoginPage from './pages/staff/StaffLoginPage'
import BookManagementPage from './pages/staff/BookManagementPage'
import CategoryManagementPage from './pages/staff/CategoryManagementPage'
import OrderManagementPage from './pages/staff/OrderManagementPage'

// Manager pages
import ManagerLoginPage from './pages/manager/ManagerLoginPage'
import DashboardPage from './pages/manager/DashboardPage'
import CustomerListPage from './pages/manager/CustomerListPage'

export default function App() {
  return (
    <Routes>
      {/* Customer Routes */}
      <Route element={<CustomerLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/books" element={<BookListPage />} />
        <Route path="/books/:id" element={<BookDetailPage />} />
        <Route path="/cart" element={<RequireCustomer><CartPage /></RequireCustomer>} />
        <Route path="/checkout" element={<RequireCustomer><CheckoutPage /></RequireCustomer>} />
        <Route path="/orders" element={<RequireCustomer><OrderHistoryPage /></RequireCustomer>} />
        <Route path="/orders/:id" element={<RequireCustomer><OrderHistoryPage /></RequireCustomer>} />
        <Route path="/reviews" element={<RequireCustomer><ReviewPage /></RequireCustomer>} />
        <Route path="/recommendations" element={<RequireCustomer><RecommendationPage /></RequireCustomer>} />
        <Route path="/profile" element={<RequireCustomer><ProfilePage /></RequireCustomer>} />
      </Route>

      {/* Staff Routes */}
      <Route path="/staff/login" element={<StaffLoginPage />} />
      <Route path="/staff" element={<RequireStaff><StaffLayout /></RequireStaff>}>
        <Route index element={<Navigate to="/staff/books" replace />} />
        <Route path="books" element={<BookManagementPage />} />
        <Route path="categories" element={<CategoryManagementPage />} />
        <Route path="orders" element={<OrderManagementPage />} />
      </Route>

      {/* Manager Routes */}
      <Route path="/manager/login" element={<ManagerLoginPage />} />
      <Route path="/manager" element={<RequireManager><ManagerLayout /></RequireManager>}>
        <Route index element={<Navigate to="/manager/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="customers" element={<CustomerListPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
