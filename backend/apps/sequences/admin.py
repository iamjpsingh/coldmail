from django.contrib import admin

from apps.sequences.models import (
    Sequence, SequenceStep, SequenceEnrollment,
    SequenceStepExecution, SequenceEvent
)


class SequenceStepInline(admin.TabularInline):
    model = SequenceStep
    extra = 0
    ordering = ['order']
    fields = ['order', 'step_type', 'name', 'delay_value', 'delay_unit', 'is_active']


@admin.register(Sequence)
class SequenceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'status', 'total_enrolled', 'active_enrolled',
        'total_sent', 'total_opened', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = [
        'total_enrolled', 'active_enrolled', 'completed_count', 'stopped_count',
        'total_sent', 'total_opened', 'total_clicked', 'total_replied',
        'created_at', 'updated_at'
    ]
    inlines = [SequenceStepInline]


@admin.register(SequenceStep)
class SequenceStepAdmin(admin.ModelAdmin):
    list_display = ['sequence', 'order', 'step_type', 'name', 'is_active', 'sent_count']
    list_filter = ['step_type', 'is_active']
    search_fields = ['sequence__name', 'name', 'subject']


@admin.register(SequenceEnrollment)
class SequenceEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'contact', 'sequence', 'status', 'current_step_index',
        'emails_sent', 'enrolled_at'
    ]
    list_filter = ['status', 'enrollment_source', 'enrolled_at']
    search_fields = ['contact__email', 'sequence__name']
    readonly_fields = [
        'emails_sent', 'emails_opened', 'emails_clicked', 'has_replied',
        'enrolled_at', 'started_at', 'completed_at', 'stopped_at'
    ]


@admin.register(SequenceStepExecution)
class SequenceStepExecutionAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'step', 'status', 'scheduled_at', 'sent_at']
    list_filter = ['status', 'scheduled_at']
    search_fields = ['enrollment__contact__email']


@admin.register(SequenceEvent)
class SequenceEventAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'event_type', 'step', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['enrollment__contact__email', 'message']
