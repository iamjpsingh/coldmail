from django.urls import path

from apps.core.views import (
    dashboard_stats,
    email_stats_over_time,
    campaign_report,
    campaigns_comparison,
    activity_timeline,
    hot_leads_report,
    score_distribution,
    performance_summary,
    export_campaign_report,
    export_contacts,
    export_hot_leads,
)

urlpatterns = [
    # Dashboard
    path('dashboard/', dashboard_stats, name='dashboard-stats'),
    path('email-stats/', email_stats_over_time, name='email-stats'),
    path('performance/', performance_summary, name='performance-summary'),

    # Activity
    path('activity/', activity_timeline, name='activity-timeline'),

    # Campaign reports
    path('campaigns/<str:campaign_id>/', campaign_report, name='campaign-report'),
    path('campaigns/<str:campaign_id>/export/', export_campaign_report, name='campaign-report-export'),
    path('campaigns/compare/', campaigns_comparison, name='campaigns-comparison'),

    # Hot leads
    path('hot-leads/', hot_leads_report, name='hot-leads-report'),
    path('hot-leads/export/', export_hot_leads, name='hot-leads-export'),

    # Score distribution
    path('score-distribution/', score_distribution, name='score-distribution'),

    # Exports
    path('contacts/export/', export_contacts, name='contacts-export'),
]
