import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Building2,
  Save,
  Loader2,
  Globe,
  Clock,
  Palette,
  Mail,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useCurrentWorkspace, useUpdateWorkspace } from '@/hooks/use-workspaces';
import type { WorkspaceUpdate } from '@/types/workspaces';

const workspaceSchema = z.object({
  name: z.string().min(1, 'Workspace name is required').max(100),
  description: z.string().max(500).optional(),
  company_name: z.string().max(100).optional(),
  company_website: z.string().url().optional().or(z.literal('')),
  default_timezone: z.string().optional(),
  default_from_name: z.string().max(100).optional(),
  default_reply_to: z.string().email().optional().or(z.literal('')),
  primary_color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid color').optional(),
});

type WorkspaceFormData = z.infer<typeof workspaceSchema>;

const timezones = [
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time (US & Canada)' },
  { value: 'America/Chicago', label: 'Central Time (US & Canada)' },
  { value: 'America/Denver', label: 'Mountain Time (US & Canada)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (US & Canada)' },
  { value: 'Europe/London', label: 'London' },
  { value: 'Europe/Paris', label: 'Paris' },
  { value: 'Europe/Berlin', label: 'Berlin' },
  { value: 'Asia/Tokyo', label: 'Tokyo' },
  { value: 'Asia/Shanghai', label: 'Shanghai' },
  { value: 'Asia/Kolkata', label: 'India Standard Time' },
  { value: 'Australia/Sydney', label: 'Sydney' },
];

