import { useState } from 'react';
import { Loader2, Mail, Shield } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useCreateEmailAccount } from '@/hooks/use-email-accounts';
import { emailAccountsApi } from '@/api/email-accounts';
import type { EmailAccountCreate } from '@/types/email-account';

interface AddEmailAccountDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const GoogleIcon = () => (
  <svg className="h-5 w-5" viewBox="0 0 24 24">
    <path
      fill="currentColor"
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
    />
    <path
      fill="currentColor"
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
    />
    <path
      fill="currentColor"
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
    />
    <path
      fill="currentColor"
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
    />
  </svg>
);

const MicrosoftIcon = () => (
  <svg className="h-5 w-5" viewBox="0 0 24 24">
    <path fill="#f25022" d="M1 1h10v10H1z" />
    <path fill="#00a4ef" d="M1 13h10v10H1z" />
    <path fill="#7fba00" d="M13 1h10v10H13z" />
    <path fill="#ffb900" d="M13 13h10v10H13z" />
  </svg>
);

export function AddEmailAccountDialog({ open, onOpenChange }: AddEmailAccountDialogProps) {
  const [isLoadingOAuth, setIsLoadingOAuth] = useState<'google' | 'microsoft' | null>(null);
  const [smtpForm, setSmtpForm] = useState<EmailAccountCreate>({
    name: '',
    email: '',
    provider: 'smtp',
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    smtp_use_tls: true,
    smtp_use_ssl: false,
    from_name: '',
    daily_limit: 100,
    hourly_limit: 20,
  });
  const [error, setError] = useState<string | null>(null);

  const createMutation = useCreateEmailAccount();

  const handleGoogleOAuth = async () => {
    setIsLoadingOAuth('google');
    setError(null);
    try {
      const { authorization_url } = await emailAccountsApi.getGoogleAuthUrl();
      window.location.href = authorization_url;
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Failed to initiate Google OAuth');
      setIsLoadingOAuth(null);
    }
  };

  const handleMicrosoftOAuth = async () => {
    setIsLoadingOAuth('microsoft');
    setError(null);
    try {
      const { authorization_url } = await emailAccountsApi.getMicrosoftAuthUrl();
      window.location.href = authorization_url;
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Failed to initiate Microsoft OAuth');
      setIsLoadingOAuth(null);
    }
  };

  const handleSmtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      await createMutation.mutateAsync(smtpForm);
      onOpenChange(false);
      // Reset form
      setSmtpForm({
        name: '',
        email: '',
        provider: 'smtp',
        smtp_host: '',
        smtp_port: 587,
        smtp_username: '',
        smtp_password: '',
        smtp_use_tls: true,
        smtp_use_ssl: false,
        from_name: '',
        daily_limit: 100,
        hourly_limit: 20,
      });
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Failed to create email account');
    }
  };

  const updateSmtpForm = (field: keyof EmailAccountCreate, value: string | number | boolean) => {
    setSmtpForm((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add Email Account</DialogTitle>
          <DialogDescription>
            Connect an email account to send campaigns. Choose OAuth for easy setup or SMTP for custom configuration.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="oauth" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="oauth">
              <Shield className="h-4 w-4 mr-2" />
              OAuth
            </TabsTrigger>
            <TabsTrigger value="smtp">
              <Mail className="h-4 w-4 mr-2" />
              SMTP
            </TabsTrigger>
          </TabsList>

          {/* OAuth Tab */}
          <TabsContent value="oauth" className="space-y-4 pt-4">
            <p className="text-sm text-muted-foreground">
              Connect your email provider securely with OAuth. No passwords stored.
            </p>

            <div className="space-y-3">
              <Button
                variant="outline"
                className="w-full justify-start h-12"
                onClick={handleGoogleOAuth}
                disabled={isLoadingOAuth !== null}
              >
                {isLoadingOAuth === 'google' ? (
                  <Loader2 className="h-5 w-5 mr-3 animate-spin" />
                ) : (
                  <GoogleIcon />
                )}
                <span className="ml-3">Connect with Google (Gmail)</span>
              </Button>

              <Button
                variant="outline"
                className="w-full justify-start h-12"
                onClick={handleMicrosoftOAuth}
                disabled={isLoadingOAuth !== null}
              >
                {isLoadingOAuth === 'microsoft' ? (
                  <Loader2 className="h-5 w-5 mr-3 animate-spin" />
                ) : (
                  <MicrosoftIcon />
                )}
                <span className="ml-3">Connect with Microsoft (Outlook)</span>
              </Button>
            </div>

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </TabsContent>

          {/* SMTP Tab */}
          <TabsContent value="smtp" className="space-y-4 pt-4">
            <form onSubmit={handleSmtpSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Account Name</Label>
                  <Input
                    id="name"
                    placeholder="My Email"
                    value={smtpForm.name}
                    onChange={(e) => updateSmtpForm('name', e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={smtpForm.email}
                    onChange={(e) => updateSmtpForm('email', e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="smtp_host">SMTP Host</Label>
                  <Input
                    id="smtp_host"
                    placeholder="smtp.example.com"
                    value={smtpForm.smtp_host}
                    onChange={(e) => updateSmtpForm('smtp_host', e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp_port">SMTP Port</Label>
                  <Input
                    id="smtp_port"
                    type="number"
                    placeholder="587"
                    value={smtpForm.smtp_port}
                    onChange={(e) => updateSmtpForm('smtp_port', parseInt(e.target.value))}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="smtp_username">SMTP Username</Label>
                  <Input
                    id="smtp_username"
                    placeholder="username"
                    value={smtpForm.smtp_username}
                    onChange={(e) => updateSmtpForm('smtp_username', e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp_password">SMTP Password</Label>
                  <Input
                    id="smtp_password"
                    type="password"
                    placeholder="password"
                    value={smtpForm.smtp_password}
                    onChange={(e) => updateSmtpForm('smtp_password', e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="from_name">From Name (optional)</Label>
                <Input
                  id="from_name"
                  placeholder="John Doe"
                  value={smtpForm.from_name}
                  onChange={(e) => updateSmtpForm('from_name', e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="daily_limit">Daily Limit</Label>
                  <Input
                    id="daily_limit"
                    type="number"
                    value={smtpForm.daily_limit}
                    onChange={(e) => updateSmtpForm('daily_limit', parseInt(e.target.value))}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="hourly_limit">Hourly Limit</Label>
                  <Input
                    id="hourly_limit"
                    type="number"
                    value={smtpForm.hourly_limit}
                    onChange={(e) => updateSmtpForm('hourly_limit', parseInt(e.target.value))}
                    required
                  />
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={smtpForm.smtp_use_tls}
                    onChange={(e) => updateSmtpForm('smtp_use_tls', e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">Use TLS</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={smtpForm.smtp_use_ssl}
                    onChange={(e) => updateSmtpForm('smtp_use_ssl', e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">Use SSL</span>
                </label>
              </div>

              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}

              <div className="flex justify-end space-x-2 pt-4">
                <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    'Add Account'
                  )}
                </Button>
              </div>
            </form>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
