import { useState } from 'react';
import { Loader2, Send, CheckCircle2, XCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useSendTestEmail } from '@/hooks/use-email-accounts';

interface TestEmailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accountId: string;
  accountEmail: string;
}

export function TestEmailDialog({ open, onOpenChange, accountId, accountEmail }: TestEmailDialogProps) {
  const [toEmail, setToEmail] = useState('');
  const [subject, setSubject] = useState('Test email from ColdMail');
  const [body, setBody] = useState('This is a test email sent from ColdMail to verify your email account configuration.');
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  const sendTestMutation = useSendTestEmail();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setResult(null);

    try {
      const response = await sendTestMutation.mutateAsync({
        id: accountId,
        data: { to_email: toEmail, subject, body },
      });
      setResult({ success: response.success, message: response.message });
    } catch (error: any) {
      setResult({
        success: false,
        message: error?.response?.data?.message || 'Failed to send test email',
      });
    }
  };

  const handleClose = () => {
    setResult(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Send Test Email</DialogTitle>
          <DialogDescription>
            Send a test email from {accountEmail} to verify the account is working correctly.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="to_email">Recipient Email</Label>
            <Input
              id="to_email"
              type="email"
              placeholder="test@example.com"
              value={toEmail}
              onChange={(e) => setToEmail(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="subject">Subject</Label>
            <Input
              id="subject"
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="body">Message</Label>
            <Textarea
              id="body"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={4}
              required
            />
          </div>

          {result && (
            <div
              className={`flex items-center gap-2 p-3 rounded-md ${
                result.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
              }`}
            >
              {result.success ? (
                <CheckCircle2 className="h-5 w-5" />
              ) : (
                <XCircle className="h-5 w-5" />
              )}
              <span className="text-sm">{result.message}</span>
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={sendTestMutation.isPending}>
              {sendTestMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Send Test
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
