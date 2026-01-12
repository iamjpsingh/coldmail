import { MoreVertical, Mail, Building2, Briefcase, MapPin, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useDeleteContact } from '@/hooks/use-contacts';
import type { Contact } from '@/types/contact';

interface ContactsTableProps {
  contacts: Contact[];
  selectedContacts: string[];
  onSelectionChange: (selected: string[]) => void;
}

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  unsubscribed: 'bg-yellow-100 text-yellow-800',
  bounced: 'bg-red-100 text-red-800',
  complained: 'bg-red-100 text-red-800',
};

export function ContactsTable({ contacts, selectedContacts, onSelectionChange }: ContactsTableProps) {
  const deleteMutation = useDeleteContact();

  const toggleAll = () => {
    if (selectedContacts.length === contacts.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(contacts.map((c) => c.id));
    }
  };

  const toggleOne = (id: string) => {
    if (selectedContacts.includes(id)) {
      onSelectionChange(selectedContacts.filter((i) => i !== id));
    } else {
      onSelectionChange([...selectedContacts, id]);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this contact?')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  return (
    <div className="rounded-md border">
      <table className="w-full">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="w-12 px-4 py-3 text-left">
              <input
                type="checkbox"
                checked={selectedContacts.length === contacts.length && contacts.length > 0}
                onChange={toggleAll}
                className="rounded border-gray-300"
              />
            </th>
            <th className="px-4 py-3 text-left text-sm font-medium">Contact</th>
            <th className="px-4 py-3 text-left text-sm font-medium">Company</th>
            <th className="px-4 py-3 text-left text-sm font-medium">Location</th>
            <th className="px-4 py-3 text-left text-sm font-medium">Score</th>
            <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
            <th className="px-4 py-3 text-left text-sm font-medium">Engagement</th>
            <th className="w-12 px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          {contacts.map((contact) => (
            <tr key={contact.id} className="border-b hover:bg-muted/50">
              <td className="px-4 py-3">
                <input
                  type="checkbox"
                  checked={selectedContacts.includes(contact.id)}
                  onChange={() => toggleOne(contact.id)}
                  className="rounded border-gray-300"
                />
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-col">
                  <span className="font-medium">
                    {contact.full_name}
                  </span>
                  <span className="text-sm text-muted-foreground flex items-center gap-1">
                    <Mail className="h-3 w-3" />
                    {contact.email}
                  </span>
                </div>
              </td>
              <td className="px-4 py-3">
                {contact.company && (
                  <div className="flex flex-col">
                    <span className="flex items-center gap-1">
                      <Building2 className="h-3 w-3 text-muted-foreground" />
                      {contact.company}
                    </span>
                    {contact.job_title && (
                      <span className="text-sm text-muted-foreground flex items-center gap-1">
                        <Briefcase className="h-3 w-3" />
                        {contact.job_title}
                      </span>
                    )}
                  </div>
                )}
              </td>
              <td className="px-4 py-3">
                {(contact.city || contact.country) && (
                  <span className="flex items-center gap-1 text-sm text-muted-foreground">
                    <MapPin className="h-3 w-3" />
                    {[contact.city, contact.country].filter(Boolean).join(', ')}
                  </span>
                )}
              </td>
              <td className="px-4 py-3">
                <span className={`text-sm font-medium ${
                  contact.score >= 70 ? 'text-green-600' :
                  contact.score >= 40 ? 'text-yellow-600' :
                  'text-gray-600'
                }`}>
                  {contact.score}
                </span>
              </td>
              <td className="px-4 py-3">
                <Badge className={statusColors[contact.status]}>
                  {contact.status}
                </Badge>
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-4 text-sm">
                  <div className="flex flex-col items-center">
                    <span className="font-medium">{contact.emails_sent}</span>
                    <span className="text-xs text-muted-foreground">sent</span>
                  </div>
                  <div className="flex flex-col items-center">
                    <span className="font-medium">{contact.open_rate}%</span>
                    <span className="text-xs text-muted-foreground">open</span>
                  </div>
                  <div className="flex flex-col items-center">
                    <span className="font-medium">{contact.click_rate}%</span>
                    <span className="text-xs text-muted-foreground">click</span>
                  </div>
                </div>
              </td>
              <td className="px-4 py-3">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>View Details</DropdownMenuItem>
                    <DropdownMenuItem>Edit</DropdownMenuItem>
                    <DropdownMenuItem>Add to List</DropdownMenuItem>
                    <DropdownMenuItem>Add Tags</DropdownMenuItem>
                    <DropdownMenuSeparator />
                    {contact.linkedin_url && (
                      <DropdownMenuItem asChild>
                        <a href={contact.linkedin_url} target="_blank" rel="noopener noreferrer">
                          <ExternalLink className="h-4 w-4 mr-2" />
                          LinkedIn
                        </a>
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      className="text-destructive focus:text-destructive"
                      onClick={() => handleDelete(contact.id)}
                    >
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
