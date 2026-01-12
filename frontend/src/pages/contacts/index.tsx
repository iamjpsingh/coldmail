import { useState } from 'react';
import { Plus, Search, Upload, Download, Users, Tags, List, Loader2, AlertCircle, Trash2, RefreshCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { StatCard, StatGrid } from '@/components/ui/stat-card';
import { EmptyStateCard } from '@/components/ui/empty-state';
import { useContacts, useTags, useContactLists, useBulkDeleteContacts } from '@/hooks/use-contacts';
import { ContactsTable } from './components/contacts-table';
import { AddContactDialog } from './components/add-contact-dialog';
import { ImportContactsDialog } from './components/import-contacts-dialog';
import type { Contact } from '@/types/contact';
import { useQueryClient } from '@tanstack/react-query';

export default function ContactsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: contacts, isLoading, error, refetch, isRefetching } = useContacts();
  const { data: tags } = useTags();
  const { data: lists } = useContactLists();
  const bulkDeleteMutation = useBulkDeleteContacts();

  const filteredContacts = contacts?.filter((contact: Contact) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      contact.email.toLowerCase().includes(query) ||
      contact.first_name.toLowerCase().includes(query) ||
      contact.last_name.toLowerCase().includes(query) ||
      contact.company.toLowerCase().includes(query) ||
      contact.job_title.toLowerCase().includes(query)
    );
  });

  const handleBulkDelete = async () => {
    if (selectedContacts.length === 0) return;
    if (!window.confirm(`Are you sure you want to delete ${selectedContacts.length} contacts?`)) return;

    await bulkDeleteMutation.mutateAsync(selectedContacts);
    setSelectedContacts([]);
  };

  const getStatusCounts = () => {
    if (!contacts) return { active: 0, unsubscribed: 0, bounced: 0, total: 0 };
    return {
      active: contacts.filter((c: Contact) => c.status === 'active').length,
      unsubscribed: contacts.filter((c: Contact) => c.status === 'unsubscribed').length,
      bounced: contacts.filter((c: Contact) => c.status === 'bounced').length,
      total: contacts.length,
    };
  };

  const counts = getStatusCounts();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Contacts</h1>
            <p className="text-muted-foreground">Manage your contacts and contact lists</p>
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
            <h1 className="text-3xl font-bold tracking-tight">Contacts</h1>
            <p className="text-muted-foreground">Manage your contacts and contact lists</p>
          </div>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="rounded-full bg-destructive/10 p-4 mb-4">
              <AlertCircle className="h-8 w-8 text-destructive" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Unable to Load Contacts</h3>
            <p className="text-muted-foreground text-center max-w-md mb-6">
              We couldn't fetch your contacts. This might be due to a connection issue or the server being unavailable.
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
          <h1 className="text-3xl font-bold tracking-tight">Contacts</h1>
          <p className="text-muted-foreground">
            Manage your contacts and contact lists
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setIsImportDialogOpen(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Import
          </Button>
          <Button onClick={() => setIsAddDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Contact
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <StatGrid columns={4}>
        <StatCard
          label="Total Contacts"
          value={counts.total}
          icon={Users}
          variant="primary"
        />
        <StatCard
          label="Active"
          value={counts.active}
          icon={Users}
          variant="success"
        />
        <StatCard
          label="Tags"
          value={tags?.length || 0}
          icon={Tags}
        />
        <StatCard
          label="Lists"
          value={lists?.length || 0}
          icon={List}
        />
      </StatGrid>

      {/* Search and Actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search contacts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          {selectedContacts.length > 0 && (
            <>
              <Badge variant="secondary">{selectedContacts.length} selected</Badge>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleBulkDelete}
                disabled={bulkDeleteMutation.isPending}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </>
          )}
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Contacts Table */}
      {filteredContacts && filteredContacts.length > 0 ? (
        <ContactsTable
          contacts={filteredContacts}
          selectedContacts={selectedContacts}
          onSelectionChange={setSelectedContacts}
        />
      ) : (
        <EmptyStateCard
          icon={Users}
          title="No contacts yet"
          description="Add contacts manually or import from a file to get started."
          action={
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setIsImportDialogOpen(true)}>
                <Upload className="h-4 w-4 mr-2" />
                Import
              </Button>
              <Button onClick={() => setIsAddDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Contact
              </Button>
            </div>
          }
        />
      )}

      {/* Dialogs */}
      <AddContactDialog
        open={isAddDialogOpen}
        onOpenChange={setIsAddDialogOpen}
      />
      <ImportContactsDialog
        open={isImportDialogOpen}
        onOpenChange={setIsImportDialogOpen}
      />
    </div>
  );
}
