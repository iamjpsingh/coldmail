from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.sequences.views import (
    SequenceViewSet, SequenceStepViewSet, SequenceEnrollmentViewSet
)

# Main router
router = DefaultRouter()
router.register(r'sequences', SequenceViewSet, basename='sequence')
router.register(r'enrollments', SequenceEnrollmentViewSet, basename='enrollment')

# Steps router (will use query params for sequence filtering)
steps_router = DefaultRouter()
steps_router.register(r'sequence-steps', SequenceStepViewSet, basename='sequence-steps')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(steps_router.urls)),
]
