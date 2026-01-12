import { useState } from 'react';
import { Loader2, User } from 'lucide-react';
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
import { useCreateContact } from '@/hooks/use-contacts';
import type { ContactCreate } from '@/types/contact';

interface AddContactDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddContactDialog({ open, onOpenChange }: AddContactDialogProps) {
  const [formData, setFormData] = useState<ContactCreate>({
    email: '',
    first_name: '',
    last_name: '',
    company: '',
    job_title: '',
    phone: '',
    website: '',
    linkedin_url: '',
    city: '',
    country: '',
    notes: '',
  });
  const [error, setError] = useState<string | null>(null);

  const createMutation = useCreateContact();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      await createMutation.mutateAsync(formData);
      onOpenChange(false);
      setFormData({
        email: '',
        first_name: '',
        last_name: '',
        company: '',
        job_title: '',
        phone: '',
        website: '',
        linkedin_url: '',
        city: '',
        country: '',
        notes: '',
      });
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Failed to create contact');
    }
  };

  const updateField = (field: keyof ContactCreate, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Add Contact
          </DialogTitle>
          <DialogDescription>
            Add a new contact to your database. Required fields are marked with *.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email */}
          <div className="space-y-2">
            <Label htmlFor="email">Email *</Label>
            <Input
              id="email"
              type="email"
              placeholder="john@example.com"
              value={formData.email}
              onChange={(e) => updateField('email', e.target.value)}
              required
            />
          </div>

          {/* Name */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="first_name">First Name</Label>
              <Input
                id="first_name"
                placeholder="John"
                value={formData.first_name}
                onChange={(e) => updateField('first_name', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="last_name">Last Name</Label>
              <Input
                id="last_name"
                placeholder="Doe"
                value={formData.last_name}
                onChange={(e) => updateField('last_name', e.target.value)}
              />
            </div>
          </div>

          {/* Company Info */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="company">Company</Label>
              <Input
                id="company"
                placeholder="Acme Inc."
                value={formData.company}
                onChange={(e) => updateField('company', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="job_title">Job Title</Label>
              <Input
                id="job_title"
                placeholder="Software Engineer"
                value={formData.job_title}
                onChange={(e) => updateField('job_title', e.target.value)}
              />
            </div>
          </div>

          {/* Contact Info */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                placeholder="+1 234 567 8900"
                value={formData.phone}
                onChange={(e) => updateField('phone', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="website">Website</Label>
              <Input
                id="website"
                type="url"
                placeholder="https://example.com"
                value={formData.website}
                onChange={(e) => updateField('website', e.target.value)}
              />
            </div>
          </div>

          {/* Social */}
          <div className="space-y-2">
            <Label htmlFor="linkedin_url">LinkedIn URL</Label>
            <Input
              id="linkedin_url"
              type="url"
              placeholder="https://linkedin.com/in/johndoe"
              value={formData.linkedin_url}
              onChange={(e) => updateField('linkedin_url', e.target.value)}
            />
          </div>

          {/* Location */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="city">City</Label>
              <Input
                id="city"
                placeholder="San Francisco"
                value={formData.city}
                onChange={(e) => updateField('city', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="country">Country</Label>
              <Input
                id="country"
                placeholder="United States"
                value={formData.country}
                onChange={(e) => updateField('country', e.target.value)}
              />
            </div>
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              placeholder="Additional notes about this contact..."
              value={formData.notes}
              onChange={(e) => updateField('notes', e.target.value)}
              rows={3}
            />
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <DialogFooter>
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
                'Add Contact'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
