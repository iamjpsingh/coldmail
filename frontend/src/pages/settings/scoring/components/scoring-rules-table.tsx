import { MoreHorizontal, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToggleScoringRule, useDeleteScoringRule } from '@/hooks/use-contacts';
import type { ScoringRule } from '@/types/contact';

interface ScoringRulesTableProps {
  rules: ScoringRule[];
}

const eventTypeLabels: Record<string, string> = {
  email_opened: 'Email Opened',
  email_clicked: 'Email Clicked',
  email_replied: 'Email Replied',
  email_bounced: 'Email Bounced',
  email_unsubscribed: 'Email Unsubscribed',
  link_clicked: 'Link Clicked',
  form_submitted: 'Form Submitted',
  page_visited: 'Page Visited',
  meeting_scheduled: 'Meeting Scheduled',
  manual: 'Manual',
  decay: 'Decay',
  import: 'Import',
};

export function ScoringRulesTable({ rules }: ScoringRulesTableProps) {
  const toggleMutation = useToggleScoringRule();
  const deleteMutation = useDeleteScoringRule();

  const handleToggle = async (id: string) => {
    await toggleMutation.mutateAsync(id);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this rule?')) return;
    await deleteMutation.mutateAsync(id);
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Event Type</TableHead>
          <TableHead>Score Change</TableHead>
          <TableHead>Applications</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="w-[50px]"></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rules.map((rule) => (
          <TableRow key={rule.id}>
            <TableCell>
              <div>
                <div className="font-medium">{rule.name}</div>
                {rule.description && (
                  <div className="text-sm text-muted-foreground">{rule.description}</div>
                )}
              </div>
            </TableCell>
            <TableCell>
              <Badge variant="outline">
                {eventTypeLabels[rule.event_type] || rule.event_type}
              </Badge>
            </TableCell>
            <TableCell>
              <span className={rule.score_change >= 0 ? 'text-green-600' : 'text-red-600'}>
                {rule.score_change >= 0 ? '+' : ''}{rule.score_change}
              </span>
            </TableCell>
            <TableCell>
              {rule.applications_count}
              {rule.max_applications && ` / ${rule.max_applications}`}
            </TableCell>
            <TableCell>
              <Badge variant={rule.is_active ? 'default' : 'secondary'}>
                {rule.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => handleToggle(rule.id)}>
                    {rule.is_active ? (
                      <>
                        <ToggleLeft className="h-4 w-4 mr-2" />
                        Disable
                      </>
                    ) : (
                      <>
                        <ToggleRight className="h-4 w-4 mr-2" />
                        Enable
                      </>
                    )}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleDelete(rule.id)} className="text-destructive">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
