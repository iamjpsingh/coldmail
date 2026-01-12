import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  Mail,
  Users,
  Send,
  GitBranch,
  Settings,
  Menu,
  X,
  FileText,
  LayoutDashboard,
  FileBarChart,
  Activity,
  Eye,
  Key,
  Webhook,
  Plug,
  Target,
  ChevronDown,
  UsersRound,
  Building2,
  Bell,
  Search,
  LogOut,
  User,
  HelpCircle,
  Zap,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Campaigns', href: '/campaigns', icon: Send },
  { name: 'Contacts', href: '/contacts', icon: Users },
  { name: 'Templates', href: '/templates', icon: FileText },
  { name: 'Email Accounts', href: '/email-accounts', icon: Mail },
  { name: 'Sequences', href: '/sequences', icon: GitBranch },
  { name: 'Visitors', href: '/visitors', icon: Eye },
  { name: 'Analytics', href: '/analytics', icon: Activity },
  { name: 'Reports', href: '/reports', icon: FileBarChart },
];

const settingsNavigation = [
  { name: 'Team', href: '/settings/team', icon: UsersRound },
  { name: 'Workspace', href: '/settings/workspace', icon: Building2 },
  { name: 'Lead Scoring', href: '/settings/scoring', icon: Target },
  { name: 'Integrations', href: '/settings/integrations', icon: Plug },
  { name: 'Webhooks', href: '/settings/webhooks', icon: Webhook },
  { name: 'API Keys', href: '/settings/api-keys', icon: Key },
];

export function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsExpanded, setSettingsExpanded] = useState(false);
  const location = useLocation();
  const isSettingsActive = location.pathname.startsWith('/settings');

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-sidebar text-sidebar-foreground transform transition-transform lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between px-5 border-b border-sidebar-border">
          <Link to="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
              <Mail className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold tracking-tight">ColdMail</span>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden text-sidebar-foreground hover:bg-sidebar-accent"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 scrollbar-thin">
          <div className="space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href ||
                (item.href !== '/dashboard' && location.pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-sidebar-muted hover:bg-sidebar-accent hover:text-sidebar-foreground'
                  )}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {item.name}
                </Link>
              );
            })}
          </div>

          {/* Settings Section */}
          <div className="mt-6 pt-6 border-t border-sidebar-border">
            <button
              onClick={() => setSettingsExpanded(!settingsExpanded)}
              className={cn(
                'flex items-center justify-between w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isSettingsActive
                  ? 'bg-sidebar-accent text-sidebar-foreground'
                  : 'text-sidebar-muted hover:bg-sidebar-accent hover:text-sidebar-foreground'
              )}
            >
              <div className="flex items-center gap-3">
                <Settings className="h-5 w-5" />
                Settings
              </div>
              <ChevronDown
                className={cn(
                  'h-4 w-4 transition-transform',
                  (settingsExpanded || isSettingsActive) && 'rotate-180'
                )}
              />
            </button>

            {(settingsExpanded || isSettingsActive) && (
              <div className="mt-1 ml-3 pl-3 border-l border-sidebar-border space-y-1">
                {settingsNavigation.map((item) => {
                  const isActive = location.pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-sidebar-muted hover:bg-sidebar-accent hover:text-sidebar-foreground'
                      )}
                    >
                      <item.icon className="h-4 w-4" />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </nav>

        {/* Sidebar Footer */}
        <div className="p-3 border-t border-sidebar-border">
          <div className="rounded-lg bg-sidebar-accent p-3">
            <div className="flex items-center gap-2 text-sm">
              <Zap className="h-4 w-4 text-primary" />
              <span className="font-medium">Pro Plan</span>
            </div>
            <p className="mt-1 text-xs text-sidebar-muted">
              10,000 emails/month
            </p>
            <div className="mt-2 h-1.5 rounded-full bg-sidebar-border overflow-hidden">
              <div className="h-full w-3/4 rounded-full bg-primary" />
            </div>
            <p className="mt-1 text-xs text-sidebar-muted">7,500 / 10,000 used</p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64 min-h-screen flex flex-col">
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-card/80 backdrop-blur-md px-4 lg:px-6">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>

          {/* Search */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search contacts, campaigns..."
                className="pl-9 bg-muted/50 border-0 focus-visible:ring-1"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Notifications */}
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-primary text-[10px] font-medium text-primary-foreground flex items-center justify-center">
                3
              </span>
            </Button>

            {/* Help */}
            <Button variant="ghost" size="icon">
              <HelpCircle className="h-5 w-5" />
            </Button>

            {/* User menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="gap-2 pl-2 pr-3">
                  <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center text-primary-foreground text-sm font-semibold">
                    JD
                  </div>
                  <div className="hidden md:block text-left">
                    <p className="text-sm font-medium">John Doe</p>
                    <p className="text-xs text-muted-foreground">Admin</p>
                  </div>
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive">
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-6">
          <Outlet />
        </main>

        {/* Footer */}
        <footer className="border-t py-4 px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-2 text-sm text-muted-foreground">
            <p>ColdMail - Open Source Cold Email Platform</p>
            <div className="flex items-center gap-4">
              <a href="#" className="hover:text-foreground transition-colors">Documentation</a>
              <a href="#" className="hover:text-foreground transition-colors">Support</a>
              <a href="#" className="hover:text-foreground transition-colors">GitHub</a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
