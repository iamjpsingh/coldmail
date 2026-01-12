import { Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './components/layout/dashboard-layout';
import { Toaster } from './components/ui/toaster';
import DashboardPage from './pages/dashboard';
import EmailAccountsPage from './pages/email-accounts';
import ContactsPage from './pages/contacts';
import ScoringSettingsPage from './pages/settings/scoring';
import APIKeysPage from './pages/settings/api-keys';
import WebhooksPage from './pages/settings/webhooks';
import IntegrationsPage from './pages/settings/integrations';
import TeamSettingsPage from './pages/settings/team';
import WorkspaceSettingsPage from './pages/settings/workspace';
import TemplatesPage from './pages/templates';
import CampaignsPage from './pages/campaigns';
import SequencesPage from './pages/sequences';
import AnalyticsPage from './pages/analytics';
import ReportsPage from './pages/reports';
import VisitorsPage from './pages/visitors';

function App() {
  return (
    <>
      <Routes>
        {/* Dashboard routes */}
        <Route path="/" element={<DashboardLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="campaigns" element={<CampaignsPage />} />
        <Route path="email-accounts" element={<EmailAccountsPage />} />
        <Route path="contacts" element={<ContactsPage />} />
        <Route path="templates" element={<TemplatesPage />} />
        <Route path="sequences" element={<SequencesPage />} />
        <Route path="visitors" element={<VisitorsPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="settings/scoring" element={<ScoringSettingsPage />} />
        <Route path="settings/api-keys" element={<APIKeysPage />} />
        <Route path="settings/webhooks" element={<WebhooksPage />} />
        <Route path="settings/integrations" element={<IntegrationsPage />} />
        <Route path="settings/team" element={<TeamSettingsPage />} />
        <Route path="settings/workspace" element={<WorkspaceSettingsPage />} />
        {/* More routes will be added here */}
        </Route>
      </Routes>
      <Toaster />
    </>
  );
}

export default App;
