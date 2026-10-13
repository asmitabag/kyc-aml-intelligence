import { AlertTriangle, BrainCircuit, ClipboardList, FileText, Gauge, LayoutDashboard, MessageSquareText, Users } from 'lucide-react';
import AppLayout from '../components/layout/AppLayout';

const NAV = [
  { to: '/analyst/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { divider: 'Investigation' },
  { to: '/analyst/customers', label: 'Customers', icon: Users },
  { to: '/analyst/alerts', label: 'Alerts', icon: AlertTriangle },
  { to: '/analyst/cases', label: 'Cases', icon: ClipboardList },
  { divider: 'Analysis' },
  { to: '/analyst/assessments', label: 'Risk assessments', icon: Gauge },
  { to: '/analyst/aml', label: 'AML analysis', icon: BrainCircuit },
  { to: '/analyst/sar', label: 'SAR workspace', icon: FileText },
  { divider: 'Model quality' },
  { to: '/analyst/feedback', label: 'Feedback & datasets', icon: MessageSquareText },
];


export default function AnalystLayout() {
  return <AppLayout nav={NAV} portalLabel="Analyst workspace" showHealth maxWidth="max-w-[90rem]" />;
}
