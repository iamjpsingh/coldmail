from django.urls import path

from apps.tracking.views import (
    track_open,
    track_click,
    unsubscribe,
    one_click_unsubscribe,
)

urlpatterns = [
    # Open tracking pixel
    path('o/<str:token>.gif', track_open, name='track-open'),
    # Click tracking redirect
    path('c/<str:token>', track_click, name='track-click'),
    # Unsubscribe
    path('u/<str:token>', unsubscribe, name='unsubscribe'),
    path('u/<str:token>/one-click', one_click_unsubscribe, name='one-click-unsubscribe'),
]
