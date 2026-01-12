from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone
from django.db.models import Q

from apps.contacts.models import (
    Contact,
    ScoringRule,
    ScoreHistory,
    ScoreThreshold,
    ScoreDecayConfig,
)


@dataclass
class ScoringResult:
    """Result of a scoring operation."""
    success: bool
    contact_id: str
    previous_score: int
    new_score: int
    score_change: int
    rules_applied: List[str]
    message: str


class ScoringEngine:
    """Engine for applying scoring rules to contacts."""

    def __init__(self, workspace):
        self.workspace = workspace

    def apply_event(
        self,
        contact: Contact,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> ScoringResult:
        """Apply scoring rules for an event on a contact."""
        event_data = event_data or {}
        rules_applied = []
        total_change = 0
        previous_score = contact.score

        # Get active rules for this event type
        rules = ScoringRule.objects.filter(
            workspace=self.workspace,
            event_type=event_type,
            is_active=True
        ).order_by('-priority')

        for rule in rules:
            # Check if rule conditions are met
            if not self._check_conditions(rule, event_data):
                continue

            # Check cooldown
            if rule.cooldown_hours and not self._check_cooldown(contact, rule):
                continue

            # Check max applications
            if rule.max_applications and not self._check_max_applications(contact, rule):
                continue

            # Apply the rule
            total_change += rule.score_change
            rules_applied.append(rule.name)

            # Record history
            ScoreHistory.objects.create(
                contact=contact,
                previous_score=contact.score,
                new_score=contact.score + rule.score_change,
                score_change=rule.score_change,
                reason=f"Rule: {rule.name}",
                rule=rule,
                event_type=event_type,
                event_data=event_data
            )

            # Update contact score
            contact.score += rule.score_change

        if total_change != 0:
            contact.score_updated_at = timezone.now()
            contact.save(update_fields=['score', 'score_updated_at'])

        return ScoringResult(
            success=True,
            contact_id=str(contact.id),
            previous_score=previous_score,
            new_score=contact.score,
            score_change=total_change,
            rules_applied=rules_applied,
            message=f"Applied {len(rules_applied)} rules, score changed by {total_change:+d}"
        )

    def _check_conditions(self, rule: ScoringRule, event_data: Dict[str, Any]) -> bool:
        """Check if rule conditions are met."""
        conditions = rule.conditions
        if not conditions:
            return True

        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')

            if field not in event_data:
                if operator == 'is_not_set':
                    continue
                elif operator == 'is_set':
                    return False
                else:
                    return False

            field_value = event_data.get(field)

            if operator == 'equals':
                if str(field_value) != str(value):
                    return False
            elif operator == 'not_equals':
                if str(field_value) == str(value):
                    return False
            elif operator == 'contains':
                if str(value).lower() not in str(field_value).lower():
                    return False
            elif operator == 'not_contains':
                if str(value).lower() in str(field_value).lower():
                    return False
            elif operator == 'greater_than':
                try:
                    if float(field_value) <= float(value):
                        return False
                except (ValueError, TypeError):
                    return False
            elif operator == 'less_than':
                try:
                    if float(field_value) >= float(value):
                        return False
                except (ValueError, TypeError):
                    return False
            elif operator == 'is_set':
                if field_value is None or field_value == '':
                    return False
            elif operator == 'is_not_set':
                if field_value is not None and field_value != '':
                    return False

        return True

    def _check_cooldown(self, contact: Contact, rule: ScoringRule) -> bool:
        """Check if rule is still in cooldown period for this contact."""
        if not rule.cooldown_hours:
            return True

        cutoff = timezone.now() - timedelta(hours=rule.cooldown_hours)
        recent_application = ScoreHistory.objects.filter(
            contact=contact,
            rule=rule,
            created_at__gte=cutoff
        ).exists()

        return not recent_application

    def _check_max_applications(self, contact: Contact, rule: ScoringRule) -> bool:
        """Check if rule has reached max applications for this contact."""
        if not rule.max_applications:
            return True

        application_count = ScoreHistory.objects.filter(
            contact=contact,
            rule=rule
        ).count()

        return application_count < rule.max_applications

    def set_score(
        self,
        contact: Contact,
        new_score: int,
        reason: str = "Manual adjustment"
    ) -> ScoringResult:
        """Manually set a contact's score."""
        previous_score = contact.score
        score_change = new_score - previous_score

        # Record history
        ScoreHistory.objects.create(
            contact=contact,
            previous_score=previous_score,
            new_score=new_score,
            score_change=score_change,
            reason=reason,
            event_type='manual'
        )

        # Update contact
        contact.score = new_score
        contact.score_updated_at = timezone.now()
        contact.save(update_fields=['score', 'score_updated_at'])

        return ScoringResult(
            success=True,
            contact_id=str(contact.id),
            previous_score=previous_score,
            new_score=new_score,
            score_change=score_change,
            rules_applied=[],
            message=f"Score manually set to {new_score}"
        )

    def adjust_score(
        self,
        contact: Contact,
        adjustment: int,
        reason: str = "Manual adjustment"
    ) -> ScoringResult:
        """Adjust a contact's score by a given amount."""
        return self.set_score(contact, contact.score + adjustment, reason)

    def get_classification(self, contact: Contact) -> Optional[str]:
        """Get the classification (hot/warm/cold) for a contact based on thresholds."""
        thresholds = ScoreThreshold.objects.filter(
            workspace=self.workspace
        ).order_by('-min_score')

        for threshold in thresholds:
            if contact.score >= threshold.min_score:
                if threshold.max_score is None or contact.score <= threshold.max_score:
                    return threshold.classification

        return None

    def get_hot_leads(self, limit: int = 50) -> List[Contact]:
        """Get hot leads (contacts above hot threshold)."""
        try:
            hot_threshold = ScoreThreshold.objects.get(
                workspace=self.workspace,
                classification=ScoreThreshold.Classification.HOT
            )
            return Contact.objects.filter(
                workspace=self.workspace,
                status=Contact.Status.ACTIVE,
                score__gte=hot_threshold.min_score
            ).order_by('-score')[:limit]
        except ScoreThreshold.DoesNotExist:
            # Default: top 50 by score
            return Contact.objects.filter(
                workspace=self.workspace,
                status=Contact.Status.ACTIVE
            ).order_by('-score')[:limit]

    def run_score_decay(self) -> Dict[str, Any]:
        """Run score decay for inactive contacts."""
        try:
            config = ScoreDecayConfig.objects.get(workspace=self.workspace)
        except ScoreDecayConfig.DoesNotExist:
            return {'success': False, 'message': 'No decay config found'}

        if not config.is_enabled:
            return {'success': False, 'message': 'Decay is disabled'}

        # Check if we should run
        if config.last_run_at:
            next_run = config.last_run_at + timedelta(days=config.decay_interval_days)
            if timezone.now() < next_run:
                return {'success': False, 'message': 'Not yet time to run decay'}

        # Find inactive contacts above minimum score
        inactivity_cutoff = timezone.now() - timedelta(days=config.inactivity_days)
        inactive_contacts = Contact.objects.filter(
            workspace=self.workspace,
            status=Contact.Status.ACTIVE,
            score__gt=config.min_score
        ).filter(
            Q(last_emailed_at__lt=inactivity_cutoff) | Q(last_emailed_at__isnull=True),
            Q(last_opened_at__lt=inactivity_cutoff) | Q(last_opened_at__isnull=True),
            Q(last_clicked_at__lt=inactivity_cutoff) | Q(last_clicked_at__isnull=True),
            Q(last_replied_at__lt=inactivity_cutoff) | Q(last_replied_at__isnull=True),
        )

        decayed_count = 0
        for contact in inactive_contacts:
            new_score = max(contact.score - config.decay_points, config.min_score)
            if new_score != contact.score:
                ScoreHistory.objects.create(
                    contact=contact,
                    previous_score=contact.score,
                    new_score=new_score,
                    score_change=new_score - contact.score,
                    reason="Automatic score decay",
                    event_type='decay'
                )
                contact.score = new_score
                contact.score_updated_at = timezone.now()
                contact.save(update_fields=['score', 'score_updated_at'])
                decayed_count += 1

        # Update last run
        config.last_run_at = timezone.now()
        config.save(update_fields=['last_run_at'])

        return {
            'success': True,
            'decayed_count': decayed_count,
            'decay_points': config.decay_points
        }

    def get_score_stats(self) -> Dict[str, Any]:
        """Get scoring statistics for the workspace."""
        contacts = Contact.objects.filter(
            workspace=self.workspace,
            status=Contact.Status.ACTIVE
        )

        total = contacts.count()
        if total == 0:
            return {
                'total_contacts': 0,
                'average_score': 0,
                'hot_count': 0,
                'warm_count': 0,
                'cold_count': 0
            }

        from django.db.models import Avg
        avg_score = contacts.aggregate(avg=Avg('score'))['avg'] or 0

        # Get counts by classification
        thresholds = {
            t.classification: t.min_score
            for t in ScoreThreshold.objects.filter(workspace=self.workspace)
        }

        hot_min = thresholds.get('hot', 70)
        warm_min = thresholds.get('warm', 40)

        hot_count = contacts.filter(score__gte=hot_min).count()
        warm_count = contacts.filter(score__gte=warm_min, score__lt=hot_min).count()
        cold_count = contacts.filter(score__lt=warm_min).count()

        return {
            'total_contacts': total,
            'average_score': round(avg_score, 1),
            'hot_count': hot_count,
            'warm_count': warm_count,
            'cold_count': cold_count,
            'hot_percentage': round((hot_count / total) * 100, 1),
            'warm_percentage': round((warm_count / total) * 100, 1),
            'cold_percentage': round((cold_count / total) * 100, 1)
        }
