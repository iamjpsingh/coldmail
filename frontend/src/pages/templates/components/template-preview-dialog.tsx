import { useState, useEffect } from 'react';
import { RefreshCw, Mail, FileText, Variable, Shuffle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useTemplate, usePreviewTemplate } from '@/hooks/use-templates';

interface TemplatePreviewDialogProps {
  templateId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TemplatePreviewDialog({
  templateId,
  open,
  onOpenChange,
}: TemplatePreviewDialogProps) {
  const { data: template, isLoading } = useTemplate(templateId);
  const previewMutation = usePreviewTemplate();
  const [previewKey, setPreviewKey] = useState(0);

  useEffect(() => {
    if (template && open) {
      previewMutation.mutate({
        subject: template.subject,
        content_html: template.content_html,
        content_text: template.content_text,
      });
    }
  }, [template, open, previewKey]);

  const handleRefreshPreview = () => {
    setPreviewKey((k) => k + 1);
  };

  if (isLoading || !template) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl">
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  const preview = previewMutation.data;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle>{template.name}</DialogTitle>
              <DialogDescription>{template.description || 'No description'}</DialogDescription>
            </div>
            {template.has_spintax && (
              <Button variant="outline" size="sm" onClick={handleRefreshPreview}>
                <Shuffle className="h-4 w-4 mr-2" />
                Shuffle Spintax
              </Button>
            )}
          </div>
        </DialogHeader>

        <div className="space-y-4">
          {/* Template info */}
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">{template.category}</Badge>
            {template.has_spintax && (
              <Badge variant="outline">
                {preview?.spintax_variations || 0} variations
              </Badge>
            )}
            <Badge variant="outline">
              <Variable className="h-3 w-3 mr-1" />
              {template.variables.length} variables
            </Badge>
          </div>

          {/* Subject */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Mail className="h-4 w-4" />
                Subject
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-medium">{preview?.subject || template.subject}</p>
            </CardContent>
          </Card>

          {/* Content Preview */}
          <Tabs defaultValue="html">
            <TabsList>
              <TabsTrigger value="html">
                <FileText className="h-4 w-4 mr-2" />
                HTML Preview
              </TabsTrigger>
              <TabsTrigger value="text">
                <FileText className="h-4 w-4 mr-2" />
                Plain Text
              </TabsTrigger>
              <TabsTrigger value="source">
                <FileText className="h-4 w-4 mr-2" />
                Source
              </TabsTrigger>
            </TabsList>

            <TabsContent value="html" className="mt-4">
              <Card>
                <CardContent className="pt-6">
                  <div
                    className="prose prose-sm max-w-none"
                    dangerouslySetInnerHTML={{
                      __html: preview?.content_html || template.content_html,
                    }}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="text" className="mt-4">
              <Card>
                <CardContent className="pt-6">
                  <pre className="whitespace-pre-wrap text-sm font-mono bg-muted p-4 rounded-lg">
                    {preview?.content_text || template.content_text}
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="source" className="mt-4">
              <Card>
                <CardContent className="pt-6">
                  <pre className="whitespace-pre-wrap text-sm font-mono bg-muted p-4 rounded-lg overflow-x-auto">
                    {template.content_html}
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Variables used */}
          {template.variables.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Variables Used</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {template.variables.map((variable) => (
                    <Badge key={variable} variant="outline">
                      {`{{${variable}}}`}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Missing variables warning */}
          {preview?.missing_variables && preview.missing_variables.length > 0 && (
            <Card className="border-yellow-500">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-yellow-600">
                  Missing Variables (will show as placeholders)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {preview.missing_variables.map((variable) => (
                    <Badge key={variable} variant="outline" className="border-yellow-500 text-yellow-600">
                      {`{{${variable}}}`}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
