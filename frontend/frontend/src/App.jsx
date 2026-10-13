import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth, homePathForRole } from './auth/AuthProvider';
import ProtectedRoute, { PublicRoute } from './auth/ProtectedRoute';
import RoleRoute from './auth/RoleRoute';
import CustomerLayout from './layouts/CustomerLayout';
import AnalystLayout from './layouts/AnalystLayout';

import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import AccessDenied from './pages/auth/AccessDenied';
import NotFound from './pages/auth/NotFound';

import CustomerDashboard from './pages/customer/Dashboard';
import CustomerKYC from './pages/customer/KYC';
import CustomerAccounts from './pages/customer/Accounts';
import CustomerTransactions from './pages/customer/Transactions';
import CustomerRisk from './pages/customer/RiskAssessment';
import CustomerProfile from './pages/customer/Profile';

import AnalystDashboard from './pages/analyst/Dashboard';
import Customers from './pages/analyst/Customers';
import CustomerDetail from './pages/analyst/CustomerDetail';
import Cases from './pages/analyst/Cases';
import CaseDetail from './pages/analyst/CaseDetail';
import Alerts from './pages/analyst/Alerts';
import AlertDetail from './pages/analyst/AlertDetail';
import Assessments from './pages/analyst/Assessments';
import AmlAnalysis from './pages/analyst/AmlAnalysis';
import SARWorkspace from './pages/analyst/SARWorkspace';
import Feedback from './pages/analyst/Feedback';

function RootRedirect() {
  const { status, role } = useAuth();
  if (status !== 'authenticated') return <Navigate to="/login" replace />;
  return <Navigate to={homePathForRole(role)} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />

      {/* Public */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<Login portal="customer" />} />
        <Route path="/register" element={<Register />} />
        <Route path="/analyst/login" element={<Login portal="analyst" />} />
      </Route>

      {/* Authenticated */}
      <Route element={<ProtectedRoute />}>
        <Route path="/access-denied" element={<AccessDenied />} />

        <Route element={<RoleRoute allow={['customer']} />}>
          <Route path="/customer" element={<CustomerLayout />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<CustomerDashboard />} />
            <Route path="kyc" element={<CustomerKYC />} />
            <Route path="accounts" element={<CustomerAccounts />} />
            <Route path="transactions" element={<CustomerTransactions />} />
            <Route path="risk" element={<CustomerRisk />} />
            <Route path="profile" element={<CustomerProfile />} />
          </Route>
        </Route>

        <Route element={<RoleRoute allow={['analyst']} />}>
          <Route path="/analyst" element={<AnalystLayout />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<AnalystDashboard />} />
            <Route path="customers" element={<Customers />} />
            <Route path="customers/:customerId" element={<CustomerDetail />} />
            <Route path="cases" element={<Cases />} />
            <Route path="cases/:caseId" element={<CaseDetail />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="alerts/:alertId" element={<AlertDetail />} />
            <Route path="assessments" element={<Assessments />} />
            <Route path="aml" element={<AmlAnalysis />} />
            <Route path="sar" element={<SARWorkspace />} />
            <Route path="feedback" element={<Feedback />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
