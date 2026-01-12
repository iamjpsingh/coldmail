from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TagViewSet,
    ContactViewSet,
    ContactListViewSet,
    CustomFieldViewSet,
    ImportJobViewSet,
    ScoringRuleViewSet,
    ScoreThresholdViewSet,
    ScoreDecayConfigViewSet,
    ScoringViewSet,
)

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'lists', ContactListViewSet, basename='contact-list')
router.register(r'custom-fields', CustomFieldViewSet, basename='custom-field')
router.register(r'imports', ImportJobViewSet, basename='import-job')
router.register(r'scoring/rules', ScoringRuleViewSet, basename='scoring-rule')
router.register(r'scoring/thresholds', ScoreThresholdViewSet, basename='score-threshold')
router.register(r'scoring/decay-config', ScoreDecayConfigViewSet, basename='score-decay-config')
router.register(r'scoring', ScoringViewSet, basename='scoring')
router.register(r'', ContactViewSet, basename='contact')

urlpatterns = [
    path('', include(router.urls)),
]