export default function WorkspaceSettingsPage() {
  const { toast } = useToast();
  const { data: workspace, isLoading: isLoadingWorkspace } = useCurrentWorkspace();
  const updateWorkspace = useUpdateWorkspace();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isDirty },
  } = useForm<WorkspaceFormData>({
    resolver: zodResolver(workspaceSchema),
    values: workspace ? {
      name: workspace.name,
      description: workspace.description || '',
      company_name: workspace.company_name || '',
      company_website: workspace.company_website || '',
      default_timezone: workspace.default_timezone || 'UTC',
      default_from_name: workspace.default_from_name || '',
      default_reply_to: workspace.default_reply_to || '',
      primary_color: workspace.primary_color || '#3B82F6',
    } : undefined,
  });

  const watchedColor = watch('primary_color');

  const onSubmit = async (data: WorkspaceFormData) => {
    if (!workspace) return;

    try {
      const updateData: WorkspaceUpdate = {
        name: data.name,
        description: data.description || undefined,
        company_name: data.company_name || undefined,
        company_website: data.company_website || undefined,
        default_timezone: data.default_timezone || undefined,
        default_from_name: data.default_from_name || undefined,
        default_reply_to: data.default_reply_to || undefined,
        primary_color: data.primary_color || undefined,
      };

      await updateWorkspace.mutateAsync({ id: workspace.id, data: updateData });
      toast({
        title: 'Settings saved',
        description: 'Your workspace settings have been updated.',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to update workspace settings.',
        variant: 'destructive',
      });
    }
  };

  if (isLoadingWorkspace) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!workspace) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No workspace found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Workspace Settings</h1>
        <p className="text-muted-foreground">
          Manage your workspace details, branding, and default settings.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* General Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              General Information
            </CardTitle>
            <CardDescription>
              Basic information about your workspace
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Workspace Name *</Label>
                <Input
                  id="name"
                  {...register('name')}
                  placeholder="My Workspace"
                />
                {errors.name && (
                  <p className="text-sm text-destructive">{errors.name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="slug">Workspace Slug</Label>
                <Input
                  id="slug"
                  value={workspace.slug}
                  disabled
                  className="bg-muted"
                />
                <p className="text-xs text-muted-foreground">
                  URL-friendly identifier (cannot be changed)
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                {...register('description')}
                placeholder="A brief description of your workspace"
                rows={3}
              />
              {errors.description && (
                <p className="text-sm text-destructive">{errors.description.message}</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Company Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="h-5 w-5" />
              Company Information
            </CardTitle>
            <CardDescription>
              Your company details for branding and compliance
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="company_name">Company Name</Label>
                <Input
                  id="company_name"
                  {...register('company_name')}
                  placeholder="Acme Inc."
                />
                {errors.company_name && (
                  <p className="text-sm text-destructive">{errors.company_name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="company_website">Company Website</Label>
                <Input
                  id="company_website"
                  {...register('company_website')}
                  placeholder="https://example.com"
                  type="url"
                />
                {errors.company_website && (
                  <p className="text-sm text-destructive">{errors.company_website.message}</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Email Defaults */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Email Defaults
            </CardTitle>
            <CardDescription>
              Default settings for outgoing emails
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="default_from_name">Default From Name</Label>
                <Input
                  id="default_from_name"
                  {...register('default_from_name')}
                  placeholder="John from Acme"
                />
                {errors.default_from_name && (
                  <p className="text-sm text-destructive">{errors.default_from_name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="default_reply_to">Default Reply-To</Label>
                <Input
                  id="default_reply_to"
                  {...register('default_reply_to')}
                  placeholder="support@example.com"
                  type="email"
                />
                {errors.default_reply_to && (
                  <p className="text-sm text-destructive">{errors.default_reply_to.message}</p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="default_timezone">Default Timezone</Label>
              <Select
                value={watch('default_timezone') || 'UTC'}
                onValueChange={(value) => setValue('default_timezone', value, { shouldDirty: true })}
              >
                <SelectTrigger>
                  <Clock className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Select timezone" />
                </SelectTrigger>
                <SelectContent>
                  {timezones.map((tz) => (
                    <SelectItem key={tz.value} value={tz.value}>
                      {tz.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Used for scheduling emails and displaying timestamps
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Branding */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
              Branding
            </CardTitle>
            <CardDescription>
              Customize the appearance of your workspace
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="primary_color">Primary Color</Label>
              <div className="flex items-center gap-3">
                <input
                  type="color"
                  id="primary_color"
                  value={watchedColor || '#3B82F6'}
                  onChange={(e) => {
                    setValue('primary_color', e.target.value, { shouldDirty: true });
                  }}
                  className="h-10 w-20 rounded border cursor-pointer"
                />
                <Input
                  value={watchedColor || '#3B82F6'}
                  onChange={(e) => {
                    if (/^#[0-9A-Fa-f]{6}$/.test(e.target.value)) {
                      setValue('primary_color', e.target.value, { shouldDirty: true });
                    }
                  }}
                  placeholder="#3B82F6"
                  className="w-32"
                />
                <div
                  className="h-10 w-10 rounded-full border"
                  style={{ backgroundColor: watchedColor || '#3B82F6' }}
                />
              </div>
              {errors.primary_color && (
                <p className="text-sm text-destructive">{errors.primary_color.message}</p>
              )}
            </div>

            {/* Logo upload placeholder */}
            <div className="space-y-2">
              <Label>Workspace Logo</Label>
              <div className="border-2 border-dashed rounded-lg p-6 text-center">
                {workspace.logo_url ? (
                  <img
                    src={workspace.logo_url}
                    alt="Workspace logo"
                    className="h-16 w-16 mx-auto mb-2 object-contain"
                  />
                ) : (
                  <Building2 className="h-12 w-12 mx-auto mb-2 text-muted-foreground" />
                )}
                <p className="text-sm text-muted-foreground">
                  Logo upload coming soon
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Usage Limits */}
        <Card>
          <CardHeader>
            <CardTitle>Usage Limits</CardTitle>
            <CardDescription>
              Your current plan limits
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="p-4 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">Team Members</p>
                <p className="text-2xl font-bold">
                  {workspace.member_count} / {workspace.max_members}
                </p>
              </div>
              <div className="p-4 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">Contacts</p>
                <p className="text-2xl font-bold">
                  - / {workspace.max_contacts.toLocaleString()}
                </p>
              </div>
              <div className="p-4 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">Emails per Day</p>
                <p className="text-2xl font-bold">
                  - / {workspace.max_emails_per_day.toLocaleString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Submit Button */}
        <div className="flex justify-end">
          <Button
            type="submit"
            disabled={!isDirty || updateWorkspace.isPending}
          >
            {updateWorkspace.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
