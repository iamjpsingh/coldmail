from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EmailSignatureViewSet,
    EmailTemplateViewSet,
    TemplateFolderViewSet,
    SnippetLibraryViewSet,
    CampaignViewSet,
)

router = DefaultRouter()
router.register(r'signatures', EmailSignatureViewSet, basename='signature')
router.register(r'templates', EmailTemplateViewSet, basename='template')
router.register(r'folders', TemplateFolderViewSet, basename='folder')
router.register(r'snippets', SnippetLibraryViewSet, basename='snippet')
router.register(r'campaigns', CampaignViewSet, basename='campaign')

urlpatterns = [
    path('', include(router.urls)),
]
