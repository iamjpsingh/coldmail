import { useState } from 'react';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RichTextEditor } from '@/components/ui/rich-text-editor';
import { useCreateTemplate, useTemplateVariables } from '@/hooks/use-templates';
import type { TemplateCategory } from '@/types/template';

interface AddTemplateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const categories: { value: TemplateCategory; label: string }[] = [
  { value: 'outreach', label: 'Cold Outreach' },
  { value: 'followup', label: 'Follow-up' },
  { value: 'nurture', label: 'Nurture' },
  { value: 'promotional', label: 'Promotional' },
  { value: 'transactional', label: 'Transactional' },
  { value: 'other', label: 'Other' },
];

export function AddTemplateDialog({ open, onOpenChange }: AddTemplateDialogProps) {
  const [name, setName] = useState('');
  const [subject, setSubject] = useState('');
  const [contentHtml, setContentHtml] = useState('');
  const [category, setCategory] = useState<TemplateCategory>('outreach');
  const [description, setDescription] = useState('');

  const createMutation = useCreateTemplate();
  const { data: variablesData } = useTemplateVariables();

  // Transform variables for the editor
  const editorVariables = variablesData
    ? Object.entries(variablesData).reduce(
        (acc, [category, vars]) => ({
          ...acc,
          [category]: Object.keys(vars),
        }),
        {} as Record<string, string[]>
      )
    : undefined;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    await createMutation.mutateAsync({
      name,
      subject,
      content_html: contentHtml,
      category,
      description: description || undefined,
    });

    // Reset form
    setName('');
    setSubject('');
    setContentHtml('');
    setCategory('outreach');
    setDescription('');

    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Template</DialogTitle>
          <DialogDescription>
            Create a new email template with variables and spintax support
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Template Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Initial Outreach"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select value={category} onValueChange={(v) => setCategory(v as TemplateCategory)}>
                <SelectTrigger id="category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="subject">Subject Line</Label>
            <Input
              id="subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g., Quick question about {{company}}"
              required
            />
            <p className="text-xs text-muted-foreground">
              Use {'{{variable}}'} for personalization and {'{option1|option2}'} for spintax
            </p>
          </div>

          <div className="space-y-2">
            <Label>Email Content</Label>
            <RichTextEditor
              content={contentHtml}
              onChange={setContentHtml}
              placeholder="Write your email content here..."
              variables={editorVariables}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (optional)</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of when to use this template..."
              rows={2}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!name || !subject || !contentHtml || createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create Template'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
