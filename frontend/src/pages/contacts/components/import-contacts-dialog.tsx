import { useState, useCallback } from 'react';
import { Upload, FileSpreadsheet, Loader2, CheckCircle2, XCircle, ArrowRight } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { useUploadImport, useStartImport, useImportJob } from '@/hooks/use-contacts';

interface ImportContactsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type Step = 'upload' | 'mapping' | 'progress' | 'complete';

const CONTACT_FIELDS = [
  { key: 'email', label: 'Email', required: true },
  { key: 'first_name', label: 'First Name' },
  { key: 'last_name', label: 'Last Name' },
  { key: 'company', label: 'Company' },
  { key: 'job_title', label: 'Job Title' },
  { key: 'phone', label: 'Phone' },
  { key: 'website', label: 'Website' },
  { key: 'linkedin_url', label: 'LinkedIn URL' },
  { key: 'city', label: 'City' },
  { key: 'state', label: 'State' },
  { key: 'country', label: 'Country' },
  { key: 'source', label: 'Source' },
  { key: 'notes', label: 'Notes' },
];

export function ImportContactsDialog({ open, onOpenChange }: ImportContactsDialogProps) {
  const [step, setStep] = useState<Step>('upload');
  const [importJobId, setImportJobId] = useState<string | null>(null);
  const [preview, setPreview] = useState<{
    headers: string[];
    rows: Record<string, unknown>[];
  } | null>(null);
  const [fieldMapping, setFieldMapping] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const uploadMutation = useUploadImport();
  const startMutation = useStartImport();
  const { data: importJob } = useImportJob(importJobId || '');

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    try {
      const result = await uploadMutation.mutateAsync(file);
      setImportJobId(result.import_job_id);
      setPreview(result.preview);

      // Auto-map fields based on header names
      const autoMapping: Record<string, string> = {};
      const headers = result.preview.headers || [];
      for (const field of CONTACT_FIELDS) {
        const matchingHeader = headers.find(
          (h: string) => h.toLowerCase().replace(/[^a-z]/g, '') === field.key.replace(/_/g, '')
        );
        if (matchingHeader) {
          autoMapping[field.key] = matchingHeader;
        }
      }
      setFieldMapping(autoMapping);
      setStep('mapping');
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to upload file');
    }
  }, [uploadMutation]);

  const handleStartImport = async () => {
    if (!importJobId || !fieldMapping.email) {
      setError('Email field mapping is required');
      return;
    }

    try {
      await startMutation.mutateAsync({ id: importJobId, fieldMapping });
      setStep('progress');
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to start import');
    }
  };

  const handleClose = () => {
    setStep('upload');
    setImportJobId(null);
    setPreview(null);
    setFieldMapping({});
    setError(null);
    onOpenChange(false);
  };

  // Check if import is complete
  if (step === 'progress' && importJob?.status === 'completed') {
    setStep('complete');
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5" />
            Import Contacts
          </DialogTitle>
          <DialogDescription>
            Upload a CSV, Excel, or JSON file to import contacts.
          </DialogDescription>
        </DialogHeader>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 py-4">
          {['upload', 'mapping', 'progress', 'complete'].map((s, i) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                  step === s
                    ? 'bg-primary text-primary-foreground'
                    : ['upload', 'mapping', 'progress', 'complete'].indexOf(step) > i
                    ? 'bg-green-500 text-white'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {['upload', 'mapping', 'progress', 'complete'].indexOf(step) > i ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : (
                  i + 1
                )}
              </div>
              {i < 3 && <ArrowRight className="h-4 w-4 mx-2 text-muted-foreground" />}
            </div>
          ))}
        </div>

        {/* Upload Step */}
        {step === 'upload' && (
          <div className="space-y-4">
            <div
              className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary transition-colors cursor-pointer"
              onClick={() => document.getElementById('file-upload')?.click()}
            >
              <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-lg font-medium">Drop your file here or click to browse</p>
              <p className="text-sm text-muted-foreground mt-2">
                Supports CSV, Excel (.xlsx), and JSON files
              </p>
              <input
                id="file-upload"
                type="file"
                accept=".csv,.xlsx,.xls,.json"
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>

            {uploadMutation.isPending && (
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Uploading...</span>
              </div>
            )}
          </div>
        )}

        {/* Mapping Step */}
        {step === 'mapping' && preview && (
          <div className="space-y-4">
            <div className="text-sm text-muted-foreground">
              Map your file columns to contact fields. Email is required.
            </div>

            <div className="max-h-[400px] overflow-y-auto space-y-3">
              {CONTACT_FIELDS.map((field) => (
                <div key={field.key} className="flex items-center gap-4">
                  <Label className="w-32 text-sm">
                    {field.label}
                    {field.required && <span className="text-destructive ml-1">*</span>}
                  </Label>
                  <select
                    className="flex-1 h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                    value={fieldMapping[field.key] || ''}
                    onChange={(e) =>
                      setFieldMapping((prev) => ({ ...prev, [field.key]: e.target.value }))
                    }
                  >
                    <option value="">-- Select column --</option>
                    {preview.headers.map((header) => (
                      <option key={header} value={header}>
                        {header}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            {/* Preview */}
            {preview.rows.length > 0 && (
              <div className="border rounded-md p-4 bg-muted/50">
                <p className="text-sm font-medium mb-2">Preview (first {preview.rows.length} rows)</p>
                <div className="text-xs text-muted-foreground overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr>
                        {preview.headers.map((h) => (
                          <th key={h} className="text-left p-1 border-b">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {preview.rows.slice(0, 3).map((row, i) => (
                        <tr key={i}>
                          {preview.headers.map((h) => (
                            <td key={h} className="p-1 border-b truncate max-w-[150px]">
                              {String(row[h] || '')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Progress Step */}
        {step === 'progress' && importJob && (
          <div className="space-y-4 py-8">
            <div className="text-center">
              <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
              <p className="text-lg font-medium">Importing contacts...</p>
              <p className="text-sm text-muted-foreground mt-2">
                {importJob.processed_rows} of {importJob.total_rows} rows processed
              </p>
            </div>

            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${importJob.progress_percentage}%` }}
              />
            </div>

            <div className="grid grid-cols-4 gap-4 text-center text-sm">
              <div>
                <div className="font-medium text-green-600">{importJob.created_count}</div>
                <div className="text-muted-foreground">Created</div>
              </div>
              <div>
                <div className="font-medium text-blue-600">{importJob.updated_count}</div>
                <div className="text-muted-foreground">Updated</div>
              </div>
              <div>
                <div className="font-medium text-yellow-600">{importJob.skipped_count}</div>
                <div className="text-muted-foreground">Skipped</div>
              </div>
              <div>
                <div className="font-medium text-red-600">{importJob.error_count}</div>
                <div className="text-muted-foreground">Errors</div>
              </div>
            </div>
          </div>
        )}

        {/* Complete Step */}
        {step === 'complete' && importJob && (
          <div className="space-y-4 py-8 text-center">
            <CheckCircle2 className="h-16 w-16 mx-auto text-green-500" />
            <p className="text-xl font-medium">Import Complete</p>

            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-2xl font-bold text-green-600">{importJob.created_count}</div>
                <div className="text-muted-foreground">Created</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-600">{importJob.updated_count}</div>
                <div className="text-muted-foreground">Updated</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-yellow-600">{importJob.skipped_count}</div>
                <div className="text-muted-foreground">Skipped</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600">{importJob.error_count}</div>
                <div className="text-muted-foreground">Errors</div>
              </div>
            </div>

            {importJob.errors.length > 0 && (
              <div className="text-left mt-4 p-4 bg-red-50 rounded-md max-h-[200px] overflow-y-auto">
                <p className="font-medium text-red-700 mb-2">Errors:</p>
                {importJob.errors.slice(0, 10).map((err, i) => (
                  <p key={i} className="text-sm text-red-600">
                    Row {err.row}: {err.error}
                  </p>
                ))}
                {importJob.errors.length > 10 && (
                  <p className="text-sm text-red-600 mt-2">
                    ...and {importJob.errors.length - 10} more errors
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-md">
            <XCircle className="h-5 w-5" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        <DialogFooter>
          {step === 'upload' && (
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
          )}
          {step === 'mapping' && (
            <>
              <Button variant="outline" onClick={() => setStep('upload')}>
                Back
              </Button>
              <Button onClick={handleStartImport} disabled={startMutation.isPending}>
                {startMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Starting...
                  </>
                ) : (
                  'Start Import'
                )}
              </Button>
            </>
          )}
          {(step === 'progress' || step === 'complete') && (
            <Button onClick={handleClose}>
              {step === 'complete' ? 'Done' : 'Close'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
