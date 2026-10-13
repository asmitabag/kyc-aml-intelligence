import { CreditCard, FileCheck2, Gauge, LayoutDashboard, ReceiptText, UserRound } from 'lucide-react';
import AppLayout from '../components/layout/AppLayout';

// Customers only ever see these links. No analyst navigation exists here.
const NAV = [
  { to: '/customer/dashboard', label: 'Overview', icon: LayoutDashboard },
  { to: '/customer/kyc', label: 'Identity verification', icon: FileCheck2 },
  { to: '/customer/accounts', label: 'My accounts', icon: CreditCard },
  { to: '/customer/transactions', label: 'My transactions', icon: ReceiptText },
  { to: '/customer/risk', label: 'Risk assessment', icon: Gauge },
  { to: '/customer/profile', label: 'Profile', icon: UserRound },
];

export default function CustomerLayout() {
  return <AppLayout nav={NAV} portalLabel="Customer portal" maxWidth="max-w-5xl" />;
}
