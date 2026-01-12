import { useState } from 'react';
import { Plus, Search, FileText, FolderOpen, Loader2, AlertCircle, MoreHorizontal, Copy, Trash2, Eye, RefreshCcw, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StatCard, StatGrid } from '@/components/ui/stat-card';
import { EmptyStateCard } from '@/components/ui/empty-state';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useTemplates, useFolders, useDeleteTemplate, useDuplicateTemplate } from '@/hooks/use-templates';
import { AddTemplateDialog } from './components/add-template-dialog';
import { TemplatePreviewDialog } from './components/template-preview-dialog';
import type { EmailTemplateListItem, TemplateCategory } from '@/types/template';

const categoryLabels: Record<TemplateCategory, string> = {
  outreach: 'Cold Outreach',
  followup: 'Follow-up',
  nurture: 'Nurture',
  promotional: 'Promotional',
  transactional: 'Transactional',
  other: 'Other',
};

const categoryColors: Record<TemplateCategory, string> = {
  outreach: 'bg-blue-100 text-blue-800',
  followup: 'bg-green-100 text-green-800',
  nurture: 'bg-purple-100 text-purple-800',
  promotional: 'bg-orange-100 text-orange-800',
  transactional: 'bg-gray-100 text-gray-800',
  other: 'bg-slate-100 text-slate-800',
};

export default function TemplatesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [previewTemplate, setPreviewTemplate] = useState<string | null>(null);

  const { data: templates, isLoading, error, refetch, isRefetching } = useTemplates({
    category: selectedCategory !== 'all' ? selectedCategory : undefined,
    search: searchQuery || undefined,
  });
  const { data: folders } = useFolders('root');
  const deleteMutation = useDeleteTemplate();
  const duplicateMutation = useDuplicateTemplate();

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this template?')) return;
    await deleteMutation.mutateAsync(id);
  };

  const handleDuplicate = async (template: EmailTemplateListItem) => {
    const name = window.prompt('Enter name for the duplicate:', `${template.name} (Copy)`);
    if (!name) return;
    await duplicateMutation.mutateAsync({ id: template.id, name });
  };

  const getCategoryCounts = () => {
    if (!templates) return {};
    const counts: Record<string, number> = { all: templates.length };
    for (const template of templates) {
      counts[template.category] = (counts[template.category] || 0) + 1;
    }
    return counts;
  };

  const counts = getCategoryCounts();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Templates</h1>
            <p className="text-muted-foreground">Create and manage your email templates</p>
          </div>
        </div>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Templates</h1>
            <p className="text-muted-foreground">Create and manage your email templates</p>
          </div>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="rounded-full bg-destructive/10 p-4 mb-4">
              <AlertCircle className="h-8 w-8 text-destructive" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Unable to Load Templates</h3>
            <p className="text-muted-foreground text-center max-w-md mb-6">
              We couldn't fetch your templates. Please check your connection and try again.
            </p>
            <Button onClick={() => refetch()} disabled={isRefetching}>
              {isRefetching ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCcw className="h-4 w-4 mr-2" />
              )}
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Templates</h1>
          <p className="text-muted-foreground">
            Create and manage your email templates
          </p>
        </div>
        <Button onClick={() => setIsAddDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Template
        </Button>
      </div>

      {/* Stats Cards */}
      <StatGrid columns={4}>
        <StatCard
          label="Total Templates"
          value={templates?.length || 0}
          icon={FileText}
          variant="primary"
        />
        <StatCard
          label="Folders"
          value={folders?.length || 0}
          icon={FolderOpen}
        />
        <StatCard
          label="With Spintax"
          value={templates?.filter((t) => t.has_spintax).length || 0}
          icon={Sparkles}
        />
        <StatCard
          label="Total Uses"
          value={templates?.reduce((acc, t) => acc + t.times_used, 0) || 0}
          icon={FileText}
          variant="success"
        />
      </StatGrid>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Category Tabs */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList>
          <TabsTrigger value="all">
            All ({counts.all || 0})
          </TabsTrigger>
          {Object.entries(categoryLabels).map(([key, label]) => (
            <TabsTrigger key={key} value={key}>
              {label} ({counts[key] || 0})
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={selectedCategory} className="mt-4">
          {templates && templates.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {templates.map((template) => (
                <Card key={template.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <CardTitle className="text-lg">{template.name}</CardTitle>
                        <CardDescription className="line-clamp-1">
                          {template.subject}
                        </CardDescription>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => setPreviewTemplate(template.id)}>
                            <Eye className="h-4 w-4 mr-2" />
                            Preview
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDuplicate(template)}>
                            <Copy className="h-4 w-4 mr-2" />
                            Duplicate
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleDelete(template.id)}
                            className="text-destructive"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      <Badge className={categoryColors[template.category]}>
                        {categoryLabels[template.category]}
                      </Badge>
                      {template.has_spintax && (
                        <Badge variant="outline">Spintax</Badge>
                      )}
                      {template.is_shared && (
                        <Badge variant="secondary">Shared</Badge>
                      )}
                    </div>
                    <div className="mt-4 text-sm text-muted-foreground">
                      Used {template.times_used} times
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyStateCard
              icon={FileText}
              title="No templates yet"
              description="Create your first email template to get started with your campaigns."
              action={
                <Button onClick={() => setIsAddDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Template
                </Button>
              }
            />
          )}
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <AddTemplateDialog
        open={isAddDialogOpen}
        onOpenChange={setIsAddDialogOpen}
      />
      {previewTemplate && (
        <TemplatePreviewDialog
          templateId={previewTemplate}
          open={!!previewTemplate}
          onOpenChange={(open) => !open && setPreviewTemplate(null)}
        />
      )}
    </div>
  );
}
